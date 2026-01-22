import pyshacl
import owlrl
from rdflib import Graph, Namespace, URIRef
from rdflib.namespace import RDF, OWL
from rdflib import Literal as RdflibLiteral
import os

def run():
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    abox_path = os.path.join(base_dir, 'abox_final.ttl')
    tbox_path = os.path.join(base_dir, 'ontology', 'tbox.ttl')
    shacl_path = os.path.join(base_dir, 'ontology', 'shacl.ttl')
    
    print("Loading Graphs...")
    # Load TBox separately to know what to subtract later
    g_tbox = Graph()
    g_tbox.parse(tbox_path, format='turtle')
    
    # Load ABox
    g = Graph()
    g.parse(abox_path, format='turtle')
    
    # Merge for reasoning
    g_combined = g + g_tbox
    
    print(f"Loaded {len(g_combined)} triples (ABox + TBox).")

    # 1. SHACL Validation (on combined)
    print("Running SHACL Validation...")
    conforms, report_graph, report_text = pyshacl.validate(
        data_graph=g_combined,
        shacl_graph=shacl_path,
        inference='rdfs',
        abort_on_first=False,
        meta_shacl=False,
        debug=False
    )
    
    if conforms:
        print("SHACL Validation Passed!")
    else:
        print("SHACL Validation Failed!")
        print(report_text[:500] + "...") # Truncate log

    # 2. OWLRL Reasoning
    print("Running OWLRL Reasoning...")
    owlrl.DeductiveClosure(owlrl.OWLRL_Semantics).expand(g_combined)
    print(f"Graph expanded to {len(g_combined)} triples.")
    
    # Clean up 1: Remove triples where subject is a Literal (invalid in Turtle)
    triples_to_remove = []
    for s, p, o in g_combined:
        if isinstance(s, RdflibLiteral):
            triples_to_remove.append((s, p, o))
    
    if triples_to_remove:
        print(f"Removing {len(triples_to_remove)} invalid triples (Literal subjects)...")
        for t in triples_to_remove:
            g_combined.remove(t)

    # Clean up 2: Subtract TBox triples so we don't duplicate them in ABox file
    # outcomes: ABox file will depend on TBox file.
    initial_len = len(g_combined)
    g_combined -= g_tbox
    print(f"Removed {initial_len - len(g_combined)} TBox triples from inferred graph.")

    # Add Ontology Declaration and Import for ABox
    SNU_NS = "http://snu.ac.kr/dining/"
    ABOX_URI = URIRef(SNU_NS + "abox") # http://snu.ac.kr/dining/abox
    TBOX_URI = URIRef(SNU_NS)          # http://snu.ac.kr/dining/
    
    g_combined.add((ABOX_URI, RDF.type, OWL.Ontology))
    g_combined.add((ABOX_URI, OWL.imports, TBOX_URI))

    # Save Inferred
    inferred_path = os.path.join(base_dir, 'abox_inferred.ttl')
    g_combined.serialize(destination=inferred_path, format='turtle')
    print(f"Saved inferred graph to {inferred_path} (Ontology URI: {ABOX_URI})")

    # 3. Simple SPARQL check
    print("Running check query...")
    # Need to query the combined graph again for verification, or re-add logic.
    # Since we subtracted tbox, let's verify on g_combined (which is Inferred - TBox).
    # This might fail if reasoning result depended on TBox presence for querying, 
    # but the expanded triples (inferred) are still there (e.g. inferred types).
    q = """
    PREFIX snu: <http://snu.ac.kr/dining/>
    SELECT ?name ?price
    WHERE {
        ?s a snu:MenuItem ;
           snu:menuName ?name ;
           snu:price ?price .
        FILTER (?price < 5000)
    } LIMIT 5
    """
    results = g_combined.query(q)
    for row in results:
        print(f"Cheap Item: {row.name} ({row.price} won)")

if __name__ == "__main__":
    run()
