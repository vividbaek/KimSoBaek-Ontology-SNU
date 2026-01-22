# 지식 그래프 기반 맛집 검색 서비스 구현 명세서

## 1. 개요
이 프로젝트는 `abox_inferred.ttl` 지식 그래프를 활용하여, 사용자의 자연어 질문에 대해 투명한 추론 과정(Text-to-SPARQL)을 거쳐 답변을 제공하는 웹 서비스를 구축하는 것을 목표로 합니다.

## 2. 아키텍처 및 기술 스택
- **Architecture**: Text-to-SPARQL (Vector Search 미사용)
- **Flow**: 사용자 질문 -> LLM -> SPARQL -> RDFLib -> 결과 -> LLM -> 자연어 답변
- **Tech Stack**:
    - **Engine**: `rdflib`
    - **LLM**: `gemini-3-pro-preview` (Google AI Studio API)
    - **Web Framework**: `Streamlit`
    - **Language**: Python 3.11

## 3. 구현 마일스톤

### Step 0. 초기 세팅
- 명세서 작성 및 규칙 파일 생성
- 환경 변수(.env) 설정 안내

### Step 1. 그래프 로더 및 스키마 추출
- `rdflib`으로 `abox_inferred.ttl` 로드
- 그래프 구조(클래스, 속성, 관계) 추출 함수 구현

### Step 2. 검색 파이프라인 (Core Logic)
- `generate_sparql`: 자연어 -> SPARQL 변환
- `execute_sparql`: 쿼리 실행 및 Raw Data 추출
- `generate_answer`: 최종 답변 생성

### Step 3. Streamlit 웹 서비스 (UI/UX)
- 채팅 인터페이스 구현
- 답변 구조화: 최종 답변, 근거 데이터, SPARQL 쿼리, 쿼리 해석

## 4. 출력 요구사항
- **투명성**: AI가 어떤 쿼리를 짰고, 어떤 데이터를 가져왔는지 명확히 시각화(Expander 활용).
- **정확성**: 온톨로지 스키마에 부합하는 SPARQL 생성.

## 5. 원칙
- **언어**: 모든 진행 상황 보고 및 최종 답변은 **한글**로 수행.
- **보고**: 각 Step 종료 시 진행 상황 요약 보고.
