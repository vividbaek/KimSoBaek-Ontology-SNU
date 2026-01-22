import sys
from rdflib import Graph, Namespace, RDF, RDFS, OWL

def verify_ontology():
    print("Loading ontology files...")
    g = Graph()
    
    # Load Schema
    try:
        g.parse("data/ontology/schema.ttl", format="turtle")
        print("✅ schema.ttl loaded successfully.")
    except Exception as e:
        print(f"❌ Failed to load schema.ttl: {e}")
        return

    # Load Data
    try:
        g.parse("data/ontology/knowledge_graph.ttl", format="turtle")
        print("✅ knowledge_graph.ttl loaded successfully.")
    except Exception as e:
        print(f"❌ Failed to load knowledge_graph.ttl: {e}")
        return

    # Namespaces
    CURR = Namespace("http://example.org/curriculum/")
    
    # Statistics
    subjects = list(g.subjects(RDF.type, CURR.Subject)) + \
               list(g.subjects(RDF.type, CURR.JBNUSubject)) + \
               list(g.subjects(RDF.type, CURR.COSSSubject))
    # Dedup in case inference adds types or exact matches
    subjects = list(set(subjects))
    
    competencies = list(g.subjects(RDF.type, CURR.Competency))
    tracks = list(g.subjects(RDF.type, CURR.Track))

    print(f"\n📊 Statistics:")
    print(f"  - Total Subjects: {len(subjects)}")
    print(f"  - Total Competencies: {len(competencies)}") # Might be 0 if they are only inferred or just URIs without explicit type declaration in KG, checking...
    
    # Check consistency: Subjects should have titles
    print("\n🔍 Consistency Checks:")
    missing_title = 0
    for s in subjects:
        if not (s, CURR.hasTitle, None) in g:
            # print(f"  ⚠️ Subject missing title: {s}")
            missing_title += 1
    
    if missing_title == 0:
        print("  ✅ All subjects have titles.")
    else:
        print(f"  ❌ {missing_title} subjects are missing titles.")

    # Try SHACL if available
    try:
        import pyshacl
        print("\n🛡️ Running SHACL Validation...")
        conforms, results_graph, results_text = pyshacl.validate(
            data_graph=g,
            shacl_graph="data/ontology/curriculum_shacl.ttl",
            inference='rdfs',
            abort_on_first=False,
            meta_shacl=False,
            advanced=True
        )
        if conforms:
            print("  ✅ SHACL Validation Passed!")
        else:
            print("  ❌ SHACL Validation Failed!")
            print(results_text)
    except ImportError:
        print("\n⚠️ pyshacl not installed, skipping SHACL validation.")

if __name__ == "__main__":
    verify_ontology()
