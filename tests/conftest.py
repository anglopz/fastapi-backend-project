"""
Pytest configuration and fixtures for FastAPI tests
"""
import os
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlmodel import SQLModel

# Set TESTING environment variable before imports
os.environ["TESTING"] = "true"

from app.main import app
from app.database.session import get_session
from app.database.redis import close_redis

# Import all models to ensure they're registered with SQLModel
from app.database.models import Seller, Shipment, DeliveryPartner  # noqa: F401

# Test database URL - Use PostgreSQL for UUID and ARRAY support
# In Docker, use 'db' as host; locally use 'localhost'
# Fallback to environment variable or use test database
TEST_DB_HOST = os.getenv("TEST_DB_HOST", "db" if os.path.exists("/.dockerenv") else "localhost")
TEST_DATABASE_URL = os.getenv(
    "TEST_DATABASE_URL",
    f"postgresql+asyncpg://postgres:password@{TEST_DB_HOST}:5432/fastapi_db"
)


@pytest.fixture(scope="function")
async def test_engine():
    """Create a test engine for each test"""
    engine = create_async_engine(
        url=TEST_DATABASE_URL,
        echo=False,
    )
    yield engine
    await engine.dispose()


@pytest.fixture(scope="function")
async def test_db(test_engine):
    """Create test database tables for each test"""
    # Create tables
    async with test_engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)
    
    yield
    
    # Drop tables after test
    async with test_engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.drop_all)


@pytest.fixture(scope="function")
async def test_session(test_db, test_engine):
    """Create a test database session and override dependency"""
    # Create a new session maker for each test
    async_session_maker = async_sessionmaker(
        bind=test_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    async def override_get_session():
        async with async_session_maker() as session:
            yield session

    # Override the dependency
    app.dependency_overrides[get_session] = override_get_session

    yield async_session_maker

    # Clean up
    app.dependency_overrides.clear()


@pytest.fixture(scope="function")
async def client(test_session):
    """Create a test client"""
    async with AsyncClient(app=app, base_url="http://test") as test_client:
        yield test_client
    # Clean up Redis connections after each test
    await close_redis()
