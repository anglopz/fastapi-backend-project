"""
Handlers globales de excepciones para FastAPI
"""
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

from .exceptions import AppError

def setup_exception_handlers(app: FastAPI):
    """Configura handlers de excepciones globales"""
    
    @app.exception_handler(AppError)
    async def app_error_handler(request: Request, exc: AppError):
        """Maneja excepciones personalizadas de la app"""
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error": exc.__class__.__name__,
                "message": exc.message,
                "status_code": exc.status_code
            }
        )
    
    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        """Maneja errores de validación de Pydantic"""
        return JSONResponse(
            status_code=422,
            content={
                "error": "ValidationError",
                "message": "Validation error",
                "details": exc.errors()
            }
        )
    
    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(request: Request, exc: StarletteHTTPException):
        """Maneja excepciones HTTP de Starlette"""
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error": "HTTPException",
                "message": exc.detail,
                "status_code": exc.status_code
            }
        )
    
    @app.exception_handler(Exception)
    async def general_exception_handler(request: Request, exc: Exception):
        """Maneja cualquier otra excepción no capturada"""
        # Log del error (en producción usarías un logger)
        print(f"Unhandled exception: {type(exc).__name__}: {exc}")
        
        return JSONResponse(
            status_code=500,
            content={
                "error": "InternalServerError",
                "message": "Internal server error",
                "status_code": 500
            }
        )
    
    return app
