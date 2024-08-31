from pydantic import BaseModel, Field
from datetime import datetime
from typing import Literal, Optional

class Message(BaseModel):
    sender: Optional[int] = None
    receiver: Optional[int] = None
    message: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    message_type: Literal['text', 'image', 'file']

