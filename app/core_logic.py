import os
import google.generativeai as genai
import rdflib
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure Gemini API
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
if not GOOGLE_API_KEY:
    raise ValueError("GOOGLE_API_KEY not found in environment variables. Please check .env file.")

genai.configure(api_key=GOOGLE_API_KEY)
model = genai.GenerativeModel('gemini-3-pro-preview')

def generate_sparql(question: str, schema_info: str) -> str:
    """
    Generates a SPARQL query from a natural language question using Gemini.
    
    Args:
        question (str): The user's question.
        schema_info (str): The schema information string.
        
    Returns:
        str: The generated SPARQL query string.
    """
    prompt = f"""
You are an expert in SPARQL and Ontology Graph Databases.
Your goal is to convert the User's Question into a precise SPARQL query based *strictly* on the provided Schema Information.

[Schema Information]
{schema_info}

[Prefixes]
PREFIX : <http://snu.ac.kr/dining/>
PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX owl: <http://www.w3.org/2002/07/owl#>
PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>

[Rules]
1. Use the prefixes defined above.
2. The specific namespace for this ontology is <http://snu.ac.kr/dining/>, represented by the prefix `:`.
3. Do NOT invent new classes or properties. Use ONLY what is provided in Schema Information.
4. If the user asks about fuzzy concepts (e.g., "Engineering Zone"), infer them based on string matching in `placeName` or `building` if no specific class exists (e.g., FILTER regex(?venueName, "공대|301동", "i")).
5. For prices, ensure you handle datatype correctly (xsd:integer).
6. Return ONLY the SPARQL query code block (markdown ```sparql ... ```). Do not add explanations outside the code block.

[User Question]
{question}
"""
    
    try:
        response = model.generate_content(prompt)
        text = response.text
        # Extract code block if present
        if "```sparql" in text:
            query = text.split("```sparql")[1].split("```")[0].strip()
        elif "```" in text:
            query = text.split("```")[1].split("```")[0].strip()
        else:
            query = text.strip()
        return query
    except Exception as e:
        print(f"Error generating SPARQL: {e}")
        return ""

def execute_sparql(query: str, graph: rdflib.Graph):
    """
    Executes a SPARQL query against the provided graph.
    
    Args:
        query (str): The SPARQL query string.
        graph (rdflib.Graph): The loaded graph.
        
    Returns:
        list[dict] | None: A list of result rows (as dictionaries) or None if error.
    """
    print(f"Executing SPARQL Query:\n{query}")
    try:
        results = graph.query(query)
        
        # Convert results to a clean list of dictionaries for easier consumption
        parsed_results = []
        for row in results:
            item = {}
            if hasattr(results, 'vars'): # Select query
                for var in results.vars:
                    val = row[var]
                    # Convert rdflib literals/uris to simple strings/ints
                    if isinstance(val, rdflib.Literal):
                        item[str(var)] = val.value
                    else:
                        item[str(var)] = str(val)
            parsed_results.append(item)
            
        return parsed_results
    except Exception as e:
        print(f"Error executing SPARQL: {e}")
        return None

def generate_answer(question: str, raw_data: list, sparql_query: str) -> str:
    """
    Generates a natural language answer based on the raw data retrieved.
    
    Args:
        question (str): User's original question.
        raw_data (list): The list of result dictionaries from the SPARQL query.
        sparql_query (str): The query used (for context).
        
    Returns:
        str: Final answer in Korean.
    """
    
    prompt = f"""
You are an intelligent knowledge assistant.
Your task is to answer the User's Question based on the provided [Raw Data] retrieved from a Knowledge Graph.

[User Question]
{question}

[Raw Data]
{raw_data}

[Context (SPARQL used)]
{sparql_query}

[Instructions]
1. Answer in natural, friendly Korean (polite tone, honorifics).
2. Summarize the findings clearly.
3. If the [Raw Data] is empty, politely inform the user that no matching information was found in the database.
4. Do not mention "DB" or "SPARQL" or "JSON" in the final answer unless necessary for debugging. Just present the facts.
5. If there are prices, format them with commas (e.g., 5,000원).
"""
    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"답변 생성 중 오류가 발생했습니다: {e}"
