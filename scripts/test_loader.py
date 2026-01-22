import sys
import os

# Add the project root to the python path so modules can be imported
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.graph_loader import load_graph, get_schema_info

ABOX_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), '../data/knowledge_graph/abox_inferred.ttl'))

def main():
    print("=== Testing Graph Loader ===")
    if not os.path.exists(ABOX_PATH):
        print(f"Error: File not found at {ABOX_PATH}")
        return

    try:
        g = load_graph(ABOX_PATH)
        print("Graph loaded!")
    except Exception as e:
        print(f"Failed to load graph: {e}")
        return

    print("\n=== Testing Schema Extraction ===")
    try:
        schema_info = get_schema_info(g)
        print("Schema Info Extracted:")
        print("-" * 40)
        print(schema_info[:1000] + "..." if len(schema_info) > 1000 else schema_info)
        print("-" * 40)
        print("Schema extraction successful!")
    except Exception as e:
        print(f"Failed to extract schema info: {e}")

if __name__ == "__main__":
    main()
