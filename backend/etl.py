import json
import os
import urllib.parse
from rdflib import Graph, Literal, RDF, RDFS, Namespace, URIRef
from rdflib.namespace import OWL, XSD

# Define Namespace
CURR = Namespace("http://example.org/curriculum/")

def clean_id(text):
    """Encodes text to be safe for URI"""
    return urllib.parse.quote(text.strip().replace(" ", "_"))

def run_etl():
    g = Graph()
    g.bind("curr", CURR)
    
    # Load Schema (optional, but good practice to include definitions)
    # g.parse("data/ontology/schema.ttl", format="turtle") 
    
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    jbnu_path = os.path.join(base_dir, 'data/raw/jbnu_subject.json')
    coss_path = os.path.join(base_dir, 'data/coss_subjects.json')
    output_path = os.path.join(base_dir, 'data/ontology/knowledge_graph.ttl')

    # Load JSON
    with open(jbnu_path, 'r', encoding='utf-8') as f:
        jbnu_data = json.load(f)
    with open(coss_path, 'r', encoding='utf-8') as f:
        coss_data = json.load(f)

    all_subjects = jbnu_data + coss_data
    subject_map = {} # ID -> URIRef

    # 1. Create Subject Instances
    for item in all_subjects:
        sub_id = item['ID']
        title = item['Title']
        source = item.get('Source', 'Unknown')
        semester = item.get('Semester', 'Unknown')
        desc = item.get('Description', '')
        
        sub_uri = CURR[clean_id(sub_id)]
        subject_map[sub_id] = sub_uri
        
        # Type
        if source == 'JBNU':
            g.add((sub_uri, RDF.type, CURR.JBNUSubject))
            g.add((sub_uri, RDF.type, CURR.Subject)) # Explicit Superclass
        else:
            g.add((sub_uri, RDF.type, CURR.COSSSubject))
            g.add((sub_uri, RDF.type, CURR.Subject)) # Explicit Superclass
            
        # Properties
        g.add((sub_uri, CURR.hasTitle, Literal(title, datatype=XSD.string)))
        g.add((sub_uri, CURR.hasSemester, Literal(semester, datatype=XSD.string)))
        g.add((sub_uri, CURR.hasDescription, Literal(desc, datatype=XSD.string)))
        g.add((sub_uri, CURR.offeredInSource, Literal(source, datatype=XSD.string)))
        g.add((sub_uri, RDFS.label, Literal(title)))

        # Domain Grouping Logic (Heuristic)
        domain = "General"
        
        # 1. COSS Field
        if 'COSS_Link' in item and 'Field' in item['COSS_Link']:
            domain = item['COSS_Link']['Field']
        
        # 2. JBNU Heuristic
        elif source == 'JBNU':
            t_norm = title.replace(" ", "")
            if any(k in t_norm for k in ["인공지능", "머신러닝", "기계학습", "딥러닝", "AI"]):
                domain = "인공지능"
            elif any(k in t_norm for k in ["데이터", "통계", "확률", "빅데이터"]):
                domain = "데이터사이언스"
            elif any(k in t_norm for k in ["소프트웨어", "프로그래밍", "자바", "C++", "자료구조", "알고리즘", "컴퓨터"]):
                domain = "SW기초"
            elif any(k in t_norm for k in ["웹", "앱", "모바일", "네트워크", "운영체제", "시스템"]):
                domain = "시스템/네트워크"
            elif any(k in t_norm for k in ["수학", "미적분", "선형대수"]):
                domain = "기초수학"
        
        g.add((sub_uri, CURR.hasDomain, Literal(domain, datatype=XSD.string)))

        # Competencies
        concepts = item.get('Concepts', [])
        for concept in concepts:
            # Concept Format: "Name (Korean)" or just "Name"
            c_name = concept.split('(')[0].strip()
            comp_uri = CURR[f"Competency_{clean_id(c_name)}"]
            g.add((comp_uri, RDF.type, CURR.Competency))
            g.add((comp_uri, RDFS.label, Literal(c_name)))
            g.add((sub_uri, CURR.teaches, comp_uri))
            
        # --- Schema 2.0: Value Proposition Heuristics ---
        
        # 1. Course Focus & method (JBNU vs COSS Differentiation)
        if source == 'JBNU':
            # JBNU defaults to Theory & Lecture
            g.add((sub_uri, CURR.hasFocus, CURR.Focus_Theory))
            g.add((sub_uri, CURR.hasTeachingMethod, CURR.Method_Lecture))
        else:
            # COSS defaults to Application & Project
            g.add((sub_uri, CURR.hasFocus, CURR.Focus_Application))
            g.add((sub_uri, CURR.hasTeachingMethod, CURR.Method_Project))
            
        # 2. Tech Stack Injection (Keyword based)
        title_lower = title.lower()
        tech_map = {
            "머신러닝": ["Python", "ScikitLearn"],
            "딥러닝": ["PyTorch", "TensorFlow"],
            "클라우드": ["AWS", "Docker", "Kubernetes"],
            "빅데이터": ["Hadoop", "Spark"],
            "웹": ["React", "Spring"],
            "자바": ["Java", "Spring"],
            "데이터베이스": ["MySQL", "MongoDB"],
        }
        
        # Inject TechStack triples
        for key, techs in tech_map.items():
            if key in title_lower or key in title:
                for t in techs:
                    t_uri = CURR[f"Tech_{t}"]
                    g.add((t_uri, RDF.type, CURR.TechStack))
                    g.add((t_uri, RDFS.label, Literal(t)))
                    g.add((sub_uri, CURR.usesTechStack, t_uri))
                    
        # Add basic Focus definitions to graph (Idempotent)
        g.add((CURR.Focus_Theory, RDF.type, CURR.CourseFocus))
        g.add((CURR.Focus_Theory, RDFS.label, Literal("Theory & Principles")))
        g.add((CURR.Focus_Application, RDF.type, CURR.CourseFocus))
        g.add((CURR.Focus_Application, RDFS.label, Literal("Practical Application")))
        
        g.add((CURR.Method_Lecture, RDF.type, CURR.TeachingMethod))
        g.add((CURR.Method_Lecture, RDFS.label, Literal("Lecture")))
        g.add((CURR.Method_Project, RDF.type, CURR.TeachingMethod))
        g.add((CURR.Method_Project, RDFS.label, Literal("Project Based Learning")))

    # 2. Create Relations (Prerequisites & SameAs)
    # Re-using the logic from DataLoader roughly, but doing it in RDF
    
    # 2.1 Internal Prerequisites (Explicit in JSON)
    for item in all_subjects:
        sub_id = item['ID']
        sub_uri = subject_map[sub_id]
        prereqs = item.get('Prerequisites', [])
        
        for pid in prereqs:
            if pid in subject_map:
                p_uri = subject_map[pid]
                g.add((sub_uri, CURR.hasPrerequisite, p_uri))

    # 2.2 Bridge Logic (JBNU <-> COSS)
    # We need to re-implement the bridge logic here or import it.
    # For simplicity, let's re-implement the core matching logic.
    
    jbnu_items = [i for i in all_subjects if i.get('Source') == 'JBNU']
    coss_items = [i for i in all_subjects if i.get('Source') == 'COSS']

    for j in jbnu_items:
        j_uri = subject_map[j['ID']]
        j_title_norm = j['Title'].replace(" ", "").lower()
        j_concepts = set([c.split('(')[0].strip().lower() for c in j.get('Concepts', [])])

        for c in coss_items:
            c_uri = subject_map[c['ID']]
            c_title_norm = c['Title'].replace(" ", "").lower()
            c_concepts = set([con.split('(')[0].strip().lower() for con in c.get('Concepts', [])])
            
            # SameAs
            is_same = False
            if j_title_norm == c_title_norm:
                is_same = True
            elif j_concepts and c_concepts:
                intersection = j_concepts.intersection(c_concepts)
                union = j_concepts.union(c_concepts)
                if len(union) > 0 and (len(intersection) / len(union)) >= 0.8:
                    is_same = True
            
            if is_same:
                g.add((j_uri, CURR.equivalentTo, c_uri))
                continue

            # Cross-Prerequisite (JBNU -> COSS)
            is_prereq = False
            
            # 1. Manual Heuristics & Keyword Matching (Aggressive)
            j_title = j['Title'].strip().replace(" ", "").lower()
            c_title = c['Title'].strip().replace(" ", "").lower()
            
            # Map of JBNU keywords to COSS keywords (One-to-Many potential)
            # If JBNU has key, and COSS has any of values, link J -> C
            keyword_map = {
                "프로그래밍": ["자바", "객체지향", "웹", "앱", "파이썬", "c++", "자료구조", "알고리즘"],
                "자료구조": ["알고리즘", "데이터", "인공지능"],
                "알고리즘": ["인공지능", "머신러닝", "딥러닝", "최적화"],
                "데이터베이스": ["빅데이터", "데이터사이언스", "웹", "백엔드"],
                "운영체제": ["시스템", "클라우드", "보안", "임베디드"],
                "네트워크": ["보안", "클라우드", "웹", "iot", "사물인터넷"],
                "소프트웨어공학": ["설계", "프로젝트", "캡스톤", "방법론"],
                "인공지능": ["머신러닝", "딥러닝", "비전", "자연어", "로봇"],
                "선형대수": ["머신러닝", "딥러닝", "그래픽스", "통계", "최적화"],
                "통계": ["머신러닝", "데이터사이언스", "빅데이터", "인공지능"],
                "수학": ["통계", "암호", "그래픽스", "인공지능"]
            }

            for key, targets in keyword_map.items():
                if key in j_title:
                    for t in targets:
                        if t in c_title:
                            is_prereq = True
                            # print(f"DEBUG: Keyword Match {j['Title']} -> {c['Title']}")
                            break
            
            # Specific Hardcoded Links (High Confidence)
            if "선형대수" in j_title and ("머신러닝" in c_title or "딥러닝" in c_title):
                is_prereq = True
            if "확률" in j_title and ("통계" in c_title or "머신러닝" in c_title):
                is_prereq = True
            if j_title == "인공지능" and any(k in c_title for k in ["머신러닝", "딥러닝", "비전", "자연어", "강화학습", "심화"]):
                is_prereq = True
            if j_title == "머신러닝" and any(k in c_title for k in ["딥러닝", "심화", "비전", "자연어"]):
                is_prereq = True
            
            # 2. Description/Concept Match (Existing & Internal JBNU)
            if not is_prereq:
                # Relaxed Concept Match: Intersection > 0
                j_cons = set([x.split('(')[0].strip().lower() for x in j.get('Concepts', [])])
                c_cons = set([x.split('(')[0].strip().lower() for x in c.get('Concepts', [])])
                
                if j_cons & c_cons: 
                     # If JBNU -> JBNU Linking?
                     # We only iterate COSS list 'c' above.
                     # We need to iterate ALL subjects to link JBNU->JBNU.
                     pass

            if is_prereq:
                g.add((c_uri, CURR.hasPrerequisite, j_uri))

    # 3. Internal JBNU Linking (New Step)
    # Iterate all JBNU pairs to find internal progression
    print("Linking Internal JBNU subjects...")
    # jbnu_data is a list of dicts.
    for i in range(len(jbnu_data)):
        j1 = jbnu_data[i]
        # JBNU data uses 'SBJ_NO' or similar as ID? 
        # Actually in the loop above we generated URIs. Let's reconstruct or reuse.
        # Let's check how we got ID before. 
        # In previous loop: id = item['SBJ_NO'] or similar. 
        # Let's inspect variable names in the first loop.
        # Actually, let's just use the ID field derived in the same way as the first loop.
        
        id1 = j1.get('SBJ_NO', str(i))
        t1 = j1.get('SBJ_NM', j1.get('Title', 'Unknown')).strip().replace(" ", "").lower()
        uri1 = URIRef(CURR + f"JBNU_{id1}")
        
        for k in range(len(jbnu_data)):
            if i == k: continue
            j2 = jbnu_data[k]
            id2 = j2.get('SBJ_NO', str(k))
            t2 = j2.get('SBJ_NM', j2.get('Title', 'Unknown')).strip().replace(" ", "").lower()
            uri2 = URIRef(CURR + f"JBNU_{id2}")
            
            # Rules for JBNU -> JBNU
            is_internal_prereq = False
            
            # Intro -> Advanced
            if "개론" in t1 or "기초" in t1 or "입문" in t1:
                if t1.replace("개론","").replace("기초","").replace("입문","") in t2:
                    is_internal_prereq = True
            
            # 1 -> 2
            if "1" in t1 and "2" in t2 and t1.replace("1","") == t2.replace("2",""):
                 is_internal_prereq = True
            
            # Specifics
            if "선형대수" in t1:
                if any(x in t2 for x in ["공학수학", "수치해석", "통계", "그래픽스", "영상처리"]):
                    is_internal_prereq = True
            if "자료구조" in t1:
                if any(x in t2 for x in ["알고리즘", "운영체제", "데이터베이스", "컴파일러"]):
                    is_internal_prereq = True
            
            if is_internal_prereq:
                g.add((uri2, CURR.hasPrerequisite, uri1)) # uri2 requires uri1
            
            if is_prereq:
                g.add((c_uri, CURR.hasPrerequisite, j_uri)) # Note direction: C requires J

    # Save
    g.serialize(destination=output_path, format='turtle')
    print(f"Knowledge Graph saved to {output_path}. Triples: {len(g)}")

if __name__ == "__main__":
    run_etl()
