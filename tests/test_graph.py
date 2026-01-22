import unittest
import sys
import os

# Add app to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.services.graph_manager import GraphManager

class TestGraphManager(unittest.TestCase):
    def setUp(self):
        # Point to the data directory where coss_subjects.json resides
        self.data_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '../data'))
        self.graph_manager = GraphManager(self.data_dir)

    def test_load_data(self):
        self.assertTrue(len(self.graph_manager.raw_data) > 0)
        print(f"Loaded {len(self.graph_manager.raw_data)} items")

    def test_build_graph(self):
        self.assertTrue(self.graph_manager.graph.number_of_nodes() > 0)

    def test_search(self):
        # Search for "Data" which appears in many concepts like "Data Lifecycle"
        results = self.graph_manager.search_by_concept("Data")
        self.assertTrue(len(results) > 0)
        # Verify one of the results has "Data" in concepts
        has_match = False
        for item in results:
            concepts = [c.lower() for c in item.get('concepts', [])]
            if any("data" in c for c in concepts):
                has_match = True
                break
        self.assertTrue(has_match)

    def test_roadmap_data_engineer(self):
        # Search for "데이터엔지니어링" (Data Engineering in Korean)
        roadmap = self.graph_manager.get_roadmap("데이터엔지니어링")
        print("Roadmap for 데이터엔지니어링:")
        for item in roadmap:
            print(f"- {item['title']}")
        
        titles = [item['title'] for item in roadmap]
        # In real data, '데이터베이스' related courses are key
        # COSS_39: 데이터베이스설계와질의
        # COSS_41: 데이터베이스
        self.assertTrue(any("데이터베이스" in t for t in titles))
        
        # Verify order if possible (Prerequisites check)
        # COSS_39 (DB Design) might depend on COSS_04 (Data Structures)
        # Not strictly checking full chain as real data is complex
        self.assertTrue(len(roadmap) >= 1)

if __name__ == '__main__':
    unittest.main()
