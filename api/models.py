from pydantic import BaseModel
from typing import List, Any

class TopItem(BaseModel):
    id: str
    text: str
    score: float

class EraEntry(BaseModel):
    era: str
    top: List[TopItem]
    centroid_shift_from_prev: float

class TimelineResponse(BaseModel):
    concept: str
    timeline: List[EraEntry]
