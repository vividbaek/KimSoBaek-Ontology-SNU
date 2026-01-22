from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.data_loader import DataLoader
from backend.models import GraphResponse

app = FastAPI(title="Curriculum Recommender System")

# CORS Setup
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from backend.recommender import Recommender
from typing import List

# ... existing imports ...

# Initialize Data Loader
data_loader = DataLoader()
recommender: Recommender = None

@app.on_event("startup")
async def startup_event():
    global recommender
    data_loader.load_data()
    recommender = Recommender(data_loader.nodes, data_loader.edges, data_loader.subjects)
    print(f"Data Loaded: {len(data_loader.nodes)} nodes, {len(data_loader.edges)} edges")

@app.get("/health")
def health_check():
    return {"status": "ok"}

@app.get("/graph", response_model=GraphResponse)
def get_graph():
    return GraphResponse(nodes=data_loader.nodes, edges=data_loader.edges)

@app.get("/roadmap", response_model=List[dict]) 
# Using List[dict] to return subject dictionaries directly or we can use Subject model if properly exported
# For simplicity let's return list of Subject models dumps? No, response_model can handle it.
def get_roadmap(grade: str, track: str):
    if not recommender:
        return []
    roadmap = recommender.get_roadmap(grade, track)
    return roadmap
