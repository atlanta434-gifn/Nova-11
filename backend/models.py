from pydantic import BaseModel
from typing import List, Optional

class Dimensions(BaseModel):
    width: float
    length: float
    height: Optional[float] = 3.0

class LandInput(BaseModel):
    dimensions: Dimensions
    num_floors: int = 1
    style: str = "modern"
    budget_tier: str = "mid"

class Room(BaseModel):
    name: str
    position: List[float]  # [x, y, z]
    dimensions: Dimensions

class Layer(BaseModel):
    id: str
    name: str
    type: str  # electrical, plumbing, etc.
    elements: List[dict] = []

class Blueprint(BaseModel):
    id: str
    name: str
    rooms: List[Room]
    layers: List[Layer]
    metadata: dict = {}

