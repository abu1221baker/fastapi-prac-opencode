"""Order service."""
from typing import Optional, List
from decimal import Decimal

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError, ValidationError, AuthorizationError
from app.repositories.order import OrderRepository
from app.repositories.product import ProductRepository
from app.schemas.order import (
    OrderCreate,
    OrderUpdate,
    OrderStatusUpdate,
    OrderResponse,
    OrderListResponse,
    OrderFilters,
    OrderSummary,
)
from app.models.order import OrderStatus


class OrderService:
    """Order service."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.repo = OrderRepository(db)
        self.product_repo = ProductRepository(db)

    async def create(self, user_id: int, order_data: OrderCreate) -> OrderResponse:
        """Create a new order."""
        # Validate all products exist and have stock
        for item in order_data.items:
            product = await self.product_repo.get(item.product_id)
            if not product or not product.is_active:
                raise ValidationError(f"Product {item.product_id} not found or inactive")
            if product.stock_quantity < item.quantity:
                raise ValidationError(
                    f"Insufficient stock for {product.name}. Available: {product.stock_quantity}"
                )

        order = await self.repo.create_order_with_items(
            user_id=user_id,
            items=order_data.items,
            shipping_address=order_data.shipping_address,
            billing_address=order_data.billing_address,
            phone_number=order_data.phone_number,
            notes=order_data.notes,
        )

        return await self._to_response(order)

    async def get(self, order_id: int, user_id: Optional[int] = None, is_admin: bool = False) -> OrderResponse:
        """Get order by ID."""
        if is_admin:
            order = await self.repo.get_with_items(order_id)
        else:
            if not user_id:
                raise AuthorizationError("User ID required")
            order = await self.repo.get_user_order(order_id, user_id)

        if not order:
            raise NotFoundError("Order not found")

        return await self._to_response(order)

    async def list(
        self,
        filters: OrderFilters,
        user_id: Optional[int] = None,
        is_admin: bool = False,
    ) -> OrderListResponse:
        """List orders with filters."""
        if not is_admin and user_id:
            filters.user_id = user_id

        items = await self.repo.list_with_filters(filters)
        total = await self.repo.count_with_filters(filters)

        return OrderListResponse(
            items=[await self._to_response(item) for item in items],
            total=total,
            page=filters.page,
            size=filters.size,
            pages=(total + filters.size - 1) // filters.size,
        )

    async def update(
        self,
        order_id: int,
        order_data: OrderUpdate,
        is_admin: bool = False,
    ) -> OrderResponse:
        """Update an order (admin only for most fields)."""
        order = await self.repo.get(order_id)
        if not order:
            raise NotFoundError("Order not found")

        # Non-admin users can only update certain fields
        if not is_admin:
            allowed_fields = {"shipping_address", "billing_address", "phone_number", "notes"}
            update_data = order_data.model_dump(exclude_unset=True)
            for field in list(update_data.keys()):
                if field not in allowed_fields:
                    del update_data[field]
            order_data = OrderUpdate(**update_data)

        updated = await self.repo.update(order, order_data)
        return await self._to_response(updated)

    async def update_status(
        self,
        order_id: int,
        status_data: OrderStatusUpdate,
        is_admin: bool = False,
    ) -> OrderResponse:
        """Update order status."""
        if not is_admin:
            raise AuthorizationError("Only admins can update order status")

        order = await self.repo.update_status(order_id, status_data.status)
        if not order:
            raise NotFoundError("Order not found")

        return await self._to_response(order)

    async def cancel(self, order_id: int, user_id: int, is_admin: bool = False) -> OrderResponse:
        """Cancel an order."""
        order = await self.repo.get(order_id)
        if not order:
            raise NotFoundError("Order not found")

        # Check permissions
        if not is_admin and order.user_id != user_id:
            raise AuthorizationError("Not authorized to cancel this order")

        # Check if order can be cancelled
        if order.status in [OrderStatus.SHIPPED, OrderStatus.DELIVERED, OrderStatus.CANCELLED, OrderStatus.REFUNDED]:
            raise ValidationError(f"Cannot cancel order in {order.status.value} status")

        # Restore stock
        for item in order.items:
            await self.product_repo.adjust_stock(item.product_id, item.quantity)

        order.status = OrderStatus.CANCELLED
        await self.db.flush()
        await self.db.refresh(order)

        return await self._to_response(order)

    async def get_stats(self, user_id: Optional[int] = None, is_admin: bool = False) -> dict:
        """Get order statistics."""
        if not is_admin and user_id:
            return await self.repo.get_order_stats(user_id)
        elif is_admin:
            return await self.repo.get_order_stats()
        else:
            raise AuthorizationError("Admin access required")

    async def _to_response(self, order) -> OrderResponse:
        """Convert order to response schema."""
        # Load items with products if not already loaded
        if not order.items:
            order = await self.repo.get_with_items(order.id)

        return OrderResponse.model_validate(order)