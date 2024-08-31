from typing import List
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select
from ..models.items import Item, ItemCreate, ItemRead
from ..db import get_session
from ..utils.auth import get_current_user
from ..models.user import User

router = APIRouter()

# Create a new item
@router.post("/", response_model=ItemRead)
async def create_item(
    item: ItemCreate, 
    session: AsyncSession = Depends(get_session), 
    current_user: User = Depends(get_current_user)
):
    db_item = Item(**item.dict(), owner_id=current_user.id)
    session.add(db_item)
    await session.commit()
    await session.refresh(db_item)
    return db_item

# Get all items posted by the current user
@router.get("/my-items", response_model=List[ItemRead])
async def get_user_items(
    session: AsyncSession = Depends(get_session), 
    current_user: User = Depends(get_current_user)
):
    result = await session.execute(select(Item).where(Item.owner_id == current_user.id))
    items = result.scalars().all()
    return items

# Get all items (optionally with search query)
@router.get("/", response_model=List[ItemRead])
async def get_items(
    session: AsyncSession = Depends(get_session), 
    query: str = Query(None, min_length=3, description="Search query for items")
):
    statement = select(Item)
    
    if query:
        statement = statement.where(Item.title.ilike(f"%{query}%"))
    
    result = await session.execute(statement)
    items = result.scalars().all()
    return items

# Get item by ID
@router.get("/{item_id}", response_model=ItemRead)
async def get_item(
    item_id: int, 
    session: AsyncSession = Depends(get_session)
):
    item = await session.get(Item, item_id)
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Item not found")
    return item

# Update an existing item
@router.put("/{item_id}", response_model=ItemRead)
async def update_item(
    item_id: int, 
    item: ItemCreate, 
    session: AsyncSession = Depends(get_session), 
    current_user: User = Depends(get_current_user)
):
    db_item = await session.get(Item, item_id)
    if not db_item or db_item.owner_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Item not found or you do not have permission to update it")
    
    db_item.title = item.title
    db_item.description = item.description
    
    await session.commit()
    await session.refresh(db_item)
    return db_item

# Delete an item
@router.delete("/{item_id}")
async def delete_item(
    item_id: int, 
    session: AsyncSession = Depends(get_session), 
    current_user: User = Depends(get_current_user)
):
    db_item = await session.get(Item, item_id)
    if not db_item or db_item.owner_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Item not found or you do not have permission to delete it")
    
    await session.delete(db_item)
    await session.commit()
    return {"message": "Item deleted successfully"}
