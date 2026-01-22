from backend.reasoner import Reasoner

r = Reasoner()
query = "선형대수학 다음에 뭘 들을까?"
print(f"Query: {query}")

# 1. Test Subject Finding
found = r.find_subject_in_text(query)
print(f"Found Subject: '{found}'")

if found:
    # 2. Test Recommendation
    recs = r.recommend_forward(found)
    print(f"Recommendations count: {len(recs)}")
    for rec in recs:
        print(f" - {rec['Title']}")
else:
    print("Subject not found in text.")
