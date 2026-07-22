"""
Request category endpoints. 
- Read access for all authenticated users
- Write access restricted to administrators
- Full CRUD operations for admin
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from typing import Optional

from app.database import get_db
from app.core.permissions import require_admin, require_any_authenticated
from app.models.request_category import RequestCategory
from app.models.user import User
from app.models.service_request import RequestStatus  # Import the enum
from app.schemas.category import CategoryCreate, CategoryOut, CategoryUpdate, CategoryListOut

router = APIRouter(prefix="/categories", tags=["Categories"])


@router.get("", response_model=list[CategoryOut])
def list_categories(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_any_authenticated),
):
    """
    List all categories.

    - **Access**: Any authenticated user
    - **Returns**: List of all categories sorted by name
    """
    return db.query(RequestCategory).order_by(RequestCategory.name).all()


@router.get("/paginated", response_model=CategoryListOut)
def list_categories_paginated(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(10, ge=1, le=100, description="Items per page"),
    search: Optional[str] = Query(None, description="Search by name"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_any_authenticated),
):
    """
    List categories with pagination and search.

    - **Access**: Any authenticated user
    - **Pagination**: Page and page_size parameters
    - **Search**: Optional search by name
    """
    query = db.query(RequestCategory)

    # Apply search filter
    if search:
        query = query.filter(RequestCategory.name.ilike(f"%{search}%"))

    # Get total count
    total = query.count()

    # Apply pagination
    items = query.order_by(RequestCategory.name).offset(
        (page - 1) * page_size).limit(page_size).all()

    return CategoryListOut(total=total, items=items)


@router.get("/{category_id}", response_model=CategoryOut)
def get_category(
    category_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_any_authenticated),
):
    """
    Get a specific category by ID.

    - **Access**: Any authenticated user
    - **Returns**: Category details
    - **Raises**: 404 if category not found
    """
    category = db.query(RequestCategory).filter(
        RequestCategory.id == category_id).first()
    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Category with ID {category_id} not found"
        )
    return category


@router.post("", response_model=CategoryOut, status_code=status.HTTP_201_CREATED)
def create_category(
    category_in: CategoryCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    """
    Create a new category.

    - **Access**: Admin only
    - **Validation**: Prevents duplicate category names
    - **Returns**: The created category
    """
    # Check if category already exists
    existing = db.query(RequestCategory).filter(
        RequestCategory.name == category_in.name
    ).first()

    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Category '{category_in.name}' already exists"
        )

    # Create new category
    category = RequestCategory(
        name=category_in.name,
        description=category_in.description
    )

    db.add(category)
    db.commit()
    db.refresh(category)

    return category


@router.patch("/{category_id}", response_model=CategoryOut)
def update_category(
    category_id: int,
    category_in: CategoryUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    """
    Update an existing category.

    - **Access**: Admin only
    - **Validation**: Prevents duplicate category names
    - **Returns**: The updated category
    - **Raises**: 404 if category not found
    """
    # Get existing category
    category = db.query(RequestCategory).filter(
        RequestCategory.id == category_id).first()
    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Category with ID {category_id} not found"
        )

    # Update name if provided
    if category_in.name is not None:
        # Check if new name conflicts with another category
        existing = db.query(RequestCategory).filter(
            RequestCategory.name == category_in.name,
            RequestCategory.id != category_id
        ).first()

        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Category '{category_in.name}' already exists"
            )
        category.name = category_in.name

    # Update description if provided
    if category_in.description is not None:
        category.description = category_in.description

    db.commit()
    db.refresh(category)

    return category


@router.delete("/{category_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_category(
    category_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    """
    Delete a category.

    - **Access**: Admin only
    - **Validation**: Prevents deletion if category is in use
    - **Raises**: 404 if category not found
    - **Raises**: 400 if category has service requests
    """
    # Get existing category
    category = db.query(RequestCategory).filter(
        RequestCategory.id == category_id).first()
    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Category with ID {category_id} not found"
        )

    # Check if category is in use
    if category.service_requests:
        request_count = len(category.service_requests)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot delete category '{category.name}' because it has {request_count} existing service request(s)"
        )

    db.delete(category)
    db.commit()

    return None


@router.get("/{category_id}/stats", response_model=dict)
def get_category_stats(
    category_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    """
    Get statistics for a category.

    - **Access**: Admin only
    - **Returns**: Category usage statistics
    - **Raises**: 404 if category not found
    """
    category = db.query(RequestCategory).filter(
        RequestCategory.id == category_id).first()
    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Category with ID {category_id} not found"
        )

    # Get request counts by status
    request_counts = {}

    # ✅ FIXED: Use 'stat' instead of 'status' to avoid conflict
    for stat in RequestStatus:
        count = sum(1 for r in category.service_requests if r.status == stat)
        request_counts[stat.value] = count

    return {
        "category_id": category.id,
        "category_name": category.name,
        "total_requests": len(category.service_requests),
        "requests_by_status": request_counts
    }
