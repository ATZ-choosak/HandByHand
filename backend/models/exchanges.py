from sqlmodel import SQLModel, Field, Relationship
from datetime import datetime
from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from .user import User
    from .items import Item

class ExchangeBase(SQLModel):
    item_id: int
    
  

class ExchangeCreate(ExchangeBase):
    pass

class ExchangeRead(ExchangeBase):
    id: int

class Exchange(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    item_id: Optional[int] = Field(default=None, foreign_key="item.id")
    requester_id: Optional[int] = Field(default=None, foreign_key="user.id")
    item: "Item" = Relationship(back_populates="exchanges")
    requester: "User" = Relationship(back_populates="exchanges_requested")
    status: str = Field(default="pending")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)