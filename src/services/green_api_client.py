import json
import urllib.error
import urllib.request
from typing import Any, Dict, List, Optional, Tuple
from src.config import settings, get_logger

logger = get_logger("green_api_client")


class GreenAPIClient:
    """Capa de integración y comunicación HTTP con Green API (WhatsApp)."""

    def __init__(
        self,
        host: Optional[str] = None,
        id_instance: Optional[str] = None,
        api_token: Optional[str] = None,
    ) -> None:
        self.host = (host or settings.GREEN_HOST).rstrip("/")
        self.id_instance = (id_instance or settings.ID_INSTANCE).strip()
        self.api_token = (api_token or settings.API_TOKEN_INSTANCE).strip()

        if not self.id_instance or not self.api_token:
            logger.warning(
                "ID_INSTANCE o API_TOKEN_INSTANCE no configurados. Las llamadas de red a WhatsApp fallarán."
            )

    def enviar_mensaje(self, chat_id: str, mensaje: str) -> Dict[str, Any]:
        """Envía un mensaje de texto formateado al chat indicado de WhatsApp."""
        url = f"{self.host}/waInstance{self.id_instance}/sendMessage/{self.api_token}"
        payload = json.dumps({"chatId": chat_id, "message": mensaje}).encode("utf-8")
        req = urllib.request.Request(
            url,
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=15) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                logger.info("Mensaje enviado exitosamente a WhatsApp (%s)", chat_id)
                return data
        except Exception as exc:
            logger.error("Error enviando mensaje a WhatsApp (%s): %s", chat_id, exc)
            raise

    def descargar_archivo(self, download_url: str) -> Tuple[bytes, str]:
        """Descarga nota de voz (.ogg) desde el almacenamiento temporal de Green API."""
        req = urllib.request.Request(download_url)
        try:
            logger.info("Descargando archivo multimedia desde Green API...")
            with urllib.request.urlopen(req, timeout=20) as resp:
                mime_type = resp.headers.get("Content-Type", "audio/ogg")
                contenido = resp.read()
                logger.info("Archivo descargado (%d bytes, mime: %s)", len(contenido), mime_type)
                return contenido, mime_type
        except Exception as exc:
            logger.error("Error descargando archivo de audio desde Green API: %s", exc)
            raise

    def recibir_notificacion_cola(self, borrar_al_leer: bool = True) -> Optional[Dict[str, Any]]:
        """Extrae la siguiente notificación entrante de la cola (receiveNotification)."""
        url = f"{self.host}/waInstance{self.id_instance}/receiveNotification/{self.api_token}"
        req = urllib.request.Request(url, method="GET")
        try:
            with urllib.request.urlopen(req, timeout=15) as resp:
                raw = resp.read().decode("utf-8")
                if not raw or raw == "null":
                    return None
                data = json.loads(raw)
        except Exception as exc:
            logger.debug("Cola de notificaciones vacía o error leve: %s", exc)
            return None

        if borrar_al_leer and data and "receiptId" in data:
            receipt_id = data["receiptId"]
            del_url = f"{self.host}/waInstance{self.id_instance}/deleteNotification/{self.api_token}/{receipt_id}"
            del_req = urllib.request.Request(del_url, method="DELETE")
            try:
                urllib.request.urlopen(del_req, timeout=10).read()
            except Exception as del_err:
                logger.warning("No se pudo confirmar eliminación de receiptId %s: %s", receipt_id, del_err)

        return data.get("body") if data else None

    def obtener_ultimos_mensajes(self, minutos: int = 2) -> List[Dict[str, Any]]:
        """Consulta mensajes recientes (entrantes y salientes) del historial de la instancia."""
        mensajes: List[Dict[str, Any]] = []
        for endpoint in ("lastIncomingMessages", "lastOutgoingMessages"):
            url = f"{self.host}/waInstance{self.id_instance}/{endpoint}/{self.api_token}?minutes={minutos}"
            req = urllib.request.Request(url)
            try:
                with urllib.request.urlopen(req, timeout=10) as resp:
                    data = json.loads(resp.read().decode("utf-8"))
                    if isinstance(data, list):
                        mensajes.extend(data)
            except Exception as exc:
                logger.debug("Error consultando endpoint '%s': %s", endpoint, exc)
        return mensajes

