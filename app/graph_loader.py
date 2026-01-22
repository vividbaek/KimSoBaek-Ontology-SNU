import os
import rdflib
from rdflib import Graph, Namespace, Literal

# Namespaces
CURR = Namespace("http://example.org/curriculum/")
RDFS = rdflib.RDFS
RDF = rdflib.RDF

class GraphLoader:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(GraphLoader, cls).__new__(cls)
            cls._instance.g = Graph()
            cls._instance.loaded = False
        return cls._instance

    def load_graph(self):
        if self.loaded:
            return self.g
            
        print("Loading RDF Data...")
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        ttl_path = os.path.join(base_dir, 'data/ontology/knowledge_graph.ttl')
        schema_path = os.path.join(base_dir, 'data/ontology/schema.ttl')
        
        try:
            self.g.parse(ttl_path, format="turtle")
            print(f"Loaded {len(self.g)} triples from {ttl_path}")
            
            # Load Schema for context if needed (optional for query execution, but good for LLM context)
            self.g.parse(schema_path, format="turtle")
            self.g.bind("curr", CURR)
            self.loaded = True
        except Exception as e:
            print(f"Error loading graph: {e}")
            raise e
            
        return self.g

    def get_graph(self):
        if not self.loaded:
            return self.load_graph()
        return self.g

    def get_schema_info(self):
        """
        Returns schema information (classes, properties) to help LLM generate SPARQL.
        """
        # Hardcoded High-level summary for Prompt Context
        return """
        Prefix: curr: <http://example.org/curriculum/>
        Classes: curr:Subject, curr:JBNUSubject, curr:COSSSubject, curr:Track, curr:Competency
        Properties:
          - curr:hasTitle (string)
          - curr:hasSemester (string)
          - curr:hasPrerequisite (Subject -> Subject)
          - curr:teaches (Subject -> Competency)
          - curr:requiredBy (Competency -> Track)
          - curr:offeredInSource (string: 'JBNU' or 'COSS')
          - curr:hasDomain (string: '인공지능', '데이터사이언스' etc)
        """

# Singleton Accessor
graph_loader = GraphLoader()
