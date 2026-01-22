import requests
import json

def verify():
    base_url = "http://localhost:8000/chat"
    query = "현재 금융 도메인에 관심이 있고 머신러닝 관련 강의를 들었고 나는 이론 보다는 실무 위주로 진행하고 싶어. 그 다음 관련 수업은 뭘 들으면 좋을까?"
    
    print(f"Sending Complex Query: {query}")
    try:
        response = requests.get(base_url, params={"query": query})
        if response.status_code == 200:
            data = response.json()
            answer = data.get("answer", "")
            print("\n--- ANSWER (Snippet) ---")
            print(answer[:2000] + "..." if len(answer) > 2000 else answer)
            
            # Check for Key Elements
            if "금융" in answer and "실무" in answer:
                 print("\n✅ PASSED: Answer contextually acknowledges 'Finance' and 'Practical'.")
            else:
                 print("\n⚠️ WARNING: Answer might not be specific enough.")

        else:
            print(f"Error: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"Exception: {e}")

if __name__ == "__main__":
    verify()
