from app.graph_loader import graph_loader
from rdflib import Namespace

g = graph_loader.get_graph()
CURR = Namespace("http://example.org/curriculum/")

print(f"Total Triples: {len(g)}")

# 1. Find '선형대수학' URI
print("\n--- Finding Subject URI ---")
q_find = """
SELECT ?s ?title WHERE {
    ?s curr:hasTitle ?title .
    FILTER(CONTAINS(?title, "선형대수학"))
}
"""
res = g.query(q_find)
uris = []
for row in res:
    print(f"Found: {row.s} | Title: {row.title}")
    uris.append(row.s)

# 2. Check Prerequisites (Forward & Backward)
if uris:
    target = uris[0]
    print(f"\n--- Checking usage of {target} ---")
    
    # Who requires valid 'target'? (Successors)
    print("\n[Successors] (Nodes that have this as prerequisite):")
    q_succ = """
    SELECT ?s ?p ?o WHERE {
        ?s curr:hasPrerequisite ?target .
    }
    """
    res_succ = g.query(q_succ, initBindings={'target': target})
    for row in res_succ:
        print(f"{row.s} requires {target}")

    # What does 'target' require? (Predecessors)
    print("\n[Predecessors] (Prerequisites of this node):")
    q_pred = """
    SELECT ?o WHERE {
        ?target curr:hasPrerequisite ?o .
    }
    """
    res_pred = g.query(q_pred, initBindings={'target': target})
    for row in res_pred:
        print(f"{target} requires {row.o}")

# 3. Test User's Query Exact Match
print("\n--- Testing User's Generated Query ---")
user_query = """
SELECT ?nextSubjectTitle WHERE {
  ?linearAlgebraSubject a curr:Subject ;
    curr:hasTitle ?linearAlgebraTitle .
  FILTER CONTAINS(?linearAlgebraTitle, "선형대수학")
  ?nextSubject a curr:Subject ;
    curr:hasPrerequisite ?linearAlgebraSubject ;
    curr:hasTitle ?nextSubjectTitle .
}
"""
res_u = g.query(user_query)
print(f"Results count: {len(res_u)}")
for row in res_u:
    print(row)
