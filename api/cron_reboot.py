import json
import urllib.error
import urllib.request
from http.server import BaseHTTPRequestHandler

from src.config import get_logger, settings

logger = get_logger("cron_reboot")


class handler(BaseHTTPRequestHandler):
    """Controlador HTTP Serverless (Vercel) para tareas programadas de mantenimiento (Cron)."""

    def do_GET(self) -> None:
        try:
            host = settings.GREEN_HOST.rstrip("/")
            inst = settings.ID_INSTANCE.strip()
            tok = settings.API_TOKEN_INSTANCE.strip()

            if not inst or not tok:
                logger.error("Credenciales de Green API no configuradas para reboot.")
                self._responder_json(
                    500,
                    {"status": "error", "message": "Missing Green API credentials"},
                )
                return

            url = f"{host}/waInstance{inst}/reboot/{tok}"
            req = urllib.request.Request(url, method="GET")

            with urllib.request.urlopen(req, timeout=15) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                logger.info("Reinicio preventivo de Green API ejecutado con éxito: %s", data)
                self._responder_json(
                    200,
                    {
                        "status": "ok",
                        "service": "Green API Auto-Reboot Cron",
                        "response": data,
                    },
                )
        except Exception as exc:
            logger.error("Error durante el reinicio programado de Green API: %s", exc)
            self._responder_json(500, {"status": "error", "detail": str(exc)})

    def _responder_json(self, status_code: int, payload: dict) -> None:
        self.send_response(status_code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.end_headers()
        self.wfile.write(json.dumps(payload, ensure_ascii=False).encode("utf-8"))
