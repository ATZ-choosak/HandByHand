from sqlmodel import SQLModel, Field, Relationship
from datetime import datetime
from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from .user import User
    from .items import Item

class ExchangeBase(SQLModel):
    requested_item_id: int
    offered_item_id: int

class ExchangeCreate(ExchangeBase):
    pass

class ExchangeRead(ExchangeBase):
    id: int
    status: str

class Exchange(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    requester_id: Optional[int] = Field(default=None, foreign_key="user.id")
    requested_item_id: Optional[int] = Field(default=None, foreign_key="item.id")
    offered_item_id: Optional[int] = Field(default=None, foreign_key="item.id")
    
    requester: "User" = Relationship(back_populates="exchanges_requested")
    requested_item: "Item" = Relationship(sa_relationship_kwargs={"foreign_keys": "Exchange.requested_item_id"})
    offered_item: "Item" = Relationship(sa_relationship_kwargs={"foreign_keys": "Exchange.offered_item_id"})

    status: str = Field(default="pending")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)