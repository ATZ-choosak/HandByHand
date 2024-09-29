import os
import re
import shutil
from typing import List, Optional
import uuid
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from backend.models.category import Category
from ..models.items import Item, ItemCreate, ItemRead
from ..db import get_session
from ..utils.auth import get_current_user
from ..models.user import User

router = APIRouter()

@router.post("/", response_model=ItemRead)
async def create_item(
    title: str = Form(...),
    description: str = Form(...),
    category_id: int = Form(...),
    preferred_category_ids: str = Form(...),  # Change this to str
    is_exchangeable: bool = Form(...),
    require_all_categories: bool = Form(...),
    address: Optional[str] = Form(None),
    lon: Optional[float] = Form(None),
    lat: Optional[float] = Form(None),
    images: List[UploadFile] = File(None),
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    if not re.match(r'^[0-9,]+$', preferred_category_ids):
        raise HTTPException(status_code=400, detail="Invalid format for preferred_category_ids. Please provide comma-separated integers only.")

    try:
        preferred_category_ids = [int(id.strip()) for id in preferred_category_ids.split(',') if id.strip()]
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid category IDs format. Please provide valid integers.")
    # Rest of your function remains the same
    category = await session.get(Category, category_id)
    if not category:
        raise HTTPException(status_code=400, detail=f"Invalid category ID: {category_id}")

    result = await session.execute(select(Category.id).where(Category.id.in_(preferred_category_ids)))
    existing_category_ids = set(result.scalars().all())
    invalid_category_ids = set(preferred_category_ids) - existing_category_ids
    if invalid_category_ids:
        raise HTTPException(status_code=400, detail=f"Invalid preferred category IDs: {invalid_category_ids}")

    db_item = Item(
        title=title,
        description=description,
        category_id=category_id,
        preferred_category_ids=list(existing_category_ids),
        is_exchangeable=is_exchangeable,
        require_all_categories=require_all_categories,
        address=address,
        lon=lon,
        lat=lat,
        owner_id=current_user.id
    )
    session.add(db_item)
    await session.flush()

    item_directory = f"images/{current_user.id}/items/{db_item.id}"
    os.makedirs(item_directory, exist_ok=True)

    image_ids = []
    image_urls = []

    if images:
        for image in images:
            image_id = str(uuid.uuid4())
            file_extension = os.path.splitext(image.filename)[1]
            file_name = f"{image_id}{file_extension}"
            file_location = f"{item_directory}/{file_name}"
            
            with open(file_location, "wb") as f:
                f.write(await image.read())
            
            image_ids.append(image_id)
            image_urls.append(file_location)

    db_item.image_ids = image_ids
    db_item.image_urls = image_urls

    await session.commit()
    await session.refresh(db_item)
    return db_item
# Get all items posted by the current user
@router.get("/my-items", response_model=List[ItemRead])
async def get_user_items(
    session: AsyncSession = Depends(get_session), 
    current_user: User = Depends(get_current_user)
):
    result = await session.execute(select(Item).where(Item.owner_id == current_user.id))
    items = result.scalars().all()
    return items

# Get all items (optionally with search query)
@router.get("/", response_model=List[ItemRead])
async def get_items(
    session: AsyncSession = Depends(get_session), 
    query: str = Query(None, min_length=3, description="Search query for items")
):
    statement = select(Item)
    
    if query:
        statement = statement.where(Item.title.ilike(f"%{query}%"))
    
    result = await session.execute(statement)
    items = result.scalars().all()
    return items

# Get item by ID
@router.get("/{item_id}", response_model=ItemRead)
async def get_item(
    item_id: int, 
    session: AsyncSession = Depends(get_session)
):
    item = await session.get(Item, item_id)
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Item not found")
    return item

# Update an existing item
@router.put("/{item_id}", response_model=ItemRead)
async def update_item(
    item_id: int, 
    item: ItemCreate, 
    session: AsyncSession = Depends(get_session), 
    current_user: User = Depends(get_current_user)
):
    db_item = await session.get(Item, item_id)
    if not db_item or db_item.owner_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Item not found or you do not have permission to update it")
    
    db_item.title = item.title
    db_item.description = item.description
    
    await session.commit()
    await session.refresh(db_item)
    return db_item


# Delete an item
@router.delete("/{item_id}")
async def delete_item(
    item_id: int, 
    session: AsyncSession = Depends(get_session), 
    current_user: User = Depends(get_current_user)
):
    db_item = await session.get(Item, item_id)
    if not db_item or db_item.owner_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Item not found or you do not have permission to delete it")
    

    # Delete the item's image directory
    item_directory = f"images/{current_user.id}/items/{item_id}"
    shutil.rmtree(item_directory, ignore_errors=True)
    await session.delete(db_item)
    await session.commit()
    return {"message": "Item deleted successfully"}

@router.delete("/{item_id}/delete-image")
async def delete_item_image(
    item_id: int,
    image_filename: str,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    # Fetch the item from the database
    db_item = await session.get(Item, item_id)
    if not db_item or db_item.owner_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Item not found or you do not have permission to delete images for this item")

    # Construct the file path
    file_path = f"images/{current_user.id}/items/{item_id}/{image_filename}"
    
    # Check if the file exists and delete it
    if os.path.exists(file_path):
        os.remove(file_path)
        print(f"Deleted image: {file_path}")
    else:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Image not found")

    # Remove the image URL from the item's image_urls list
    if file_path in db_item.image_urls:
        db_item.image_urls.remove(file_path)
        await session.commit()
    
    return {"message": "Image deleted successfully"}

@router.put("/{item_id}/set-preferred-categories", response_model=ItemRead)
async def set_preferred_categories(
    item_id: int,
    category_ids: List[int],
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    # Fetch the item from the database
    db_item = await session.get(Item, item_id)
    if not db_item or db_item.owner_id != current_user.id:
        raise HTTPException(status_code=404, detail="Item not found or you do not have permission to update it")

    # Validate category IDs
    result = await session.execute(select(Category.id).where(Category.id.in_(category_ids)))
    valid_category_ids = set(result.scalars().all())
    invalid_category_ids = set(category_ids) - valid_category_ids
    
    if invalid_category_ids:
        raise HTTPException(status_code=400, detail=f"Invalid category IDs: {invalid_category_ids}")

    # Update preferred categories
    db_item.preferred_category_ids = list(valid_category_ids)
    
    await session.commit()
    await session.refresh(db_item)

    return db_item
