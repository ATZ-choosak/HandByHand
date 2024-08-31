import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlmodel import SQLModel
from backend.models.user import User
from backend.models.items import Item
from backend.models.exchanges import Exchange

@pytest_asyncio.fixture(scope="function")
async def async_engine():
    engine = create_async_engine("sqlite+aiosqlite:///./test-data/test-sqlalchemy.db", echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.drop_all)  # ลบตารางก่อน
        await conn.run_sync(SQLModel.metadata.create_all)  # สร้างตารางใหม่
    yield engine
    await engine.dispose()

@pytest_asyncio.fixture
async def async_session(async_engine):
    async_session_maker = sessionmaker(
        bind=async_engine,
        class_=AsyncSession,
        expire_on_commit=False
    )
    async with async_session_maker() as session:
        yield session
