import os
import json
import re
import time
import google.generativeai as genai
from typing import List, Dict

# Configuration
API_KEY = os.environ.get("GOOGLE_API_KEY")
MODEL_NAME = "gemini-2.0-flash-exp"
BATCH_SIZE = 50 
CACHE_FILE = "data/menu_classification.json"
INPUT_FILE = "menus.json"

if not API_KEY:
    print("Warning: GOOGLE_API_KEY environment variable not set. Please set it to run classification.")

def load_unique_menus() -> List[str]:
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    input_path = os.path.join(base_dir, INPUT_FILE)
    
    with open(input_path, 'r') as f:
        data = json.load(f)
    
    unique_names = set()
    
    for day in data:
        for meal in ['breakfast', 'lunch', 'dinner']:
            if meal not in day: continue
            desc = day[meal].get('description', '')
            if not desc: continue
            
            # Extract names similar to generate_knowledge_graph.py
            lines = desc.split('\n')
            for line in lines:
                line = line.strip()
                if not line or line.startswith("<") or line.startswith("※"):
                    continue
                # Remove price
                name = re.sub(r'[:\-]?\s*[0-9,]+원.*', '', line).strip()
                if len(name) > 1:
                    unique_names.add(name)
                    
    return sorted(list(unique_names))

def classify_batch(names: List[str]) -> Dict[str, Dict]:
    if not API_KEY:
        return {} # Mock return or skip
    
    genai.configure(api_key=API_KEY)
    model = genai.GenerativeModel(MODEL_NAME)
    
    prompt = """
    You are a food ontology expert. Classify the following menu items (Korean university cafeteria food).
    Return a JSON object where keys are the menu names and values are objects with these properties:
    - cuisineType: String (Korean, Western, Chinese, Japanese, Other)
    - containsMeat: Boolean (true if meat/poultry/ham is main ingredient, false for vegetarian/seafood-only)
    - carbType: String (Rice, Noodle, Bread, None)
    - isSpicy: Boolean (true if spicy based on name like 'bull', 'hot', 'spicy')
    
    Input items:
    {items}
    
    Output JSON only.
    """
    
    try:
        response = model.generate_content(prompt.format(items=json.dumps(names, ensure_ascii=False)))
        text = response.text.strip()
        # Cleanup json block format if present
        if text.startswith("```json"):
            text = text[7:-3]
        elif text.startswith("```"):
            text = text[3:-3]
            
        return json.loads(text)
    except Exception as e:
        print(f"Error classifying batch: {e}")
        return {}

def run():
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    cache_path = os.path.join(base_dir, CACHE_FILE)
    os.makedirs(os.path.dirname(cache_path), exist_ok=True)
    
    # Load existing cache
    known_map = {}
    if os.path.exists(cache_path):
        with open(cache_path, 'r') as f:
            known_map = json.load(f)
            
    all_names = load_unique_menus()
    unknown_names = [n for n in all_names if n not in known_map]
    
    print(f"Total items: {len(all_names)}, Known: {len(known_map)}, To classify: {len(unknown_names)}")
    
    if not unknown_names:
        print("All items classified.")
        return

    # Process in batches
    for i in range(0, len(unknown_names), BATCH_SIZE):
        batch = unknown_names[i:i+BATCH_SIZE]
        print(f"Processing batch {i} to {i+len(batch)}...")
        
        results = classify_batch(batch)
        if results:
            known_map.update(results)
            # Save intermediate
            with open(cache_path, 'w') as f:
                json.dump(known_map, f, indent=2, ensure_ascii=False)
            print(f"Saved {len(results)} items.")
        
        time.sleep(1) # Rate limit courtesy

    print("Classification Done.")

if __name__ == "__main__":
    run()
