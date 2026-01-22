from pydantic import BaseModel
from typing import List, Optional

class Subject(BaseModel):
    ID: str
    Title: str
    Semester: str = "Unknown"
    Concepts: List[str] = []
    Prerequisites: List[str] = []
    # New Field
    Domain: str = "General" 

class Node(BaseModel):
    id: str
    label: str
    type: str # JBNU or COSS
    semester: str
    concepts: List[str]
    domain: str # New Field for Grouping

class Edge(BaseModel):
    source: str
    target: str
    type: str # prerequisite or sameAs

class GraphResponse(BaseModel):
    nodes: List[Node]
    edges: List[Edge]
