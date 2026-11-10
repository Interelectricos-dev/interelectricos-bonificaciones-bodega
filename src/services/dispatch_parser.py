import json
from typing import Any, Dict, List, Optional, Tuple

from src.config import get_logger

logger = get_logger("dispatch_parser")


class DispatchParser:
    """Capa de ingesta, lectura y estructuración de datos de entrada."""

    @staticmethod
    def parse_webhook_payload(body: Dict[str, Any]) -> Tuple[Optional[str], Optional[str], Optional[str], Optional[str]]:
        """
        Extrae datos limpios de un payload de webhook (Green API):
        Retorna (chat_id, texto, download_url_audio, id_mensaje).
        """
        tipo_webhook = body.get("typeWebhook")
        if tipo_webhook not in ("incomingMessageReceived", "outgoingMessageReceived"):
            return None, None, None, None

        sender_data = body.get("senderData", {})
        chat_id = sender_data.get("chatId")
        msg_data = body.get("messageData", {})
        msg_type = msg_data.get("typeMessage")
        msg_id = body.get("idMessage")

        if msg_type == "textMessage":
            texto = msg_data.get("textMessageData", {}).get("textMessage")
            return chat_id, texto, None, msg_id

        if msg_type == "extendedTextMessage":
            texto = msg_data.get("extendedTextMessageData", {}).get("text")
            return chat_id, texto, None, msg_id

        if msg_type in ("audioMessage", "voiceMessage"):
            download_url = msg_data.get("fileMessageData", {}).get("downloadUrl")
            return chat_id, None, download_url, msg_id

        return chat_id, None, None, msg_id

    @staticmethod
    def parse_ai_json_response(raw_text: str) -> List[Dict[str, Any]]:
        """
        Parsea el texto JSON devuelto por el modelo multimodal y extrae la lista de despachos.
        Lanza ValueError si el mensaje no corresponde a un despacho o si el JSON es inválido.
        """
        try:
            data = json.loads(raw_text.strip())
        except json.JSONDecodeError as exc:
            logger.error("Error al decodificar JSON de IA: %s | Contenido: %s", exc, raw_text)
            raise ValueError(f"Respuesta de IA con formato JSON inválido: {exc}")

        if isinstance(data, dict):
            if data.get("es_despacho") is False:
                raise ValueError("NO_ES_DESPACHO: El mensaje no describe despachos de bodega.")
            if "despachos" in data and isinstance(data["despachos"], list):
                despachos = data["despachos"]
            else:
                despachos = [data]
        elif isinstance(data, list):
            despachos = data
        else:
            raise ValueError("Formato de respuesta inesperado del extractor de datos.")

        if not despachos:
            raise ValueError("NO_ES_DESPACHO: No se detectaron despachos en el mensaje.")

        return despachos

