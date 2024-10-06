import os
import uuid
from fastapi import APIRouter, Form, UploadFile, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from sqlmodel import select
from ..models.category import Category
from ..db import get_session

router = APIRouter()
# ฟังก์ชันสำหรับลบไฟล์รูปภาพเก่า
def delete_old_image(file_path: str):
    if file_path and os.path.exists(file_path):
        os.remove(file_path)
# ตรวจสอบว่ามีโฟลเดอร์สำหรับเก็บรูปภาพหรือไม่ ถ้าไม่มีให้สร้างขึ้น
def create_directory_if_not_exists(path: str):
    if not os.path.exists(path):
        os.makedirs(path)

@router.get("/categories", response_model=List[Category])
async def get_categories(session: AsyncSession = Depends(get_session)):
    result = await session.execute(select(Category))
    categories = result.scalars().all()
    return categories

@router.post("/categories", response_model=Category)
async def create_category(
    name: str = Form(...),
    session: AsyncSession = Depends(get_session)
):
    new_category = Category(name=name)
    session.add(new_category)
    await session.commit()
    await session.refresh(new_category)
    
    # สร้างโฟลเดอร์สำหรับ category_id หลังจากที่ Category ถูกสร้าง
    category_directory = f"images/categories/{new_category.id}"
    create_directory_if_not_exists(category_directory)  # ตรวจสอบและสร้างโฟลเดอร์
    
    return new_category

@router.post("/categories/{category_id}/upload-image", response_model=Category)
async def upload_category_image(
    category_id: int,
    file: UploadFile,
    session: AsyncSession = Depends(get_session)
):
    category = await session.get(Category, category_id)
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")

    category_directory = f"images/categories/{category_id}"
    os.makedirs(category_directory, exist_ok=True)

    image_id = str(uuid.uuid4())
    file_extension = os.path.splitext(file.filename)[1]
    file_name = f"{image_id}{file_extension}"
    file_location = f"{category_directory}/{file_name}"

    # Delete the old image if it exists
    if category.image and os.path.exists(category.image["url"]):
        os.remove(category.image["url"])

    # Save the new image
    with open(file_location, "wb+") as file_object:
        file_object.write(await file.read())

    category.image = {"id": image_id, "url": file_location}

    session.add(category)
    await session.commit()
    await session.refresh(category)
    return category