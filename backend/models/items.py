from pydantic import BaseModel
from sqlalchemy import JSON, Column
from sqlmodel import SQLModel, Field, Relationship
from typing import Any, Dict, List, Optional, TYPE_CHECKING
from datetime import datetime
from .user import OwnerInfo

if TYPE_CHECKING:
    from .user import User
    from .exchanges import Exchange
    from .category import Category

class CategoryInfo(BaseModel):
    id: int
    name: str

class ItemBase(SQLModel):
    title: str
    description: Optional[str] = None
    preferred_category_ids: List[int] = Field(sa_column=Column(JSON), default_factory=list)
    images: List[Dict[str, str]] = Field(sa_column=Column(JSON), default_factory=list)
    is_exchangeable: bool = Field(default=False)
    require_all_categories: bool = Field(default=False)
    category_id: Optional[int] = Field(default=None, foreign_key="category.id")
    address: Optional[str] = None
    lon: Optional[float] = None
    lat: Optional[float] = None

class ItemCreate(ItemBase):
    pass

class ItemRead(ItemBase):
    id: int
    category: CategoryInfo
    preferred_category: List[CategoryInfo]
    owner: OwnerInfo

    class Config:
        orm_mode = True

class PaginatedItemResponse(BaseModel):
    items: List[ItemRead]
    total_items: int
    page: int
    items_per_page: int
    total_pages: int

class Item(ItemBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    owner_id: Optional[int] = Field(default=None, foreign_key="user.id")
    owner: "User" = Relationship(back_populates="items")
    exchanges_requested: List["Exchange"] = Relationship(sa_relationship_kwargs={"foreign_keys": "Exchange.requested_item_id"})
    exchanges_offered: List["Exchange"] = Relationship(sa_relationship_kwargs={"foreign_keys": "Exchange.offered_item_id"})
    category: Optional["Category"] = Relationship(back_populates="items")
    category_id: Optional[int] = Field(default=None, foreign_key="category.id")