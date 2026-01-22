# SNU Dining Ontology - Competency Questions

이 문서는 온톨로지 설계의 기준이 되는 **핵심 질문 10가지**를 정의한 문서입니다.
단순한 데이터 조회를 넘어, 데이터 간의 **관계(Relationship)**와 **속성(Property)**이 어떻게 연결되어야 하는지를 보여줍니다. 개발자는 이 질문들이 논리적으로 해결 가능하도록 온톨로지를 구축해야 합니다.

---

### 1. 기본 연결 (Availability Check)
**"지금 아침 식사 되는 식당 어디야?"**

가장 기초적인 질문으로, 식당(Venue)과 식사 서비스(MealService) 간의 존재 여부와 시간 관계를 확인합니다.

*   **Logical Path:**
    `User(Time)` ➜ `check(CurrentTime ∈ Service.timeWindow)` ➜ `MealService` ➜ `Venue`
*   **Graph Pattern:**
    ```sparql
    ?service a :MealService ;
             :mealType "Breakfast" ;
             :providedAt ?venue .
    ```

---

### 2. 속성 필터링 (Attribute Filtering)
**"5,000원 이하로 점심 먹을 수 있는 곳 있어?"**

메뉴(MenuItem)의 구체적인 속성(가격)을 기준으로 필터링하고, 이를 상위 개념인 식당과 연결합니다.

*   **Logical Path:**
    `MenuItem(price <= 5000)` ➜ `partOfService` ➜ `MealService(Lunch)` ➜ `providedAt` ➜ `Venue`
*   **Graph Pattern:**
    ```sparql
    ?menu :price ?p ;
          :partOfService ?service .
    FILTER (?p <= 5000)
    ?service :providedAt ?venue .
    ```

---

### 3. 의미 기반 분류 (Semantic Categorization)
**"오늘 면 요리(Noodle) 먹고 싶은데 어디로 가면 돼?"**

단순한 메뉴 이름 매칭("국수")이 아니라, '면 요리'라는 **개념(Concept)**으로 데이터를 묶을 수 있어야 합니다.

*   **Logical Path:**
    `Concept(Noodle)` ➜ `isTypeOf` ➜ `MenuItem` ➜ `partOfService` ➜ `Venue`
*   **Graph Pattern:**
    ```sparql
    ?menu :carbType "Noodle" .   # 혹은 :category "Noodle"
    ?menu :partOfService ?service .
    ?service :providedAt ?venue .
    ```

---

### 4. 공간과 콘텐츠의 결합 (Spatial + Content Relation)
**"301동(공대) 근처에 일식 파는 식당 찾아줘."**

단순히 이름에 '301'이 들어간 곳이 아니라, **지리적 거리(Geospatial Distance)**가 가까운 곳을 찾아야 합니다.
'근처'라는 개념은 기준 지점(301동)의 좌표와 후보 식당들의 좌표 간 유클리드 거리(혹은 Haversine) 계산을 필요로 합니다.

*   **Logical Path:**
    1. `Location(301동)` ➜ `getCoordinate(lat, lng)`
    2. `Venue(All)` ➜ `calcDistance(Venue.geo, 301.geo)` ➜ `Filter(dist < Threshold)`
    3. `Venue` ➜ `offers` ➜ `MealService` ➜ `hasMenu` ➜ `MenuItem(Japanese)`
*   **Graph Pattern (Conceptual):**
    ```sparql
    # 1. 기준 장소 (301동) 좌표 획득
    ?target :name "301동 (제1공학관)" ;
            :geoLat ?tLat ;
            :geoLng ?tLng .

    # 2. 후보 식당 탐색 및 거리 계산
    ?venue a :Venue ;
           :geoLat ?vLat ;
           :geoLng ?vLng .
    
    # 3. 메뉴 조건 필터링
    ?venue :offers ?service .
    ?service :hasMenu ?menu .
    ?menu :cuisineType "Japanese" .

    # 4. 거리 정렬 (SPARQL 확장 함수 가정)
    BIND( ( (?tLat - ?vLat)* (?tLat - ?vLat) + (?tLng - ?vLng)* (?tLng - ?vLng) ) AS ?distSq )
    FILTER (?distSq < 0.0001) # 약 1km 반경 (좌표계에 따라 다름)
    ORDER BY ?distSq
    ```

