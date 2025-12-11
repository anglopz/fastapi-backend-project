from contextlib import asynccontextmanager

from fastapi import FastAPI
from scalar_fastapi import get_scalar_api_reference

from api.api_router import master_router
from database.session import create_db_tables
from database.redis import get_redis, close_redis  # <-- NUEVO


@asynccontextmanager
async def lifespan_handler(app: FastAPI):
    # Startup
    print("🚀 Starting application...")

    # Crear tablas de la base de datos
    await create_db_tables()

    # Inicializar Redis (con manejo de errores)
    try:
        await get_redis()
        print("✅ Redis connected successfully")
    except Exception as e:
        print(f"⚠️  Redis connection failed: {e}")
        print("⚠️  Application will continue without Redis caching")

    yield

    # Shutdown
    print("🛑 Shutting down application...")
    await close_redis()


app = FastAPI(
    # Server start/stop listener
    lifespan=lifespan_handler,
)

app.include_router(master_router)


### Scalar API Documentation
@app.get("/scalar", include_in_schema=False)
def get_scalar_docs():
    return get_scalar_api_reference(
        openapi_url=app.openapi_url,
        title="Scalar API",
    )


### Health Check Endpoint (NUEVO - para monitoreo)
@app.get("/health")
async def health_check():
    """Health check endpoint with Redis status"""
    from database.redis import get_redis

    redis_status = "disconnected"
    try:
        redis_client = await get_redis()
        await redis_client.ping()
        redis_status = "connected"
    except Exception:
        redis_status = "disconnected"

    return {"status": "healthy", "redis": redis_status, "service": "FastAPI Backend"}


### Test Redis Endpoint (NUEVO - para desarrollo)
@app.get("/test-redis")
async def test_redis():
    """Test Redis connection and basic operations"""
    from database.redis import get_redis, set_cache, get_cache

    try:
        # Test básico
        redis_client = await get_redis()
        await redis_client.set("test_key", "Redis is working!")
        value = await redis_client.get("test_key")

        # Test con cache functions
        await set_cache("test_cache", "Cache funciona!", 60)
        cached = await get_cache("test_cache")

        # Limpiar
        await redis_client.delete("test_key")
        await redis_client.delete("fastapi:cache:test_cache")

        return {
            "success": True,
            "message": "Redis is working correctly",
            "basic_test": value,
            "cache_test": cached,
            "timestamp": "test_completed",
        }
    except Exception as e:
        return {"success": False, "error": str(e), "message": "Redis test failed"}

# Setup exception handlers
from core.exception_handlers import setup_exception_handlers
setup_exception_handlers(app)

# Include all routers
app.include_router(master_router)

# Add scalar API reference
@app.get("/reference", include_in_schema=False)
async def scalar_api_reference():
    return get_scalar_api_reference(
        title="FastAPI Scalar API Reference",
        spec_url="/openapi.json"
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
