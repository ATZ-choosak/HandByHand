from sqlalchemy import JSON, Column
from sqlmodel import SQLModel, Field, Relationship
from typing import Dict, List, Optional, TYPE_CHECKING
from datetime import datetime

if TYPE_CHECKING:
    from .user import User
    from .exchanges import Exchange
    from .category import Category
class ItemBase(SQLModel):
    title: str
    description: Optional[str] = None
    preferred_category_ids: List[int] = Field(sa_column=Column(JSON), default_factory=list)
    images: List[Dict[str, str]] = Field(sa_column=Column(JSON), default_factory=list)  # เปลี่ยนจาก image_ids และ image_urls
    is_exchangeable: bool = Field(default=False)  # เพิ่ม field นี้
    require_all_categories: bool = Field(default=False)  # เพิ่ม field นี้
    category_id: Optional[int] = Field(default=None, foreign_key="category.id")  # เพิ่ม field นี้
    address: Optional[str] = None  # เพิ่ม field นี้
    lon: Optional[float] = None  # เพิ่ม field นี้
    lat: Optional[float] = None  # เพิ่ม field นี้
class ItemCreate(ItemBase):
    pass

class ItemRead(ItemBase):
    id: int
    owner_id: int

class Item(ItemBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    owner_id: Optional[int] = Field(default=None, foreign_key="user.id")
    image_urls: List[str] = Field(sa_column=Column(JSON), default_factory=list)
    owner: "User" = Relationship(back_populates="items")
    exchanges_requested: List["Exchange"] = Relationship(sa_relationship_kwargs={"foreign_keys": "Exchange.requested_item_id"})
    exchanges_offered: List["Exchange"] = Relationship(sa_relationship_kwargs={"foreign_keys": "Exchange.offered_item_id"})
    category: Optional["Category"] = Relationship(back_populates="items")  # เพิ่ม relationship นี้