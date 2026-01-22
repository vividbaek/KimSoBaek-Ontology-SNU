import requests
import json

def verify():
    base_url = "http://localhost:8000/chat"
    query = "나는 데이터 엔지니어가 되고 싶어. 실무 위주로 어떤 수업을 들어야 해?"
    
    print(f"Sending Role Query: {query}")
    try:
        response = requests.get(base_url, params={"query": query})
        if response.status_code == 200:
            data = response.json()
            answer = data.get("answer", "")
            print("\n--- ANSWER (Snippet) ---")
            print(answer[:2000] + "..." if len(answer) > 2000 else answer)
            
            # Check for Key Elements
            if "데이터 엔지니어" in answer or "Data Engineer" in answer:
                 print("\n✅ PASSED: Context 'Data Engineer' found.")
            else:
                 print("\n⚠️ WARNING: Context 'Data Engineer' NOT explicit.")
                 
            if "Hadoop" in answer or "Spark" in answer or "빅데이터" in answer:
                 print("✅ PASSED: Relevant Tech Stack found.")
            else:
                 print("⚠️ WARNING: Relevant Tech Stack (Hadoop/Spark) NOT found.")

        else:
            print(f"Error: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"Exception: {e}")

if __name__ == "__main__":
    verify()
