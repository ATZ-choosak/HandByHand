import pytest
from backend.models.exchanges import Exchange
from backend.models.items import Item
from backend.models.user import User
from sqlalchemy.ext.asyncio import AsyncSession

@pytest.mark.asyncio
async def test_create_exchange(async_session: AsyncSession):
    # Create Users
    user1 = User(name="User 1", email="user1@example.com", hashed_password="hashedpassword")
    user2 = User(name="User 2", email="user2@example.com", hashed_password="hashedpassword")
    
    async_session.add_all([user1, user2])
    await async_session.commit()
    await async_session.refresh(user1)
    await async_session.refresh(user2)
    
    # Create Items
    item1 = Item(title="Item 1", owner_id=user1.id)
    item2 = Item(title="Item 2", owner_id=user2.id)
    
    async_session.add_all([item1, item2])
    await async_session.commit()
    await async_session.refresh(item1)
    await async_session.refresh(item2)
    
    # Create Exchange
    exchange = Exchange(
        requester_id=user2.id,
        requested_item_id=item1.id,
        offered_item_id=item2.id,
        status="pending"
    )
    
    async_session.add(exchange)
    await async_session.commit()
    await async_session.refresh(exchange)
    
    assert exchange.id is not None
    assert exchange.requested_item_id == item1.id
    assert exchange.offered_item_id == item2.id
    assert exchange.requester_id == user2.id
    assert exchange.status == "pending"

@pytest.mark.asyncio
async def test_read_exchange(async_session: AsyncSession):
    # สร้างข้อมูลที่จำเป็นสำหรับการทดสอบ
    user1 = User(name="User 1", email="user1@example.com", hashed_password="hashedpassword")
    user2 = User(name="User 2", email="user2@example.com", hashed_password="hashedpassword")
    
    async_session.add_all([user1, user2])
    await async_session.commit()
    await async_session.refresh(user1)
    await async_session.refresh(user2)
    
    item1 = Item(title="Item 1", owner_id=user1.id)
    item2 = Item(title="Item 2", owner_id=user2.id)
    
    async_session.add_all([item1, item2])
    await async_session.commit()
    await async_session.refresh(item1)
    await async_session.refresh(item2)
    
    exchange = Exchange(
        requester_id=user2.id,
        requested_item_id=item1.id,
        offered_item_id=item2.id,
        status="pending"
    )
    async_session.add(exchange)
    await async_session.commit()
    await async_session.refresh(exchange)
    
    # เริ่มทดสอบการอ่าน
    exchange_from_db = await async_session.get(Exchange, exchange.id)
    assert exchange_from_db is not None
    assert exchange_from_db.status == "pending"

@pytest.mark.asyncio
async def test_accept_exchange(async_session: AsyncSession):
    # สร้างข้อมูลที่จำเป็นสำหรับการทดสอบ
    user1 = User(name="User 1", email="user1@example.com", hashed_password="hashedpassword")
    user2 = User(name="User 2", email="user2@example.com", hashed_password="hashedpassword")
    
    async_session.add_all([user1, user2])
    await async_session.commit()
    await async_session.refresh(user1)
    await async_session.refresh(user2)
    
    item1 = Item(title="Item 1", owner_id=user1.id)
    item2 = Item(title="Item 2", owner_id=user2.id)
    
    async_session.add_all([item1, item2])
    await async_session.commit()
    await async_session.refresh(item1)
    await async_session.refresh(item2)
    
    exchange = Exchange(
        requester_id=user2.id,
        requested_item_id=item1.id,
        offered_item_id=item2.id,
        status="pending"
    )
    async_session.add(exchange)
    await async_session.commit()
    await async_session.refresh(exchange)
    
    # เริ่มทดสอบการแก้ไข Exchange
    exchange.status = "accepted"
    await async_session.commit()
    await async_session.refresh(exchange)
    
    assert exchange.status == "accepted"

@pytest.mark.asyncio
async def test_delete_exchange(async_session: AsyncSession):
    # สร้างข้อมูลที่จำเป็นสำหรับการทดสอบ
    user1 = User(name="User 1", email="user1@example.com", hashed_password="hashedpassword")
    user2 = User(name="User 2", email="user2@example.com", hashed_password="hashedpassword")
    
    async_session.add_all([user1, user2])
    await async_session.commit()
    await async_session.refresh(user1)
    await async_session.refresh(user2)
    
    item1 = Item(title="Item 1", owner_id=user1.id)
    item2 = Item(title="Item 2", owner_id=user2.id)
    
    async_session.add_all([item1, item2])
    await async_session.commit()
    await async_session.refresh(item1)
    await async_session.refresh(item2)
    
    exchange = Exchange(
        requester_id=user2.id,
        requested_item_id=item1.id,
        offered_item_id=item2.id,
        status="pending"
    )
    async_session.add(exchange)
    await async_session.commit()
    await async_session.refresh(exchange)
    
    # เริ่มทดสอบการลบ Exchange
    await async_session.delete(exchange)
    await async_session.commit()
    
    exchange_from_db = await async_session.get(Exchange, exchange.id)
    assert exchange_from_db is None
