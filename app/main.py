import streamlit as st
import os
import sys

# Add project root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.graph_loader import load_graph, get_schema_info
from app.core_logic import generate_sparql, execute_sparql, generate_answer
import google.generativeai as genai

# Page Config
st.set_page_config(
    page_title="SNU 학식 지식 그래프",
    page_icon="🍲",
    layout="wide"
)

# Constants
ABOX_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), '../data/knowledge_graph/abox_inferred.ttl'))

# Session State Initialization
if "messages" not in st.session_state:
    st.session_state.messages = []

if "graph" not in st.session_state:
    with st.spinner("지식 그래프를 로딩 중입니다... (약 10초 소요)"):
        try:
            st.session_state.graph = load_graph(ABOX_PATH)
            st.session_state.schema_info = get_schema_info(st.session_state.graph)
            st.success("지식 그래프 로드 완료!")
        except Exception as e:
            st.error(f"그래프 로드 실패: {e}")
            st.stop()

def get_explanation(query: str) -> str:
    """
    Generates an explanation for the SPARQL query using Gemini.
    """
    try:
        model = genai.GenerativeModel('gemini-3-pro-preview')
        prompt = f"""
        Explain the following SPARQL query in simple Korean.
        Focus on what criteria are used to filter the data.
        
        [SPARQL Query]
        {query}
        """
        response = model.generate_content(prompt)
        return response.text
    except:
        return "쿼리 해석을 생성할 수 없습니다."

# Title & Sidebar
st.title("🎓 SNU Dining Knowledge Graph")
st.markdown("서울대학교 학식 메뉴를 **온톨로지 기반**으로 스마트하게 검색해보세요.")

with st.sidebar:
    st.header("사용 가이드")
    st.markdown("""
    이 서비스는 **Graph RAG (Retrieval Augmented Generation)** 기술을 활용합니다.
    
    1. **질문 입력**: 찾고 싶은 메뉴나 식당 조건을 자연어로 질문하세요.
    2. **투명한 추론**: AI가 어떻게 SPARQL 쿼리를 짜고 답을 찾았는지 보여줍니다.
    
    **💡 추천 질문**
    - "오늘 점심에 5000원 이하 메뉴 있어?"
    - "공대 근처에서 면 요리 파는 곳 알려줘"
    - "저녁에 운영하는 식당 어디야?"
    - "돈까스 파는 곳 찾아줘"
    """)
    st.divider()
    st.caption(f"Graph Triples: {len(st.session_state.graph):,}")

# Chat Interface
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.write(message["content"])
        if "details" in message:
            with st.expander("🔍 추론 과정 및 근거 데이터 (클릭해서 펼치기)"):
                st.markdown("**[1단계] SPARQL 쿼리**")
                st.code(message["details"]["sparql"], language="sparql")
                
                st.markdown("**[2단계] 쿼리 해석**")
                st.write(message["details"]["explanation"])
                
                st.markdown("**[3단계] 근거 데이터 (Raw Data)**")
                if message["details"]["raw_data"]:
                    st.dataframe(message["details"]["raw_data"])
                else:
                    st.info("조건에 맞는 데이터가 없습니다.")

if prompt := st.chat_input("질문을 입력하세요..."):
    # User Message
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.write(prompt)

    # Assistant Response
    with st.chat_message("assistant"):
        with st.status("지식 그래프에서 답을 찾는 중...", expanded=True) as status:
            
            # Step 1: SPARQL Generation
            status.write("🧠 1. 질문 이해 및 SPARQL 쿼리 작성 중...")
            sparql_query = generate_sparql(prompt, st.session_state.schema_info)
            if not sparql_query:
                st.error("SPARQL 쿼리 생성에 실패했습니다.")
                st.stop()
            
            # Step 2: Query Execution
            status.write("🔎 2. 지식 그래프 검색 (SPARQL 실행)...")
            raw_data = execute_sparql(sparql_query, st.session_state.graph)
            
            # Step 3: Explanation & Answer Generation
            status.write("📝 3. 결과 해석 및 답변 작성 중...")
            explanation = get_explanation(sparql_query)
            final_answer = generate_answer(prompt, raw_data, sparql_query)
            
            status.update(label="답변 생성 완료!", state="complete", expanded=False)

        # Output
        st.write(final_answer)
        
        # Save context for history with details
        st.session_state.messages.append({
            "role": "assistant", 
            "content": final_answer,
            "details": {
                "sparql": sparql_query,
                "explanation": explanation,
                "raw_data": raw_data
            }
        })
        
        # Show details immediately for the current turn
        with st.expander("🔍 추론 과정 및 근거 데이터 (클릭해서 펼치기)", expanded=True):
            st.markdown("**[1단계] SPARQL 쿼리**")
            st.code(sparql_query, language="sparql")
            
            st.markdown("**[2단계] 쿼리 해석**")
            st.write(explanation)
            
            st.markdown("**[3단계] 근거 데이터 (Raw Data)**")
            if raw_data:
                st.dataframe(raw_data)
            else:
                st.info("조건에 맞는 데이터가 없습니다.")
