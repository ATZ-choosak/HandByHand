from sqlalchemy import JSON, Column
from sqlmodel import SQLModel, Field, Relationship
from typing import List, Optional, TYPE_CHECKING
from datetime import datetime

if TYPE_CHECKING:
    from .user import User
    from .exchanges import Exchange

class ItemBase(SQLModel):
    title: str
    description: Optional[str] = None
    preferred_category_ids: List[int] = Field(sa_column=Column(JSON), default_factory=list)  # New field
    image_ids: List[str] = Field(sa_column=Column(JSON), default_factory=list)
    image_urls: List[str] = Field(sa_column=Column(JSON), default_factory=list)
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