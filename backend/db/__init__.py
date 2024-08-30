from typing import AsyncIterator
from sqlmodel import SQLModel
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import SQLAlchemyError

from backend.models.items import *
from backend.models.user import *
from backend.models.exchanges import *

connect_args = {}

engine = None


def init_db(settings):
    global engine

    engine = create_async_engine(
        settings.DATABASE_URL,
        echo=True,
        future=True,
        connect_args=connect_args,
    )


async def recreate_table():
    try:
        async with engine.begin() as conn:
            await conn.run_sync(SQLModel.metadata.drop_all)
            await conn.run_sync(SQLModel.metadata.create_all)
    except SQLAlchemyError as e:
        print(f"Database error occurred: {e}")

async def get_session() -> AsyncIterator[AsyncSession]:
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with async_session() as session:
        yield session


async def close_session():
    global engine
    if engine is None:
        raise Exception("DatabaseSessionManager is not initialized")
    await engine.dispose()
