from sqlmodel import Relationship, SQLModel, Field
from typing import List, Optional

from backend.models.items import Item

class Category(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    image_url: Optional[str] = None  # เพิ่มฟิลด์สำหรับเก็บ URL รูปภาพ
    items: List["Item"] = Relationship(back_populates="category")  # เพิ่ม relationship นี้