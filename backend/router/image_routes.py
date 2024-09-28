import os
from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from typing import TYPE_CHECKING, List


from backend.models.items import Item
from ..db import get_session
from ..models.user import User
from ..utils.auth import get_current_user

from ..utils.utils import create_user_directory
router = APIRouter()

@router.post("/upload-profile-image")
async def upload_profile_image(file: UploadFile = File(...), current_user: User = Depends(get_current_user), session: AsyncSession = Depends(get_session)):
    user_directory = f"images/{current_user.id}"
    
    # Ensure the user's directory exists
    create_user_directory(current_user.id)

    # Define the path for the old profile image if it exists
    old_image_path = f"{user_directory}/{current_user.profile_image_url.split('/')[-1]}" if current_user.profile_image_url else None

    # Delete the old profile image if it exists
    if old_image_path and os.path.exists(old_image_path):
        os.remove(old_image_path)
        print(f"Deleted old profile image: {old_image_path}")

    # Save the new profile image
    file_location = f"{user_directory}/{file.filename}"  # Save the file in the user's directory
    with open(file_location, "wb") as f:
        f.write(await file.read())

    # Update user's profile image URL in the database
    current_user.profile_image_url = file_location
    session.add(current_user)
    await session.commit()

    return {"message": "Profile image uploaded successfully", "url": file_location}
