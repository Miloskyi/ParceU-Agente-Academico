"""
Configuración de CORS y otros settings del backend.
"""

import os

# Configuración de CORS
def get_cors_origins():
    """Retorna los orígenes permitidos para CORS"""
    # En producción, usar variable de entorno
    if cors_origins := os.environ.get("CORS_ORIGINS"):
        return cors_origins.split(",")
    
    # Configuración por defecto para desarrollo y despliegue
    return [
        "http://localhost:3000",
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "https://parceru-frontend.vercel.app",
    ]

def get_cors_regex():
    """Retorna el regex pattern para CORS"""
    return r"https://.*\.vercel\.app$|http://localhost:.*|http://127\.0\.0\.1:.*"

def allow_all_cors():
    """Determina si se debe usar CORS permisivo (solo para debugging)"""
    return os.environ.get("ALLOW_ALL_CORS", "false").lower() == "true"