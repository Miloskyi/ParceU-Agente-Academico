"""
tests/conftest.py
-----------------
Configuración de pytest: agrega la raíz del proyecto al sys.path para que
los imports de los módulos del proyecto funcionen correctamente al correr
`pytest tests/ -v` desde cualquier directorio.
"""

import sys
from pathlib import Path

# Directorio raíz del proyecto (un nivel arriba de tests/)
ROOT = Path(__file__).parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
