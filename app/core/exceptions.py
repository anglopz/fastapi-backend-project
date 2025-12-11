"""
Excepciones personalizadas para la aplicación
"""

class AppError(Exception):
    """Excepción base para errores de la aplicación"""
    def __init__(self, message: str, status_code: int = 500):
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)

class NotFoundError(AppError):
    """Recurso no encontrado"""
    def __init__(self, resource: str = "Resource"):
        super().__init__(f"{resource} not found", 404)

class AlreadyExistsError(AppError):
    """Recurso ya existe"""
    def __init__(self, resource: str = "Resource"):
        super().__init__(f"{resource} already exists", 409)

class ValidationError(AppError):
    """Error de validación"""
    def __init__(self, message: str = "Validation error"):
        super().__init__(message, 422)

class UnauthorizedError(AppError):
    """No autorizado"""
    def __init__(self, message: str = "Unauthorized"):
        super().__init__(message, 401)

class ForbiddenError(AppError):
    """Prohibido"""
    def __init__(self, message: str = "Forbidden"):
        super().__init__(message, 403)
