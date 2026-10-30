import json
import os
import urllib.request
from typing import Any, Dict, Optional, Tuple


class GreenAPIService:
    """Cliente ligero para Green API reutilizando la configuración de Intereléctricos."""

    def __init__(self) -> None:
        self.host = os.getenv("GREEN_HOST", "https://7107.api.greenapi.com").rstrip("/")
        self.id_instance = os.getenv("ID_INSTANCE", "").strip()
        self.api_token = os.getenv("API_TOKEN_INSTANCE", "").strip()

        if not self.id_instance or not self.api_token:
            raise RuntimeError(
                "Faltan ID_INSTANCE o API_TOKEN_INSTANCE en el archivo bot/.env"
            )

    def enviar_mensaje(self, chat_id: str, mensaje: str) -> Dict[str, Any]:
        """Envía un mensaje de confirmación al chat de WhatsApp."""
        url = f"{self.host}/waInstance{self.id_instance}/sendMessage/{self.api_token}"
        payload = json.dumps({"chatId": chat_id, "message": mensaje}).encode("utf-8")
        req = urllib.request.Request(
            url,
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=15) as resp:
            return json.loads(resp.read().decode("utf-8"))

    def descargar_archivo(self, download_url: str) -> Tuple[bytes, str]:
        """Descarga una nota de voz (.ogg) desde la URL temporal de Green API."""
        req = urllib.request.Request(download_url)
        with urllib.request.urlopen(req, timeout=20) as resp:
            mime_type = resp.headers.get("Content-Type", "audio/ogg")
            return resp.read(), mime_type

    def recibir_notificacion_cola(self, borrar_al_leer: bool = True) -> Optional[Dict[str, Any]]:
        """
        Extrae la siguiente notificación entrante de la cola de Green API (receiveNotification).
        Ideal para pruebas locales sin necesidad de exponer puertos ni configurar Webhook público.
        """
        url = f"{self.host}/waInstance{self.id_instance}/receiveNotification/{self.api_token}"
        req = urllib.request.Request(url, method="GET")
        with urllib.request.urlopen(req, timeout=15) as resp:
            raw = resp.read().decode("utf-8")
            if not raw or raw == "null":
                return None
            data = json.loads(raw)

        if borrar_al_leer and data and "receiptId" in data:
            receipt_id = data["receiptId"]
            del_url = f"{self.host}/waInstance{self.id_instance}/deleteNotification/{self.api_token}/{receipt_id}"
            del_req = urllib.request.Request(del_url, method="DELETE")
            try:
                urllib.request.urlopen(del_req, timeout=10).read()
            except Exception:
                pass

        return data.get("body") if data else None

    @staticmethod
    def extraer_contenido_webhook(body: Dict[str, Any]) -> Tuple[Optional[str], Optional[str], Optional[str]]:
        """
        Extrae (chat_id, texto, download_url_audio) de un payload de Green API.
        Soporta tanto mensajes entrantes ('incomingMessageReceived') como mensajes
        enviados desde el mismo teléfono en el chat propio ('outgoingMessageReceived').
        """
        if body.get("typeWebhook") not in ("incomingMessageReceived", "outgoingMessageReceived"):
            return None, None, None

        sender_data = body.get("senderData", {})
        chat_id = sender_data.get("chatId")
        msg_data = body.get("messageData", {})
        msg_type = msg_data.get("typeMessage")

        if msg_type == "textMessage":
            texto = msg_data.get("textMessageData", {}).get("textMessage")
            return chat_id, texto, None

        if msg_type == "extendedTextMessage":
            texto = msg_data.get("extendedTextMessageData", {}).get("text")
            return chat_id, texto, None

        if msg_type in ("audioMessage", "voiceMessage"):
            file_data = msg_data.get("fileMessageData", {})
            download_url = file_data.get("downloadUrl")
            return chat_id, None, download_url

        return chat_id, None, None


def formatear_mensaje_confirmacion(registro: Dict[str, Any], datos_json: Dict[str, Any]) -> str:
    """Genera el mensaje de respuesta para Luis en WhatsApp."""
    return (
        "✅ *¡Despacho registrado con éxito!*\n"
        f"📄 *Documento:* {registro['factura_label']}\n"
        f"👷 *Auxiliar:* {registro['nombre_oficial']} (ID: {registro['id_empleado']})\n"
        f"⚡ *Esfuerzo:* {datos_json['puntos_esfuerzo']} pts | "
        f"⚠️ *Errores:* {datos_json['puntos_error']}\n"
        f"🕒 *Hora:* {registro['fecha_hora']} (ID: `{registro['id_registro']}`)"
    )
