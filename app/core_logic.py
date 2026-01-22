import os
import google.generativeai as genai
from dotenv import load_dotenv
from app.graph_loader import graph_loader
import re

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
    Handles queries like "머신러닝 관련 수업을 들었는데 다음에 뭐 들으면 좋을지"
    """
    schema_info = graph_loader.get_schema_info()
    
    prompt = f"""
    You are an expert in SPARQL and RDF.
    Ontology Schema:
    {schema_info}
    
    Task: Convert natural language to SPARQL.
    
    **JOB ROLE MAPPING LOGIC** (Critical):
    - **Backend Developer**: DO NOT filter title by "Backend". FILTER ?tech IN ("Java", "Spring", "MySQL", "AWS")
    - **AI Modeler**: DO NOT filter title by "Modeler". FILTER ?tech IN ("PyTorch", "TensorFlow", "Python")
    - **Data Engineer**: DO NOT filter title by "Engineer". FILTER ?tech IN ("Hadoop", "Spark", "Kafka", "Cloud")
    - **Data Analyst**: DO NOT filter title by "Analyst". FILTER ?tech IN ("R", "Tableau", "SQL", "Python")
    
    Rules:
    1. Use 'curr:' prefix.
    2. Return ONLY the SPARQL query string.
    3. **Aggregation**: Combine "History" (Prerequisite) + "Role" (Tech Filter) + "Style" (Practical).
    4. **Fallback**: If no tech stack match, then look for Domain.
    
    Example Schema Usage:
    - ?s curr:usesTechStack ?t . ?t rdfs:label "Spring"
    
    Example:
    User: "I want to be a Data Engineer and I've taken Machine Learning."
    SPARQL:
    SELECT DISTINCT ?subjectTitle ?sem ?source ?domain ?tech ?method ?focus WHERE {{
        {{
            # Strategy A: JOB ROLE (Tech Stack Filter)
            ?subject curr:usesTechStack ?t .
            ?t rdfs:label ?tech .
            FILTER(REGEX(?tech, "Hadoop", "i") || REGEX(?tech, "Spark", "i"))
        }} UNION {{
            # Strategy B: HISTORY (Prerequisite Chain)
            ?prereq curr:hasTitle ?pTitle .
            FILTER(CONTAINS(LCASE(?pTitle), "머신러닝") || CONTAINS(LCASE(?pTitle), "machine learning"))
            ?subject curr:hasPrerequisite ?prereq .
        }} UNION {{
            # Strategy C: RELATED (Domain Match)
            ?subject curr:hasDomain ?domain .
            FILTER(CONTAINS(LCASE(STR(?domain)), "데이터"))
        }}
        
        # Global Preference (if specified): Practical
        OPTIONAL {{
             ?subject curr:hasTeachingMethod ?tm .
             ?tm rdfs:label ?method .
        }}
        # Note: Move rigid filters to separate blocks if you want loose coupling
        
        ?subject curr:hasTitle ?subjectTitle .
        ?subject curr:offeredInSource ?source .
        OPTIONAL {{ ?subject curr:hasDomain ?domain }}
        OPTIONAL {{ ?subject curr:hasSemester ?sem }}
        OPTIONAL {{ ?subject curr:usesTechStack ?t . ?t rdfs:label ?tech }}
        OPTIONAL {{ ?subject curr:hasFocus ?f . ?f rdfs:label ?focus }}
    }}
        
        ?subject curr:hasTitle ?subjectTitle .
        ?subject curr:offeredInSource ?source .
        OPTIONAL {{ ?subject curr:hasDomain ?domain }}
        OPTIONAL {{ ?subject curr:hasSemester ?sem }}
        OPTIONAL {{ ?subject curr:hasFocus ?f . ?f rdfs:label ?focus }}
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
        return ""

def execute_sparql(query: str):
    g = graph_loader.get_graph()
    try:
        results = g.query(query)
        # Convert to list of dicts
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
        import traceback
        traceback.print_exc()
        return []

