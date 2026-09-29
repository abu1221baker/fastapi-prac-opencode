"""Product service."""
from typing import Optional, List
from decimal import Decimal

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError, ValidationError, ConflictError
from app.repositories.product import ProductRepository
from app.schemas.product import (
    ProductCreate,
    ProductUpdate,
    ProductResponse,
    ProductListResponse,
    ProductFilters,
    ProductStockAdjust,
)


class ProductService:
    """Product service."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.repo = ProductRepository(db)

    async def create(self, product_data: ProductCreate) -> ProductResponse:
        """Create a new product."""
        # Check SKU uniqueness
        if product_data.sku:
            existing = await self.repo.get_by_sku(product_data.sku)
            if existing:
                raise ConflictError("SKU already exists")

        product = await self.repo.create(product_data)
        return ProductResponse.model_validate(product)

    async def get(self, product_id: int) -> ProductResponse:
        """Get product by ID."""
        product = await self.repo.get(product_id)
        if not product:
            raise NotFoundError("Product not found")
        return ProductResponse.model_validate(product)

    async def update(self, product_id: int, product_data: ProductUpdate) -> ProductResponse:
        """Update a product."""
        product = await self.repo.get(product_id)
        if not product:
            raise NotFoundError("Product not found")

        # Check SKU uniqueness if changing
        if product_data.sku and product_data.sku != product.sku:
            existing = await self.repo.get_by_sku(product_data.sku)
            if existing:
                raise ConflictError("SKU already exists")

        updated = await self.repo.update(product, product_data)
        return ProductResponse.model_validate(updated)

    async def delete(self, product_id: int) -> bool:
        """Delete a product (soft delete by setting inactive)."""
        product = await self.repo.get(product_id)
        if not product:
            raise NotFoundError("Product not found")

        # Soft delete - set inactive
        product.is_active = False
        await self.db.flush()
        return True

    async def list(self, filters: ProductFilters) -> ProductListResponse:
        """List products with filters."""
        items = await self.repo.list_with_filters(filters)
        total = await self.repo.count_with_filters(filters)

        return ProductListResponse(
            items=[ProductResponse.model_validate(item) for item in items],
            total=total,
            page=filters.page,
            size=filters.size,
            pages=(total + filters.size - 1) // filters.size,
        )

    async def adjust_stock(self, product_id: int, adjustment: ProductStockAdjust) -> ProductResponse:
        """Adjust product stock."""
        product = await self.repo.get(product_id)
        if not product:
            raise NotFoundError("Product not found")

        try:
            updated = await self.repo.adjust_stock(product_id, adjustment.adjustment)
        except ValueError as e:
            raise ValidationError(str(e))

        return ProductResponse.model_validate(updated)

    async def set_stock(self, product_id: int, quantity: int) -> ProductResponse:
        """Set product stock to specific quantity."""
        if quantity < 0:
            raise ValidationError("Stock quantity cannot be negative")

        product = await self.repo.get(product_id)
        if not product:
            raise NotFoundError("Product not found")

        updated = await self.repo.update_stock(product_id, quantity)
        return ProductResponse.model_validate(updated)

    async def check_availability(self, product_id: int, quantity: int) -> bool:
        """Check if product has sufficient stock."""
        return await self.repo.check_stock(product_id, quantity)

    async def get_categories(self) -> List[str]:
        """Get all product categories."""
        return await self.repo.get_categories()