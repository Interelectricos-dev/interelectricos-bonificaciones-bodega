import json
import os
import sys
from http.server import BaseHTTPRequestHandler
from pathlib import Path

# Asegurar que `src` sea importable en entorno Serverless de Vercel
BOT_DIR = Path(__file__).resolve().parent.parent
if str(BOT_DIR) not in sys.path:
    sys.path.insert(0, str(BOT_DIR))

from src.parser_ai import parse_con_gemini
from src.sheets_service import guardar_en_google_sheets
from src.whatsapp_service import GreenAPIService, formatear_mensaje_confirmacion


class handler(BaseHTTPRequestHandler):
    """
    Endpoint Serverless en Vercel (/api/webhook) que recibe los Webhooks
    entrantes de Green API cuando Luis envía 1 o múltiples despachos por texto o voz.
    """

    def do_GET(self) -> None:
        self.send_response(200)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.end_headers()
        self.wfile.write(
            json.dumps(
                {
                    "status": "ok",
                    "service": "Bot WhatsApp Bonificaciones Bodega - Intereléctricos",
                },
                ensure_ascii=False,
            ).encode("utf-8")
        )

    def do_POST(self) -> None:
        try:
            content_length = int(self.headers.get("Content-Length", 0))
            raw_body = self.rfile.read(content_length)
            body = json.loads(raw_body.decode("utf-8"))

            wa = GreenAPIService()
            chat_id, texto, audio_url = wa.extraer_contenido_webhook(body)

            # Ignorar eventos de estado o mensajes que no sean texto/audio entrante
            if not chat_id or (not texto and not audio_url):
                self._responder_json(200, {"status": "ignored"})
                return

            # Ignorar los mensajes de confirmación generados por el propio bot
            if texto and texto.startswith(("✅", "⚠️")):
                self._responder_json(200, {"status": "ignored_bot_reply"})
                return

            # SEGURO DE PRIVACIDAD: Solo procesar mensajes del número autorizado en CHAT_ID_PRUEBA
            # Cualquier otro chat normal del celular se ignora por completo sin responder ni gastar cuota.
            chat_autorizado = os.getenv("CHAT_ID_PRUEBA", "").strip()
            if chat_autorizado:
                lista_chats = [c.strip() for c in chat_autorizado.split(",") if c.strip()]
                if chat_id not in lista_chats:
                    self._responder_json(200, {"status": "ignored_other_chat"})
                    return

            try:
                if audio_url:
                    audio_bytes, mime_type = wa.descargar_archivo(audio_url)
                    lote_despachos = parse_con_gemini(
                        audio_bytes=audio_bytes, mime_type=mime_type
                    )
                else:
                    lote_despachos = parse_con_gemini(texto=texto)

                registros = guardar_en_google_sheets(lote_despachos)
                confirmacion = formatear_mensaje_confirmacion(registros)
                wa.enviar_mensaje(chat_id, confirmacion)

                self._responder_json(
                    200,
                    {
                        "status": "registered",
                        "count": len(registros),
                        "rows": [r["fila_sheets"] for r in registros],
                    },
                )
            except Exception as err_negocio:
                msg_err = str(err_negocio)
                # Si fue una conversación normal ("hola", etc.), ignorar en silencio
                if "NO_ES_DESPACHO" in msg_err:
                    self._responder_json(200, {"status": "ignored_non_dispatch"})
                    return

                # Si sí intentaba registrar despachos pero faltó un dato, avisar por WhatsApp
                wa.enviar_mensaje(
                    chat_id,
                    f"⚠️ *No se pudo registrar en Google Sheets:*\n{msg_err}\n\n"
                    "💡 *Ejemplo individual:* `IC2021 Edward 2 puntos 1 error`\n"
                    "💡 *Ejemplo por bloque:* `IC2021 Edward 2 puntos, DP3040 Sneider 3 puntos`",
                )
                self._responder_json(200, {"status": "validation_error", "detail": msg_err})

        except Exception as exc:
            self._responder_json(500, {"status": "error", "detail": str(exc)})

    def _responder_json(self, status_code: int, payload: dict) -> None:
        self.send_response(status_code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.end_headers()
        self.wfile.write(json.dumps(payload, ensure_ascii=False).encode("utf-8"))
