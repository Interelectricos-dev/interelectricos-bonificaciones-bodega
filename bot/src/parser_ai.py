"""Fachada de compatibilidad hacia atrás para parser_ai."""
import sys
from pathlib import Path
from typing import Any, Dict, Optional

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from src.services.dispatch_analyzer import (
    validar_un_despacho as normalizar_un_despacho,
    segregar_despachos_lote as normalizar_lote_resultado,
)
from src.services.dispatch_parser import DispatchParser
from src.services.gemini_client import GeminiClient, SYSTEM_PROMPT


def parse_con_gemini(
    texto: Optional[str] = None,
    audio_bytes: Optional[bytes] = None,
    mime_type: str = "audio/ogg",
) -> Dict[str, Any]:
    """Función de compatibilidad para llamadas heredadas."""
    cliente = GeminiClient()
    raw_ai = cliente.extraer_despachos_raw(texto=texto, audio_bytes=audio_bytes, mime_type=mime_type)
    despachos = DispatchParser.parse_ai_json_response(raw_ai)
    return normalizar_lote_resultado(despachos)


__all__ = ["SYSTEM_PROMPT", "normalizar_un_despacho", "normalizar_lote_resultado", "parse_con_gemini"]
