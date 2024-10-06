from sqlalchemy import JSON, Column
from sqlmodel import Relationship, SQLModel, Field
from typing import Dict, List, Optional

from backend.models.items import Item

class Category(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    image: Optional[Dict[str, str]] = Field(sa_column=Column(JSON), default=None)
    items: List["Item"] = Relationship(back_populates="category")  # เพิ่ม relationship นี้
    