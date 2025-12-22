"""
Pytest configuration and fixtures for FastAPI tests
"""
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlmodel import SQLModel

from app.main import app
from app.database.session import get_session

# Import all models to ensure they're registered with SQLModel
from app.database.models import Seller, Shipment, DeliveryPartner  # noqa: F401

# Test database URL
# Note: For UUID and ARRAY support, PostgreSQL is preferred
# But for quick tests, we'll try SQLite first and handle errors gracefully
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

# Create test engine
test_engine = create_async_engine(
    url=TEST_DATABASE_URL,
    echo=False,
)


@pytest.fixture(scope="function")
async def test_db():
    """Create test database tables for each test"""
    async with test_engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)
    yield
    async with test_engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.drop_all)


@pytest.fixture(scope="function")
async def test_session(test_db):
    """Create a test database session and override dependency"""
    async_session = async_sessionmaker(
        bind=test_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    async def override_get_session():
        async with async_session() as session:
            yield session

    # Override the dependency
    app.dependency_overrides[get_session] = override_get_session

    yield async_session

    # Clean up
    app.dependency_overrides.clear()


@pytest.fixture(scope="function")
async def client(test_session):
    """Create a test client"""
    async with AsyncClient(app=app, base_url="http://test") as test_client:
        yield test_client
