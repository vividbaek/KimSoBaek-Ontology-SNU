# 향후 고도화 계획: 위치 기반 길찾기 및 내비게이션 (Future Roadmap)

사용자가 제안한 기능 중 **"내 위치 기반 식당 길찾기"** 기능의 구현 전략과 기술적 실현 가능성을 집중적으로 분석합니다.

## 1. 기능 목표
**"현재 내 위치를 기반으로 원하는 식당까지 가는 방법(도보/버스)을 알려줘"** 라는 사용자 질문을 해결하는 것을 목표로 합니다.

---

## 2. 데이터 요구사항 및 온톨로지 확장

이 기능을 구현하기 위해서는 온톨로지(지식 그래프)에 **공간 정보(Spatial Data)**가 필수적으로 보강되어야 합니다.

### 2-1. 식당(Venue) 좌표 데이터 정밀화
현재 TBox에는 `geoLat`, `geoLng` 속성이 존재하지만, 모든 식당(Venue)에 대해 정확한 좌표값이 입력되어 있어야 합니다.
*   **Action**: `abox.ttl`에 모든 `Venue` 인스턴스에 대해 정확한 위도/경도 데이터를 검증하고 채워 넣습니다.
*   **Example**:
    ```turtle
    :Venue_301 a :Venue ;
        :name "301동 식당" ;
        :geoLat "37.449123" ;
        :geoLng "126.952456" .
    ```

### 2-2. 버스 정류장 연계 (Optional but Recommended)
서울대 내부 셔틀버스나 시내버스 정류장 정보를 온톨로지에 추가하면 더 풍부한 경로 안내가 가능합니다.
*   **New Class**: `BusStop`
*   **New Property**: `nearBusStop` (Venue와 가장 가까운 정류장 연결)

---

## 3. 하이브리드 아키텍처 (Hybrid Architecture)

**온톨로지(Knowledge)**와 **외부 지도 API(Computation)**가 협력해야 합니다.

*   **Role 1: 온톨로지 (지식 제공)**
    *   질문에서 언급된 "식당인 `301동 식당`"이 **어떤 좌표**에 위치하는지 알려줍니다.
*   **Role 2: 지도 API (경로 계산)**
    *   사용자의 "현재 위치"와 온톨로지가 알려준 "목적지 좌표" 사이의 **경로(Route)**를 계산하고 시각화합니다.
    *   네이버 지도(Naver Map) 또는 카카오맵(Kakao Map)의 URL Scheme을 활용합니다.

---

## 4. [Deep Dive] LLM 프롬프트 및 구현 전략

LLM은 단순히 SPARQL을 생성하는 것을 넘어, **사용자의 의도(Intent)를 파악하고 적절한 도구(Tool)를 선택하는 Router** 역할을 수행해야 합니다.

### 4-1. Intent Classification (의도 분류)

사용자의 질문이 들어오면 LLM은 다음 두 모드 중 하나를 선택합니다.

1.  **지식 검색 (Knowledge Search)**
    *   질문: "301동 식당 메뉴 뭐야?", "가격 얼마야?"
    *   행동: `generate_sparql()` 실행
2.  **길찾기 (Navigation)**
    *   질문: "301동 식당 가는 길 알려줘", "여기서 거기 어떻게 가?"
    *   행동: `generate_navigation_link()` 실행

### 4-2. 길찾기 프로세스 상세 (Sequence)

1.  **User**: "지금 301동 식당 가는 법 좀 알려줘."
2.  **LLM Router**:
    *   Intent: **Navigation** 감지
    *   Target Entity Extraction: "301동 식당"
3.  **System Action (Python)**:
    *   SPARQL 실행: "301동 식당"의 `:geoLat`, `:geoLng` 조회
    *   Result: `lat=37.449...`, `lng=126.952...`
4.  **Answer Generation**:
    *   좌표를 활용해 네이버 지도 URL 생성
    *   URL Format: `nmap://route/public?dlat={lat}&dlng={lng}&dname={name}&appname=SNUDining`
    *   **Final Output**: "301동 식당은 관악캠퍼스 가장 위쪽에 위치해 있습니다. 아래 버튼을 누르면 길안내를 시작합니다." (링크 카드 제공)

### 4-3. (Simulated) 프롬프트 예시

```text
You are an intelligent router.
If the user asks for the location or route to a specific place:
1. Identify the target venue name.
2. DO NOT generate SPARQL for attributes like menu/price.
3. Instead, output a specific function call token: [NAVIGATE: <VenueName>]

User: "301동 식당 어떻게 가?"
AI: [NAVIGATE: 301동 식당]
```

## 5. 결론

위치 데이터 기반 서비스 확장은 **온톨로지의 정적 데이터(좌표)**와 **외부 앱의 동적 기능(길찾기)**을 결합하는 것이 핵심입니다. 이를 통해 사용자는 "정보 확인"에서 "실제 방문"까지 끊김 없는(Seamless) 경험을 할 수 있습니다.
