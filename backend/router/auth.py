from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.ext.asyncio import AsyncSession
from jose import JWTError, jwt
from datetime import timedelta
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.templating import Jinja2Templates
from typing import Annotated
from sqlmodel import select
from pydantic import EmailStr
from ..models.user import User, UserCreate, UserRead, UserLoginInput
from ..db import get_session
from ..utils.email import send_password_reset_email
from ..utils.auth import create_access_token, get_password_hash, verify_password,create_password_reset_token,create_verification_token
from ..utils.email import send_verification_email
from ..core.config import get_settings
from sqlalchemy.exc import IntegrityError
router = APIRouter()
settings = get_settings()

@router.post("/register", response_model=UserRead)
async def register_user(user: UserCreate, session: AsyncSession = Depends(get_session)):
    # ตรวจสอบว่ามีอีเมลนี้ในระบบหรือยัง
    existing_user = await session.execute(select(User).where(User.email == user.email))
    existing_user = existing_user.scalar_one_or_none()

    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email is already registered",
        )

    hashed_password = get_password_hash(user.password)
    db_user = User(email=user.email, name=user.name, hashed_password=hashed_password)
    session.add(db_user)
    
    try:
        await session.commit()
        await session.refresh(db_user)
    except IntegrityError:
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="An error occurred during registration",
        )

    verification_token = create_access_token(
        data={"sub": db_user.email},
        expires_delta=timedelta(minutes=settings.EMAIL_VERIFICATION_TOKEN_EXPIRE_MINUTES)
    )
    verification_url = f"{settings.BASE_URL}/auth/verify-email?token={verification_token}"
    await send_verification_email(db_user.email, verification_url)
    
    return db_user

@router.get("/verify-email")
async def verify_email(token: str, request: Request, session: AsyncSession = Depends(get_session)):
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
        email = payload.get("sub")
        if email is None:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid token")
        
        db_user = await session.execute(select(User).where(User.email == email))
        db_user = db_user.scalar_one_or_none()
        if not db_user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

        db_user.is_verified = True
        await session.commit()
        
        templates = Jinja2Templates(directory='backend/template')

        return templates.TemplateResponse(
            request=request, name="email_verify_success.html", context={ "message" :"Email verified successfully"}
        )

    except JWTError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid token")

@router.post("/token")
async def login_for_access_token(form_data: Annotated[OAuth2PasswordRequestForm, Depends(UserLoginInput)], session: AsyncSession = Depends(get_session)):
    await session.flush()
    user = await session.execute(select(User).where(User.email == form_data.username))  # ใช้ `email` ในการล็อกอิน
    user = user.scalar_one_or_none()
    
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if not user.is_verified:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email not verified",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.email}, expires_delta=access_token_expires  # เก็บ `email` ในโทเค็น
    )
    return {"access_token": access_token, "token_type": "bearer"}

@router.post("/password-reset/request")
async def request_password_reset(email: EmailStr, session: AsyncSession = Depends(get_session)):
    # Find user by email
    result = await session.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Email not found")

    # Generate a password reset token
    reset_token = create_password_reset_token(user.email)

    # Create password reset URL
    reset_url = f"{settings.BASE_URL}/reset-password?token={reset_token}"

    # Send password reset email
    await send_password_reset_email(user.email, reset_url)

    return {"message": "Password reset email sent"}


@router.post("/password-reset/reset")
async def reset_password(token: str, new_password: str, session: AsyncSession = Depends(get_session)):
    try:
        # Decode token
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
        email = payload.get("sub")

        if not email:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid token")

        # Find the user by email
        result = await session.execute(select(User).where(User.email == email))
        user = result.scalar_one_or_none()

        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

        # Hash the new password
        hashed_password = get_password_hash(new_password)

        # Update user password
        user.hashed_password = hashed_password
        await session.commit()

        return {"message": "Password reset successful"}

    except JWTError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid token")

@router.post("/resend-verification")
async def resend_verification_link(email: EmailStr, session: AsyncSession = Depends(get_session)):
    # Find user by email
    result = await session.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    if user.is_verified:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="User is already verified")

    # Generate a new verification token
    verification_token = create_verification_token(user.email)

    # Create verification URL
    verification_url = f"http://127.0.0.1:8000/api/auth/verify-email?token={verification_token}"

    # Send verification email
    await send_verification_email(user.email, verification_url)

    return {"message": "Verification email resent successfully"}