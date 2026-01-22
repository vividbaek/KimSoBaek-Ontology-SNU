import os
from pathlib import Path

# Project Root
PROJECT_ROOT = Path(__file__).parent.absolute()

# Data Paths
DATA_DIR = PROJECT_ROOT / "data"
RAW_DATA_DIR = DATA_DIR / "raw"
ONTOLOGY_DIR = DATA_DIR / "ontology"
KG_DIR = DATA_DIR / "knowledge_graph"

# File Paths
MENUS_JSON_PATH = RAW_DATA_DIR / "menus.json"
VENUES_LOCATION_JSON_PATH = RAW_DATA_DIR / "venues_location.json"

TBOX_PATH = ONTOLOGY_DIR / "tbox.ttl"
ABOX_INFERRED_PATH = KG_DIR / "abox_inferred.ttl"
CLEAN_GRAPH_PATH = KG_DIR / "clean_graph.ttl"
ABOX_FINAL_PATH = KG_DIR / "abox_final.ttl"

# Model Config
MODEL_NAME = "gemini-3-pro-preview"
