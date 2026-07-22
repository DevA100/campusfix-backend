"""
Pydantic schemas for request categories.
"""

from pydantic import BaseModel, Field
from typing import Optional


class CategoryBase(BaseModel):
    """Base category schema with common fields."""
    name: str = Field(..., min_length=2, max_length=100,
                      description="Category name")
    description: Optional[str] = Field(
        None, max_length=255, description="Category description")


class CategoryCreate(CategoryBase):
    """Schema for creating a new category."""
    pass


class CategoryUpdate(BaseModel):
    """Schema for updating an existing category."""
    name: Optional[str] = Field(
        None, min_length=2, max_length=100, description="Category name")
    description: Optional[str] = Field(
        None, max_length=255, description="Category description")


class CategoryOut(CategoryBase):
    """Schema for category response."""
    id: int

    class Config:
        from_attributes = True


class CategoryListOut(BaseModel):
    """Schema for paginated category list response."""
    total: int
    items: list[CategoryOut]
