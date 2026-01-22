from streamlit_agraph import Config, Node, Edge

def get_agraph_config(hierarchical: bool = False):
    """
    Returns the configuration for the agraph component.
    """
    layout_algo = "hierarchical" if hierarchical else "physics"
    
    config = Config(
        width=1000,
        height=700,
        directed=True,
        physics=not hierarchical,
        hierarchical=hierarchical,
        nodeHighlightBehavior=True,
        highlightColor="#F7A7A6",
        collapsible=False,
        node={'labelProperty': 'label'},
        link={'labelProperty': 'label', 'renderLabel': False},
        # Premium/Dark Theme Colors
        graphviz_layout=False,
        from_json=None
    )
    return config

def convert_to_agraph_data(nodes_data, edges_data):
    """
    Converts raw node/edge dictionaries to agraph Node/Edge objects.
    """
    agraph_nodes = []
    agraph_edges = []
    
    # Define color scheme for groups
    color_map = {
        "Foundation": "#00C853", # Green
        "CS Core": "#2962FF",    # Blue
        "AI Core": "#6200EA",    # Purple
        "AI Advanced": "#AA00FF",# Violet
        "Data Engineering": "#FF6D00", # Orange
        "Data Science": "#00B8D4", # Cyan
        "Project": "#D50000",      # Red
        "Other": "#757575"         # Grey
    }

    for n in nodes_data:
        group = n.get('group', 'Other')
        color = color_map.get(group, "#757575")
        
        agraph_nodes.append(Node(
            id=n['id'],
            label=n['label'],
            size=25,
            shape="dot",
            color=color,
            title=n['title'],
            group=group
        ))
        
    for e in edges_data:
        agraph_edges.append(Edge(
            source=e['from'],
            target=e['to'],
            color="#BDBDBD",
            type="CURVE_SMOOTH" 
        ))
        
    return agraph_nodes, agraph_edges
