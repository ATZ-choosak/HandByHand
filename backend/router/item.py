import os
import re
import shutil
from typing import List, Optional
import uuid
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status, Query
from sqlalchemy import asc, desc, func, not_, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select
from sqlalchemy.orm import joinedload
from backend.models.category import Category
from backend.models.exchanges import Exchange
from ..models.items import CategoryInfo, Item, ItemCreate, ItemRead, PaginatedItemResponse, thailand_now
from ..db import get_session
from ..utils.auth import get_current_user
from ..models.user import OwnerInfo, User
from sqlalchemy.orm import selectinload

router = APIRouter()

@router.post("/", response_model=ItemRead)
async def create_item(
    title: str = Form(...),
    description: str = Form(...),
    category_id: int = Form(...),
    preferred_category_ids: Optional[str] = Form(None),
    is_exchangeable: bool = Form(...),
    require_all_categories: bool = Form(...),
    address: Optional[str] = Form(None),
    lon: Optional[float] = Form(None),
    lat: Optional[float] = Form(None),
    images: List[UploadFile] = File(default=None),
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    if preferred_category_ids:
        if not re.match(r'^[0-9,]+$', preferred_category_ids):
            raise HTTPException(status_code=400, detail="Invalid format for preferred_category_ids. Please provide comma-separated integers only.")

        try:
            preferred_category_ids = [int(id.strip()) for id in preferred_category_ids.split(',') if id.strip()]
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid category IDs format. Please provide valid integers.")

        result = await session.execute(select(Category.id).where(Category.id.in_(preferred_category_ids)))
        existing_category_ids = set(result.scalars().all())
        invalid_category_ids = set(preferred_category_ids) - existing_category_ids
        if invalid_category_ids:
            raise HTTPException(status_code=400, detail=f"Invalid preferred category IDs: {invalid_category_ids}")
    else:
        preferred_category_ids = []

    category = await session.get(Category, category_id)
    if not category:
        raise HTTPException(status_code=400, detail=f"Invalid category ID: {category_id}")

    current_time = thailand_now()
    db_item = Item(
        title=title,
        description=description,
        category_id=category_id,
        preferred_category_ids=preferred_category_ids,
        is_exchangeable=is_exchangeable,
        require_all_categories=require_all_categories,
        address=address,
        lon=lon,
        lat=lat,
        owner_id=current_user.id,
        created_at=current_time,
        updated_at=current_time,
        
        
    )
    session.add(db_item)
    await session.flush()

    item_directory = f"images/{current_user.id}/items/{db_item.id}"
    os.makedirs(item_directory, exist_ok=True)

    images_data = []
    if images:
        for image in images:
            image_id = str(uuid.uuid4())
            file_extension = os.path.splitext(image.filename)[1]
            file_name = f"{image_id}{file_extension}"
            file_location = f"{item_directory}/{file_name}"
            
            with open(file_location, "wb") as f:
                f.write(await image.read())
            
            images_data.append({"id": image_id, "url": file_location})

    db_item.images = images_data
    await session.commit()
    await session.refresh(db_item)
    # Fetch preferred categories
    preferred_categories = await session.execute(
        select(Category).where(Category.id.in_(db_item.preferred_category_ids))
    )
    preferred_categories = preferred_categories.scalars().all()

    return ItemRead(
        **{k: v for k, v in db_item.__dict__.items() if k not in ['owner', 'category']},
        owner=OwnerInfo(
            id=db_item.owner.id,
            name=db_item.owner.name,
            phone=db_item.owner.phone,
            profile_image=db_item.owner.profile_image
        ),
        category=CategoryInfo(
            id=db_item.category.id,
            name=db_item.category.name
        ) if db_item.category else None,
        preferred_category=[
            CategoryInfo(id=cat.id, name=cat.name)
            for cat in preferred_categories
        ]
    )


# Get all items posted by the current user
@router.get("/my-items", response_model=List[ItemRead])
async def get_user_items(
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    result = await session.execute(
        select(Item)
        .options(selectinload(Item.owner), selectinload(Item.category))
        .where(Item.owner_id == current_user.id)
    )
    items = result.scalars().all()

    item_reads = []
    for item in items:
        preferred_categories = await session.execute(
            select(Category).where(Category.id.in_(item.preferred_category_ids))
        )
        preferred_categories = preferred_categories.scalars().all()

        item_reads.append(ItemRead(
            **{k: v for k, v in item.__dict__.items() if k not in ['owner', 'category']},
            owner=item.owner.owner_info,
            category=CategoryInfo(
                id=item.category.id,
                name=item.category.name
            ) if item.category else None,
            preferred_category=[
                CategoryInfo(id=cat.id, name=cat.name)
                for cat in preferred_categories
            ]
        ))

    return item_reads
# Get all items (optionally with search query)
@router.get("/", response_model=PaginatedItemResponse)
async def get_items(
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),  # เพิ่มบรรทัดนี้
    query: str = Query(None, min_length=0, description="Search query for items"),
    page: int = Query(1, ge=1, description="Page number"),
    items_per_page: int = Query(10, ge=1, le=100, description="Items per page"),
    sort_by: str = Query("created_at", description="Field to sort by"),
    sort_order: str = Query("desc", description="Sort order (asc or desc)")
):
    # Get the IDs of items that the user has requested to exchange
    requested_items = await session.execute(
        select(Exchange.requested_item_id)
        .where(Exchange.requester_id == current_user.id)
    )
    requested_item_ids = [item[0] for item in requested_items.fetchall()]

    # Modify the main query to exclude these items
    statement = select(Item).options(selectinload(Item.owner), selectinload(Item.category))
    
    if query:
        statement = statement.where(Item.title.ilike(f"%{query}%"))
    
    # Exclude items that the user has requested and their own items
    statement = statement.where(
        not_(or_(
            Item.id.in_(requested_item_ids),
            Item.owner_id == current_user.id
        ))
    )

    # Add sorting
    if hasattr(Item, sort_by):
        order_func = desc if sort_order.lower() == "desc" else asc
        statement = statement.order_by(order_func(getattr(Item, sort_by)))

    # Count total items (with the same filters)
    count_statement = select(func.count()).select_from(Item)
    if query:
        count_statement = count_statement.where(Item.title.ilike(f"%{query}%"))
    count_statement = count_statement.where(
        not_(or_(
            Item.id.in_(requested_item_ids),
            Item.owner_id == current_user.id
        ))
    )
    total_items = await session.execute(count_statement)
    total_items = total_items.scalar_one()

    # Apply pagination
    offset = (page - 1) * items_per_page
    statement = statement.offset(offset).limit(items_per_page)
    result = await session.execute(statement)
    items = result.scalars().all()

    items_with_preferred_categories = []
    for item in items:
        preferred_categories = await session.execute(
            select(Category).where(Category.id.in_(item.preferred_category_ids))
        )
        preferred_categories = preferred_categories.scalars().all()

        items_with_preferred_categories.append(ItemRead(
            **{k: v for k, v in item.__dict__.items() if k not in ['owner', 'category']},
            owner=OwnerInfo(
                id=item.owner.id,
                name=item.owner.name,
                phone=item.owner.phone,
                profile_image=item.owner.profile_image
            ),
            category=CategoryInfo(
                id=item.category.id,
                name=item.category.name
            ) if item.category else None,
            preferred_category=[
                CategoryInfo(id=cat.id, name=cat.name)
                for cat in preferred_categories
            ]
        ))

    return PaginatedItemResponse(
        items=items_with_preferred_categories,
        total_items=total_items,
        page=page,
        items_per_page=items_per_page,
        total_pages=(total_items + items_per_page - 1) // items_per_page
    )
# Get item by ID
@router.get("/{item_id}", response_model=ItemRead)
async def get_item(
    item_id: int,
    session: AsyncSession = Depends(get_session)
):
    stmt = select(Item).options(selectinload(Item.owner), selectinload(Item.category)).where(Item.id == item_id)
    result = await session.execute(stmt)
    item = result.scalar_one_or_none()

    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Item not found")

    # Fetch preferred categories
    preferred_categories = await session.execute(
        select(Category).where(Category.id.in_(item.preferred_category_ids))
    )
    preferred_categories = preferred_categories.scalars().all()

    return ItemRead(
        **{k: v for k, v in item.__dict__.items() if k not in ['owner', 'category']},
        owner=OwnerInfo(
            id=item.owner.id,
            name=item.owner.name,
            phone=item.owner.phone,
            profile_image=item.owner.profile_image
        ),
        category=CategoryInfo(
            id=item.category.id,
            name=item.category.name
        ) if item.category else None,
        preferred_category=[
            CategoryInfo(id=cat.id, name=cat.name)
            for cat in preferred_categories
        ]
    )
# Update an existing item
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

@router.put("/items/{item_id}", response_model=ItemRead)
async def update_item(
    item_id: int,
    title: str = Form(...),
    description: str = Form(None),
    category_id: int = Form(...),
    preferred_category_ids: Optional[str] = Form(None),
    is_exchangeable: bool = Form(...),
    require_all_categories: bool = Form(...),
    address: str = Form(None),
    lon: float = Form(None),
    lat: float = Form(None),
    images: List[UploadFile] = File(None),
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session)
):
    stmt = select(Item).options(selectinload(Item.owner), selectinload(Item.category)).where(Item.id == item_id, Item.owner_id == current_user.id)
    result = await session.execute(stmt)
    db_item = result.scalar_one_or_none()

    if not db_item:
        raise HTTPException(status_code=404, detail="Item not found or you don't have permission")

    # อัปเดตข้อมูล
    db_item.title = title
    db_item.description = description
    db_item.category_id = category_id
    if preferred_category_ids:
        db_item.preferred_category_ids = [int(id.strip()) for id in preferred_category_ids.split(',') if id.strip()]
    db_item.is_exchangeable = is_exchangeable
    db_item.require_all_categories = require_all_categories
    db_item.address = address
    db_item.lon = lon
    db_item.lat = lat
    db_item.updated_at = thailand_now() 

    # จัดการกับรูปภาพใหม่
    if images:
        images_data = []
        for image in images:
            image_id = str(uuid.uuid4())
            file_location = f"images/{current_user.id}/items/{db_item.id}/{image_id}{os.path.splitext(image.filename)[1]}"
            os.makedirs(os.path.dirname(file_location), exist_ok=True)
            with open(file_location, "wb+") as file_object:
                file_object.write(await image.read())
            images_data.append({"id": image_id, "url": file_location})
        db_item.images = images_data

    session.add(db_item)
    await session.commit()
    await session.refresh(db_item)

    # Fetch preferred categories
    if db_item.preferred_category_ids:
        preferred_categories = await session.execute(
            select(Category).where(Category.id.in_(db_item.preferred_category_ids))
        )
        preferred_categories = preferred_categories.scalars().all()
    else:
        preferred_categories = []

    return ItemRead(
        **{k: v for k, v in db_item.__dict__.items() if k not in ['owner', 'category']},
        owner=OwnerInfo(
            id=db_item.owner.id,
            name=db_item.owner.name,
            phone=db_item.owner.phone,
            profile_image=db_item.owner.profile_image
        ),
        category=CategoryInfo(
            id=db_item.category.id,
            name=db_item.category.name
        ) if db_item.category else None,
        preferred_category=[
            CategoryInfo(id=cat.id, name=cat.name)
            for cat in preferred_categories
        ]
    )


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

