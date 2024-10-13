import asyncio
import random
from datetime import datetime
from sqlmodel import select
from backend.db import init_db, get_session
from backend.models.items import Item
from backend.models.user import User
from backend.models.category import Category
from backend.core.config import get_settings

# Sample data for items
sample_titles = [
    "โทรศัพท์มือถือ", "แล็ปท็อป", "กล้องดิจิตอล", "หูฟังไร้สาย", "สมาร์ทวอทช์",
    "เครื่องชงกาแฟ", "หม้อหุงข้าวไฟฟ้า", "เครื่องปิ้งขนมปัง", "เตาอบไมโครเวฟ", "เครื่องดูดฝุ่น",
    "จักรยาน", "รองเท้าวิ่ง", "ชุดโยคะ", "ลู่วิ่งไฟฟ้า", "ดัมเบล",
    "กีตาร์", "เปียโนไฟฟ้า", "กลองชุด", "ไมโครโฟน", "ลำโพงบลูทูธ"
]

sample_descriptions = [
    "สภาพดีมาก ใช้งานได้ปกติ", "ของใหม่ ยังไม่ได้แกะกล่อง", "ใช้งานมาประมาณ 1 ปี",
    "มีรอยขีดข่วนเล็กน้อย แต่ใช้งานได้ปกติ", "สภาพ 90% ใช้งานน้อย",
    "ของมือสอง สภาพดี", "เพิ่งซื้อมาได้ 3 เดือน", "ใช้งานมาประมาณ 6 เดือน",
    "สภาพใหม่ ใช้งานเพียง 2-3 ครั้ง", "มีประกันศูนย์เหลืออีก 1 ปี"
]

async def add_items(num_items: int):
    settings = get_settings()
    init_db(settings)
    
    async for session in get_session():
        # Get all users
        result = await session.execute(select(User))
        users = result.scalars().all()
        
        # Get all categories
        result = await session.execute(select(Category))
        categories = result.scalars().all()
        
        for _ in range(num_items):
            # Randomly select a user and category
            user = random.choice(users)
            category = random.choice(categories)
            
            # Generate 3 random unique numbers between 1 and 21 for preferred_category_ids
            preferred_category_ids = random.sample(range(1, 22), 3)
            
            # Create a new item
            new_item = Item(
                title=random.choice(sample_titles),
                description=random.choice(sample_descriptions),
                owner_id=user.id,
                category_id=category.id,
                is_exchangeable=random.choice([True, False]),
                require_all_categories=random.choice([True, False]),
                address=f"ที่อยู่สมมติ {random.randint(1, 100)}",
                lon=random.uniform(100, 101),  # Example longitude range for Thailand
                lat=random.uniform(13, 14),  # Example latitude range for Thailand
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
                preferred_category_ids=preferred_category_ids  # Add this line
            )
            
            session.add(new_item)
        
        await session.commit()
    
    print(f"{num_items} items have been added to the database.")

if __name__ == "__main__":
    num_items_to_add = 10  # You can change this number
    asyncio.run(add_items(num_items_to_add))