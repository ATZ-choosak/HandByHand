import os
import uuid
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status, Request
from fastapi.responses import HTMLResponse
import pytz
from sqlalchemy.ext.asyncio import AsyncSession
from jose import JWTError, jwt
from datetime import datetime, timedelta
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.templating import Jinja2Templates
from typing import TYPE_CHECKING, Annotated, Optional
from sqlmodel import select
from pydantic import EmailStr


from ..models.user import User, UserCreate, UserRead, UserLoginInput, UserResendVerifyInput, UserResetPasswordInput
from ..db import get_session
from ..utils.email import send_password_reset_email
from ..utils.auth import create_access_token, get_password_hash, verify_password,create_password_reset_token,create_verification_token
from ..utils.email import send_verification_email
from ..core.config import get_settings
from sqlalchemy.exc import IntegrityError

from ..utils.utils import create_user_directory
   

router = APIRouter()
settings = get_settings()

@router.post("/register", response_model=UserRead)
async def register_user(
    user_input: UserCreate,
    session: AsyncSession = Depends(get_session)
):
    existing_user = await session.execute(select(User).where(User.email == user_input.email))
    existing_user = existing_user.scalar_one_or_none()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email is already registered",
        )

    hashed_password = get_password_hash(user_input.password)
    thailand_tz = pytz.timezone('Asia/Bangkok')
    current_time = datetime.now(thailand_tz).replace(tzinfo=None)
    db_user = User(
        email=user_input.email,
        hashed_password=hashed_password,
        created_at=current_time,
        updated_at=current_time,
    )

    session.add(db_user)
    try:
        await session.commit()
        await session.refresh(db_user)
        create_user_directory(db_user.id)
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
    
@router.post("/login")
async def login_for_access_token(
    user_input: UserLoginInput,
    session: AsyncSession = Depends(get_session)
):
    user = await session.execute(select(User).where(User.email == user_input.username))
    user = user.scalar_one_or_none()
    if not user or not verify_password(user_input.password, user.hashed_password):
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
        data={"sub": user.email},
        expires_delta=access_token_expires
    )

    return {"access_token": access_token, "token_type": "bearer", "is_first_login": user.is_first_login}
@router.post("/token")
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), session: AsyncSession = Depends(get_session)):
    user = await session.execute(select(User).where(User.email == form_data.username))
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
        data={"sub": user.email},
        expires_delta=access_token_expires
    )

    return {"access_token": access_token, "token_type": "bearer", "is_first_login": user.is_first_login}
@router.post("/password-reset/request")
async def request_password_reset(
    input: UserResetPasswordInput,
    session: AsyncSession = Depends(get_session)
):
    result = await session.execute(select(User).where(User.email == input.email))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Email not found")
    reset_token = create_password_reset_token(user.email)
    reset_url = f"{settings.BASE_URL}/auth/reset-password?token={reset_token}"
    await send_password_reset_email(user.email, reset_url)
    return {"message": "Password reset email sent"}

@router.post("/password-reset/reset")
async def reset_password(
    request: Request,
    token: str = Form(...),
    new_password: str = Form(...),
    session: AsyncSession = Depends(get_session)
):
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
        email = payload.get("sub")
        if not email:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid token")
        result = await session.execute(select(User).where(User.email == email))
        user = result.scalar_one_or_none()
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
        hashed_password = get_password_hash(new_password)
        user.hashed_password = hashed_password
        await session.commit()
        return templates.TemplateResponse("password_reset_success.html", {"request": request})
    except JWTError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid token")
@router.post("/resend-verification")
async def resend_verification_link(
    input: UserResendVerifyInput,
    session: AsyncSession = Depends(get_session)
):
    result = await session.execute(select(User).where(User.email == input.email))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    if user.is_verified:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="User is already verified")
    verification_token = create_verification_token(user.email)
    verification_url = f"{settings.BASE_URL}/auth/verify-email?token={verification_token}"
    await send_verification_email(user.email, verification_url)
    return {"message": "Verification email resent successfully"}

templates = Jinja2Templates(directory="backend/template")

@router.get("/reset-password", response_class=HTMLResponse)
async def reset_password_page(request: Request, token: str):
    return templates.TemplateResponse("reset_password.html", {"request": request, "token": token})