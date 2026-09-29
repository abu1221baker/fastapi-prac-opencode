"""Order repository."""
from typing import Optional, List
from decimal import Decimal
from datetime import datetime
from sqlalchemy import select, func, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.repositories.base import BaseRepository
from app.models.order import Order, OrderItem, OrderStatus
from app.schemas.order import OrderCreate, OrderUpdate, OrderFilters, OrderItemCreate


class OrderRepository(BaseRepository[Order, OrderCreate, OrderUpdate]):
    """Order repository with custom queries."""

    def __init__(self, db: AsyncSession):
        super().__init__(Order, db)

    async def get_with_items(self, order_id: int) -> Optional[Order]:
        """Get order with items loaded."""
        result = await self.db.execute(
            select(Order)
            .options(selectinload(Order.items).selectinload(OrderItem.product))
            .where(Order.id == order_id)
        )
        return result.scalar_one_or_none()

    async def get_user_order(self, order_id: int, user_id: int) -> Optional[Order]:
        """Get user's order with items."""
        result = await self.db.execute(
            select(Order)
            .options(selectinload(Order.items).selectinload(OrderItem.product))
            .where(and_(Order.id == order_id, Order.user_id == user_id))
        )
        return result.scalar_one_or_none()

    async def list_user_orders(
        self,
        user_id: int,
        skip: int = 0,
        limit: int = 20,
        status: Optional[OrderStatus] = None,
    ) -> List[Order]:
        """List orders for a specific user."""
        query = (
            select(Order)
            .options(selectinload(Order.items).selectinload(OrderItem.product))
            .where(Order.user_id == user_id)
        )

        if status:
            query = query.where(Order.status == status)

        query = query.order_by(Order.created_at.desc()).offset(skip).limit(limit)
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def count_user_orders(
        self,
        user_id: int,
        status: Optional[OrderStatus] = None,
    ) -> int:
        """Count user's orders."""
        query = select(func.count(Order.id)).where(Order.user_id == user_id)
        if status:
            query = query.where(Order.status == status)
        result = await self.db.execute(query)
        return result.scalar_one()

    async def list_with_filters(self, filters: OrderFilters) -> List[Order]:
        """List orders with advanced filters."""
        query = (
            select(Order)
            .options(selectinload(Order.items).selectinload(OrderItem.product))
        )

        if filters.status:
            query = query.where(Order.status == filters.status)
        if filters.user_id:
            query = query.where(Order.user_id == filters.user_id)
        if filters.date_from:
            query = query.where(Order.created_at >= filters.date_from)
        if filters.date_to:
            query = query.where(Order.created_at <= filters.date_to)
        if filters.min_amount is not None:
            query = query.where(Order.total_amount >= filters.min_amount)
        if filters.max_amount is not None:
            query = query.where(Order.total_amount <= filters.max_amount)

        # Sorting
        sort_column = getattr(Order, filters.sort_by, Order.created_at)
        if filters.sort_order == "desc":
            query = query.order_by(sort_column.desc())
        else:
            query = query.order_by(sort_column.asc())

        query = query.offset((filters.page - 1) * filters.size).limit(filters.size)
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def count_with_filters(self, filters: OrderFilters) -> int:
        """Count orders with filters."""
        query = select(func.count(Order.id))

        if filters.status:
            query = query.where(Order.status == filters.status)
        if filters.user_id:
            query = query.where(Order.user_id == filters.user_id)
        if filters.date_from:
            query = query.where(Order.created_at >= filters.date_from)
        if filters.date_to:
            query = query.where(Order.created_at <= filters.date_to)
        if filters.min_amount is not None:
            query = query.where(Order.total_amount >= filters.min_amount)
        if filters.max_amount is not None:
            query = query.where(Order.total_amount <= filters.max_amount)

        result = await self.db.execute(query)
        return result.scalar_one()

    async def create_order_with_items(
        self,
        user_id: int,
        items: List[OrderItemCreate],
        shipping_address: str,
        billing_address: Optional[str] = None,
        phone_number: Optional[str] = None,
        notes: Optional[str] = None,
    ) -> Order:
        """Create order with items in a single transaction."""
        from app.repositories.product import ProductRepository

        product_repo = ProductRepository(self.db)

        # Calculate total and validate stock
        total_amount = Decimal("0")
        order_items_data = []

        for item in items:
            product = await product_repo.get(item.product_id)
            if not product or not product.is_active:
                raise ValueError(f"Product {item.product_id} not found or inactive")
            if product.stock_quantity < item.quantity:
                raise ValueError(f"Insufficient stock for product {product.name}")

            # Use current product price
            unit_price = product.price
            total_price = unit_price * item.quantity
            total_amount += total_price

            order_items_data.append({
                "product_id": item.product_id,
                "quantity": item.quantity,
                "unit_price": unit_price,
                "total_price": total_price,
            })

        # Create order
        order = Order(
            user_id=user_id,
            total_amount=total_amount,
            shipping_address=shipping_address,
            billing_address=billing_address,
            phone_number=phone_number,
            notes=notes,
            status=OrderStatus.PENDING,
        )
        self.db.add(order)
        await self.db.flush()

        # Create order items and update stock
        for item_data in order_items_data:
            order_item = OrderItem(order_id=order.id, **item_data)
            self.db.add(order_item)

            # Decrease stock
            await product_repo.adjust_stock(item_data["product_id"], -item_data["quantity"])

        await self.db.flush()
        await self.db.refresh(order)
        return order

    async def update_status(self, order_id: int, status: OrderStatus) -> Optional[Order]:
        """Update order status with timestamps."""
        order = await self.get(order_id)
        if not order:
            return None

        order.status = status
        now = datetime.now()

        if status == OrderStatus.SHIPPED and not order.shipped_at:
            order.shipped_at = now
        elif status == OrderStatus.DELIVERED and not order.delivered_at:
            order.delivered_at = now

        await self.db.flush()
        await self.db.refresh(order)
        return order

    async def get_order_stats(self, user_id: Optional[int] = None) -> dict:
        """Get order statistics."""
        base_query = select(
            Order.status,
            func.count(Order.id).label("count"),
            func.sum(Order.total_amount).label("total"),
        ).group_by(Order.status)

        if user_id:
            base_query = base_query.where(Order.user_id == user_id)

        result = await self.db.execute(base_query)
        stats = {row.status.value: {"count": row.count, "total": float(row.total or 0)} for row in result.all()}

        # Total orders
        total_query = select(func.count(Order.id))
        if user_id:
            total_query = total_query.where(Order.user_id == user_id)
        total_result = await self.db.execute(total_query)
        stats["total_orders"] = total_result.scalar_one()

        # Total revenue
        revenue_query = select(func.sum(Order.total_amount)).where(Order.status != OrderStatus.CANCELLED)
        if user_id:
            revenue_query = revenue_query.where(Order.user_id == user_id)
        revenue_result = await self.db.execute(revenue_query)
        stats["total_revenue"] = float(revenue_result.scalar_one() or 0)

        return stats