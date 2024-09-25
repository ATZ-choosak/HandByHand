from sqlmodel import SQLModel, Field
from typing import Optional

class Category(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    image_url: Optional[str] = None  # เพิ่มฟิลด์สำหรับเก็บ URL รูปภาพ
