from pydantic import BaseModel, EmailStr
from sqlmodel import SQLModel, Field, Relationship
from typing import Optional, List
from datetime import datetime

from typing import Optional, List, TYPE_CHECKING

if TYPE_CHECKING:
    from .items import Item
    from .exchanges import Exchange

class UserBase(BaseModel):
    email: EmailStr
    name: str

class UserCreate(UserBase):
    password: str

class UserRead(UserBase):
    id: int

class User(SQLModel, UserBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    email: EmailStr = Field(unique=True, index=True)
    hashed_password: str
    is_active: bool = Field(default=False)
    is_verified: bool = Field(default=False)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    items: List["Item"] = Relationship(back_populates="user")
    exchanges_requested: List["Exchange"] = Relationship(back_populates="requester")