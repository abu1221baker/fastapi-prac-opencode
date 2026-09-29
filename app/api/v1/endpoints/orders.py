"""Order API endpoints."""
from fastapi import APIRouter, Depends, status, Query
from typing import Optional
from decimal import Decimal
from datetime import datetime

from app.api.deps import (
    get_order_service,
    get_current_active_user,
    get_current_admin_user,
)
from app.services.order import OrderService
from app.schemas.order import (
    OrderCreate,
    OrderUpdate,
    OrderStatusUpdate,
    OrderResponse,
    OrderListResponse,
    OrderFilters,
)
from app.models.user import User, UserRole
from app.models.order import OrderStatus

router = APIRouter()


@router.post("", response_model=OrderResponse, status_code=status.HTTP_201_CREATED)
async def create_order(
    order_data: OrderCreate,
    order_service: OrderService = Depends(get_order_service),
    current_user: User = Depends(get_current_active_user),
):
    """Create a new order."""
    return await order_service.create(current_user.id, order_data)


@router.get("", response_model=OrderListResponse)
async def list_orders(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    status: Optional[OrderStatus] = None,
    date_from: Optional[datetime] = None,
    date_to: Optional[datetime] = None,
    min_amount: Optional[Decimal] = Query(None, ge=0),
    max_amount: Optional[Decimal] = Query(None, ge=0),
    sort_by: str = Query("created_at", pattern="^(created_at|total_amount|status)$"),
    sort_order: str = Query("desc", pattern="^(asc|desc)$"),
    order_service: OrderService = Depends(get_order_service),
    current_user: User = Depends(get_current_active_user),
):
    """List current user's orders."""
    is_admin = current_user.role in [UserRole.ADMIN, UserRole.SUPERADMIN]

    filters = OrderFilters(
        page=page,
        size=size,
        status=status,
        date_from=date_from,
        date_to=date_to,
        min_amount=min_amount,
        max_amount=max_amount,
        sort_by=sort_by,
        sort_order=sort_order,
    )

    return await order_service.list(filters, current_user.id, is_admin)


@router.get("/stats", response_model=dict)
async def get_order_stats(
    order_service: OrderService = Depends(get_order_service),
    current_user: User = Depends(get_current_admin_user),
):
    """Get order statistics (admin only)."""
    return await order_service.get_stats(is_admin=True)


@router.get("/my-stats", response_model=dict)
async def get_my_order_stats(
    order_service: OrderService = Depends(get_order_service),
    current_user: User = Depends(get_current_active_user),
):
    """Get current user's order statistics."""
    return await order_service.get_stats(user_id=current_user.id, is_admin=False)


@router.get("/{order_id}", response_model=OrderResponse)
async def get_order(
    order_id: int,
    order_service: OrderService = Depends(get_order_service),
    current_user: User = Depends(get_current_active_user),
):
    """Get order by ID."""
    is_admin = current_user.role in [UserRole.ADMIN, UserRole.SUPERADMIN]
    return await order_service.get(order_id, current_user.id, is_admin)


@router.patch("/{order_id}", response_model=OrderResponse)
async def update_order(
    order_id: int,
    order_data: OrderUpdate,
    order_service: OrderService = Depends(get_order_service),
    current_user: User = Depends(get_current_active_user),
):
    """Update an order."""
    is_admin = current_user.role in [UserRole.ADMIN, UserRole.SUPERADMIN]
    return await order_service.update(order_id, order_data, is_admin)


@router.patch("/{order_id}/status", response_model=OrderResponse)
async def update_order_status(
    order_id: int,
    status_data: OrderStatusUpdate,
    order_service: OrderService = Depends(get_order_service),
    current_user: User = Depends(get_current_admin_user),
):
    """Update order status (admin only)."""
    return await order_service.update_status(order_id, status_data, is_admin=True)


@router.post("/{order_id}/cancel", response_model=OrderResponse)
async def cancel_order(
    order_id: int,
    order_service: OrderService = Depends(get_order_service),
    current_user: User = Depends(get_current_active_user),
):
    """Cancel an order."""
    is_admin = current_user.role in [UserRole.ADMIN, UserRole.SUPERADMIN]
    return await order_service.cancel(order_id, current_user.id, is_admin)