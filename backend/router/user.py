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
    # Query the current user with their post count
    result = await session.execute(
        select(User, func.count(Item.id).label('post_count'))
        .outerjoin(Item, User.id == Item.owner_id)
        .where(User.id == current_user.id)
        .group_by(User.id)
    )
    user, post_count = result.first()

    # Update the user object with the post count
    user.post_count = post_count

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

    # Refresh the user to ensure we have the latest data
    await session.refresh(user)

    return user

    # exchange_complete_count is already stored in the User model
    # No need to recalculate it here

    # Refresh the current_user to ensure we have the latest data
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

    # Create new rating
    new_rating = Rating(user_id=rating.user_id, rater_id=current_user.id, score=rating.score)
    session.add(new_rating)

    # Calculate the new average rating
    all_ratings = await session.execute(
        select(Rating.score).where(Rating.user_id == rating.user_id)
    )
    all_ratings = all_ratings.scalars().all()
    
    user.rating = sum(all_ratings) / len(all_ratings)
    user.rating_count = len(all_ratings)

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
    # Query the user with their post count
    result = await session.execute(
        select(User, func.count(Item.id).label('post_count'))
        .outerjoin(Item, User.id == Item.owner_id)
        .where(User.id == user_id)
        .group_by(User.id)
    )
    user_and_post_count = result.first()

    if not user_and_post_count:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    user, post_count = user_and_post_count

    # Update the user object with the post count
    user.post_count = post_count

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

    # Refresh the user to ensure we have the latest data
    await session.refresh(user)

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
