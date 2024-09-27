from sqlalchemy import JSON, Column
from sqlmodel import SQLModel, Field
from typing import List, Optional

class CustomerInterest(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int
    category_ids: List[int] = Field(sa_column=Column(JSON), default_factory=list)