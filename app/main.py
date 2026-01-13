from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.utils import get_openapi
from fastapi.responses import HTMLResponse
from scalar_fastapi import get_scalar_api_reference

from app.api.api_router import master_router
from app.config import cors_settings
from app.core.exception_handlers import setup_exception_handlers
from app.core.middleware import request_logging_middleware
from app.core.security import oauth2_scheme_seller, oauth2_scheme_partner
from app.database.redis import close_redis, get_redis
from app.database.session import create_db_tables


async def wait_for_database(max_retries: int = 10, delay: float = 2.0):
    """Wait for database to be ready with exponential backoff"""
    import asyncio
    from sqlalchemy import text
    from app.database.session import engine
    
    for attempt in range(max_retries):
        try:
            async with engine.begin() as conn:
                await conn.execute(text("SELECT 1"))
            print("✅ Database connection successful")
            return True
        except Exception as e:
            if attempt < max_retries - 1:
                wait_time = delay * (2 ** min(attempt, 5))  # Exponential backoff, max 32s
                print(f"⏳ Waiting for database... (attempt {attempt + 1}/{max_retries}) - {e}")
                await asyncio.sleep(wait_time)
            else:
                print(f"❌ Database connection failed after {max_retries} attempts: {e}")
                raise
    return False


async def wait_for_redis(max_retries: int = 5, delay: float = 2.0):
    """Wait for Redis to be ready with exponential backoff"""
    import asyncio
    from app.database.redis import get_redis
    
    for attempt in range(max_retries):
        try:
            await get_redis()
            print("✅ Redis connection successful")
            return True
        except Exception as e:
            if attempt < max_retries - 1:
                wait_time = delay * (2 ** min(attempt, 3))  # Exponential backoff, max 8s
                print(f"⏳ Waiting for Redis... (attempt {attempt + 1}/{max_retries}) - {e}")
                await asyncio.sleep(wait_time)
            else:
                print(f"⚠️  Redis connection failed after {max_retries} attempts: {e}")
                print("⚠️  Application will continue without Redis caching")
                return False
    return False


@asynccontextmanager
async def lifespan_handler(app: FastAPI):
    # Startup - run checks in background to not block port binding
    import os
    import asyncio
    port = os.getenv("PORT", "8000")
    print(f"🚀 Starting application on port {port}...")
    print(f"📡 Server will bind to port {port} immediately")

    # Start database/Redis checks in background task (non-blocking)
    async def startup_checks():
        # Wait for database to be ready (with shorter timeout for Render)
        try:
            await wait_for_database(max_retries=10, delay=2.0)
        except Exception as e:
            print(f"❌ Database connection failed: {e}")
            print("⚠️  Application will start but database operations may fail")
            return
        
        # Crear tablas de la base de datos
        try:
            await create_db_tables()
            print("✅ Database tables created/verified")
        except Exception as e:
            print(f"⚠️  Could not create database tables: {e}")

        # Wait for Redis to be ready (non-blocking, continues if fails)
        await wait_for_redis(max_retries=5, delay=2.0)
        print(f"✅ Application startup checks complete")

    # Start checks in background (don't await - let server bind port first)
    asyncio.create_task(startup_checks())

    yield

    # Shutdown
    print("🛑 Shutting down application...")
    await close_redis()


# Section 28: API Documentation - General Metadata
app = FastAPI(
    title="FastShip API",
    description="""
    FastShip is a comprehensive shipping management API that enables sellers and delivery partners 
    to manage shipments efficiently.
    
    ## Features
    
    * **Seller Management**: Register, authenticate, and manage seller accounts
    * **Delivery Partner Management**: Register and manage delivery partner accounts with serviceable locations
    * **Shipment Management**: Create, track, and manage shipments with real-time status updates
    * **Tagging System**: Add tags to shipments for special handling instructions
    * **Location-Based Routing**: Automatic assignment of delivery partners based on destination
    * **Real-time Notifications**: Email and SMS notifications for shipment status changes
    * **Review System**: Collect customer reviews after delivery
    
    ## Authentication
    
    The API uses OAuth2 with JWT tokens. Two separate authentication schemes are available:
    
    * **Seller Authentication**: For seller endpoints (`/seller/*`)
    * **Delivery Partner Authentication**: For delivery partner endpoints (`/partner/*`)
    
    ## Getting Started
    
    1. Register as a seller or delivery partner
    2. Verify your email address
    3. Login to get an access token
    4. Use the token in the Authorization header: `Bearer <token>`
    """,
    version="1.0.0",
    contact={
        "name": "FastShip API Support",
        "email": "support@fastship.com",
        "url": "https://fastship.com/support",
    },
    license_info={
        "name": "MIT",
        "url": "https://opensource.org/licenses/MIT",
    },
    servers=[
        {
            "url": "http://localhost:8000",
            "description": "Development server",
        },
        {
            "url": "https://api.fastship.com",
            "description": "Production server",
        },
    ],
    terms_of_service="https://fastship.com/terms",
    lifespan=lifespan_handler,
)

