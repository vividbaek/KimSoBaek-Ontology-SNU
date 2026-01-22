from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.data_loader import DataLoader
from backend.models import GraphResponse, Subject
from backend.recommender import Recommender
from backend.reasoner import Reasoner
from typing import List

app = FastAPI(title="Curriculum Recommender System")

# CORS Setup
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ... existing middleware ...

# Initialize Data Loader & Reasoner
data_loader = DataLoader()
recommender: Recommender = None
reasoner: Reasoner = None

@app.on_event("startup")
async def startup_event():
    global recommender, reasoner
    data_loader.load_data()
    recommender = Recommender(data_loader.nodes, data_loader.edges, data_loader.subjects)
    reasoner = Reasoner() # Load RDF Graph
    print(f"Data Loaded: {len(data_loader.nodes)} nodes. RDF Triples: {len(reasoner.g)}")

@app.get("/health")
def health_check():
    return {"status": "ok"}

@app.get("/graph", response_model=GraphResponse)
def get_graph():
    return GraphResponse(nodes=data_loader.nodes, edges=data_loader.edges)

@app.get("/roadmap", response_model=List[dict])
def get_roadmap(grade: str, track: str):
    # Using SPARQL Reasoner preferred now, but let's keep old one as fallback or switch?
    # User asked for "Ontology Inference". Let's use Reasoner.
    if reasoner:
        return reasoner.recommend_roadmap(track)
    return []

@app.get("/recommend/interest", response_model=List[dict])
def recommend_interest(subject_title: str):
    if reasoner:
        return reasoner.recommend_forward(subject_title)
    return []

@app.get("/chat")
def chat(query: str):
    """
    Simple Rule-based Chatbot (NL -> SPARQL Logic)
    """
    query = query.lower()
    answer = ""
    roadmap = []
    
    try:
        if "추천" in query or "로드맵" in query or "어떻게" in query:
            # Check for Track keywords
            if "ai" in query or "인공지능" in query:
                roadmap = reasoner.recommend_roadmap("AI 모델러")
                answer = "🤖 **AI 모델러** 트랙을 위한 로드맵을 찾았습니다!<br>기초 수학부터 시작해서 딥러닝 심화 과정까지 수강하시는 것을 추천합니다."
            elif "데이터" in query:
                roadmap = reasoner.recommend_roadmap("데이터 엔지니어")
                answer = "📊 **데이터 엔지니어** 트랙 로드맵입니다.<br>데이터베이스와 빅데이터 처리 기술을 중심으로 학습해보세요."
            elif "백엔드" in query:
                roadmap = reasoner.recommend_roadmap("백엔드 개발자")
                answer = "💻 **백엔드 개발자** 로드맵입니다.<br>Java와 시스템 설계를 탄탄히 다지는 것이 중요합니다."
            else:
                 answer = "어떤 분야에 관심이 있으신가요? (예: AI, 데이터, 백엔드)"
        
        elif "다음" in query or "뭐 들을까" in query or "후수" in query:
             # Extract Subject Name? (Simple heuristic)
             # Try to match known subjects in query
             found_subj = None
             # Iterate all nodes to find match in query (Inefficient but okay for small graph)
             # Optimally we should use Named Entity Recognition
             known_titles = ["선형대수학", "자료구조", "파이썬", "머신러닝", "딥러닝", "자바", "프로그래밍"]
             for t in known_titles:
                 if t in query:
                     found_subj = t
                     break
             
             if found_subj:
                 roadmap, spark_query = reasoner.recommend_forward(found_subj)
                 if roadmap:
                     # Create bullet list with reasons and source
                     lines = []
                     for s in roadmap[:5]:
                         src_badge = "🔵JBNU" if s['Source'] == 'JBNU' else "🟠COSS"
                         lines.append(f"- {src_badge} **{s['Title']}** ({s['Semester']}) : _{s['Reason']}_")
                     
                     list_str = "<br>".join(lines)
                     
                     # Explanation Block
                     explanation = f"""
                     <details style='margin-top:10px; border:1px solid #ddd; padding:10px; border-radius:5px;'>
                        <summary style='cursor:pointer; font-weight:bold; color:#555;'>🛠️ SPARQL Reasoning Logic (Click)</summary>
                        <pre style='background:#f4f4f4; padding:5px; font-size:0.8em; overflow-x:auto;'>{spark_query.strip().replace('<', '&lt;')}</pre>
                        <p style='font-size:0.8em; color:#666;'>Reasoning Strategy: Forward Chaining (Transitive Closure on Prerequisites)</p>
                     </details>
                     """
                     
                     answer = f"🔍 **{found_subj}**을(를) 들으셨군요.<br>지식그래프 추론 결과, 다음 과목들을 추천합니다:<br><br>{list_str}<br>{explanation}<br>관련된 과목들을 그래프에 표시해 드렸어요!"
                 else:
                     answer = f"🤔 **{found_subj}** 과목과 직접 연결된 후수 과목(Successor) 정보가 지식그래프에 없습니다.<br>하지만 같은 트랙의 다른 과목을 찾아보시는 건 어떨까요?"
             else:
                 answer = "어떤 과목을 들으셨나요? (예: 선형대수학 듣고 뭐 들을까?)"
                 
        else:
            answer = "죄송해요, 아직 배우고 있는 중이라 간단한 질문만 이해할 수 있어요.<br>예: 'AI 트랙 추천해줘', '선형대수학 다음엔 뭐 들어?'"

        return {"answer": answer, "roadmap": roadmap}
        
    except Exception as e:
        print(f"Chat Error: {e}")
        return {"answer": "오류가 발생했습니다.", "roadmap": []}
