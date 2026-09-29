"""Order tests."""
import pytest
from httpx import AsyncClient
from decimal import Decimal


class TestOrders:
    """Order endpoint tests."""

    @pytest.mark.asyncio
    async def test_create_order(self, client: AsyncClient, auth_headers: dict, admin_auth_headers: dict):
        """Test creating an order."""
        # Create products first
        product1_response = await client.post(
            "/api/v1/products/",
            headers=admin_auth_headers,
            json={
                "name": "Order Product 1",
                "price": "10.00",
                "stock_quantity": 100,
            },
        )
        product1_id = product1_response.json()["id"]

        product2_response = await client.post(
            "/api/v1/products/",
            headers=admin_auth_headers,
            json={
                "name": "Order Product 2",
                "price": "20.00",
                "stock_quantity": 50,
            },
        )
        product2_id = product2_response.json()["id"]

        # Create order
        response = await client.post(
            "/api/v1/orders/",
            headers=auth_headers,
            json={
                "items": [
                    {"product_id": product1_id, "quantity": 2},
                    {"product_id": product2_id, "quantity": 1},
                ],
                "shipping_address": "123 Test St, Test City, TS 12345",
                "phone_number": "+1234567890",
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert data["user_id"] == 1  # test_user id
        assert data["status"] == "pending"
        assert data["total_amount"] == "40.00"  # 2*10 + 1*20
        assert len(data["items"]) == 2

    @pytest.mark.asyncio
    async def test_create_order_insufficient_stock(self, client: AsyncClient, auth_headers: dict, admin_auth_headers: dict):
        """Test creating an order with insufficient stock."""
        product_response = await client.post(
            "/api/v1/products/",
            headers=admin_auth_headers,
            json={
                "name": "Low Stock Product",
                "price": "10.00",
                "stock_quantity": 5,
            },
        )
        product_id = product_response.json()["id"]

        response = await client.post(
            "/api/v1/orders/",
            headers=auth_headers,
            json={
                "items": [{"product_id": product_id, "quantity": 10}],
                "shipping_address": "123 Test St",
            },
        )
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_create_order_invalid_product(self, client: AsyncClient, auth_headers: dict):
        """Test creating an order with invalid product."""
        response = await client.post(
            "/api/v1/orders/",
            headers=auth_headers,
            json={
                "items": [{"product_id": 999999, "quantity": 1}],
                "shipping_address": "123 Test St",
            },
        )
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_list_orders(self, client: AsyncClient, auth_headers: dict, admin_auth_headers: dict):
        """Test listing user's orders."""
        # Create an order first
        product_response = await client.post(
            "/api/v1/products/",
            headers=admin_auth_headers,
            json={"name": "List Order Product", "price": "15.00", "stock_quantity": 10},
        )
        product_id = product_response.json()["id"]

        await client.post(
            "/api/v1/orders/",
            headers=auth_headers,
            json={
                "items": [{"product_id": product_id, "quantity": 1}],
                "shipping_address": "123 Test St",
            },
        )

        response = await client.get("/api/v1/orders/", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert data["total"] >= 1

    @pytest.mark.asyncio
    async def test_list_orders_with_filters(self, client: AsyncClient, auth_headers: dict):
        """Test listing orders with filters."""
        response = await client.get(
            "/api/v1/orders/",
            headers=auth_headers,
            params={"status": "pending", "page": 1, "size": 10},
        )
        assert response.status_code == 200
        data = response.json()
        assert "items" in data

    @pytest.mark.asyncio
    async def test_get_order(self, client: AsyncClient, auth_headers: dict, admin_auth_headers: dict):
        """Test getting a specific order."""
        product_response = await client.post(
            "/api/v1/products/",
            headers=admin_auth_headers,
            json={"name": "Get Order Product", "price": "25.00", "stock_quantity": 10},
        )
        product_id = product_response.json()["id"]

        create_response = await client.post(
            "/api/v1/orders/",
            headers=auth_headers,
            json={
                "items": [{"product_id": product_id, "quantity": 1}],
                "shipping_address": "123 Test St",
            },
        )
        order_id = create_response.json()["id"]

        response = await client.get(f"/api/v1/orders/{order_id}", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == order_id
        assert data["total_amount"] == "25.00"

    @pytest.mark.asyncio
    async def test_get_other_user_order(self, client: AsyncClient, auth_headers: dict, admin_auth_headers: dict):
        """Test that users can't access other users' orders."""
        # Admin creates a product
        product_response = await client.post(
            "/api/v1/products/",
            headers=admin_auth_headers,
            json={"name": "Other User Product", "price": "30.00", "stock_quantity": 10},
        )
        product_id = product_response.json()["id"]

        # Admin creates an order (as admin user)
        admin_order_response = await client.post(
            "/api/v1/orders/",
            headers=admin_auth_headers,
            json={
                "items": [{"product_id": product_id, "quantity": 1}],
                "shipping_address": "Admin Address",
            },
        )
        order_id = admin_order_response.json()["id"]

        # Regular user tries to access admin's order
        response = await client.get(f"/api/v1/orders/{order_id}", headers=auth_headers)
        assert response.status_code == 404  # Should not find it (different user)

    @pytest.mark.asyncio
    async def test_update_order(self, client: AsyncClient, auth_headers: dict, admin_auth_headers: dict):
        """Test updating an order (shipping address)."""
        product_response = await client.post(
            "/api/v1/products/",
            headers=admin_auth_headers,
            json={"name": "Update Order Product", "price": "10.00", "stock_quantity": 10},
        )
        product_id = product_response.json()["id"]

        create_response = await client.post(
            "/api/v1/orders/",
            headers=auth_headers,
            json={
                "items": [{"product_id": product_id, "quantity": 1}],
                "shipping_address": "Original Address",
            },
        )
        order_id = create_response.json()["id"]

        # User can update shipping address
        response = await client.patch(
            f"/api/v1/orders/{order_id}",
            headers=auth_headers,
            json={"shipping_address": "Updated Address"},
        )
        assert response.status_code == 200
        assert response.json()["shipping_address"] == "Updated Address"

    @pytest.mark.asyncio
    async def test_cancel_order(self, client: AsyncClient, auth_headers: dict, admin_auth_headers: dict):
        """Test cancelling an order."""
        product_response = await client.post(
            "/api/v1/products/",
            headers=admin_auth_headers,
            json={"name": "Cancel Product", "price": "50.00", "stock_quantity": 10},
        )
        product_id = product_response.json()["id"]

        create_response = await client.post(
            "/api/v1/orders/",
            headers=auth_headers,
            json={
                "items": [{"product_id": product_id, "quantity": 2}],
                "shipping_address": "123 Test St",
            },
        )
        order_id = create_response.json()["id"]

        # Cancel order
        response = await client.post(
            f"/api/v1/orders/{order_id}/cancel",
            headers=auth_headers,
        )
        assert response.status_code == 200
        assert response.json()["status"] == "cancelled"

        # Verify stock was restored
        product_response = await client.get(f"/api/v1/products/{product_id}", headers=admin_auth_headers)
        assert product_response.json()["stock_quantity"] == 10  # Restored to original

    @pytest.mark.asyncio
    async def test_cancel_shipped_order(self, client: AsyncClient, auth_headers: dict, admin_auth_headers: dict):
        """Test that shipped orders cannot be cancelled."""
        product_response = await client.post(
            "/api/v1/products/",
            headers=admin_auth_headers,
            json={"name": "Shipped Product", "price": "10.00", "stock_quantity": 10},
        )
        product_id = product_response.json()["id"]

        create_response = await client.post(
            "/api/v1/orders/",
            headers=auth_headers,
            json={
                "items": [{"product_id": product_id, "quantity": 1}],
                "shipping_address": "123 Test St",
            },
        )
        order_id = create_response.json()["id"]

        # Admin ships the order
        await client.patch(
            f"/api/v1/orders/{order_id}/status",
            headers=admin_auth_headers,
            json={"status": "shipped"},
        )

        # User tries to cancel
        response = await client.post(
            f"/api/v1/orders/{order_id}/cancel",
            headers=auth_headers,
        )
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_admin_update_order_status(self, client: AsyncClient, auth_headers: dict, admin_auth_headers: dict):
        """Test admin updating order status."""
        product_response = await client.post(
            "/api/v1/products/",
            headers=admin_auth_headers,
            json={"name": "Status Product", "price": "100.00", "stock_quantity": 5},
        )
        product_id = product_response.json()["id"]

        create_response = await client.post(
            "/api/v1/orders/",
            headers=auth_headers,
            json={
                "items": [{"product_id": product_id, "quantity": 1}],
                "shipping_address": "123 Test St",
            },
        )
        order_id = create_response.json()["id"]

        # Admin updates status through workflow
        for status in ["confirmed", "processing", "shipped", "delivered"]:
            response = await client.patch(
                f"/api/v1/orders/{order_id}/status",
                headers=admin_auth_headers,
                json={"status": status},
            )
            assert response.status_code == 200
            assert response.json()["status"] == status

    @pytest.mark.asyncio
    async def test_user_cannot_update_status(self, client: AsyncClient, auth_headers: dict, admin_auth_headers: dict):
        """Test that regular users cannot update order status."""
        product_response = await client.post(
            "/api/v1/products/",
            headers=admin_auth_headers,
            json={"name": "Status Product 2", "price": "10.00", "stock_quantity": 10},
        )
        product_id = product_response.json()["id"]

        create_response = await client.post(
            "/api/v1/orders/",
            headers=auth_headers,
            json={
                "items": [{"product_id": product_id, "quantity": 1}],
                "shipping_address": "123 Test St",
            },
        )
        order_id = create_response.json()["id"]

        # User tries to update status
        response = await client.patch(
            f"/api/v1/orders/{order_id}/status",
            headers=auth_headers,
            json={"status": "cancelled"},
        )
        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_get_order_stats(self, client: AsyncClient, admin_auth_headers: dict):
        """Test getting order statistics (admin)."""
        response = await client.get("/api/v1/orders/stats", headers=admin_auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "total_orders" in data
        assert "total_revenue" in data

    @pytest.mark.asyncio
    async def test_get_my_order_stats(self, client: AsyncClient, auth_headers: dict):
        """Test getting current user's order statistics."""
        response = await client.get("/api/v1/orders/my-stats", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "total_orders" in data
        assert "total_revenue" in data