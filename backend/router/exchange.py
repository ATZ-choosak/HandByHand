from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from sqlmodel import select
from ..models.exchanges import Exchange, ExchangeCreate, ExchangeRead
from ..models.items import Item
from ..db import get_session
from ..utils.auth import get_current_user

router = APIRouter()

@router.post("/request", response_model=ExchangeRead)
async def request_exchange(exchange: ExchangeCreate, session: AsyncSession = Depends(get_session), current_user=Depends(get_current_user)):
    item = await session.get(Item, exchange.item_id)
    if item.owner_id == current_user.id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="You cannot exchange your own item.")
    
    db_exchange = Exchange(**exchange.dict(exclude={"requester_id"}), requester_id=current_user.id)
    session.add(db_exchange)
    await session.commit()
    await session.refresh(db_exchange)
    return db_exchange

@router.get("/{item_id}/requests", response_model=List[ExchangeRead])
async def get_exchange_requests(item_id: int, session: AsyncSession = Depends(get_session), current_user=Depends(get_current_user)):
    item = await session.get(Item, item_id)
    if item.owner_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You do not own this item.")
    
    exchanges = await session.execute(select(Exchange).where(Exchange.item_id == item_id))
    return exchanges.scalars().all()

@router.post("/{exchange_id}/accept")
async def accept_exchange(exchange_id: int, session: AsyncSession = Depends(get_session), current_user=Depends(get_current_user)):
    exchange = await session.get(Exchange, exchange_id)
    if not exchange:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Exchange request not found.")
    
    item = await session.get(Item, exchange.item_id)
    if item.owner_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You do not own this item.")
    
    exchange.status = "accepted"
    await session.commit()
    return {"message": "Exchange accepted", "exchange_id": exchange_id, "status": exchange.status}

@router.post("/{exchange_id}/reject")
async def reject_exchange(exchange_id: int, session: AsyncSession = Depends(get_session), current_user=Depends(get_current_user)):
    exchange = await session.get(Exchange, exchange_id)
    if not exchange:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Exchange request not found.")
    
    item = await session.get(Item, exchange.item_id)
    if item.owner_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You do not own this item.")
    
    exchange.status = "rejected"
    await session.commit()
    return {"message": "Exchange rejected", "exchange_id": exchange_id, "status": exchange.status}

@router.delete("/{exchange_id}", response_model=dict)
async def delete_exchange(exchange_id: int, session: AsyncSession = Depends(get_session), current_user=Depends(get_current_user)):
    # ตรวจสอบว่ามี exchange ที่มี exchange_id หรือไม่
    exchange = await session.get(Exchange, exchange_id)
    
    if not exchange:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Exchange not found")
    
    # ตรวจสอบว่า current_user เป็นผู้ร้องขอแลกเปลี่ยนนี้หรือไม่
    if exchange.requester_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not allowed to delete this exchange")
    
    await session.delete(exchange)
    await session.commit()
    return {"message": "Exchange deleted successfully"}