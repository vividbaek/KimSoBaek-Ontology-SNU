import json
import networkx as nx
import pandas as pd
import os
from typing import List, Dict, Any, Set

class GraphManager:
    def __init__(self, data_dir: str):
        self.data_dir = data_dir
        self.graph = nx.DiGraph()
        self.data_map = {}
        self.load_data()
        self.build_graph()

    def load_data(self):
        """Loads data from all JSON files ending in '_subjects.json' in the data directory."""
        self.raw_data = []
        
        # files to look for
        files = [f for f in os.listdir(self.data_dir) if f.endswith('_subjects.json')]
        
        if not files:
            print("No subject data files found. Trying sample.")
            files = ['coss_subjects_sample.json']

        print(f"Loading data from: {files}")

        for filename in files:
            target_path = os.path.join(self.data_dir, filename)
            try:
                with open(target_path, 'r', encoding='utf-8') as f:
                    raw = json.load(f)
                    # Normalize keys to lowercase
                    for item in raw:
                        if not isinstance(item, dict): continue
                        normalized_item = {k.lower(): v for k, v in item.items()}
                        # Tag source if not present
                        if 'source' not in normalized_item:
                            normalized_item['source'] = filename.replace('_subjects.json', '').upper()
                        self.raw_data.append(normalized_item)
            except Exception as e:
                print(f"Error loading {filename}: {e}")
        
        # Create a map for quick access
        for item in self.raw_data:
            if 'id' in item:
                self.data_map[item['id']] = item

    def build_graph(self):
        """Builds the NetworkX graph from the raw data."""
        self.graph.clear()
        
        for item in self.raw_data:
            # Add node with attributes
            self.graph.add_node(
                item['id'],
                label=item['title'],
                title=item['title'],
                concepts=item.get('concepts', []),
                coss_link=item.get('coss_link', {}).get('field') or item.get('coss_link', {}).get('Field') or 'General' if isinstance(item.get('coss_link'), dict) else item.get('coss_link', 'General'),
                competency=", ".join(item.get('competency', [])) if isinstance(item.get('competency'), list) else item.get('competency', '')
            )
            
            # Add edges based on prerequisites
            for prereq_id in item.get('prerequisites', []):
                if prereq_id in self.data_map:
                    self.graph.add_edge(prereq_id, item['id'])

    def get_all_concepts(self) -> Set[str]:
        """Returns a set of all unique concepts in the graph."""
        concepts = set()
        for item in self.raw_data:
            concepts.update(item.get('concepts', []))
        return concepts

    def search_by_concept(self, query: str) -> List[Dict[str, Any]]:
        """
        Searches for subjects that contain the query string in their concepts.
        Case-insensitive.
        """
        query = query.lower()
        results = []
        for item in self.raw_data:
            item_concepts = [c.lower() for c in item.get('concepts', [])]
            # Check if query matches any concept substring or title
            if any(query in c for c in item_concepts):
                results.append(item)
        return results

    def get_roadmap(self, target_role_or_competency: str) -> List[Dict[str, Any]]:
        """
        Generates a learning roadmap for a specific target role or competency.
        1. Find all courses relevant to the target (e.g., 'Data Engineer').
        2. Find all ancestors (prerequisites) of these courses.
        3. Create a subgraph and perform topological sort or level-based ordering.
        """
        target_role_or_competency = target_role_or_competency.lower()
        target_nodes = []
        
        # Identify target nodes based on coss_link or competency
        for node, data in self.graph.nodes(data=True):
            # coss_link might be a string or cleaned up string from build_graph
            coss_link = str(data.get('coss_link', '')).lower()
            competency = str(data.get('competency', '')).lower()
            
            if target_role_or_competency in coss_link or target_role_or_competency in competency:
                target_nodes.append(node)
        
        if not target_nodes:
            return []

        # Find all ancestors (prerequisites)
        relevant_nodes = set(target_nodes)
        for target in target_nodes:
            ancestors = nx.ancestors(self.graph, target)
            relevant_nodes.update(ancestors)
            
        # Create subgraph
        subgraph = self.graph.subgraph(relevant_nodes)
        
        # Topological sort to ensure prerequisite order
        try:
            sorted_nodes = list(nx.topological_sort(subgraph))
        except nx.NetworkXUnfeasible:
            # Fallback if cycle exists (shouldn't happen in DAG)
            sorted_nodes = list(subgraph.nodes())

        # Retrieve full data for sorted nodes
        roadmap = [self.data_map[node_id] for node_id in sorted_nodes]
        return roadmap

    def get_graph_data(self):
        """Returns nodes and edges for visualization."""
        nodes = []
        edges = []
        
        for node, data in self.graph.nodes(data=True):
            nodes.append({
                "id": node,
                "label": data['label'],
                "group": data.get('coss_link', 'Other'),
                "title": f"{data['label']}\nConcepts: {', '.join(data['concepts'])}"
            })
            
        for source, target in self.graph.edges():
            edges.append({
                "from": source,
                "to": target
            })
            
        return nodes, edges
