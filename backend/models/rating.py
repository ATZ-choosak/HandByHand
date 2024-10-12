from pydantic import BaseModel
from sqlmodel import SQLModel, Field
from typing import Optional
from datetime import datetime

class Rating(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id")
    rater_id: int = Field(foreign_key="user.id")
    score: float
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
class RatingCreate(BaseModel):
    user_id: int
    score: float = Field(..., ge=1, le=5)