# Section 27: Add request logging middleware
app.middleware("http")(request_logging_middleware)

# Section 31-32: Add CORS middleware for frontend integration
# CORS origins are configured via CORS_ORIGINS environment variable
# Default includes common development ports, override in production
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API router with /api/v1 prefix for versioning
app.include_router(master_router, prefix="/api/v1")


# Custom OpenAPI schema to include both OAuth2 schemes
def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    
    # Section 28: Enhanced OpenAPI schema with comprehensive metadata
    openapi_schema = get_openapi(
        title=app.title,
        version=app.version,
        description=app.description,
        routes=app.routes,
        contact=app.contact,
        license_info=app.license_info,
        servers=app.servers,
        terms_of_service=app.terms_of_service,
    )
    
    # Replace the single OAuth2 scheme with both seller and partner schemes
    openapi_schema["components"]["securitySchemes"] = {
        "OAuth2PasswordBearerSeller": {
            "type": "oauth2",
            "flows": {
                "password": {
                    "tokenUrl": "/seller/token",
                    "scopes": {}
                }
            }
        },
        "OAuth2PasswordBearerPartner": {
            "type": "oauth2",
            "flows": {
                "password": {
                    "tokenUrl": "/partner/token",
                    "scopes": {}
                }
            }
        }
    }
    
    # Update endpoints to use the correct OAuth2 scheme based on path
    # Seller endpoints use OAuth2PasswordBearerSeller
    # Partner endpoints use OAuth2PasswordBearerPartner
    for path, methods in openapi_schema.get("paths", {}).items():
        for method, operation in methods.items():
            if isinstance(operation, dict) and "security" in operation:
                new_security = []
                for sec_item in operation["security"]:
                    # sec_item is a dict like {"OAuth2PasswordBearer": []}
                    if isinstance(sec_item, dict) and "OAuth2PasswordBearer" in sec_item:
                        # Determine which scheme to use based on path
                        if "/seller" in path or (path.startswith("/shipment") and method.lower() == "post"):
                            # Seller endpoints or shipment creation (requires seller)
                            new_security.append({"OAuth2PasswordBearerSeller": []})
                        elif "/partner" in path or (path.startswith("/shipment") and method.lower() == "patch"):
                            # Partner endpoints or shipment update (requires partner)
                            new_security.append({"OAuth2PasswordBearerPartner": []})
                        else:
                            # Default to seller for other endpoints
                            new_security.append({"OAuth2PasswordBearerSeller": []})
                    else:
                        new_security.append(sec_item)
                operation["security"] = new_security
    
    app.openapi_schema = openapi_schema
    return app.openapi_schema

app.openapi = custom_openapi


