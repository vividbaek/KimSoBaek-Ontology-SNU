import networkx as nx
from typing import List, Set, Dict
from backend.models import Subject, Node, Edge

class Recommender:
    def __init__(self, nodes: List[Node], edges: List[Edge], subjects: Dict[str, Subject]):
        self.subjects = subjects
        self.graph = nx.DiGraph()
        
        # Build NetworkX Graph
        for node in nodes:
            self.graph.add_node(node.id, **node.dict())
            
        for edge in edges:
            self.graph.add_edge(edge.source, edge.target, type=edge.type)

    def get_roadmap(self, current_grade: str, target_track: str) -> List[Subject]:
        """
        Generates a roadmap based on target track.
        1. Identify target subjects based on Track keywords.
        2. Backtrack prerequisites (ancestors).
        3. Sort by Semester.
        """
        
        # 1. Identify Targets
        # Map Track to Keywords
        track_keywords = self._get_track_keywords(target_track)
        target_ids = set()
        
        for sub_id, sub in self.subjects.items():
            # Only consider COSS subjects as "Targets" usually? Or both.
            # Usually users want to achieve a COSS competency.
            if sub.type == "COSS":
                # Check Field
                if sub.coss_link and sub.coss_link.Field:
                    for kw in track_keywords:
                        if kw in sub.coss_link.Field:
                            target_ids.add(sub_id)
                            break
                # Check Competency
                if sub.competency:
                    for comp in sub.competency:
                        for kw in track_keywords:
                            if kw.lower() in comp.lower():
                                target_ids.add(sub_id)
                                break
                                
        # 2. Backtrack Prerequisites (Ancestors)
        roadmap_ids = set(target_ids)
        for tid in target_ids:
            if tid in self.graph:
                ancestors = nx.ancestors(self.graph, tid)
                roadmap_ids.update(ancestors)
        
        # 3. Retrieve Subjects and Sort
        roadmap_subjects = []
        for rid in roadmap_ids:
            if rid in self.subjects:
                roadmap_subjects.append(self.subjects[rid])
        
        # Sort by Semester (Heuristic sort)
        # 1-1 < 1-2 < 2-1 < ... < Any
        roadmap_subjects.sort(key=self._semester_sort_key)
        
        return roadmap_subjects

    def _get_track_keywords(self, track: str) -> List[str]:
        # Simple mapping
        m = {
            "데이터 엔지니어": ["데이터", "Data", "Engineering", "엔지니어링", "Database", "Cloud", "Infrastructure"],
            "AI 모델러": ["인공지능", "AI", "머신러닝", "Machine Learning", "Deep Learning", "딥러닝", "Model", "Vision", "NLP"],
            "백엔드 개발자": ["Backend", "Server", "Database", "Cloud", "Java", "Spring", "System"],
            "프론트엔드 개발자": ["Frontend", "Web", "UI", "UX", "HCI"],
        }
        # Fuzzy match
        for k, v in m.items():
            if k in track:
                return v
        
        # Default: treat track as keyword
        return [track]

    def _semester_sort_key(self, sub: Subject):
        sem = sub.semester
        if sem == "Any": return 100
        if "Any" in sem: return 100 # Any-1, Any-2
        
        parts = sem.split("-")
        if len(parts) == 2:
            try:
                return int(parts[0]) * 10 + int(parts[1])
            except:
                pass
        return 999 
