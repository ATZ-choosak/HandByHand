import os
import uuid
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from pydantic import EmailStr
from sqlalchemy import func, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select
from typing import List, Optional

from backend.models.exchanges import Exchange
from backend.models.items import Item
from backend.models.rating import Rating, RatingCreate
from backend.utils.utils import create_user_directory

from ..models.user import User, UserRead, UserCreate
from ..utils.auth import get_current_user, get_password_hash
from ..db import get_session

router = APIRouter()
# @router.delete("/{user_id}")
# async def delete_user(user_id: int, session: AsyncSession = Depends(get_session)):
#     db_user = await session.get(User, user_id)
#     if not db_user:
#         raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    
#     await session.delete(db_user)
#     await session.commit()
#     return {"message": "User deleted successfully"}
# Get current user's information
@router.get("/me", response_model=UserRead)
async def get_me(
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session)
):
    # Get post count
    post_count = await session.execute(select(func.count(Item.id)).where(Item.owner_id == current_user.id))
    
    current_user.post_count = post_count.scalar_one()

    # Get exchange complete count
    exchange_complete_count = await session.execute(
        select(func.count(Exchange.id))
        .join(Item, Exchange.requested_item_id == Item.id)
        .where(or_(
            Exchange.requester_id == current_user.id,
            Item.owner_id == current_user.id
        ))
        .where(Exchange.status == "accepted")
    )
    current_user.exchange_complete_count = exchange_complete_count.scalar_one()

    return current_user
@router.post("/rating")
async def create_rating(
    rating: RatingCreate,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session)
):
    # Check if the user exists
    user = await session.get(User, rating.user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Check if the user is trying to rate themselves
    if current_user.id == rating.user_id:
        raise HTTPException(status_code=400, detail="You cannot rate yourself")

    # Check if the current user has already rated this user
    existing_rating = await session.execute(
        select(Rating).where(Rating.user_id == rating.user_id, Rating.rater_id == current_user.id)
    )
    if existing_rating.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="You have already rated this user")

    # Create new rating
    new_rating = Rating(user_id=rating.user_id, rater_id=current_user.id, score=rating.score)
    session.add(new_rating)

    # Update user's rating
    user.rating = (user.rating * user.rating_count + rating.score) / (user.rating_count + 1)
    user.rating_count += 1

    await session.commit()
    return {"message": "Rating submitted successfully"}
# Get all users (Admin only)
@router.get("/", response_model=List[UserRead])
async def get_users(session: AsyncSession = Depends(get_session), current_user: User = Depends(get_current_user)):
    # Check if the current user is an admin
    if not current_user:
        raise HTTPException(status_code=403, detail="Only admins can access this endpoint")

    # Query users with their post count
    users_with_post_count = await session.execute(
        select(User, func.count(Item.id).label('post_count'))
        .outerjoin(Item, User.id == Item.owner_id)
        .group_by(User.id)
    )

    # Process the results
    result = []
    for user, post_count in users_with_post_count:
        user_dict = user.__dict__
        user_dict['post_count'] = post_count
        result.append(user_dict)

    return result

# Update current user's information
# Update current user's information
@router.put("/me", response_model=UserRead)
async def update_me(
    name: Optional[str] = Form(None),
    phone: Optional[str] = Form(None),
    address: Optional[str] = Form(None),
    lon: Optional[float] = Form(None),
    lat: Optional[float] = Form(None),
    profile_image: UploadFile = File(None),
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    db_user = await session.get(User, current_user.id)
    if not db_user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    db_user.name = name
    db_user.phone = phone
    db_user.address = address
    db_user.lon = lon
    db_user.lat = lat

    # Handle profile image upload if provided
    if profile_image:
        user_directory = f"images/{current_user.id}"
        create_user_directory(current_user.id)
        profile_image_id = str(uuid.uuid4())
        file_extension = os.path.splitext(profile_image.filename)[1]
        file_name = f"{profile_image_id}{file_extension}"
        file_location = f"{user_directory}/{file_name}"

        # Delete the old profile image if it exists
        if db_user.profile_image and os.path.exists(db_user.profile_image["url"]):
            os.remove(db_user.profile_image["url"])

        # Save the new profile image
        with open(file_location, "wb") as f:
            f.write(await profile_image.read())

        db_user.profile_image = {"id": profile_image_id, "url": file_location}
    
    session.add(db_user)
    await session.commit()
    await session.refresh(db_user)
    return db_user
@router.get("/{user_id}", response_model=UserRead)
async def get_user_by_id(
    user_id: int,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    user = await session.get(User, user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    
    # Get post count
    post_count = await session.execute(select(func.count(Item.id)).where(Item.owner_id == user.id))
    user.post_count = post_count.scalar_one()

    # Get exchange complete count
    exchange_complete_count = await session.execute(
        select(func.count(Exchange.id))
        .join(Item, Exchange.requested_item_id == Item.id)
        .where(or_(
            Exchange.requester_id == user.id,
            Item.owner_id == user.id
        ))
        .where(Exchange.status == "completed")
    )
    user.exchange_complete_count = exchange_complete_count.scalar_one()

    return user
# Delete current user
# @router.delete("/me")
# async def delete_me(session: AsyncSession = Depends(get_session), current_user: User = Depends(get_current_user)):
#     db_user = await session.get(User, current_user.id)
#     if not db_user:
#         raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    
#     await session.delete(db_user)
#     await session.commit()
#     return {"message": "User deleted successfully"}
