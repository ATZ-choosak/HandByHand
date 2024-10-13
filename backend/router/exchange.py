from typing import List
import uuid
from fastapi import APIRouter, Body, Depends, HTTPException, status, Form
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from backend.models.category import Category
from backend.utils.email import send_exchange_confirmation_email
from ..models.exchanges import Exchange, ExchangeAcceptReject, ExchangeCreate, ExchangeRead, ExchangeRequestCheck, ExchangeUUIDCheck
from ..models.items import Item
from ..db import get_session
from ..utils.auth import get_current_user
from ..models.user import User

router = APIRouter()

@router.post("/request", response_model=ExchangeRead)
async def request_exchange(
    exchange: ExchangeCreate = Body(...),
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    # Verify the requested and offered items exist
    requested_item = await session.get(Item, exchange.requested_item_id)
    offered_item = await session.get(Item, exchange.offered_item_id)
    if not requested_item or not offered_item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Item not found")

    # Prevent users from requesting exchanges on their own items
    if requested_item.owner_id == current_user.id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot request exchange on your own item")

    # Create the exchange request
    db_exchange = Exchange(
        requested_item_id=exchange.requested_item_id,
        offered_item_id=exchange.offered_item_id,
        requester_id=current_user.id
    )
    session.add(db_exchange)
    await session.commit()
    await session.refresh(db_exchange)
    return db_exchange

@router.post("/exchange-request")
async def request_exchange_check(
    request: ExchangeRequestCheck,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    # Fetch the requested item
    requested_item = await session.get(Item, request.requested_item_id)
    if not requested_item:
        raise HTTPException(status_code=404, detail="Requested item not found")

    # Check if the item is exchangeable
    if not requested_item.is_exchangeable:
        # If not exchangeable, allow exchange directly
        return {"message": "Item is not exchangeable", "can_exchange": True}
    
    # If exchangeable, check user's items against preferred categories
    user_items = await session.execute(
        select(Item, Category)
        .join(Category, Item.category_id == Category.id)
        .where(Item.owner_id == current_user.id)
    )
    user_items = user_items.all()

    matching_items = []
    for item, category in user_items:
        # Check if the item's category_id matches any of the preferred_category_ids
        if item.category_id in requested_item.preferred_category_ids:
            matching_items.append({
                "id": item.id,
                "name": item.title,  # Assuming the item's name is stored in the 'title' field
                "category": {
                    "id": category.id,
                    "name": category.name
                }
            })

    if matching_items:
        return {
            "message": "Exchange possible based on category matching",
            "can_exchange": True,
            "matching_items": matching_items
        }
    else:
        return {
            "message": "No matching items for exchange",
            "can_exchange": False
        }
@router.get("/incoming", response_model=List[ExchangeRead])
async def get_incoming_exchanges(
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    result = await session.execute(
        select(Exchange).join(Item, Exchange.requested_item_id == Item.id).where(Item.owner_id == current_user.id)
    )
    exchanges = result.scalars().all()
    return exchanges

@router.post("/check-uuid")
async def check_exchange_uuid(
    data: ExchangeUUIDCheck,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    exchange = await session.get(Exchange, data.exchange_id)
    if not exchange:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Exchange not found")

    # Check if the current user is involved in the exchange
    requested_item = await session.get(Item, exchange.requested_item_id)
    offered_item = await session.get(Item, exchange.offered_item_id)
    if exchange.requester_id != current_user.id and requested_item.owner_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You are not involved in this exchange")

    if exchange.exchange_uuid != data.exchange_uuid:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid exchange UUID")

    if exchange.status != "exchanging":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Exchange is not in 'exchanging' status")

    # Update the exchange status to complete
    exchange.status = "completed"
    await session.commit()
    await session.refresh(exchange)

    # Fetch the requester and the owner of the requested item
    requester = await session.get(User, exchange.requester_id)
    owner = await session.get(User, requested_item.owner_id)

    # Send confirmation emails
    await send_exchange_confirmation_email(
        requester.email,
        requester.name or requester.email,
        requested_item.title,
        offered_item.title
    )
    await send_exchange_confirmation_email(
        owner.email,
        owner.name or owner.email,
        requested_item.title,
        offered_item.title
    )

    return {"message": "Exchange completed successfully", "exchange": exchange}


@router.get("/outgoing", response_model=List[ExchangeRead])
async def get_outgoing_exchanges(
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    # Query for all exchanges requested by the current user
    result = await session.execute(
        select(Exchange).where(Exchange.requester_id == current_user.id)
    )
    exchanges = result.scalars().all()
    return exchanges

@router.post("/accept", response_model=ExchangeRead)
async def accept_exchange(
    data: ExchangeAcceptReject,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    exchange = await session.get(Exchange, data.exchange_id)
    if not exchange:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Exchange not found")

    # Verify the current user is the owner of the requested item
    requested_item = await session.get(Item, exchange.requested_item_id)
    if requested_item.owner_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You are not the owner of the requested item")

    # Generate UUID for the exchange
    exchange_uuid = str(uuid.uuid4())

    # Update the exchange
    exchange.status = "exchanging"
    exchange.exchange_uuid = exchange_uuid
    await session.commit()
    await session.refresh(exchange)

    return exchange

@router.post("/reject", response_model=ExchangeRead)
async def reject_exchange(
    data: ExchangeAcceptReject = Body(...),
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    exchange = await session.get(Exchange, data.exchange_id)
    if not exchange:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Exchange not found")

    # Verify the current user is the owner of the requested item
    requested_item = await session.get(Item, exchange.requested_item_id)
    if requested_item.owner_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You are not the owner of the requested item")

    # Reject the exchange
    exchange.status = "rejected"
    await session.commit()
    await session.refresh(exchange)
    return exchange

@router.delete("/{exchange_id}")
async def delete_exchange(
    exchange_id: int,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    exchange = await session.get(Exchange, exchange_id)
    if not exchange:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Exchange not found")

    # Verify the current user is the owner of the exchange or the item
    requested_item = await session.get(Item, exchange.requested_item_id)
    if exchange.requester_id != current_user.id and requested_item.owner_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You are not authorized to delete this exchange")

    await session.delete(exchange)
    await session.commit()
    return {"message": "Exchange deleted successfully"}