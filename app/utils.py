"""
Utilidades generales de la aplicación
"""
# Reexportar funciones de core.security para compatibilidad
from core.security import (
    create_access_token,
    verify_token,
    hash_password,
    verify_password,
    get_password_context,
    oauth2_scheme
)

__all__ = [
    'create_access_token',
    'verify_token', 
    'hash_password',
    'verify_password',
    'get_password_context',
    'oauth2_scheme'
]

# Otras utilidades generales pueden ir aquí
def generate_random_string(length: int = 10) -> str:
    """Genera una cadena aleatoria"""
    import random
    import string
    return ''.join(random.choices(string.ascii_letters + string.digits, k=length))
