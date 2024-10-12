import asyncio
from sqlmodel import select
from backend.db import init_db, get_session
from backend.models.category import Category
from backend.core.config import get_settings

categories = [
    "เครื่องแต่งกายและแฟชั่น",
    "อุปกรณ์อิเล็กทรอนิกส์",
    "ของใช้ในบ้าน",
    "หนังสือและสื่อบันเทิง",
    "กีฬาและการออกกำลังกาย",
    "ของใช้สำหรับเด็ก",
    "อุปกรณ์งานฝีมือและงานศิลปะ",
    "เครื่องมือและอุปกรณ์ช่าง",
    "ยานพาหนะและอุปกรณ์เสริม",
    "ของใช้สุขภาพและความงาม",
    "ของสะสมและงานอดิเรก",
    "เครื่องดนตรีและอุปกรณ์เสียง",
    "อุปกรณ์สำหรับสัตว์เลี้ยง",
    "ของใช้สำนักงานและเครื่องเขียน",
    "อุปกรณ์การเดินทางและท่องเที่ยว",
    "เกมและของเล่น",
    "สินค้าท้องถิ่นและงานหัตถกรรม",
    "ของใช้ในงานปาร์ตี้",
    "อาหารและเครื่องดื่ม",
    "เครื่องมือการเรียนการสอน",
    "อื่นๆ"
]

async def add_categories():
    settings = get_settings()
    init_db(settings)
    
    async for session in get_session():
        for category_name in categories:
            # Check if the category already exists
            result = await session.execute(select(Category).where(Category.name == category_name))
            existing_category = result.scalar_one_or_none()
            
            if existing_category is None:
                # If the category doesn't exist, create it
                new_category = Category(name=category_name)
                session.add(new_category)
                print(f"Added category: {category_name}")
            else:
                print(f"Category already exists: {category_name}")
        
        await session.commit()
    
    print("All categories have been added or already exist.")

if __name__ == "__main__":
    asyncio.run(add_categories())