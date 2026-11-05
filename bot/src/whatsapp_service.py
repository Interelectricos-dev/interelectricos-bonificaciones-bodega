import json
import os
import urllib.request
from typing import Any, Dict, List, Optional, Tuple


class GreenAPIService:
    """Cliente ligero para Green API reutilizando la configuración de Interelectricos."""

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
            del_url = f"{self.host}/waInstance{self.id_instance}/deleteNotification/{self.id_instance if False else self.api_token}/{receipt_id}"
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


def describir_incompleto(inc: Dict[str, Any]) -> str:
    """Construye una descripción amigable del despacho omitido por datos faltantes."""
    tipo = inc.get("tipo_factura")
    num = inc.get("numero_factura")
    emp = inc.get("nombre_empleado")
    motivo = inc.get("motivo", "Datos incompletos")

    if tipo and num and not emp:
        return f"Factura *{tipo}-{num}*: falta el nombre del colaborador"
    if emp and (not num or not tipo):
        return f"Colaborador *{emp}*: falta el número o serie de factura"
    if tipo and num and emp:
        return f"Factura *{tipo}-{num}* ({emp}): {motivo}"
    return f"Despacho #{inc.get('indice', '?')}: {motivo}"


def formatear_mensaje_confirmacion(
    nuevos: List[Dict[str, Any]],
    duplicados: Optional[List[Dict[str, Any]]] = None,
    incompletos: Optional[List[Dict[str, Any]]] = None,
) -> str:
    """
    Genera el mensaje de respuesta para Luis en WhatsApp.
    Maneja despachos nuevos registrados, omitidos por duplicidad y omitidos por datos incompletos.
    """
    duplicados = duplicados or []
    incompletos = incompletos or []
    partes: List[str] = []

    # Caso A: No hay despachos nuevos insertados
    if not nuevos:
        if duplicados and not incompletos:
            partes.append("⚠️ *Aviso de duplicidad:*")
            partes.append(
                "Los siguientes despachos ya estaban registrados previamente para sus auxiliares:"
            )
            for d in duplicados:
                partes.append(f"• *{d['nombre_oficial']}*: {d['factura_label']}")
            return "\n".join(partes)

        if incompletos and not duplicados:
            partes.append("⚠️ *No se pudo registrar ningún despacho por datos incompletos:*")
            for inc in incompletos:
                partes.append(f"• {describir_incompleto(inc)}")
            partes.append("\n💡 *Por favor reenvía el audio indicando los datos faltantes.*")
            partes.append("👉 *Ejemplo:* `IC104958 Edward 3 puntos`")
            return "\n".join(partes)

        if incompletos and duplicados:
            partes.append("⚠️ *Ningún despacho nuevo registrado:*")
            partes.append("\n*Omitidos por duplicidad:*")
            for d in duplicados:
                partes.append(f"• *{d['nombre_oficial']}*: {d['factura_label']}")
            partes.append("\n*Omitidos por datos incompletos:*")
            for inc in incompletos:
                partes.append(f"• {describir_incompleto(inc)}")
            partes.append("\n💡 *Por favor reenvía únicamente los despachos con datos incompletos.*")
            return "\n".join(partes)

        return "ℹ️ *No se procesaron despachos.*"

    # Caso B: 1 despacho nuevo
    if len(nuevos) == 1:
        r = nuevos[0]
        partes.append(
            "✅ *¡Despacho registrado con éxito!*\n"
            f"📄 *Documento:* {r['factura_label']}\n"
            f"👷 *Auxiliar:* {r['nombre_oficial']} (ID: {r['id_empleado']})\n"
            f"⚡ *Esfuerzo:* {r['puntos_esfuerzo']} pts | "
            f"⚠️ *Errores:* {r['puntos_error']}\n"
            f"🕒 *Hora:* {r['fecha_hora']} (ID: `{r['id_registro']}`)"
        )
    # Caso C: Múltiples despachos nuevos
    elif len(nuevos) > 1:
        partes.append(f"✅ *¡{len(nuevos)} despachos registrados en bloque!*")
        for idx, r in enumerate(nuevos, start=1):
            partes.append(
                f"{idx}. *{r['factura_label']}* — {r['nombre_oficial']} "
                f"({r['puntos_esfuerzo']} pts | {r['puntos_error']} err)"
            )
        partes.append(f"🕒 *Hora:* {nuevos[0]['fecha_hora']}")

    # Avisos adicionales en lotes mixtos:
    if duplicados:
        partes.append(
            "\n⚠️ *Omitidos por duplicidad (ya registrados previamente):*"
        )
        for d in duplicados:
            partes.append(f"• *{d['nombre_oficial']}*: {d['factura_label']}")

    if incompletos:
        partes.append(
            "\n⚠️ *Omitidos por datos incompletos (requieren reenvío):*"
        )
        for inc in incompletos:
            partes.append(f"• {describir_incompleto(inc)}")
        partes.append(
            f"\n💡 *Los {len(nuevos)} despachos válidos ya quedaron guardados.* Por favor reenvía únicamente los omitidos."
        )

    return "\n".join(partes)
