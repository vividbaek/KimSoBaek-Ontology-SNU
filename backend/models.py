from typing import List, Optional, Dict
from pydantic import BaseModel, Field

class COSSLink(BaseModel):
    Score: int
    Field: str

class Subject(BaseModel):
    id: str = Field(alias="ID")
    title: str = Field(alias="Title")
    source: str = Field(alias="Source")
    semester: str = Field(alias="Semester", default="Unknown")
    concepts: List[str] = Field(alias="Concepts", default_factory=list)
    prerequisites: List[str] = Field(alias="Prerequisites", default_factory=list)
    description: str = Field(alias="Description", default="")
    competency: List[str] = Field(alias="Competency", default_factory=list)
    coss_link: Optional[COSSLink] = Field(alias="COSS_Link", default=None)
    
    # Graph specific fields
    type: str = "Subject"  # JBNU or COSS
    related_to: List[str] = [] # List of IDs this subject is related to

class GraphNode(BaseModel):
    id: str
    label: str
    type: str # 'JBNU' or 'COSS'
    semester: str
    concepts: List[str]

class GraphEdge(BaseModel):
    source: str
    target: str
    type: str # 'sameAs' or 'prerequisite'
    
class GraphResponse(BaseModel):
    nodes: List[GraphNode]
    edges: List[GraphEdge]
