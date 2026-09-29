"""Product repository."""
from typing import Optional, List
from decimal import Decimal
from sqlalchemy import select, func, or_, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.base import BaseRepository
from app.models.product import Product
from app.schemas.product import ProductCreate, ProductUpdate, ProductFilters


class ProductRepository(BaseRepository[Product, ProductCreate, ProductUpdate]):
    """Product repository with custom queries."""

    def __init__(self, db: AsyncSession):
        super().__init__(Product, db)

    async def get_by_sku(self, sku: str) -> Optional[Product]:
        """Get product by SKU."""
        result = await self.db.execute(
            select(Product).where(Product.sku == sku)
        )
        return result.scalar_one_or_none()

    async def get_active_products(
        self,
        skip: int = 0,
        limit: int = 100,
        category: Optional[str] = None,
    ) -> List[Product]:
        """Get active products with optional category filter."""
        query = select(Product).where(Product.is_active == True)

        if category:
            query = query.where(Product.category == category)

        query = query.order_by(Product.created_at.desc()).offset(skip).limit(limit)
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def search_products(
        self,
        search: str,
        skip: int = 0,
        limit: int = 20,
    ) -> List[Product]:
        """Search products by name or description."""
        query = select(Product).where(
            and_(
                Product.is_active == True,
                or_(
                    Product.name.ilike(f"%{search}%"),
                    Product.description.ilike(f"%{search}%"),
                )
            )
        ).order_by(Product.created_at.desc()).offset(skip).limit(limit)

        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def list_with_filters(self, filters: ProductFilters) -> List[Product]:
        """List products with advanced filters."""
        query = select(Product)

        if filters.category:
            query = query.where(Product.category == filters.category)
        if filters.is_active is not None:
            query = query.where(Product.is_active == filters.is_active)
        if filters.min_price is not None:
            query = query.where(Product.price >= filters.min_price)
        if filters.max_price is not None:
            query = query.where(Product.price <= filters.max_price)
        if filters.search:
            query = query.where(
                or_(
                    Product.name.ilike(f"%{filters.search}%"),
                    Product.description.ilike(f"%{filters.search}%"),
                )
            )

        # Sorting
        sort_column = getattr(Product, filters.sort_by, Product.created_at)
        if filters.sort_order == "desc":
            query = query.order_by(sort_column.desc())
        else:
            query = query.order_by(sort_column.asc())

        query = query.offset((filters.page - 1) * filters.size).limit(filters.size)
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def count_with_filters(self, filters: ProductFilters) -> int:
        """Count products with filters."""
        query = select(func.count(Product.id))

        if filters.category:
            query = query.where(Product.category == filters.category)
        if filters.is_active is not None:
            query = query.where(Product.is_active == filters.is_active)
        if filters.min_price is not None:
            query = query.where(Product.price >= filters.min_price)
        if filters.max_price is not None:
            query = query.where(Product.price <= filters.max_price)
        if filters.search:
            query = query.where(
                or_(
                    Product.name.ilike(f"%{filters.search}%"),
                    Product.description.ilike(f"%{filters.search}%"),
                )
            )

        result = await self.db.execute(query)
        return result.scalar_one()

    async def update_stock(self, product_id: int, quantity: int) -> Optional[Product]:
        """Update product stock quantity."""
        product = await self.get(product_id)
        if product:
            product.stock_quantity = quantity
            await self.db.flush()
            await self.db.refresh(product)
        return product

    async def adjust_stock(self, product_id: int, adjustment: int) -> Optional[Product]:
        """Adjust product stock (increment/decrement)."""
        product = await self.get(product_id)
        if product:
            new_stock = product.stock_quantity + adjustment
            if new_stock < 0:
                raise ValueError("Insufficient stock")
            product.stock_quantity = new_stock
            await self.db.flush()
            await self.db.refresh(product)
        return product

    async def check_stock(self, product_id: int, quantity: int) -> bool:
        """Check if product has sufficient stock."""
        product = await self.get(product_id)
        return product is not None and product.stock_quantity >= quantity and product.is_active

    async def get_categories(self) -> List[str]:
        """Get all unique categories."""
        result = await self.db.execute(
            select(Product.category).distinct().where(Product.category.isnot(None))
        )
        return [row[0] for row in result.all() if row[0]]