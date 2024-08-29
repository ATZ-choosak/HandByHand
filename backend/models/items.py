from pydantic import BaseModel, ConfigDict
from sqlmodel import Field, SQLModel

class BaseItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    name: str

class CreatedItem(BaseItem):
    pass


class UpdatedItem(BaseItem):
    pass


class Item(BaseItem):
    id: int

class DBItem(BaseItem, SQLModel, table=True):
    __tablename__ = "items"
    id: int = Field(default=None, primary_key=True)

class ItemList(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    items: list[Item]
    page: int
    page_count: int
    size_per_page: int