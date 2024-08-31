from fastapi import APIRouter, Depends, HTTPException
from bson import ObjectId
from typing import Literal, List, Dict, Any
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession

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
    
    # Find all chat sessions where the current user is either user1 or user2
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

        if chat["user1"] == current_user.id: # type: ignore
            user = await session.get(User, chat["user2"]) # type: ignore

        if chat["user2"] == current_user.id: # type: ignore
            user = await session.get(User, chat["user1"]) # type: ignore

        chat_list.append({
            "_id": str(chat["_id"]),  # Convert ObjectId to string for JSON serialization # type: ignore
            "user" : {
                "name" : user.name
            }
        })

    return chat_list

@router.post("", response_model=dict)
async def create_chat(
    user: int,
    current_user: User = Depends(get_current_user)
):
    collection = get_db().get_collection("chats")

    # Check if a chat session already exists
    existing_chat = collection.find_one({
        "$or": [
            {"user1": current_user.id, "user2": user},
            {"user1": user, "user2": current_user.id}
        ]
    })

    if existing_chat:
        return {"message": "Chat session already exists.", "chat_id": str(existing_chat["_id"])} # type: ignore

    # Create a new chat session
    chat_data = dict()
    chat_data["user1"] = current_user.id
    chat_data["user2"] = user
    chat_data["messages"] = []  # Initialize messages as an empty array
    result = collection.insert_one(chat_data)

    return {"message": "Chat session created successfully.", "chat_id": str(result.inserted_id)}


@router.post("/send_message", response_model=Message)
async def send_message(
    chat_id: str,
    message: str,
    message_type: Literal['text', 'image', 'file'],
    current_user: User = Depends(get_current_user)
):
    collection = get_db().get_collection("chats")

    # Convert chat_id to ObjectId
    try:
        chat_object_id = ObjectId(chat_id)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid chat ID format: {str(e)}")

    # Verify the chat exists
    chat = collection.find_one({"_id": chat_object_id})
    if chat is None:
        raise HTTPException(status_code=404, detail=f"Chat session with ID {chat_id} not found")

    # Check if the current user is part of the chat
    if chat["user1"] != current_user.id and chat["user2"] != current_user.id: # type: ignore
        raise HTTPException(status_code=403, detail="Not authorized to send message in this chat")

    # Ensure the messages field is an array
    if chat.get("messages") is None:
        chat["messages"] = [] # type: ignore

    # Add the message to the chat
    message_data = {
        "sender": current_user.id,
        "receiver": chat["user2"] if chat["user1"] == current_user.id else chat["user1"], # type: ignore
        "message": message,
        "timestamp": datetime.utcnow(),
        "message_type": message_type
    }
    chat_update = {"$push": {"messages": message_data}}
    result = collection.update_one({"_id": chat_object_id}, chat_update)

    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail=f"Chat session with ID {chat_id} not found after update")

    # Retrieve the updated chat to return the message
    updated_chat = collection.find_one({"_id": chat_object_id})
    if not updated_chat:
        raise HTTPException(status_code=404, detail=f"Chat session with ID {chat_id} not found")


    return message_data

@router.get("/messages/{chat_id}", response_model=List[Dict[str, Any]])
async def get_messages_by_chat_id(
    chat_id: str,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session)
) -> List[Dict[str, Any]]:
    collection = get_db().get_collection("chats")

    # Convert chat_id to ObjectId
    try:
        chat_object_id = ObjectId(chat_id)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid chat ID format: {str(e)}")

    # Find the chat session by chat_id
    chat = collection.find_one({"_id": chat_object_id})
    if chat is None:
        raise HTTPException(status_code=404, detail=f"Chat session with ID {chat_id} not found")

    # Check if the current user is part of the chat
    if chat["user1"] != current_user.id and chat["user2"] != current_user.id: # type: ignore
        raise HTTPException(status_code=403, detail="Not authorized to view messages in this chat")

    # Retrieve the messages from the chat
    messages = chat.get("messages", [])

    # Replace sender and receiver IDs with names
    for msg in messages:
        sender = await session.get(User, msg["sender"]) # type: ignore
        receiver = await session.get(User, msg["receiver"]) # type: ignore

        msg["sender_name"] = sender.name # type: ignore
        msg["receiver_name"] = receiver.name # type: ignore

        # Add a flag to indicate if the sender or receiver is the current user
        msg["sender_is_me"] = sender.id == current_user.id # type: ignore
        msg["receiver_is_me"] = receiver.id == current_user.id # type: ignore

    return messages
