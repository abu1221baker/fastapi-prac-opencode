"""Order schemas."""
from typing import Optional, List
from decimal import Decimal
from pydantic import BaseModel, Field, ConfigDict, EmailStr
from datetime import datetime

from app.schemas.base import BaseSchema, TimestampMixin, PaginationParams
from app.models.order import OrderStatus


class OrderItemBase(BaseSchema):
    """Base order item schema."""
    product_id: int = Field(..., description="Product ID")
    quantity: int = Field(..., gt=0, description="Quantity ordered")
    unit_price: Decimal = Field(..., ge=0, decimal_places=2, description="Price per unit")


class OrderItemCreate(OrderItemBase):
    """Schema for creating an order item."""
    pass


class OrderItemResponse(OrderItemBase, TimestampMixin):
    """Schema for order item response."""
    id: int
    order_id: int
    total_price: Decimal
    product_name: Optional[str] = None
    product_sku: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class OrderBase(BaseSchema):
    """Base order schema."""
    shipping_address: str = Field(..., min_length=10, description="Shipping address")
    billing_address: Optional[str] = Field(None, description="Billing address")
    phone_number: Optional[str] = Field(None, max_length=20, description="Contact phone")
    notes: Optional[str] = Field(None, description="Order notes")


class OrderCreate(OrderBase):
    """Schema for creating an order."""
    items: List[OrderItemCreate] = Field(..., min_length=1, description="Order items")


class OrderUpdate(BaseSchema):
    """Schema for updating an order (admin)."""
    status: Optional[OrderStatus] = None
    shipping_address: Optional[str] = Field(None, min_length=10)
    billing_address: Optional[str] = None
    phone_number: Optional[str] = Field(None, max_length=20)
    notes: Optional[str] = None


class OrderStatusUpdate(BaseSchema):
    """Schema for updating order status."""
    status: OrderStatus = Field(..., description="New order status")


class OrderResponse(OrderBase, TimestampMixin):
    """Schema for order response."""
    id: int
    user_id: int
    status: OrderStatus
    total_amount: Decimal
    shipped_at: Optional[datetime] = None
    delivered_at: Optional[datetime] = None
    items: List[OrderItemResponse] = []

    model_config = ConfigDict(from_attributes=True)


class OrderListResponse(BaseSchema):
    """Schema for paginated order list."""
    items: List[OrderResponse]
    total: int
    page: int
    size: int
    pages: int


class OrderSummary(BaseSchema):
    """Order summary for listings."""
    id: int
    status: OrderStatus
    total_amount: Decimal
    item_count: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class OrderFilters(PaginationParams):
    """Order filter parameters."""
    status: Optional[OrderStatus] = None
    user_id: Optional[int] = None
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None
    min_amount: Optional[Decimal] = Field(None, ge=0)
    max_amount: Optional[Decimal] = Field(None, ge=0)
    sort_by: str = Field(default="created_at", pattern="^(created_at|total_amount|status)$")
    sort_order: str = Field(default="desc", pattern="^(asc|desc)$")