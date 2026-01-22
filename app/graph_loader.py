import rdflib
import os

def load_graph(file_path: str) -> rdflib.Graph:
    """
    Load the RDF graph from the specified TTL file.
    
    Args:
        file_path (str): The absolute path to the .ttl file.
        
    Returns:
        rdflib.Graph: The loaded graph.
    """
    print(f"Loading graph from {file_path}...")
    g = rdflib.Graph()
    try:
        g.parse(file_path, format="turtle")
        print(f"Graph loaded successfully! Total triples: {len(g)}")
        return g
    except Exception as e:
        print(f"Error loading graph: {e}")
        raise e

def get_schema_info(graph: rdflib.Graph) -> str:
    """
    Extracts schema information (Classes, Properties, Relations) from the graph
    to provide context for the LLM.
    
    Args:
        graph (rdflib.Graph): The loaded graph.
        
    Returns:
        str: A formatted string describing the schema.
    """
    
    # 1. Extract Classes
    classes_query = """
    SELECT DISTINCT ?class
    WHERE {
        ?s a ?class .
    }
    ORDER BY ?class
    """
    classes = []
    for row in graph.query(classes_query):
        classes.append(str(row['class']))
        
    # 2. Extract Properties (Predicates)
    props_query = """
    SELECT DISTINCT ?p
    WHERE {
        ?s ?p ?o .
    }
    ORDER BY ?p
    """
    properties = []
    for row in graph.query(props_query):
        properties.append(str(row['p']))

    # 3. Extract Example Relations (Triples)
    # Get a few diverse examples to show structure
    examples_query = """
    SELECT ?s ?p ?o
    WHERE {
        ?s ?p ?o .
    }
    LIMIT 10
    """
    examples = []
    for row in graph.query(examples_query):
        examples.append(f"{row['s']} {row['p']} {row['o']}")

    schema_text = f"""
[Classes]
{chr(10).join(classes)}

[Properties]
{chr(10).join(properties)}

[Example Triples]
{chr(10).join(examples)}
    """
    
    return schema_text.strip()
