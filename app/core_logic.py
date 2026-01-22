import os
import google.generativeai as genai
from dotenv import load_dotenv
from app.graph_loader import graph_loader

# Load Env
load_dotenv()
api_key = os.getenv("GOOGLE_API_KEY")
if api_key:
    genai.configure(api_key=api_key)

# Use user-specified model
model = genai.GenerativeModel('gemini-2.0-flash-exp')

def generate_sparql(user_query: str) -> str:
    """
    Uses Gemini to translate natural language to SPARQL.
    """
    schema_info = graph_loader.get_schema_info()
    
    prompt = f"""
    You are an expert in SPARQL and RDF.
    Ontology Schema:
    {schema_info}
    
    Task: Convert the following user question into a SPARQL query.
    Rules:
    1. Use 'curr:' prefix.
    2. Return ONLY the SPARQL query string. No markdown block.
    3. Use 'FILTER(CONTAINS(LCASE(?title), "search_term"))' for robust text matching.
    4. Important properties: curr:hasTitle, curr:hasPrerequisite, curr:hasSemester, curr:offeredInSource.
    
    Example:
    User: "선형대수학 다음엔 뭐 들어?" (What comes after Linear Algebra?)
    SPARQL:
    SELECT ?nextSubjectTitle ?sem ?source WHERE {{
        ?s curr:hasTitle ?title .
        FILTER(CONTAINS(LCASE(?title), "선형대수"))
        ?next curr:hasPrerequisite ?s .
        ?next curr:hasTitle ?nextSubjectTitle .
        OPTIONAL {{ ?next curr:hasSemester ?sem }}
        OPTIONAL {{ ?next curr:offeredInSource ?source }}
    }}
    
    Question: "{user_query}"
    
    SPARQL Query:
    """
    
    try:
        response = model.generate_content(prompt)
        if not response.parts:
             print("LLM Error: Empty Response")
             return ""
        query = response.text.replace("```sparql", "").replace("```", "").strip()
        print(f"Generated SPARQL: {query}")
        return query
    except Exception as e:
        print(f"LLM Error (Generate SPARQL): {e}")
        # Fallback for debugging
        return ""

def execute_sparql(query: str):
    g = graph_loader.get_graph()
    try:
        results = g.query(query)
        # Convert to list of dicts for LLM consumption
        data = []
        for row in results:
            item = {}
            for var in results.vars:
                val = row[var]
                if val:
                    item[str(var)] = str(val)
            data.append(item)
        return data
    except Exception as e:
        print(f"SPARQL Execution Error: {e}")
        return []

def generate_answer(user_query: str, sparql_query: str, results: list) -> str:
    """
    Uses Gemini to generate natural language answer from SPARQL results.
    """
    if not results:
        return "죄송해요, 지식그래프에서 관련 정보를 찾지 못했습니다. (SPARQL 쿼리 결과 없음)"
        
    prompt = f"""
    You are a helpful AI Curriculum Tutor.
    
    User Question: "{user_query}"
    
    Data Source (SPARQL Results):
    {results}
    
    SPARQL Query Used:
    {sparql_query}
    
    Instructions:
    1. Answer the user's question based strictly on the Data Source.
    2. Suggest courses with their Semester and Source (JBNU/COSS) if available.
    3. Be friendly and helpful.
    4. Mention "Reference: Knowledge Graph" at the end.
    
    Answer (in Korean):
    """
    
    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"답변 생성 중 오류가 발생했습니다: {e}"

def process_query_pipeline(user_query: str):
    # 1. Gen SPARQL
    sparql_query = generate_sparql(user_query)
    if not sparql_query:
        return {"answer": "질문을 이해하지 못했거나 SPARQL 생성에 실패했습니다.", "query": "", "data": []}
        
    # 2. Execute
    results = execute_sparql(sparql_query)
    
    # 3. Gen Answer
    answer = generate_answer(user_query, sparql_query, results)
    
    return {
        "answer": answer,
        "query": sparql_query,
        "data": results
    }
