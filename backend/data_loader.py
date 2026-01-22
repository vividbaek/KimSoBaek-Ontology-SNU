import json
import os
from typing import List, Dict, Set
from backend.models import Subject, GraphNode, GraphEdge

class DataLoader:
    def __init__(self):
        self.subjects: Dict[str, Subject] = {}
        self.nodes: List[GraphNode] = []
        self.edges: List[GraphEdge] = []
        
        # Paths
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.jbnu_path = os.path.join(base_dir, 'data/raw/jbnu_subject.json')
        self.coss_path = os.path.join(base_dir, 'data/coss_subjects.json')

    def load_data(self):
        # 1. Load JSON files
        try:
            with open(self.jbnu_path, 'r', encoding='utf-8') as f:
                jbnu_data = json.load(f)
            with open(self.coss_path, 'r', encoding='utf-8') as f:
                coss_data = json.load(f)
        except FileNotFoundError as e:
            print(f"Error loading data: {e}")
            return

        # 2. Parse Subjects
        all_subjects = []
        
        for item in jbnu_data:
            sub = Subject(**item)
            sub.type = "JBNU"
            self.subjects[sub.id] = sub
            all_subjects.append(sub)
            
        for item in coss_data:
            sub = Subject(**item)
            sub.type = "COSS"
            self.subjects[sub.id] = sub
            all_subjects.append(sub)

        # 3. Build Nodes
        for sub in all_subjects:
            self.nodes.append(GraphNode(
                id=sub.id,
                label=sub.title,
                type=sub.type,
                semester=sub.semester,
                concepts=sub.concepts
            ))
            
        # 4. Build Edges (Internal Prerequisites)
        for sub in all_subjects:
            for pre_id in sub.prerequisites:
                # Some prerequisites might be just IDs, check if they exist
                if pre_id in self.subjects:
                    self.edges.append(GraphEdge(
                        source=pre_id,
                        target=sub.id,
                        type="prerequisite"
                    ))
        
        # 5. Bridge Logic (sameAs & Cross-Prerequisites)
        self._build_bridge(all_subjects)

    def _build_bridge(self, all_subjects: List[Subject]):
        jbnu_subjects = [s for s in all_subjects if s.type == "JBNU"]
        coss_subjects = [s for s in all_subjects if s.type == "COSS"]
        
        for j_sub in jbnu_subjects:
            for c_sub in coss_subjects:
                # 5.1 Entity Normalization (sameAs)
                is_same = False
                
                # Normalize strings
                j_title_norm = j_sub.title.replace(" ", "").lower()
                c_title_norm = c_sub.title.replace(" ", "").lower()

                # Rule 1: Title Identical
                if j_title_norm == c_title_norm:
                    is_same = True
                
                # Rule 2: Concept Overlap > 80%
                if not is_same and j_sub.concepts and c_sub.concepts:
                    j_concepts = set([c.split('(')[0].strip().lower() for c in j_sub.concepts])
                    c_concepts = set([c.split('(')[0].strip().lower() for c in c_sub.concepts])
                    
                    if j_concepts and c_concepts:
                        intersection = j_concepts.intersection(c_concepts)
                        overlap_ratio = len(intersection) / len(j_concepts.union(c_concepts)) # Jaccard Index
                        if overlap_ratio >= 0.8: # Strict overlap
                            is_same = True
                
                if is_same:
                    # Bi-directional link
                    self.edges.append(GraphEdge(source=j_sub.id, target=c_sub.id, type="sameAs"))
                    self.edges.append(GraphEdge(source=c_sub.id, target=j_sub.id, type="sameAs"))
                    continue # If they are the same, don't make them prerequisites of each other

                # 5.2 Cross-Prerequisites (JBNU -> COSS)
                # Rule: JBNU (Basic) -> COSS (Advanced)
                # Heuristic: 
                # 1. JBNU Title appears in COSS Description or Concepts
                # 2. Significant Concept overlap (but not enough for sameAs)
                
                # Semester check: Simple heuristic, assume JBNU (1,2) < COSS (3,4) often holds, 
                # but we can check if data has semester info.
                # JBNU: "1-1", "2-1" etc. COSS: "3-1", "4-1".
                
                is_prerequisite = False
                
                # Check if JBNU Title is in COSS Description
                if j_sub.title in c_sub.description:
                    is_prerequisite = True
                    
                # Check if JBNU Title is in COSS Concepts
                # example: JBNU "Linear Algebra" -> COSS Concept "Linear Algebra"
                if not is_prerequisite:
                    for concept in c_sub.concepts:
                        if j_sub.title in concept: 
                            is_prerequisite = True
                            break
                
                if is_prerequisite:
                    self.edges.append(GraphEdge(source=j_sub.id, target=c_sub.id, type="prerequisite")) 
