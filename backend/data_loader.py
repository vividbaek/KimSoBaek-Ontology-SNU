from rdflib import Graph, Namespace, RDF, RDFS
import os
from backend.models import Node, Edge, Subject

CURR = Namespace("http://example.org/curriculum/")

class DataLoader:
    def __init__(self):
        self.nodes = []
        self.edges = []
        self.subjects = {}
        self.graph = Graph()
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.ttl_path = os.path.join(base_dir, 'data/ontology/knowledge_graph.ttl')

    def load_data(self):
        print("Loading RDF Data...")
        self.graph.parse(self.ttl_path, format="turtle")
        
        # 1. Parse Nodes
        for s in self.graph.subjects(RDF.type, None):
            # Check if it's a subject
            if (s, RDF.type, CURR.JBNUSubject) in self.graph or (s, RDF.type, CURR.COSSSubject) in self.graph:
                sid = s.split('/')[-1]
                title = str(self.graph.value(s, CURR.hasTitle))
                sem = str(self.graph.value(s, CURR.hasSemester))
                
                # Domain
                domain = self.graph.value(s, CURR.hasDomain)
                if domain:
                    domain = str(domain)
                else:
                    domain = "General"

                # Concepts
                concepts = []
                for c in self.graph.objects(s, CURR.teaches):
                    c_label = self.graph.value(c, RDFS.label)
                    if c_label:
                        concepts.append(str(c_label))

                stype = "JBNU" if (s, RDF.type, CURR.JBNUSubject) in self.graph else "COSS"
                
                self.nodes.append(Node(
                    id=sid,
                    label=title,
                    type=stype,
                    semester=sem,
                    concepts=concepts,
                    domain=domain
                ))
                self.subjects[sid] = Subject(ID=sid, Title=title, Semester=sem, Domain=domain)

        # 2. Parse Edges
        # Prerequisite
        for s, o in self.graph.subject_objects(CURR.hasPrerequisite):
            src = str(o).split('/')[-1] # Prereq is Source
            tgt = str(s).split('/')[-1] # Target requires Source
            self.edges.append(Edge(source=src, target=tgt, type="prerequisite"))
        
        # SameAs (Equivalent)
        for s, o in self.graph.subject_objects(CURR.equivalentTo):
            src = str(s).split('/')[-1]
            tgt = str(o).split('/')[-1]
            # Avoid duplicates if possible, specific logic needed?
            # RDF graph has symmetric property usually, so we might get both directions.
            # Let's just add them, Cytoscape handles it or we dedupe.
            self.edges.append(Edge(source=src, target=tgt, type="sameAs"))
            
        print(f"Loaded {len(self.nodes)} nodes and {len(self.edges)} edges.")
