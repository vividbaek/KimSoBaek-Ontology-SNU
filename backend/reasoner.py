from rdflib import Graph, Namespace, URIRef
import os

CURR = Namespace("http://example.org/curriculum/")

class Reasoner:
    def __init__(self):
        self.g = Graph()
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.ttl_path = os.path.join(base_dir, 'data/ontology/knowledge_graph.ttl')
        self.schema_path = os.path.join(base_dir, 'data/ontology/schema.ttl')
        
        # Load Data
        self.g.parse(self.ttl_path, format="turtle")
        # Ensure schema is loaded for reasoning (if we use RDFS reasoning later)
        # self.g.parse(self.schema_path, format="turtle")
        self.g.bind("curr", CURR)

    def recommend_roadmap(self, track_name: str) -> list:
        """
        Backtracking: Find Track -> Competencies -> Subjects -> Prerequisites
        """
        # Note: In our simple ETL, we didn't explicitly link Tracks to Competencies in the TTL yet
        # (Schema defined them, but ETL didn't populate Track instances).
        # We need to either populate them in ETL or map them here.
        # Let's map dynamically here for the MVP.
        
        target_skills = self._get_skills_for_track(track_name)
        
        # SPARQL: Find subjects that teach these skills, then find their transitive prerequisites
        # rdflib supports Property Paths.
        
        subjects = set()
        
        for skill in target_skills:
            # 1. Find Target Subjects
            query = """
            SELECT ?sub ?sem
            WHERE {
                ?sub curr:teaches ?skill .
                ?sub curr:hasSemester ?sem .
            }
            """
            # Need to find URI for skill name (fuzzy match or direct URI if known)
            # In ETL we created URIs like Competency_Machine_Learning
            
            # Simple Text Match approach in logic + precise SPARQL
            # But let's try to query by Label
            
            q_label = """
            SELECT ?sub ?sem ?title
            WHERE {
                ?skill a curr:Competency ;
                       rdfs:label ?skillLabel .
                FILTER(CONTAINS(LCASE(?skillLabel), LCASE(?target)))
                ?sub curr:teaches ?skill .
                ?sub curr:hasTitle ?title .
                ?sub curr:hasSemester ?sem .
            }
            """
            
            res = self.g.query(q_label, initBindings={'target': Literal(skill)})
            
            for row in res:
                sub_uri = row.sub
                subjects.add((str(sub_uri), str(row.sem), str(row.title)))
                
                # 2. Transitive Prerequisites
                q_prereq = """
                SELECT ?pre ?sem ?title
                WHERE {
                    ?target curr:hasPrerequisite+ ?pre .
                    ?pre curr:hasTitle ?title .
                    ?pre curr:hasSemester ?sem .
                }
                """
                res_pre = self.g.query(q_prereq, initBindings={'target': sub_uri})
                for row_p in res_pre:
                    subjects.add((str(row_p.pre), str(row_p.sem), str(row_p.title)))

        # Convert to list of dicts for API
        result = []
        for s_uri, sem, title in subjects:
            result.append({
                "ID": s_uri.split('/')[-1], # Extract ID from URI
                "Title": title,
                "Semester": sem,
                # "URI": s_uri
            })
            
        # Sort
        result.sort(key=lambda x: self._semester_sort_key(x['Semester']))
        return result

    def recommend_forward(self, subject_title: str) -> list:
        """
        Forward Chaining: Subject -> Next Subjects (Successors)
        """
        query = """
        SELECT ?next ?sem ?title
        WHERE {
            ?subject curr:hasTitle ?targetTitle .
            ?next curr:hasPrerequisite+ ?subject . 
            ?next curr:hasTitle ?title .
            ?next curr:hasSemester ?sem .
        }
        """
        # Note: ?next hasPrerequisite ?subject means ?subject is a prerequisite of ?next.
        # So ?next is the successor.
        
        res = self.g.query(query, initBindings={'targetTitle': Literal(subject_title)})
        
        result = []
        for row in res:
            result.append({
                "ID": str(row.next).split('/')[-1],
                "Title": str(row.title),
                "Semester": str(row.sem)
            })
            
        result.sort(key=lambda x: self._semester_sort_key(x['Semester']))
        return result

    def _get_skills_for_track(self, track: str):
        # Hardcoded Mapping for MVP (Should be in Ontology later)
        if "AI" in track:
            return ["Machine Learning", "Deep Learning", "Python"]
        elif "데이터" in track:
            return ["Database", "Big Data", "SQL"]
        elif "백엔드" in track:
            return ["Server", "Database", "Java"]
        else:
            return []

    def _semester_sort_key(self, sem):
        if sem == "Unknown" or sem == "Any": return 100
        parts = sem.split("-")
        if len(parts) == 2:
            try:
                return int(parts[0]) * 10 + int(parts[1])
            except:
                pass
        return 999

    def find_subject_in_text(self, text: str) -> str:
        """
        Scans all subject titles in the graph and returns the one that appears in the text.
        Returns the longest match if multiple are found.
        """
        q = """
        SELECT ?title WHERE {
            ?s curr:hasTitle ?title .
        }
        """
        matches = []
        for row in self.g.query(q):
            title = str(row.title)
            # Remove spaces for robust matching
            clean_title = title.replace(" ", "")
            clean_text = text.replace(" ", "")
            
            if clean_title in clean_text or title in text:
                matches.append(title)
        
        if not matches:
            return None
            
        # Return longest title (e.g. prefer "Deep Learning" over "Learning" if both existed)
        matches.sort(key=len, reverse=True)
        return matches[0]
        
from rdflib import Literal
