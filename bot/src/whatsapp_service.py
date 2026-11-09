"""Fachada de compatibilidad hacia atrás para whatsapp_service."""
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from src.services.green_api_client import GreenAPIClient
from src.services.dispatch_parser import DispatchParser
from src.services.dispatch_exporter import DispatchExporter


class GreenAPIService(GreenAPIClient):
    """Alias para compatibilidad con GreenAPIService previo."""

    @staticmethod
    def extraer_contenido_webhook(body: Dict[str, Any]) -> Tuple[Optional[str], Optional[str], Optional[str]]:
        chat_id, texto, download_url, _ = DispatchParser.parse_webhook_payload(body)
        return chat_id, texto, download_url


def describir_incompleto(inc: Dict[str, Any]) -> str:
    return DispatchExporter.describir_incompleto(inc)


def formatear_mensaje_confirmacion(
    nuevos: List[Dict[str, Any]],
    duplicados: Optional[List[Dict[str, Any]]] = None,
    incompletos: Optional[List[Dict[str, Any]]] = None,
) -> str:
    return DispatchExporter.formatear_mensaje_whatsapp(nuevos, duplicados, incompletos)


__all__ = [
    "GreenAPIService",
    "describir_incompleto",
    "formatear_mensaje_confirmacion",
]
