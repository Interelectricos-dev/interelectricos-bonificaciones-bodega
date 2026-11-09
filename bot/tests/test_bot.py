import json
import sys
import time
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from main import orquestar_procesamiento_despacho
from src.config import settings, get_logger
from src.services.dispatch_exporter import DispatchExporter
from src.services.dispatch_parser import DispatchParser
from src.services.green_api_client import GreenAPIClient

logger = get_logger("test_listener")


def escuchar_whatsapp_continuo() -> None:
    """
    Consola de pruebas en vivo: escucha continuamente WhatsApp y procesa despachos
    utilizando la arquitectura modular desacoplada.
    """
    wa = GreenAPIClient()
    chats_autorizados = settings.get_authorized_chats()

    logger.info("=" * 60)
    logger.info("🎧 MODO DE ESCUCHA ACTIVO (Presiona Ctrl + C para salir)")
    logger.info("Chats autorizados: %s", chats_autorizados or "TODOS")
    logger.info("=" * 60)

    procesados = set()
    try:
        historial_inicial = wa.obtener_ultimos_mensajes(minutos=10)
        for m in historial_inicial:
            mid = m.get("idMessage")
            if mid:
                procesados.add(mid)
    except Exception as exc:
        logger.warning("No se pudo precargar historial reciente: %s", exc)

    try:
        while True:
            mensajes_a_procesar = []

            # 1. Cola de Green API
            try:
                body = wa.recibir_notificacion_cola(borrar_al_leer=True)
                if body:
                    cid, txt, aurl, mid = DispatchParser.parse_webhook_payload(body)
                    if cid:
                        mensajes_a_procesar.append((mid or "queue", cid, txt, aurl))
            except Exception:
                pass

            # 2. Sondeo de historial reciente
            try:
                recientes = wa.obtener_ultimos_mensajes(minutos=2)
                for item in recientes:
                    mid = item.get("idMessage")
                    if not mid or mid in procesados or item.get("sendByApi", False):
                        continue
                    procesados.add(mid)
                    cid = item.get("chatId")
                    txt = item.get("textMessage")
                    aurl = item.get("downloadUrl") if item.get("typeMessage") in ("audioMessage", "voiceMessage") else None
                    if cid and (txt or aurl):
                        mensajes_a_procesar.append((mid, cid, txt, aurl))
            except Exception:
                pass

            if not mensajes_a_procesar:
                time.sleep(1.5)
                continue

            for _, chat_id, texto, audio_url in mensajes_a_procesar:
                if chats_autorizados and chat_id not in chats_autorizados:
                    continue
                if texto and texto.startswith(("✅", "⚠️", "🤖")):
                    continue

                logger.info("Nuevo mensaje recibido de: %s", chat_id)
                audio_bytes = None
                mime_type = "audio/ogg"

                if audio_url:
                    logger.info("Descargando audio adjunto...")
                    audio_bytes, mime_type = wa.descargar_archivo(audio_url)

                try:
                    resultado = orquestar_procesamiento_despacho(
                        texto=texto, audio_bytes=audio_bytes, mime_type=mime_type
                    )
                    wa.enviar_mensaje(chat_id, resultado["mensaje_whatsapp"])
                    logger.info("Respuesta enviada a %s", chat_id)
                except Exception as err:
                    if "NO_ES_DESPACHO" in str(err):
                        logger.info("Mensaje conversacional omitido: %s", err)
                        continue
                    logger.error("Error al procesar despacho: %s", err)
                    alerta = DispatchExporter.formatear_error_operativo(str(err))
                    try:
                        wa.enviar_mensaje(chat_id, alerta)
                    except Exception:
                        pass

    except KeyboardInterrupt:
        logger.info("Escucha detenida por el usuario.")


if __name__ == "__main__":
    escuchar_whatsapp_continuo()
