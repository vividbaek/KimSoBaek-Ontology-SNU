import json
import re
import os
import urllib.parse
import hashlib
from datetime import datetime
from rdflib import Graph, Literal, RDF, URIRef, Namespace
from rdflib.namespace import XSD, RDFS, OWL

# Namespaces
SNU = Namespace("http://snu.ac.kr/dining/")

def make_safe_uri(base, *parts):
    # Use MD5 hash to ensure URIs are valid NCNames (safe for all parsers)
    # This avoids issues with Korean characters, spaces, or percent-encoding in PNAMEs.
    raw_id = "_".join(str(p) for p in parts)
    hash_object = hashlib.md5(raw_id.encode('utf-8'))
    # Use 'x' prefix to ensure it starts with a letter, making it a valid NCName/ID
    safe_id = f"x{hash_object.hexdigest()}"
    return base[safe_id]

def run():
    g = Graph()
    g.bind("snu", SNU)
    g.bind("owl", OWL)
    
    # Load raw data
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    with open(os.path.join(base_dir, 'venues_location.json'), 'r') as f:
        venues_data = json.load(f)
    with open(os.path.join(base_dir, 'menus.json'), 'r') as f:
        menus_data = json.load(f)

    # Load Classification Data (LLM results)
    cls_path = os.path.join(base_dir, 'data', 'menu_classification.json')
    menu_classification = {}
    if os.path.exists(cls_path):
        with open(cls_path, 'r') as f:
            menu_classification = json.load(f)
    else:
        print("Warning: menu_classification.json not found. Run classify_menus.py first.")

    # 1. Process Venues
    venue_map = {} # map id to URI
    for v in venues_data['venues']:
        vid = v['venue_id']
        venue_uri = make_safe_uri(SNU, "Venue", vid)
        venue_map[vid] = venue_uri
        
        g.add((venue_uri, RDF.type, SNU.Venue))
        g.add((venue_uri, SNU.venueId, Literal(vid, datatype=XSD.string)))
        g.add((venue_uri, SNU.name, Literal(v['display_name'] or vid, datatype=XSD.string)))
        if v.get('place_name'):
            g.add((venue_uri, SNU.placeName, Literal(v['place_name'], datatype=XSD.string)))
        if v.get('address'):
            g.add((venue_uri, SNU.address, Literal(v['address'], datatype=XSD.string)))
        if v.get('phone'):
            g.add((venue_uri, SNU.phone, Literal(v['phone'], datatype=XSD.string)))
        if v.get('building'):
            g.add((venue_uri, SNU.building, Literal(v['building'], datatype=XSD.string)))
        if v.get('floor'):
            g.add((venue_uri, SNU.floor, Literal(v['floor'], datatype=XSD.integer)))
        if v.get('lat') and v.get('lng'):
            g.add((venue_uri, SNU.geoLat, Literal(v['lat'], datatype=XSD.decimal)))
            g.add((venue_uri, SNU.geoLng, Literal(v['lng'], datatype=XSD.decimal)))

    # 2. Process Menus
    for m in menus_data:
        date_str = m['date']
        raw_rest_name = m['restaurant']
        # Clean restaurant name (remove "* " prefix)
        rest_name = raw_rest_name.replace("* ", "").strip()
        
        # Try finding venue by name mapping (venue_id)
        # Note: raw data venue_id matches rest_name usually
        venue_uri = venue_map.get(rest_name)
        if not venue_uri:
            # Fallback for unknown venues in menu (create ad-hoc)
            venue_uri = make_safe_uri(SNU, "Venue", rest_name)
            g.add((venue_uri, RDF.type, SNU.Venue))
            g.add((venue_uri, SNU.name, Literal(rest_name, datatype=XSD.string)))

        for meal_type in ['breakfast', 'lunch', 'dinner']:
            if meal_type not in m:
                continue
            
            service_data = m[meal_type]
            # Skip if empty
            if not service_data.get('description') and not service_data.get('items') and not service_data.get('time'):
                continue
            
            # Create MealService URI
            service_uri = make_safe_uri(SNU, "Service", date_str, rest_name, meal_type)
            g.add((service_uri, RDF.type, SNU.MealService))
            g.add((service_uri, SNU.providedAt, venue_uri))
            g.add((venue_uri, SNU.offers, service_uri))
            g.add((service_uri, SNU.date, Literal(date_str, datatype=XSD.date)))
            g.add((service_uri, SNU.mealType, Literal(meal_type, datatype=XSD.string)))
            
            # Time parsing
            raw_time = service_data.get('time')
            if raw_time:
                g.add((service_uri, SNU.timeRange, Literal(raw_time, datatype=XSD.string)))
                # Regex for HH:MM~HH:MM or HH:MM
                time_match = re.search(r'(\d{1,2}:\d{2})\s*~\s*(\d{1,2}:\d{2})', raw_time)
                if time_match:
                    start_t, end_t = time_match.groups()
                    # format to HH:MM:00 for xsd:time
                    if len(start_t) == 4: start_t = '0' + start_t
                    if len(end_t) == 4: end_t = '0' + end_t
                    g.add((service_uri, SNU.timeStart, Literal(f"{start_t}:00", datatype=XSD.time)))
                    g.add((service_uri, SNU.timeEnd, Literal(f"{end_t}:00", datatype=XSD.time)))

            description = service_data.get('description', '')
            if description:
                g.add((service_uri, SNU.description, Literal(description, datatype=XSD.string)))
                
                # Check for "Buffet"
                if "뷔페" in description or "세미뷔페" in description:
                    g.add((service_uri, SNU.serviceStyle, Literal("Buffet", datatype=XSD.string)))
                
                # Check for Crowd Time
                # Pattern: ※ 혼잡시간 : 11:30~12:30
                crowd_match = re.search(r'혼잡시간\s*[:]\s*([0-9:~]+)', description)
                if crowd_match:
                    g.add((service_uri, SNU.crowdTimeRange, Literal(crowd_match.group(1), datatype=XSD.string)))

            # 3. Process MenuItems from Description
            # Many menus are in description line by line e.g. "Name : Price"
            lines = description.split('\n')
            
            for line in lines:
                line = line.strip()
                if not line: continue
                if line.startswith("<") or line.startswith("※"):
                    continue

                # Pattern: capture name and price
                price_match = re.search(r'([0-9,]+)원', line)
                price = None
                name = line
                if price_match:
                    price_str = price_match.group(1).replace(',', '')
                    if price_str.isdigit():
                        price = int(price_str)
                    name = re.sub(r'[:\-]?\s*[0-9,]+원.*', '', line).strip()
                
                if not name: continue
                if len(name) < 2: continue # Ignore short noise

                # Create MenuItem
                # Hash based on name+service to be unique
                import hashlib
                item_hash = hashlib.md5(f"{service_uri}_{name}".encode('utf-8')).hexdigest()[:8]
                item_uri = SNU[f"Item_{item_hash}"]
                
                g.add((item_uri, RDF.type, SNU.MenuItem))
                g.add((item_uri, SNU.partOfService, service_uri))
                g.add((service_uri, SNU.hasMenu, item_uri))
                g.add((item_uri, SNU.menuName, Literal(name, datatype=XSD.string)))
                if price:
                    g.add((item_uri, SNU.price, Literal(price, datatype=XSD.integer)))
                
                # --- LLM-Based Classification ---
                is_mapped = False
                if name in menu_classification:
                    is_mapped = True
                    info = menu_classification[name]
                    
                    # 1. Cuisine Type
                    if info.get('cuisineType'):
                        g.add((item_uri, SNU.cuisineType, Literal(info['cuisineType'], datatype=XSD.string)))
                        # Backward compat logic for SNU.category
                        if info['cuisineType'] == 'Korean':
                            g.add((item_uri, SNU.category, Literal("Korean", datatype=XSD.string)))
                        elif info['cuisineType'] in ['Western', 'Chinese', 'Japanese']:
                            g.add((item_uri, SNU.category, Literal(info['cuisineType'], datatype=XSD.string)))

                    # 2. Meat
                    if 'containsMeat' in info:
                        g.add((item_uri, SNU.containsMeat, Literal(info['containsMeat'], datatype=XSD.boolean)))
                        if info['containsMeat']:
                            g.add((item_uri, SNU.category, Literal("Meat", datatype=XSD.string))) # Legacy
                    
                    # 3. Carb Type
                    if info.get('carbType'):
                         g.add((item_uri, SNU.carbType, Literal(info['carbType'], datatype=XSD.string)))
                         if info['carbType'] == 'Noodle':
                              g.add((item_uri, SNU.category, Literal("Noodle", datatype=XSD.string)))
                         elif info['carbType'] == 'Rice':
                              g.add((item_uri, SNU.category, Literal("Rice", datatype=XSD.string)))

                    # 4. Spicy
                    if 'isSpicy' in info:
                        g.add((item_uri, SNU.isSpicy, Literal(info['isSpicy'], datatype=XSD.boolean)))
                        if info['isSpicy']:
                            g.add((item_uri, SNU.tag, Literal("Spicy", datatype=XSD.string)))
                
                # --- Fallback Heuristics (only if not mapped or limited info) ---
                # Still enable basic tags like Takeout from description
                if "Take-Out" in description or "TAKE-OUT" in description or "테이크아웃" in name:
                    g.add((item_uri, SNU.consumptionMode, Literal("Takeout", datatype=XSD.string)))

    # Save
    output_path = os.path.join(base_dir, 'abox_final.ttl')
    g.serialize(destination=output_path, format='turtle')
    print(f"Generated ABox at {output_path} with {len(g)} triples.")

if __name__ == "__main__":
    run()
