from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select
from typing import List, Optional
from ..models.customer_interest import CustomerInterest
from ..models.category import Category  # Import Category model for validation
from ..db import get_session
from ..models.user import User
from ..utils.auth import get_current_user

router = APIRouter()

# Route to submit customer interests
@router.post("/customer-interest")
async def submit_customer_interest(
    category_ids: List[int],  # List of category IDs that user selects
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session)
):
    # Validate that category_ids contain positive integers
    if any(c <= 0 for c in category_ids):
        invalid_ids = [c for c in category_ids if c <= 0]
        raise HTTPException(status_code=400, detail=f"Invalid category IDs: {invalid_ids}. Category IDs must be positive integers.")

    # Ensure that the provided category IDs exist in the Category table
    result = await session.execute(select(Category.id).where(Category.id.in_(category_ids)))
    valid_category_ids = set(result.scalars().all())
    
    invalid_category_ids = set(category_ids) - valid_category_ids
    if invalid_category_ids:
        raise HTTPException(status_code=400, detail=f"Invalid category IDs: {invalid_category_ids}. These IDs do not exist in the database.")
    
    # Check if the user has already submitted their interests
    result = await session.execute(select(CustomerInterest).where(CustomerInterest.user_id == current_user.id))
    existing_interest = result.scalar_one_or_none()

    if existing_interest:
        # If interests already exist, update them
        existing_interest.category_ids = category_ids
        await session.commit()
        return {"message": "Customer interests updated successfully"}

    # Otherwise, create a new entry
    new_interest = CustomerInterest(user_id=current_user.id, category_ids=category_ids)
    session.add(new_interest)
    # Set is_first_login to True
    current_user.is_first_login = True
    session.add(current_user)
    await session.commit()
    return {"message": "Customer interests saved successfully"}
# Route to fetch the customer interests for the current user
@router.get("/customer-interest")
async def get_customer_interest(
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session)
):
    result = await session.execute(select(CustomerInterest).where(CustomerInterest.user_id == current_user.id))
    interest = result.scalar_one_or_none()

    if not interest:
        raise HTTPException(status_code=404, detail="Customer interests not found")

    return {"category_ids": interest.category_ids, "message": "Customer interests retrieved successfully"}


@router.put("/customer-interest")
async def update_customer_interest(
    add_category_ids: Optional[List[int]] = None,  # List of category IDs to add
    remove_category_ids: Optional[List[int]] = None,  # List of category IDs to remove
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session)
):
    # Early return if both add_category_ids and remove_category_ids are None
    if not add_category_ids and not remove_category_ids:
        return {"message": "No categories to add or remove."}

    # Validate that the provided category IDs exist in the Category table
    if add_category_ids:
        result = await session.execute(select(Category.id).where(Category.id.in_(add_category_ids)))
        valid_add_category_ids = set(result.scalars().all())
        invalid_add_category_ids = set(add_category_ids) - valid_add_category_ids
        if invalid_add_category_ids:
            raise HTTPException(status_code=400, detail=f"Invalid category IDs to add: {invalid_add_category_ids}")

    if remove_category_ids:
        result = await session.execute(select(Category.id).where(Category.id.in_(remove_category_ids)))
        valid_remove_category_ids = set(result.scalars().all())
        invalid_remove_category_ids = set(remove_category_ids) - valid_remove_category_ids
        if invalid_remove_category_ids:
            raise HTTPException(status_code=400, detail=f"Invalid category IDs to remove: {invalid_remove_category_ids}")

    # Check if the user has already submitted their interests
    result = await session.execute(select(CustomerInterest).where(CustomerInterest.user_id == current_user.id))
    existing_interest = result.scalar_one_or_none()

    if not existing_interest:
        raise HTTPException(status_code=404, detail="Customer interests not found")

    # Adding new categories: Only add those not already present in the user's interests
    if add_category_ids:
        new_categories_to_add = valid_add_category_ids - set(existing_interest.category_ids)
        if new_categories_to_add:
            # Assign a new list to the attribute
            existing_interest.category_ids = existing_interest.category_ids + list(new_categories_to_add)

    # Removing categories: Only remove those that are currently in the user's interests
    if remove_category_ids:
        updated_category_ids = [cid for cid in existing_interest.category_ids if cid not in valid_remove_category_ids]
        existing_interest.category_ids = updated_category_ids

    # Commit the changes to the database
    await session.commit()

    return {"message": "Customer interests updated successfully", "category_ids": existing_interest.category_ids}