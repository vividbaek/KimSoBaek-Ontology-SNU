import sys
import os

# Add the project root to the python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.graph_loader import load_graph, get_schema_info
from app.core_logic import generate_sparql, execute_sparql, generate_answer

ABOX_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), '../data/knowledge_graph/abox_inferred.ttl'))

def main():
    print("=== Core Logic Pipeline Test ===")
    
    # 1. Load Graph
    print(f"[1] Loading Graph from {ABOX_PATH}...")
    if not os.path.exists(ABOX_PATH):
        print(f"Error: File does not exist.")
        return
    graph = load_graph(ABOX_PATH)
    schema_info = get_schema_info(graph)
    print("Graph loaded and schema extracted.\n")

    # 2. Define Question
    test_question = "5,000원 이하로 점심 먹을 수 있는 곳 있어?"
    print(f"[2] User Question: {test_question}\n")

    # 3. Generate SPARQL
    print("[3] Generating SPARQL Query...")
    sparql_query = generate_sparql(test_question, schema_info)
    print("Generated SPARQL:")
    print("-" * 40)
    print(sparql_query)
    print("-" * 40 + "\n")

    if not sparql_query:
        print("Error: Failed to generate SPARQL.")
        return

    # 4. Execute SPARQL
    print("[4] Executing SPARQL Query...")
    raw_data = execute_sparql(sparql_query, graph)
    print(f"Execution Result (First 3 items):")
    for item in raw_data[:3]:
        print(item)
    print(f"... (Total {len(raw_data)} items found)\n")

    # 5. Generate Answer
    print("[5] Generating Final Answer...")
    final_answer = generate_answer(test_question, raw_data, sparql_query)
    print("Final Answer:")
    print("-" * 40)
    print(final_answer)
    print("-" * 40)

if __name__ == "__main__":
    main()
