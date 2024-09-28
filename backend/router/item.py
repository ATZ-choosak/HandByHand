import os
import shutil
from typing import List
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select
from ..models.items import Item, ItemCreate, ItemRead
from ..db import get_session
from ..utils.auth import get_current_user
from ..models.user import User

router = APIRouter()

# Create a new item
@router.post("/", response_model=ItemRead)
async def create_item(
    item: ItemCreate, 
    session: AsyncSession = Depends(get_session), 
    current_user: User = Depends(get_current_user)
):
    db_item = Item(**item.dict(), owner_id=current_user.id)
    session.add(db_item)
    await session.commit()
    await session.refresh(db_item)
    # Create directory for the item images
    item_directory = f"images/{current_user.id}/items/{db_item.id}"
    os.makedirs(item_directory, exist_ok=True)
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

@router.post("/{item_id}/upload-images")
async def upload_item_images(
    item_id: int,
    files: List[UploadFile] = File(...),
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    # Fetch the item from the database
    item = await session.get(Item, item_id)
    if not item or item.owner_id != current_user.id:
        raise HTTPException(status_code=404, detail="Item not found or you do not have permission to upload images for this item")

    # Create directory for storing images if it doesn't exist
    item_directory = f"images/{current_user.id}/items/{item_id}"
    os.makedirs(item_directory, exist_ok=True)

    # Save each file and update the item's image_urls
    for file in files:
        file_location = f"{item_directory}/{file.filename}"
        with open(file_location, "wb") as f:
            f.write(await file.read())
        item.image_urls.append(file_location)

    await session.commit()

    return {"message": "Images uploaded successfully", "file_paths": item.image_urls}
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
