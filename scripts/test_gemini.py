import os
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()
api_key = os.getenv("GOOGLE_API_KEY")
print(f"API Key found: {bool(api_key)}")

if api_key:
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-2.0-flash-exp')
    
    try:
        print("Sending test prompt to Gemini...")
        response = model.generate_content("Say 'Hello World' if you can hear me.")
        print(f"Response: {response.text}")
        
        print("-" * 20)
        print("Testing SPARQL gen...")
        prompt = "Convert to SPARQL: 'What is the prerequisite for Machine Learning?' Schema: curr:hasPrerequisite"
        response2 = model.generate_content(prompt)
        print(f"SPARQL Response: {response2.text}")
        
    except Exception as e:
        print(f"Error: {e}")
else:
    print("No API Key found.")
