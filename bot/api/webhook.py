import sys
from pathlib import Path

# Resolver ruta raíz del proyecto
ROOT_DIR = Path(__file__).resolve().parent.parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from api.webhook import handler

__all__ = ["handler"]
