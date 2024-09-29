import os
import uuid
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from pydantic import EmailStr
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select
from typing import List, Optional

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
async def get_me(current_user: User = Depends(get_current_user)):
    return current_user

# Get all users (Admin only)
@router.get("/", response_model=List[UserRead])
async def get_users(session: AsyncSession = Depends(get_session), current_user: User = Depends(get_current_user)):
    # Add your logic for checking if the current user is an admin
    users = await session.execute(select(User))
    return users.scalars().all()

# Update current user's information
# Update current user's information
@router.put("/me", response_model=UserRead)
async def update_me(
    email: EmailStr,
    phone: Optional[str] = None,
    address: Optional[str] = None,
    lon: Optional[float] = None,
    lat: Optional[float] = None,
    profile_image: UploadFile = File(None),
    password: Optional[str] = None,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    db_user = await session.get(User, current_user.id)
    if not db_user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    db_user.email = email
    db_user.phone = phone
    db_user.address = address
    db_user.lon = lon
    db_user.lat = lat

    if password:
        db_user.hashed_password = get_password_hash(password)

    # Handle profile image upload if provided
    if profile_image:
        user_directory = f"images/{current_user.id}"
        create_user_directory(current_user.id)
        profile_image_id = str(uuid.uuid4())  # สร้าง ID สำหรับรูปภาพโปรไฟล์ใหม่
        file_location = f"{user_directory}/{profile_image_id}.{profile_image.filename.split('.')[-1]}"

        # Define the path for the old profile image if it exists
        old_image_path = f"{user_directory}/{current_user.profile_image_url.split('/')[-1]}" if current_user.profile_image_url else None

        # Delete the old profile image if it exists
        if old_image_path and os.path.exists(old_image_path):
            os.remove(old_image_path)
            print(f"Deleted old profile image: {old_image_path}")

        # Save the new profile image
        file_location = f"{user_directory}/{profile_image.filename}"
        with open(file_location, "wb") as f:
            f.write(await profile_image.read())

        db_user.profile_image_url = file_location
        db_user.profile_image_id = profile_image_id 

    session.add(db_user)
    await session.commit()
    await session.refresh(db_user)
    return db_user

# Delete current user
# @router.delete("/me")
# async def delete_me(session: AsyncSession = Depends(get_session), current_user: User = Depends(get_current_user)):
#     db_user = await session.get(User, current_user.id)
#     if not db_user:
#         raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    
#     await session.delete(db_user)
#     await session.commit()
#     return {"message": "User deleted successfully"}
