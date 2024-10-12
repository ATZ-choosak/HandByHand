from fastapi import UploadFile
from pydantic import BaseModel, EmailStr
from sqlalchemy import JSON, Column
from sqlmodel import SQLModel, Field, Relationship
from typing import Dict, Optional, List
from datetime import datetime

from typing import Optional, List, TYPE_CHECKING

if TYPE_CHECKING:
    from .items import Item
    from .exchanges import Exchange

class OwnerInfo(BaseModel):
    id: int
    name: Optional[str] = None
    phone: Optional[str] = None
    profile_image: Optional[Dict[str, str]] = None
class UserBase(BaseModel):
    email: EmailStr
    phone: Optional[str] = None
    address: Optional[str] = None
    lon: Optional[float] = None
    lat: Optional[float] = None
    profile_image: Optional[Dict[str, str]] = Field(sa_column=Column(JSON), default=None) 

class UserCreate(BaseModel):
    email: EmailStr
    password: str


class UserRead(UserBase):
    id: int
    name: Optional[str] = None
    email: str
    phone: Optional[str] = None
    address: Optional[str] = None
    lon: Optional[float] = None
    lat: Optional[float] = None
    profile_image: Optional[Dict[str, str]] = None
    is_verified: bool
    is_first_login: bool
    created_at: datetime
    updated_at: datetime
    post_count: int
    exchange_complete_count: int
    rating: float
    class Config:
        orm_mode = True

    
class UserLoginInput(BaseModel):
    username: str
    password: str

class UserResendVerifyInput(BaseModel):
    email: str

class UserResetPasswordInput(UserResendVerifyInput):
    pass

class User(SQLModel, UserBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: Optional[str] = None
    email: EmailStr = Field(unique=True, index=True)
    hashed_password: str
    profile_image: Optional[Dict[str, str]] = Field(sa_column=Column(JSON), default=None) 
    is_active: bool = Field(default=False)
    is_verified: bool = Field(default=False)
    is_first_login: bool = Field(default=False)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    items: List["Item"] = Relationship(back_populates="owner")
    exchanges_requested: List["Exchange"] = Relationship(back_populates="requester")
    post_count: int = Field(default=0)
    exchange_complete_count: int = Field(default=0)
    rating: float = Field(default=0.0)
    rating_count: int = Field(default=0)
    
    @property
    def owner_info(self) -> OwnerInfo:
        return OwnerInfo(
            id=self.id,
            email=self.email,
            phone=self.phone,
            profile_image=self.profile_image
        )