"""
utils/logger.py
---------------
Configuración centralizada de logging para el Copiloto Administrativo UdeA.

Uso:
    from utils.logger import get_logger
    logger = get_logger(__name__)
    logger.info("Mensaje de ejemplo")
"""

import logging
import sys


# Formato estándar: timestamp ISO 8601 + nivel + nombre del módulo + mensaje
_FORMATO = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
_FECHA_FORMATO = "%Y-%m-%dT%H:%M:%S"


def _configurar_logger_raiz() -> None:
    """Configura el logger raíz una sola vez al importar el módulo."""
    logger_raiz = logging.getLogger("copiloto_udea")

    # Evitar handlers duplicados si el módulo se importa varias veces
    if logger_raiz.handlers:
        return

    logger_raiz.setLevel(logging.INFO)

    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(logging.INFO)

    formatter = logging.Formatter(fmt=_FORMATO, datefmt=_FECHA_FORMATO)
    handler.setFormatter(formatter)

    logger_raiz.addHandler(handler)

    # No propagar al logger raíz de Python para evitar mensajes duplicados
    logger_raiz.propagate = False


def get_logger(nombre: str) -> logging.Logger:
    """
    Retorna un logger hijo del logger raíz 'copiloto_udea'.

    Args:
        nombre: Nombre del módulo solicitante. Usar __name__ directamente.

    Returns:
        Logger configurado con nivel INFO y formato estándar.

    Example:
        >>> logger = get_logger(__name__)
        >>> logger.info("Sistema iniciado")
        2024-01-15T10:30:00 | INFO     | agentes.router | Sistema iniciado
    """
    _configurar_logger_raiz()

    # Si el nombre ya tiene el prefijo, lo usamos tal cual; si no, lo añadimos
    if nombre.startswith("copiloto_udea"):
        nombre_completo = nombre
    else:
        nombre_completo = f"copiloto_udea.{nombre}"

    return logging.getLogger(nombre_completo)
