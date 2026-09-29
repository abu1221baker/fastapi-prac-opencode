"""Product schemas."""
from typing import Optional
from decimal import Decimal
from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime

from app.schemas.base import BaseSchema, TimestampMixin, PaginationParams


class ProductBase(BaseSchema):
    """Base product schema."""
    name: str = Field(..., min_length=1, max_length=255, description="Product name")
    description: Optional[str] = Field(None, description="Product description")
    price: Decimal = Field(..., ge=0, decimal_places=2, description="Product price")
    stock_quantity: int = Field(default=0, ge=0, description="Available stock")
    category: Optional[str] = Field(None, max_length=100, description="Product category")
    sku: Optional[str] = Field(None, max_length=100, description="Stock Keeping Unit")
    image_url: Optional[str] = Field(None, max_length=500, description="Product image URL")


class ProductCreate(ProductBase):
    """Schema for creating a product."""
    is_active: bool = Field(default=True, description="Whether product is active")


class ProductUpdate(BaseSchema):
    """Schema for updating a product."""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    price: Optional[Decimal] = Field(None, ge=0, decimal_places=2)
    stock_quantity: Optional[int] = Field(None, ge=0)
    is_active: Optional[bool] = None
    category: Optional[str] = Field(None, max_length=100)
    sku: Optional[str] = Field(None, max_length=100)
    image_url: Optional[str] = Field(None, max_length=500)


class ProductResponse(ProductBase, TimestampMixin):
    """Schema for product response."""
    id: int
    is_active: bool

    model_config = ConfigDict(from_attributes=True)


class ProductListResponse(BaseSchema):
    """Schema for paginated product list."""
    items: list[ProductResponse]
    total: int
    page: int
    size: int
    pages: int


class ProductStockUpdate(BaseSchema):
    """Schema for updating product stock."""
    quantity: int = Field(..., ge=0, description="New stock quantity")


class ProductStockAdjust(BaseSchema):
    """Schema for adjusting product stock (increment/decrement)."""
    adjustment: int = Field(..., description="Stock adjustment (positive or negative)")


class ProductFilters(PaginationParams):
    """Product filter parameters."""
    category: Optional[str] = None
    is_active: Optional[bool] = None
    min_price: Optional[Decimal] = Field(None, ge=0)
    max_price: Optional[Decimal] = Field(None, ge=0)
    search: Optional[str] = Field(None, description="Search in name and description")
    sort_by: str = Field(default="created_at", pattern="^(name|price|created_at|stock_quantity)$")
    sort_order: str = Field(default="desc", pattern="^(asc|desc)$")