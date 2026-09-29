# Makefile for FastAPI Production Application

.PHONY: help install test lint format migrate run docker-build docker-up docker-down clean

# Default target
help:
	@echo "FastAPI Production Application - Development Commands"
	@echo ""
	@echo "Setup:"
	@echo "  make install       - Install dependencies in virtual environment"
	@echo "  make setup         - Run full setup script"
	@echo ""
	@echo "Development:"
	@echo "  make run           - Run development server with hot reload"
	@echo "  make test          - Run tests with coverage"
	@echo "  make test-watch    - Run tests in watch mode"
	@echo "  make lint          - Run linting (ruff, mypy)"
	@echo "  make format        - Format code (ruff, black)"
	@echo ""
	@echo "Database:"
	@echo "  make migrate       - Apply database migrations"
	@echo "  make migrate-create - Create new migration"
	@echo "  make db-reset      - Reset database (drop all tables and reapply migrations)"
	@echo ""
	@echo "Docker:"
	@echo "  make docker-build  - Build Docker image"
	@echo "  make docker-up     - Start all services with docker-compose"
	@echo "  make docker-down   - Stop all services"
	@echo "  make docker-logs   - View docker-compose logs"
	@echo ""
	@echo "Utilities:"
	@echo "  make clean         - Clean up cache and temporary files"
	@echo "  make check         - Run all checks (lint, test, format)"

# Setup
install:
	pip install --upgrade pip
	pip install -r requirements.txt

setup:
	chmod +x scripts/setup.sh
	./scripts/setup.sh

# Development
run:
	uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

run-prod:
	uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4

# Testing
test:
	pytest -v --tb=short

test-cov:
	pytest --cov=app --cov-report=term-missing --cov-report=html -v

test-watch:
	pytest-watch --runner "pytest -v"

# Linting and Formatting
lint:
	ruff check app/
	mypy app/

format:
	ruff check --fix app/
	black app/
	isort app/

format-check:
	ruff check app/
	black --check app/
	isort --check-only app/

# Database
migrate:
	alembic upgrade head

migrate-create:
	@read -p "Enter migration message: " msg; \
	alembic revision --autogenerate -m "$$msg"

migrate-history:
	alembic history

db-reset:
	alembic downgrade base
	alembic upgrade head

# Docker
docker-build:
	docker build -t fastapi-prod-app .

docker-up:
	docker-compose up -d

docker-down:
	docker-compose down

docker-down-v:
	docker-compose down -v

docker-logs:
	docker-compose logs -f

docker-shell:
	docker-compose exec app bash

# Cleanup
clean:
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	find . -type f -name "*.pyo" -delete 2>/dev/null || true
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".mypy_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".ruff_cache" -exec rm -rf {} + 2>/dev/null || true
	rm -rf htmlcov/ .coverage coverage.xml 2>/dev/null || true

# Checks
check: format-check lint test

# Generate requirements
requirements:
	pip freeze > requirements.txt

# Security
security-check:
	pip-audit
	bandit -r app/