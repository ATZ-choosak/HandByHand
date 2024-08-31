import pytest
from backend.models.items import Item
from backend.models.user import User
from sqlalchemy.ext.asyncio import AsyncSession

@pytest.mark.asyncio
async def test_create_item(async_session: AsyncSession):
    user = User(name="Test User", email="testuser@example.com", hashed_password="hashedpassword")
    async_session.add(user)
    await async_session.commit()
    await async_session.refresh(user)
    
    item = Item(title="Test Item", description="Test Description", owner_id=user.id)
    async_session.add(item)
    await async_session.commit()
    await async_session.refresh(item)
    
    assert item.id is not None
    assert item.title == "Test Item"

@pytest.mark.asyncio
async def test_read_item(async_session: AsyncSession):
    # สร้างข้อมูล User และ Item ก่อน
    user = User(name="Test User", email="testuser@example.com", hashed_password="hashedpassword")
    async_session.add(user)
    await async_session.commit()
    await async_session.refresh(user)
    
    item = Item(title="Test Item", description="Test Description", owner_id=user.id)
    async_session.add(item)
    await async_session.commit()
    await async_session.refresh(item)
    
    # ตรวจสอบว่า item ที่สร้างมีชื่อเป็น "Test Item"
    item_from_db = await async_session.get(Item, item.id)
    
    assert item_from_db is not None
    assert item_from_db.title == "Test Item"

@pytest.mark.asyncio
async def test_update_item(async_session: AsyncSession):
    # สร้างข้อมูล User และ Item ก่อน
    user = User(name="Test User", email="testuser@example.com", hashed_password="hashedpassword")
    async_session.add(user)
    await async_session.commit()
    await async_session.refresh(user)
    
    item = Item(title="Test Item", description="Test Description", owner_id=user.id)
    async_session.add(item)
    await async_session.commit()
    await async_session.refresh(item)
    
    # เริ่มการทดสอบการ update
    item.title = "Updated Item"
    await async_session.commit()
    await async_session.refresh(item)
    
    assert item.title == "Updated Item"

@pytest.mark.asyncio
async def test_delete_item(async_session: AsyncSession):
    # สร้างข้อมูล User และ Item ก่อน
    user = User(name="Test User", email="testuser@example.com", hashed_password="hashedpassword")
    async_session.add(user)
    await async_session.commit()
    await async_session.refresh(user)
    
    item = Item(title="Test Item", description="Test Description", owner_id=user.id)
    async_session.add(item)
    await async_session.commit()
    await async_session.refresh(item)
    
    # เริ่มการทดสอบการลบ
    await async_session.delete(item)
    await async_session.commit()
    
    item = await async_session.get(Item, item.id)
    assert item is None
