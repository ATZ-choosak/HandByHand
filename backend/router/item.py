from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select
from ..models.items import Item, ItemCreate, ItemRead
from ..db import get_session
from ..utils.auth import get_current_user

router = APIRouter()

@router.post("/", response_model=ItemRead)
async def create_item(item: ItemCreate, session: AsyncSession = Depends(get_session), current_user=Depends(get_current_user)):
    db_item = Item(**item.dict(), owner_id=current_user.id)
    session.add(db_item)
    await session.commit()
    await session.refresh(db_item)
    return db_item

@router.get("/", response_model=List[ItemRead])
async def get_items(session: AsyncSession = Depends(get_session)):
    items = await session.execute(select(Item))
    return items.scalars().all()

@router.get("/{item_id}", response_model=ItemRead)
async def get_item(item_id: int, session: AsyncSession = Depends(get_session)):
    item = await session.execute(select(Item).where(Item.id == item_id))
    item = item.scalar_one_or_none()
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Item not found")
    return item

@router.put("/{item_id}", response_model=ItemRead)
async def update_item(item_id: int, item: ItemCreate, session: AsyncSession = Depends(get_session), current_user=Depends(get_current_user)):
    db_item = await session.execute(select(Item).where(Item.id == item_id, Item.owner_id == current_user.id))
    db_item = db_item.scalar_one_or_none()
    if not db_item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Item not found")
    db_item.title = item.title
    db_item.description = item.description
    await session.commit()
    await session.refresh(db_item)
    return db_item

@router.delete("/{item_id}")
async def delete_item(item_id: int, session: AsyncSession = Depends(get_session), current_user=Depends(get_current_user)):
    db_item = await session.execute(select(Item).where(Item.id == item_id, Item.owner_id == current_user.id))
    db_item = db_item.scalar_one_or_none()
    if not db_item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Item not found")
    await session.delete(db_item)
    await session.commit()
    return {"message": "Item deleted"}
