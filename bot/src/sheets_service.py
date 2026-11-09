"""Fachada de compatibilidad hacia atrás para sheets_service."""
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from src.services.dispatch_analyzer import (
    EMPLEADOS_FALLBACK as EMPLEADOS_DEFAULT,
    resolver_empleado,
    normalizar_numero_factura,
    procesar_y_estructurar_registros,
)
from src.services.sheets_client import SheetsClient


def construir_filas_registros(
    lote_datos: Union[Dict[str, Any], List[Dict[str, Any]]],
    catalogo_empleados: Optional[List[Dict[str, Any]]] = None,
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    items = [lote_datos] if isinstance(lote_datos, dict) else lote_datos
    resultado = procesar_y_estructurar_registros(items, catalogo_empleados=catalogo_empleados)
    todos = resultado["nuevos"] + resultado["duplicados"]
    return todos, resultado["incompletos"]


def guardar_en_google_sheets(
    lote_datos: Union[Dict[str, Any], List[Dict[str, Any]]]
) -> Dict[str, List[Dict[str, Any]]]:
    items = [lote_datos] if isinstance(lote_datos, dict) else lote_datos
    cliente = SheetsClient()
    catalogo, existentes = cliente.obtener_catalogo_y_existentes()
    analisis = procesar_y_estructurar_registros(
        items, catalogo_empleados=catalogo, existentes_set=existentes
    )
    if analisis["nuevos"]:
        filas = [r["fila_sheets"] for r in analisis["nuevos"]]
        cliente.insertar_filas_registro_diario(filas)

    return analisis


__all__ = [
    "EMPLEADOS_DEFAULT",
    "resolver_empleado",
    "normalizar_numero_factura",
    "construir_filas_registros",
    "guardar_en_google_sheets",
]
