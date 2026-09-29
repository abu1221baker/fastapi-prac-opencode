"""Product tests."""
import pytest
from httpx import AsyncClient
from decimal import Decimal


class TestProducts:
    """Product endpoint tests."""

    @pytest.mark.asyncio
    async def test_create_product(self, client: AsyncClient, admin_auth_headers: dict):
        """Test creating a product (admin)."""
        response = await client.post(
            "/api/v1/products/",
            headers=admin_auth_headers,
            json={
                "name": "Test Product",
                "description": "A test product",
                "price": "29.99",
                "stock_quantity": 100,
                "category": "Electronics",
                "sku": "TEST-001",
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Test Product"
        assert data["price"] == "29.99"
        assert data["stock_quantity"] == 100
        assert data["category"] == "Electronics"
        assert data["sku"] == "TEST-001"
        assert data["is_active"] is True

    @pytest.mark.asyncio
    async def test_create_product_unauthorized(self, client: AsyncClient, auth_headers: dict):
        """Test creating a product without admin rights."""
        response = await client.post(
            "/api/v1/products/",
            headers=auth_headers,
            json={
                "name": "Test Product",
                "price": "29.99",
            },
        )
        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_list_products(self, client: AsyncClient, admin_auth_headers: dict):
        """Test listing products."""
        # Create a product first
        await client.post(
            "/api/v1/products/",
            headers=admin_auth_headers,
            json={
                "name": "List Product",
                "price": "19.99",
                "stock_quantity": 50,
            },
        )

        response = await client.get("/api/v1/products/")
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data
        assert data["total"] >= 1

    @pytest.mark.asyncio
    async def test_list_products_with_filters(self, client: AsyncClient, admin_auth_headers: dict):
        """Test listing products with filters."""
        response = await client.get(
            "/api/v1/products/",
            params={"category": "Electronics", "min_price": "10", "max_price": "50"},
        )
        assert response.status_code == 200
        data = response.json()
        assert "items" in data

    @pytest.mark.asyncio
    async def test_get_product(self, client: AsyncClient, admin_auth_headers: dict):
        """Test getting a single product."""
        create_response = await client.post(
            "/api/v1/products/",
            headers=admin_auth_headers,
            json={
                "name": "Get Product",
                "price": "9.99",
                "stock_quantity": 10,
            },
        )
        product_id = create_response.json()["id"]

        response = await client.get(f"/api/v1/products/{product_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == product_id
        assert data["name"] == "Get Product"

    @pytest.mark.asyncio
    async def test_get_nonexistent_product(self, client: AsyncClient):
        """Test getting a nonexistent product."""
        response = await client.get("/api/v1/products/999999")
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_update_product(self, client: AsyncClient, admin_auth_headers: dict):
        """Test updating a product."""
        create_response = await client.post(
            "/api/v1/products/",
            headers=admin_auth_headers,
            json={
                "name": "Update Product",
                "price": "15.00",
                "stock_quantity": 20,
            },
        )
        product_id = create_response.json()["id"]

        response = await client.patch(
            f"/api/v1/products/{product_id}",
            headers=admin_auth_headers,
            json={
                "name": "Updated Product",
                "price": "25.00",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Updated Product"
        assert data["price"] == "25.00"

    @pytest.mark.asyncio
    async def test_delete_product(self, client: AsyncClient, admin_auth_headers: dict):
        """Test deleting (deactivating) a product."""
        create_response = await client.post(
            "/api/v1/products/",
            headers=admin_auth_headers,
            json={
                "name": "Delete Product",
                "price": "5.00",
                "stock_quantity": 5,
            },
        )
        product_id = create_response.json()["id"]

        response = await client.delete(
            f"/api/v1/products/{product_id}",
            headers=admin_auth_headers,
        )
        assert response.status_code == 204

        # Verify it's deactivated
        get_response = await client.get(f"/api/v1/products/{product_id}")
        assert get_response.json()["is_active"] is False

    @pytest.mark.asyncio
    async def test_adjust_stock(self, client: AsyncClient, admin_auth_headers: dict):
        """Test adjusting product stock."""
        create_response = await client.post(
            "/api/v1/products/",
            headers=admin_auth_headers,
            json={
                "name": "Stock Product",
                "price": "10.00",
                "stock_quantity": 50,
            },
        )
        product_id = create_response.json()["id"]

        # Increase stock
        response = await client.post(
            f"/api/v1/products/{product_id}/stock/adjust",
            headers=admin_auth_headers,
            json={"adjustment": 25},
        )
        assert response.status_code == 200
        assert response.json()["stock_quantity"] == 75

        # Decrease stock
        response = await client.post(
            f"/api/v1/products/{product_id}/stock/adjust",
            headers=admin_auth_headers,
            json={"adjustment": -30},
        )
        assert response.status_code == 200
        assert response.json()["stock_quantity"] == 45

    @pytest.mark.asyncio
    async def test_adjust_stock_insufficient(self, client: AsyncClient, admin_auth_headers: dict):
        """Test adjusting stock below zero."""
        create_response = await client.post(
            "/api/v1/products/",
            headers=admin_auth_headers,
            json={
                "name": "Low Stock Product",
                "price": "10.00",
                "stock_quantity": 10,
            },
        )
        product_id = create_response.json()["id"]

        response = await client.post(
            f"/api/v1/products/{product_id}/stock/adjust",
            headers=admin_auth_headers,
            json={"adjustment": -20},
        )
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_set_stock(self, client: AsyncClient, admin_auth_headers: dict):
        """Test setting stock to specific quantity."""
        create_response = await client.post(
            "/api/v1/products/",
            headers=admin_auth_headers,
            json={
                "name": "Set Stock Product",
                "price": "10.00",
                "stock_quantity": 50,
            },
        )
        product_id = create_response.json()["id"]

        response = await client.post(
            f"/api/v1/products/{product_id}/stock/set",
            headers=admin_auth_headers,
            params={"quantity": 75},
        )
        assert response.status_code == 200
        assert response.json()["stock_quantity"] == 75

    @pytest.mark.asyncio
    async def test_get_categories(self, client: AsyncClient, admin_auth_headers: dict):
        """Test getting product categories."""
        await client.post(
            "/api/v1/products/",
            headers=admin_auth_headers,
            json={
                "name": "Category Product",
                "price": "10.00",
                "category": "TestCategory",
            },
        )

        response = await client.get("/api/v1/products/categories")
        assert response.status_code == 200
        data = response.json()
        assert "TestCategory" in data