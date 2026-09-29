"""Product API endpoints."""
from fastapi import APIRouter, Depends, status, Query
from typing import Optional
from decimal import Decimal

from app.api.deps import (
    get_product_service,
    get_current_active_user,
    get_current_admin_user,
)
from app.services.product import ProductService
from app.schemas.product import (
    ProductCreate,
    ProductUpdate,
    ProductResponse,
    ProductListResponse,
    ProductFilters,
    ProductStockAdjust,
)
from app.models.user import User, UserRole

router = APIRouter()


@router.post("", response_model=ProductResponse, status_code=status.HTTP_201_CREATED)
async def create_product(
    product_data: ProductCreate,
    product_service: ProductService = Depends(get_product_service),
    current_user: User = Depends(get_current_admin_user),
):
    """Create a new product (admin only)."""
    return await product_service.create(product_data)


@router.get("", response_model=ProductListResponse)
async def list_products(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    category: Optional[str] = None,
    is_active: Optional[bool] = None,
    min_price: Optional[Decimal] = Query(None, ge=0),
    max_price: Optional[Decimal] = Query(None, ge=0),
    search: Optional[str] = None,
    sort_by: str = Query("created_at", pattern="^(name|price|created_at|stock_quantity)$"),
    sort_order: str = Query("desc", pattern="^(asc|desc)$"),
    product_service: ProductService = Depends(get_product_service),
):
    """List products with filters (public)."""
    filters = ProductFilters(
        page=page,
        size=size,
        category=category,
        is_active=is_active,
        min_price=min_price,
        max_price=max_price,
        search=search,
        sort_by=sort_by,
        sort_order=sort_order,
    )
    return await product_service.list(filters)


@router.get("/categories", response_model=list[str])
async def get_categories(
    product_service: ProductService = Depends(get_product_service),
):
    """Get all product categories."""
    return await product_service.get_categories()


@router.get("/{product_id}", response_model=ProductResponse)
async def get_product(
    product_id: int,
    product_service: ProductService = Depends(get_product_service),
):
    """Get product by ID."""
    return await product_service.get(product_id)


@router.patch("/{product_id}", response_model=ProductResponse)
async def update_product(
    product_id: int,
    product_data: ProductUpdate,
    product_service: ProductService = Depends(get_product_service),
    current_user: User = Depends(get_current_admin_user),
):
    """Update a product (admin only)."""
    return await product_service.update(product_id, product_data)


@router.delete("/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_product(
    product_id: int,
    product_service: ProductService = Depends(get_product_service),
    current_user: User = Depends(get_current_admin_user),
):
    """Delete (deactivate) a product (admin only)."""
    await product_service.delete(product_id)


@router.post("/{product_id}/stock/adjust", response_model=ProductResponse)
async def adjust_stock(
    product_id: int,
    adjustment: ProductStockAdjust,
    product_service: ProductService = Depends(get_product_service),
    current_user: User = Depends(get_current_admin_user),
):
    """Adjust product stock (admin only)."""
    return await product_service.adjust_stock(product_id, adjustment)


@router.post("/{product_id}/stock/set", response_model=ProductResponse)
async def set_stock(
    product_id: int,
    quantity: int = Query(..., ge=0),
    product_service: ProductService = Depends(get_product_service),
    current_user: User = Depends(get_current_admin_user),
):
    """Set product stock to specific quantity (admin only)."""
    return await product_service.set_stock(product_id, quantity)