def generate_answer(user_query: str, sparql_query: str, results: list) -> str:
    """
    Uses Gemini to generate structured, well-formatted answer with COSS vs JBNU comparison.
    """
    if not results:
        return "<p>죄송해요, 지식그래프에서 관련 정보를 찾지 못했습니다.</p>"
    
    # Group results by source for comparison
    coss_courses = [r for r in results if r.get('source') == 'COSS']
    jbnu_courses = [r for r in results if r.get('source') == 'JBNU']
    
    # Extract tech stacks from COSS courses for context
    tech_stacks = set()
    for course in coss_courses:
        if course.get('tech'):
            tech_stacks.add(course['tech'])
    tech_stacks_str = ', '.join(tech_stacks) if tech_stacks else 'PyTorch, TensorFlow, AWS 등 산업 표준 도구들'
    
    prompt = f"""
    You are an expert AI Curriculum Advisor specializing in AI/Data Science education.
    
    User Question: "{user_query}"
    
    Data Source (SPARQL Results):
    {results}
    
    SPARQL Query Used:
    {sparql_query}
    
    ========== CRITICAL INSTRUCTIONS ==========
    
    1. **STRUCTURED FORMAT** (Use HTML):
       - Use <strong> for course names and key terms
       - Use bullet points (•)
       - Use sections with clear headers (<h2>, <h3>)
    
    2. **COSS vs JBNU COMPARISON LOGIC** (핵심!):
       - COSS courses typically have:
         * curr:hasTeachingMethod = "Method_Project" (프로젝트 기반 학습)
         * curr:hasFocus = "Focus_Application" (실무/응용 중심)
         * curr:usesTechStack (실제 산업 도구: PyTorch, TensorFlow, AWS 등)
       - JBNU courses are more theoretical/foundational
       
       **CRITICAL: PROVE IT'S NOT JUST AN LLM HALLUCINATION**
       - You MUST refer to the specific **data fields** provided in the Context list.
       - **Source Attribution**: Explicitly state if a course is **[COSS]** or **[JBNU]**.
       - **Connection Logic**:
         * "Since you took [History], the Knowledge Graph identifies [Recommended] as a **Prerequisite Successor**."
         * "The Ontology links [Recommended] to your goal [Role] via the **Competency: {{tech}}**."
       
    3. **ANSWER STRUCTURE** (Follow this template EXACTLY):
       
       **CRITICAL: SHOW THE TRIPLES (Triple-Based Explanation)**
       - Do not just say "It's related." Show the relationships.
       - Use a `Code` style or `Arrow` format to show the path.
       
    3. **ANSWER STRUCTURE** (Follow this template EXACTLY):
       
       <h2>🧠 지식그래프 추론 (Ontology Logic)</h2>
       
       <div style='background:#f1f8e9; padding:15px; border-radius:8px; border:1px solid #c5e1a5; margin-bottom:20px;'>
           <div style='font-weight:bold; color:#33691e; margin-bottom:8px;'>🔍 추론 경로 (Inference Path):</div>
           <ul style='font-family:monospace; font-size:0.9em; color:#558b2f; list-style-type:none; padding-left:10px;'>
              <li>👤 <strong>User(Role: [희망 직무])</strong> ➞ <code>requires_Stack</code> ➞ 🛠️ <strong>{{tech}}</strong></li>
              <li>📚 <strong>Course([Recommended])</strong> ➞ <code>uses_TechStack</code> ➞ 🛠️ <strong>{{tech}}</strong></li>
              <li>✨ <strong>Conclusion:</strong> Direct Match found via <code>curr:usesTechStack</code></li>
           </ul>
       </div>

       <h3>🌟 [COSS] 핵심 추천 과목</h3>
       [Select TOP 3 BEST COSS courses. Use this DETAILED format:]
       <div style='background:#fff; padding:15px; border-radius:8px; border:1px solid #ddd; border-left:5px solid #fd7e14; margin-bottom:15px; box-shadow:0 2px 4px rgba(0,0,0,0.05);'>
           <div style='font-size:1.1em; font-weight:bold; margin-bottom:8px; display:flex; justify-content:space-between; align-items:center;'>
               <span><span style='color:#fff; background:#fd7e14; padding:2px 6px; border-radius:4px; font-size:0.8em; margin-right:5px;'>COSS</span> [과목명]</span>
               <span style='font-size:0.8em; color:#999; font-weight:normal;'>[학기: X-X]</span>
           </div>
           
           <div style='background:#f8f9fa; padding:10px; border-radius:6px; font-size:0.9em; margin-bottom:8px;'>
               <strong>🔗 KG 연결 (Triple):</strong><br>
               <code style='color:#d63384;'>This_Course</code> ➞ <code style='color:#0d6efd;'>curr:teaches</code> ➞ <strong>{{tech}}</strong><br>
               <!-- IF Prerequisite exists -->
               <code style='color:#d63384;'>History(ML)</code> ➞ <code style='color:#0d6efd;'>curr:hasPrerequisite</code> ➞ <strong>This_Course</strong>
           </div>

           <div style='font-size:0.9em; color:#444;'>
               <strong>💡 추천 코멘트:</strong> [구체적 이유: "데이터 엔지니어에게 필수적인 하둡 생태계를 다룹니다."]
           </div>
       </div>
       
       <h3>🏫 [JBNU] 관련 기초 과목</h3>
       <ul style='font-size:0.9em; color:#555;'>
           <li><strong>[JBNU/이론] [과목명]</strong>: [간단한 Triple 관계 설명]</li>
       </ul>

       <hr>
       <p style='font-size:0.8em; color:#888; text-align:right;'>Powered by <strong>Ontology-Based Reasoning Engine</strong></p>
    
    4. **FORMATTING RULES**:
       - Use the HTML structure provided.
       - The code blocks (triples) are CRITICAL.
    
    5. **LANGUAGE**: All in Korean (한국어)
    
    Generate the answer now (HTML format):
    """
    
    try:
        response = model.generate_content(prompt)
        answer = response.text
        
        # Post-process: Convert markdown to HTML if needed
        # Convert markdown bold **text** to <strong>text</strong>
        answer = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', answer)
        # Convert markdown headers ## to <h2>, ### to <h3> if not already HTML
        if not answer.startswith('<h'):
            answer = re.sub(r'^### (.+)$', r'<h3>\1</h3>', answer, flags=re.MULTILINE)
            answer = re.sub(r'^## (.+)$', r'<h2>\1</h2>', answer, flags=re.MULTILINE)
        # Ensure line breaks are preserved
        answer = answer.replace('\n\n', '<br><br>').replace('\n', '<br>')
        
        return answer
    except Exception as e:
        return f"<p>답변 생성 중 오류가 발생했습니다: {e}</p>"

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
