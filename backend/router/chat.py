from fastapi import APIRouter,status, Body, Depends, Form, HTTPException
from bson import ObjectId
from typing import Literal, List, Dict, Any
from datetime import datetime
from requests import session
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models.chats import CreateChatRequest, SendMessageRequest

from ..models.user import User
from ..models.messages import Message
from ..utils.auth import get_current_user, get_session
from ..db.mongodb import get_db

router = APIRouter()

@router.get("/sessions", response_model=List[Dict[str, Any]])
async def get_chat_sessions(
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session)
) -> List[Dict[str, Any]]:
    collection = get_db().get_collection("chats")
    chats_cursor = collection.find({
        "$or": [
            {"user1": current_user.id},
            {"user2": current_user.id}
        ],
    })
    
    if chats_cursor is None:
        return []
    
    chat_list = []
    for chat in chats_cursor:
        other_user_id = chat["user2"] if chat["user1"] == current_user.id else chat["user1"]
        other_user = await session.get(User, other_user_id)
        
        chat_info = {
            "_id": str(chat["_id"]),
            "user": {
                "id": other_user_id,
                "name": other_user.name if other_user else "Unknown User",
                "email": other_user.email if other_user else None,
                "profile_image": other_user.profile_image if other_user and other_user.profile_image else None
            }
        }
        chat_list.append(chat_info)
    
    return chat_list

@router.post("", response_model=dict)
async def create_chat(
    chat_request: CreateChatRequest = Body(...),
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session)
):
    # ตรวจสอบว่า user_id ที่ระบุมีอยู่จริง
    target_user = await session.get(User, chat_request.user)
    if not target_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with id {chat_request.user} not found"
        )

    collection = get_db().get_collection("chats")
    
    # Check if a chat session already exists
    existing_chat = collection.find_one({
        "$or": [
            {"user1": current_user.id, "user2": chat_request.user},
            {"user1": chat_request.user, "user2": current_user.id}
        ]
    })
    
    if existing_chat:
        return {"message": "Chat session already exists.", "chat_id": str(existing_chat["_id"])}
    
    # Create a new chat session
    chat_data = {
        "user1": current_user.id,
        "user2": chat_request.user,
        "messages": []  # Initialize messages as an empty array
    }
    result = collection.insert_one(chat_data)
    return {"message": "Chat session created successfully.", "chat_id": str(result.inserted_id)}
@router.post("/send_message", response_model=Message)
async def send_message(
    message_request: SendMessageRequest = Body(...),
    current_user: User = Depends(get_current_user)
):
    collection = get_db().get_collection("chats")
    
    # Convert chat_id to ObjectId
    try:
        chat_object_id = ObjectId(message_request.chat_id)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid chat ID format: {str(e)}")
    
    # Verify the chat exists
    chat = collection.find_one({"_id": chat_object_id})
    if chat is None:
        raise HTTPException(status_code=404, detail=f"Chat session with ID {message_request.chat_id} not found")
    
    # Check if the current user is part of the chat
    if chat["user1"] != current_user.id and chat["user2"] != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to send message in this chat")
    
    # Ensure the messages field is an array
    if chat.get("messages") is None:
        chat["messages"] = []
    
    # Add the message to the chat
    message_data = {
        "sender": current_user.id,
        "receiver": chat["user2"] if chat["user1"] == current_user.id else chat["user1"],
        "message": message_request.message,
        "timestamp": datetime.utcnow(),
        "message_type": message_request.message_type
    }
    
    chat_update = {"$push": {"messages": message_data}}
    result = collection.update_one({"_id": chat_object_id}, chat_update)
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail=f"Chat session with ID {message_request.chat_id} not found after update")
    
    # Retrieve the updated chat to return the message
    updated_chat = collection.find_one({"_id": chat_object_id})
    if not updated_chat:
        raise HTTPException(status_code=404, detail=f"Chat session with ID {message_request.chat_id} not found")
    
    return message_data

@router.get("/messages/{chat_id}", response_model=List[Dict[str, Any]])
async def get_messages_by_chat_id(
    chat_id: str,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session)
) -> List[Dict[str, Any]]:
    collection = get_db().get_collection("chats")
    
    try:
        chat_object_id = ObjectId(chat_id)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid chat ID format: {str(e)}")
    
    chat = collection.find_one({"_id": chat_object_id})
    if chat is None:
        raise HTTPException(status_code=404, detail=f"Chat session with ID {chat_id} not found")
    
    if chat["user1"] != current_user.id and chat["user2"] != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to view messages in this chat")
    
    messages = chat.get("messages", [])
    
    for msg in messages:
        sender = await session.get(User, msg["sender"])
        receiver = await session.get(User, msg["receiver"])
        
        msg["sender"] = {
            "id": sender.id,
            "name": sender.name if sender else "Unknown User",
            "email": sender.email if sender else None,
            "profile_image": sender.profile_image if sender and sender.profile_image else None
        }
        msg["receiver"] = {
            "id": receiver.id,
            "name": receiver.name if receiver else "Unknown User",
            "email": receiver.email if receiver else None,
            "profile_image": receiver.profile_image if receiver and receiver.profile_image else None
        }
        
        msg["sender_is_me"] = sender.id == current_user.id if sender else False
        msg["receiver_is_me"] = receiver.id == current_user.id if receiver else False
    
    return messages
