from pydantic import BaseModel, Field
from typing import Literal, Optional, List
from datetime import datetime
from .messages import Message

class Chat(BaseModel):
    user1: Optional[int] = None # Optional User ID
    user2: int  # User ID
    messages: Optional[List[Message]] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)  # Auto-set to current time

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

# เพิ่ม Pydantic models สำหรับ request bodies
class CreateChatRequest(BaseModel):
    user: int

class SendMessageRequest(BaseModel):
    chat_id: str
    message: str
    message_type: Literal['text', 'image', 'file']