---

### 5. 서비스 메타데이터 (Service Meta-attributes)
**"바쁜데 빨리 받아서 갈 수 있는(테이크아웃) 점심 메뉴 추천해줘."**

음식 자체가 아니라, 식사의 '형태'나 '서비스 방식'에 대한 질문입니다. 메뉴나 서비스에 태그(Tag) 형태의 속성이 필요함을 시사합니다.

*   **Logical Path:**
    `Attribute(Takeout/Quick)` ➜ `hasTag` ➜ `MenuItem` (OR `MealService`) ➜ `providedAt` ➜ `Venue`
*   **Graph Pattern:**
    ```sparql
    ?menu :consumptionMode "Takeout" .
    ?menu :partOfService ?service .
    ?service :mealType "Lunch" .
    ```

---

### 6. 복합 추론 (Complex Reasoning)
**"오늘 매콤한 한식 땡기는데, 학생회관 근처에 그런 메뉴 있어?"**

다양한 조건(맛 + 스타일 + 위치)이 복합적으로 작용하는 질문입니다. 속성 간의 교집합(AND 조건)을 처리할 수 있어야 합니다.

*   **Logical Path:**
    `Venue(near 학생회관)` AND `MenuItem(Flavor=Spicy)` AND `MenuItem(Cuisine=Korean)`
*   **Graph Pattern:**
    ```sparql
    ?venue :name "학생회관" .
    ?venue :offers ?service .
    ?service :hasMenu ?menu .
    ?menu :isSpicy true ;
          :cuisineType "Korean" .
    ```

---

### 7. 식이 제한 (Dietary Restriction)
**"오늘 고기 없는 식단(채식) 있어?"**

특정 재료(고기)의 포함 여부를 속성(`containsMeat`)으로 확인하여, 식이 요법을 지키는 사용자를 위한 필터링을 수행합니다.

*   **Logical Path:**
    `Attribute(NoMeat)` ➜ `containsMeat = false` ➜ `MenuItem` ➜ `partOfService` ➜ `Venue`
*   **Graph Pattern:**
    ```sparql
    ?menu :containsMeat false .
    ?menu :partOfService ?service .
    ?service :date "TODAY"^^xsd:date .
    ?service :providedAt ?venue .
    ```

---

### 8. 운영 시간 (Operating Time)
**"오늘 저녁 6시 30분 이후에도 밥 먹을 수 있는 곳 있어?"**

서비스의 종료 시간(`timeEnd`)을 수치적으로 비교하여, 특정 시점 이후에 이용 가능한 식당을 찾습니다.

*   **Logical Path:**
    `Time(18:30)` ➜ `Filter(timeEnd >= 18:30)` ➜ `MealService(Dinner)` ➜ `Venue`
*   **Graph Pattern:**
    ```sparql
    ?service :mealType "Dinner" ;
             :timeEnd ?end .
    FILTER (?end >= "18:30:00"^^xsd:time)
    ?service :providedAt ?venue .
    ```

---

### 9. 선호/회피 필터링 (Preference Filtering)
**"나 매운 거 못 먹는데, 안 매운 걸로 추천해줘."**

`isSpicy` 속성을 활용하여 특정 맛(매운맛)을 제외(Negative Filter)하는 로직입니다.

*   **Logical Path:**
    `Preference(Not Spicy)` ➜ `isSpicy = false` ➜ `MenuItem` ➜ `partOfService` ➜ `Venue`
*   **Graph Pattern:**
    ```sparql
    ?menu :isSpicy false .
    ?menu :partOfService ?service .
    ?service :providedAt ?venue .
    ```

---

### 10. 최저가 검색 (Global Extremum)
**"오늘 나온 메뉴 중에 제일 싼 게 뭐야?"**

전체 데이터셋(오늘 기준)에서 가격(`price`)을 기준으로 정렬하고 상위 1개(Limit 1)를 추출합니다.

*   **Logical Path:**
    `MenuItem(All)` ➜ `SortBy(price ASC)` ➜ `Limit(1)`
*   **Graph Pattern:**
    ```sparql
    ?menu :price ?price ;
          :menuName ?name .
    ?menu :partOfService ?service .
    ?service :date "TODAY"^^xsd:date .
    ORDER BY ASC(?price)
    LIMIT 1
    ```
