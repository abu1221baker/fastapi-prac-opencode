# FastAPI Production Application

A production-ready FastAPI application with PostgreSQL, async SQLAlchemy 2.0, JWT authentication, and comprehensive API for products and orders.

## Features

- **FastAPI** - Modern, fast web framework for building APIs
- **PostgreSQL + asyncpg** - Async database operations with connection pooling
- **SQLAlchemy 2.0** - Modern ORM with async support
- **JWT Authentication** - Access/Refresh token pattern with rotation
- **Alembic** - Database migrations
- **Pydantic v2** - Data validation and serialization
- **Structured Logging** - JSON logging with structlog
- **Testing** - pytest with async support
- **Docker** - Containerized deployment ready
- **Role-based Access Control** - User, Admin, Superadmin roles

## Project Structure

```
├── app/
│   ├── api/
│   │   ├── deps.py              # FastAPI dependencies
│   │   └── v1/
│   │       ├── endpoints/       # API endpoints
│   │       │   ├── auth.py      # Authentication endpoints
│   │       │   ├── users.py     # User management
│   │       │   ├── products.py  # Product management
│   │       │   ├── orders.py    # Order management
│   │       │   └── health.py    # Health checks
│   │       └── router.py        # API v1 router
│   ├── core/
│   │   ├── config.py            # Configuration (Pydantic Settings)
│   │   ├── security.py          # Password hashing, JWT tokens
│   │   └── exceptions.py        # Custom exceptions
│   ├── db/
│   │   ├── session.py           # Database session management
│   │   └── base.py              # Base model class
│   ├── models/                  # SQLAlchemy models
│   │   ├── user.py
│   │   ├── product.py
│   │   ├── order.py
│   │   └── token.py
│   ├── schemas/                 # Pydantic schemas
│   │   ├── base.py
│   │   ├── user.py
│   │   ├── auth.py
│   │   ├── product.py
│   │   └── order.py
│   ├── repositories/            # Data access layer
│   │   ├── base.py
│   │   ├── user.py
│   │   ├── token.py
│   │   ├── product.py
│   │   └── order.py
│   ├── services/                # Business logic layer
│   │   ├── auth.py
│   │   ├── user.py
│   │   ├── product.py
│   │   └── order.py
│   ├── middleware/              # Custom middleware
│   │   └── logging.py
│   ├── tests/                   # Test suite
│   │   ├── conftest.py
│   │   ├── test_auth.py
│   │   ├── test_products.py
│   │   └── test_orders.py
│   ├── alembic/                 # Database migrations
│   │   ├── env.py
│   │   └── versions/
│   └── main.py                  # Application entry point
├── alembic.ini                  # Alembic configuration
├── requirements.txt             # Python dependencies
├── .env.example                 # Environment variables template
├── .gitignore
├── Dockerfile
├── docker-compose.yml
└── README.md
```

## Quick Start

### Prerequisites

- Python 3.11+
- PostgreSQL 15+
- Redis (optional, for rate limiting)

### Local Development

