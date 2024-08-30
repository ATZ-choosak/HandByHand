from sqlmodel import SQLModel, Field, Relationship
from typing import Optional, TYPE_CHECKING
from datetime import datetime

if TYPE_CHECKING:
    from .user import User
    from .exchanges import Exchange

class ItemBase(SQLModel):
    title: str
    description: Optional[str] = None

class ItemCreate(ItemBase):
    pass

class ItemRead(ItemBase):
    id: int
    owner_id: int

class Item(ItemBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    owner_id: Optional[int] = Field(default=None, foreign_key="user.id")
    user: "User" = Relationship(back_populates="items")
    exchanges: Optional["Exchange"] = Relationship(back_populates="item")
