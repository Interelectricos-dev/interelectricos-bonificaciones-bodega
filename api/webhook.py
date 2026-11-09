import json
from http.server import BaseHTTPRequestHandler
from main import orquestar_procesamiento_despacho
from src.config import settings, get_logger
from src.services.dispatch_exporter import DispatchExporter
from src.services.dispatch_parser import DispatchParser
from src.services.green_api_client import GreenAPIClient

logger = get_logger("webhook_handler")


class handler(BaseHTTPRequestHandler):
    """Controlador HTTP Serverless (Vercel) para webhooks de Green API."""

    def do_GET(self) -> None:
        self._responder_json(
            200,
            {
                "status": "ok",
                "service": "Sistema de Liquidación y Auditoría de Bonificaciones - Intereléctricos",
            },
        )

    def do_POST(self) -> None:
        try:
            content_length = int(self.headers.get("Content-Length", 0))
            raw_body = self.rfile.read(content_length)
            body = json.loads(raw_body.decode("utf-8"))

            chat_id, texto, audio_url, _ = DispatchParser.parse_webhook_payload(body)

            if not chat_id or (not texto and not audio_url):
                self._responder_json(200, {"status": "ignored_non_target_event"})
                return

            if texto and texto.startswith(("✅", "⚠️", "🤖")):
                self._responder_json(200, {"status": "ignored_bot_echo"})
                return

            # Política Fail-Closed: Solo procesar chats explícitamente autorizados
            chats_autorizados = settings.get_authorized_chats()
            if not chats_autorizados or chat_id not in chats_autorizados:
                logger.warning("Mensaje recibido de chat no autorizado: %s. Descartado.", chat_id)
                self._responder_json(200, {"status": "ignored_unauthorized_chat"})
                return

            wa_client = GreenAPIClient()
            audio_bytes = None
            mime_type = "audio/ogg"

            if audio_url:
                audio_bytes, mime_type = wa_client.descargar_archivo(audio_url)

            try:
                resultado = orquestar_procesamiento_despacho(
                    texto=texto, audio_bytes=audio_bytes, mime_type=mime_type
                )
                wa_client.enviar_mensaje(chat_id, resultado["mensaje_whatsapp"])
                self._responder_json(
                    200,
                    {
                        "status": "processed",
                        "nuevos": len(resultado["nuevos"]),
                        "duplicados": len(resultado["duplicados"]),
                        "incompletos": len(resultado["incompletos"]),
                    },
                )
            except Exception as err_negocio:
                err_str = str(err_negocio)
                if "NO_ES_DESPACHO" in err_str:
                    logger.info("Mensaje conversacional ignorado: %s", err_str)
                    self._responder_json(200, {"status": "ignored_conversational"})
                    return

                logger.error("Error operativo procesando despacho: %s", err_negocio)
                msg_alerta = DispatchExporter.formatear_error_operativo(err_str)
                wa_client.enviar_mensaje(chat_id, msg_alerta)
                self._responder_json(200, {"status": "operational_error", "detail": err_str})

        except Exception as exc:
            logger.critical("Error crítico no controlado en webhook: %s", exc, exc_info=True)
            self._responder_json(500, {"status": "server_error", "detail": str(exc)})

    def _responder_json(self, status_code: int, payload: dict) -> None:
        self.send_response(status_code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.end_headers()
        self.wfile.write(json.dumps(payload, ensure_ascii=False).encode("utf-8"))

