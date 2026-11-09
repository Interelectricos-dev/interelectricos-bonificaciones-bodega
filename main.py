import sys
from typing import Any, Dict, Optional
from src.config import settings, get_logger
from src.services.dispatch_analyzer import (
    segregar_despachos_lote,
    procesar_y_estructurar_registros,
)
from src.services.dispatch_exporter import DispatchExporter
from src.services.dispatch_parser import DispatchParser
from src.services.gemini_client import GeminiClient
from src.services.green_api_client import GreenAPIClient
from src.services.sheets_client import SheetsClient

logger = get_logger("orchestrator")


def orquestar_procesamiento_despacho(
    texto: Optional[str] = None,
    audio_bytes: Optional[bytes] = None,
    mime_type: str = "audio/ogg",
) -> Dict[str, Any]:
    """
    Orquestador declarativo de alto nivel:
    Coordina secuencialmente la extracción, parseo, validación, persistencia y reporte.
    """
    logger.info("Iniciando orquestación de nuevo despacho...")
    gemini = GeminiClient()
    sheets = SheetsClient()

    # 1. Consumo de IA multimodal (integración) y parseo estructural (ingesta)
    raw_ai_text = gemini.extraer_despachos_raw(texto=texto, audio_bytes=audio_bytes, mime_type=mime_type)
    despachos_crudos = DispatchParser.parse_ai_json_response(raw_ai_text)

    # 2. Análisis preliminar de campos y rangos con tolerancia a fallos parciales
    segregacion = segregar_despachos_lote(despachos_crudos)

    # 3. Consulta de base de datos / catálogo (con fallback resiliente no bloqueante)
    catalogo, existentes = sheets.obtener_catalogo_y_existentes()

    # 4. Reglas de negocio puras: resolución de auxiliares, deduplicación y filas físicas
    analisis = procesar_y_estructurar_registros(
        segregacion["validos"], catalogo_empleados=catalogo, existentes_set=existentes
    )
    incompletos_totales = segregacion["incompletos"] + analisis["incompletos"]

    # 5. Persistencia atómica de nuevos registros
    if analisis["nuevos"]:
        filas = [r["fila_sheets"] for r in analisis["nuevos"]]
        sheets.insertar_filas_registro_diario(filas)

    # 6. Formateo y presentación de artefactos de salida
    mensaje_salida = DispatchExporter.formatear_mensaje_whatsapp(
        nuevos=analisis["nuevos"],
        duplicados=analisis["duplicados"],
        incompletos=incompletos_totales,
    )
    DispatchExporter.exportar_reporte_auditoria_json(
        {"nuevos": analisis["nuevos"], "duplicados": analisis["duplicados"], "incompletos": incompletos_totales}
    )

    return {
        "nuevos": analisis["nuevos"],
        "duplicados": analisis["duplicados"],
        "incompletos": incompletos_totales,
        "mensaje_whatsapp": mensaje_salida,
    }


def main() -> None:
    """Punto de entrada para ejecución por línea de comandos o programador de tareas."""
    logger.info("Sistema de Bonificaciones Bodega iniciado. BaseDir: %s", settings.BASE_DIR)
    entrada_texto = " ".join(sys.argv[1:]).strip() if len(sys.argv) > 1 else None

    if not entrada_texto:
        logger.info("Modo de prueba demostrativo. Procesando caso estándar...")
        entrada_texto = "Para Edward: Factura IC 104958 3 puntos esfuerzo"

    try:
        resultado = orquestar_procesamiento_despacho(texto=entrada_texto)
        print("\n--- RESULTADO DE LA EJECUCIÓN ---\n")
        print(resultado["mensaje_whatsapp"])
    except Exception as exc:
        logger.error("Error en la ejecución del flujo principal: %s", exc)
        print(f"\n[ERROR] {exc}")


if __name__ == "__main__":
    main()

