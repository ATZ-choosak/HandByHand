from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select
from typing import List

from ..models.user import User, UserRead, UserCreate
from ..utils.auth import get_current_user, get_password_hash
from ..db import get_session

router = APIRouter()
@router.delete("/{user_id}")
async def delete_user(user_id: int, session: AsyncSession = Depends(get_session)):
    db_user = await session.get(User, user_id)
    if not db_user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    
    await session.delete(db_user)
    await session.commit()
    return {"message": "User deleted successfully"}
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
@router.put("/me", response_model=UserRead)
async def update_me(user_update: UserCreate, session: AsyncSession = Depends(get_session), current_user: User = Depends(get_current_user)):
    db_user = await session.get(User, current_user.id)
    if not db_user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    
    db_user.email = user_update.email
    db_user.name = user_update.name
    if user_update.password:
        db_user.hashed_password = get_password_hash(user_update.password)
    
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
