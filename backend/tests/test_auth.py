import pytest
from backend.models.chats import Chat
from backend.models.user import User
from sqlalchemy.ext.asyncio import AsyncSession

@pytest.mark.asyncio
async def test_create_account(async_session: AsyncSession):
    user = User(name="Test User", email="testuser1@example.com", hashed_password="hashedpassword")
    async_session.add(user)
    await async_session.commit()
    await async_session.refresh(user)
   
    assert user.id is not None
    assert user.name == "Test User"
    assert user.email == "testuser1@example.com"