1. **Clone and navigate to project**
   ```bash
   cd fastapi-prod-app
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment**
   ```bash
   cp .env.example .env
   # Edit .env with your settings
   ```

5. **Start PostgreSQL** (using Docker)
   ```bash
   docker run -d \
     --name postgres \
     -e POSTGRES_USER=postgres \
     -e POSTGRES_PASSWORD=postgres \
     -e POSTGRES_DB=fastapi_prod \
     -p 5432:5432 \
     postgres:15
   ```

6. **Run migrations**
   ```bash
   alembic upgrade head
   ```

7. **Start the application**
   ```bash
   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```

8. **Access API docs**
   - Swagger UI: http://localhost:8000/api/v1/docs
   - ReDoc: http://localhost:8000/api/v1/redoc

### Using Docker Compose

```bash
docker-compose up -d
```

This starts:
- FastAPI app on port 8000
- PostgreSQL on port 5432
- Redis on port 6379

## API Endpoints

### Authentication
- `POST /api/v1/auth/register` - Register new user
- `POST /api/v1/auth/login` - Login (returns access + refresh tokens)
- `POST /api/v1/auth/refresh` - Refresh access token
- `POST /api/v1/auth/logout` - Logout (revoke refresh token)
- `POST /api/v1/auth/logout-all` - Logout from all devices
- `POST /api/v1/auth/change-password` - Change password
- `GET /api/v1/auth/me` - Get current user info

### Users (Admin only)
- `POST /api/v1/users/` - Create user
- `GET /api/v1/users/` - List users (paginated, filterable)
- `GET /api/v1/users/me` - Get own profile
- `PATCH /api/v1/users/me` - Update own profile
- `GET /api/v1/users/{id}` - Get user by ID
- `PATCH /api/v1/users/{id}` - Update user
- `DELETE /api/v1/users/{id}` - Deactivate user
- `POST /api/v1/users/{id}/activate` - Activate user (admin)
- `POST /api/v1/users/{id}/deactivate` - Deactivate user (admin)

### Products
- `POST /api/v1/products/` - Create product (admin)
- `GET /api/v1/products/` - List products (public, paginated, filterable)
- `GET /api/v1/products/categories` - Get all categories
- `GET /api/v1/products/{id}` - Get product
- `PATCH /api/v1/products/{id}` - Update product (admin)
- `DELETE /api/v1/products/{id}` - Delete product (admin)
- `POST /api/v1/products/{id}/stock/adjust` - Adjust stock (admin)
- `POST /api/v1/products/{id}/stock/set` - Set stock quantity (admin)

### Orders
- `POST /api/v1/orders/` - Create order
- `GET /api/v1/orders/` - List own orders (paginated, filterable)
- `GET /api/v1/orders/stats` - Get order statistics (admin)
- `GET /api/v1/orders/my-stats` - Get own order statistics
- `GET /api/v1/orders/{id}` - Get order
- `PATCH /api/v1/orders/{id}` - Update order (limited fields for users)
- `PATCH /api/v1/orders/{id}/status` - Update order status (admin)
- `POST /api/v1/orders/{id}/cancel` - Cancel order

### Health Checks
- `GET /api/v1/health/` - Basic health check
- `GET /api/v1/health/db` - Database health check

## Authentication

The API uses JWT Bearer tokens. Include the access token in the Authorization header:

```
Authorization: Bearer <access_token>
```

### Token Flow

1. **Login** - Returns access token (15 min) + refresh token (7 days)
2. **Access protected endpoints** - Use access token
3. **When access token expires** - Use refresh token to get new tokens
4. **Refresh token rotation** - Old refresh token is revoked, new one issued
5. **Logout** - Revoke refresh token

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `DATABASE_URL` | PostgreSQL connection string | Required |
| `SECRET_KEY` | JWT signing key (min 32 chars) | Required |
| `ALGORITHM` | JWT algorithm | HS256 |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Access token lifetime | 15 |
| `REFRESH_TOKEN_EXPIRE_DAYS` | Refresh token lifetime | 7 |
| `BCRYPT_ROUNDS` | Password hashing rounds | 12 |
| `BACKEND_CORS_ORIGINS` | Allowed CORS origins | [] |
| `DEBUG` | Enable debug mode | false |
| `ENVIRONMENT` | Environment name | production |
| `LOG_LEVEL` | Logging level | INFO |
| `LOG_FORMAT` | Log format (json/console) | json |
| `REDIS_URL` | Redis connection string | redis://localhost:6379/0 |

## Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app --cov-report=html

# Run specific test file
pytest app/tests/test_auth.py -v
```

## Database Migrations

```bash
# Create new migration
alembic revision --autogenerate -m "description"

# Apply migrations
alembic upgrade head

# Rollback one migration
alembic downgrade -1

# Show migration history
alembic history
```

## Deployment

### Docker

```bash
# Build image
docker build -t fastapi-prod-app .

# Run container
docker run -d \
  -p 8000:8000 \
  --env-file .env \
  fastapi-prod-app
```

### Production Checklist

- [ ] Set strong `SECRET_KEY` (32+ characters)
- [ ] Set `DEBUG=false`
- [ ] Configure `BACKEND_CORS_ORIGINS`
- [ ] Use PostgreSQL with SSL
- [ ] Set up Redis for rate limiting
- [ ] Configure reverse proxy (nginx)
- [ ] Set up SSL/TLS certificates
- [ ] Configure logging aggregation
- [ ] Set up monitoring (Prometheus/Grafana)
- [ ] Configure backup strategy for PostgreSQL
- [ ] Run with multiple workers (`WORKERS=4`)

## API Documentation

Once running, visit:
- **Swagger UI**: `/api/v1/docs` - Interactive API documentation
- **ReDoc**: `/api/v1/redoc` - Alternative documentation

## License

MIT License