### Root Page
@app.get("/", response_class=HTMLResponse, include_in_schema=False)
async def root():
    """Root page with API information and links to documentation"""
    html_content = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>FastShip API</title>
        <style>
            * {
                margin: 0;
                padding: 0;
                box-sizing: border-box;
            }
            body {
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: #333;
                min-height: 100vh;
                display: flex;
                align-items: center;
                justify-content: center;
                padding: 20px;
            }
            .container {
                background: white;
                border-radius: 16px;
                box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
                max-width: 800px;
                width: 100%;
                padding: 40px;
                text-align: center;
            }
            h1 {
                color: #667eea;
                font-size: 2.5em;
                margin-bottom: 10px;
                font-weight: 700;
            }
            .subtitle {
                color: #666;
                font-size: 1.2em;
                margin-bottom: 30px;
            }
            .description {
                color: #555;
                line-height: 1.6;
                margin-bottom: 40px;
                text-align: left;
            }
            .links {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
                gap: 20px;
                margin-top: 40px;
            }
            .link-card {
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                padding: 25px;
                border-radius: 12px;
                text-decoration: none;
                transition: transform 0.3s ease, box-shadow 0.3s ease;
                display: block;
            }
            .link-card:hover {
                transform: translateY(-5px);
                box-shadow: 0 10px 30px rgba(102, 126, 234, 0.4);
            }
            .link-card h3 {
                margin-bottom: 10px;
                font-size: 1.3em;
            }
            .link-card p {
                opacity: 0.9;
                font-size: 0.9em;
            }
            .features {
                text-align: left;
                margin: 30px 0;
                padding: 20px;
                background: #f8f9fa;
                border-radius: 8px;
            }
            .features h3 {
                color: #667eea;
                margin-bottom: 15px;
            }
            .features ul {
                list-style: none;
                padding-left: 0;
            }
            .features li {
                padding: 8px 0;
                padding-left: 25px;
                position: relative;
            }
            .features li:before {
                content: "✓";
                position: absolute;
                left: 0;
                color: #667eea;
                font-weight: bold;
            }
            .status {
                display: inline-block;
                background: #10b981;
                color: white;
                padding: 8px 16px;
                border-radius: 20px;
                font-size: 0.9em;
                margin-bottom: 20px;
            }
            .version {
                color: #999;
                font-size: 0.9em;
                margin-top: 30px;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🚀 FastShip API</h1>
            <p class="subtitle">Comprehensive Shipping Management API</p>
            <span class="status">● Live</span>
            
            <div class="description">
                <p>FastShip is a comprehensive shipping management API that enables sellers and delivery partners to manage shipments efficiently.</p>
            </div>
            
            <div class="features">
                <h3>Key Features</h3>
                <ul>
                    <li>Seller & Delivery Partner Management</li>
                    <li>Real-time Shipment Tracking</li>
                    <li>Location-Based Routing</li>
                    <li>Email & SMS Notifications</li>
                    <li>Review System</li>
                    <li>OAuth2 JWT Authentication</li>
                </ul>
            </div>
            
            <div class="links">
                <a href="/docs" class="link-card">
                    <h3>📚 Swagger UI</h3>
                    <p>Interactive API documentation</p>
                </a>
                <a href="/scalar" class="link-card">
                    <h3>✨ Scalar Docs</h3>
                    <p>Modern API documentation</p>
                </a>
                <a href="/api/v1/health" class="link-card">
                    <h3>💚 Health Check</h3>
                    <p>API status endpoint</p>
                </a>
                <a href="/redoc" class="link-card">
                    <h3>📖 ReDoc</h3>
                    <p>Alternative documentation</p>
                </a>
            </div>
            
            <div class="version">
                <p>Version 1.0.0 | <a href="https://fastship.com/support" style="color: #667eea;">Support</a></p>
            </div>
        </div>
    </body>
    </html>
    """
    return html_content


### Scalar API Documentation
@app.get("/scalar", include_in_schema=False)
def get_scalar_docs():
    return get_scalar_api_reference(
        openapi_url=app.openapi_url,
        title="Scalar API",
    )


### Health Check Endpoint (available at root for backward compatibility)
# Note: /api/v1/health is provided by the health router
@app.get("/health")
async def health_check():
    """Health check endpoint with Redis status (root level for backward compatibility)"""
    redis_status = "disconnected"
    try:
        redis_client = await get_redis()
        await redis_client.ping()
        redis_status = "connected"
    except Exception:
        redis_status = "disconnected"

    return {"status": "healthy", "redis": redis_status, "service": "FastAPI Backend"}


### Test Redis Endpoint
@app.get("/test-redis")
async def test_redis():
    """Test Redis connection and basic operations"""
    from app.database.redis import get_cache, set_cache

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
setup_exception_handlers(app)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
