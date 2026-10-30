import base64
import json
import os
import re
import time
import urllib.error
import urllib.request
from typing import Any, Dict, List, Optional

SYSTEM_PROMPT = """Eres el motor de extracción de datos de la bodega de Intereléctricos Group SAS.
Tu única tarea es analizar el mensaje de texto o nota de voz enviado por el jefe de bodega (Luis) y extraer los datos del despacho en formato JSON estricto.

REGLA DE SEGURIDAD CRÍTICA (CERO INVENCIÓN DE DATOS):
- NUNCA inventes ni adivines datos que no se hayan dicho claramente en el mensaje o audio.
- Si el mensaje NO es un reporte de despacho (ej. "hola", "ok", ruido vacío), pon es_despacho en false.
- Si falta el tipo de factura, el número de factura o el nombre del empleado, devuelve null en ese campo.

Reglas de cada campo:
1. es_despacho: booleano (true si intenta reportar un documento/despacho, false si es una conversación ajena o ruido).
2. tipo_factura: Serie del documento. Solo puede ser "IC", "DP" o "IR" (en mayúsculas), o null si no se mencionó.
3. numero_factura: Número entero del documento (ej. 2021), o null si no se mencionó.
4. nombre_empleado: Nombre del auxiliar mencionado (ej. "Edward", "Sneider", "Fabian", "Sergio", "Estebi"), o null si no se mencionó.
5. puntos_esfuerzo: Número entero entre 1 y 5. Si sí es un despacho pero omitió decir los puntos, asigna 1 por defecto.
6. puntos_error: Número entero entre 0 y -3 (SIEMPRE negativo o 0).
   - Si NO menciona errores, asigna 0.
   - Si menciona "1 error", asigna -1. Si menciona "2 errores", asigna -2. Si menciona "3 errores", asigna -3.

Formato JSON obligatorio de respuesta:
{
  "es_despacho": true,
  "tipo_factura": "IC",
  "numero_factura": 2021,
  "nombre_empleado": "Edward",
  "puntos_esfuerzo": 2,
  "puntos_error": -1
}"""


def normalizar_resultado(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Seguro de validación: verifica que ningún campo obligatorio falte o esté fuera de rango
    antes de permitir que toque Google Sheets.
    """
    if data.get("es_despacho") is False:
        raise ValueError(
            "NO_ES_DESPACHO: El mensaje o audio no es un registro de despacho."
        )

    faltantes: List[str] = []

    tipo_raw = data.get("tipo_factura")
    tipo = str(tipo_raw).strip().upper() if tipo_raw is not None else ""
    if not tipo or tipo == "NULL":
        faltantes.append("Tipo de factura (IC, DP o IR)")
    elif tipo not in ("IC", "DP", "IR"):
        faltantes.append(f"Tipo de factura válido (se entendió '{tipo}', pero solo existe IC, DP o IR)")

    num_raw = data.get("numero_factura")
    numero: Optional[int] = None
    if num_raw is None or str(num_raw).strip().upper() in ("", "NULL", "NONE"):
        faltantes.append("Número de factura (ej. 2021)")
    else:
        try:
            numero = int(num_raw)
            if numero <= 0:
                faltantes.append("Número de factura positivo")
        except (ValueError, TypeError):
            faltantes.append(f"Número de factura numérico (se recibió '{num_raw}')")

    nombre_raw = data.get("nombre_empleado")
    nombre = str(nombre_raw).strip() if nombre_raw is not None else ""
    if not nombre or nombre.upper() in ("NULL", "NONE"):
        faltantes.append("Nombre del auxiliar (ej. Edward, Sneider, Fabian, Sergio, Estebi)")

    if faltantes:
        lista_str = "\n  • ".join(faltantes)
        raise ValueError(f"Faltan datos o no se escucharon con claridad:\n  • {lista_str}")

    try:
        esfuerzo = int(data.get("puntos_esfuerzo") if data.get("puntos_esfuerzo") is not None else 1)
    except (ValueError, TypeError):
        raise ValueError("Los puntos de esfuerzo deben ser un número del 1 al 5.")
    if esfuerzo < 1 or esfuerzo > 5:
        raise ValueError(f"Puntos de esfuerzo fuera de rango ({esfuerzo}). Solo se permite de 1 a 5.")

    try:
        error = int(data.get("puntos_error") if data.get("puntos_error") is not None else 0)
    except (ValueError, TypeError):
        raise ValueError("Los puntos de error deben ser un número entre 0 y 3.")
    if error > 0:
        error = -error
    if error < -3 or error > 0:
        raise ValueError(f"Puntos de error fuera de rango ({error}). Solo se permite 0, -1, -2 o -3.")

    return {
        "tipo_factura": tipo,
        "numero_factura": numero,
        "nombre_empleado": nombre,
        "puntos_esfuerzo": esfuerzo,
        "puntos_error": error,
    }


def parse_con_gemini(
    texto: Optional[str] = None,
    audio_bytes: Optional[bytes] = None,
    mime_type: str = "audio/ogg",
) -> Dict[str, Any]:
    """
    Llama a la API de Gemini en Google AI Studio con reintento automático y fallback
    entre modelos rápidos para evitar fallos por picos de carga (HTTP 503).
    """
    api_key = os.getenv("GEMINI_API_KEY", "").strip()
    if not api_key or api_key == "PENDIENTE_PEGAR_AQUI":
        raise RuntimeError(
            "Falta configurar GEMINI_API_KEY en el archivo bot/.env"
        )

    modelo_principal = os.getenv("GEMINI_MODEL", "gemini-3.5-flash").strip()
    modelos_a_probar = [modelo_principal, "gemini-3-flash-preview", "gemini-3.5-flash"]

    parts = []
    if audio_bytes:
        b64_audio = base64.b64encode(audio_bytes).decode("ascii")
        parts.append(
            {
                "inline_data": {
                    "mime_type": mime_type.split(";")[0].strip(),
                    "data": b64_audio,
                }
            }
        )
        parts.append(
            {
                "text": "Escucha esta nota de voz del jefe de bodega y extrae el JSON del despacho. Si algún dato no se dice claramente, pon null en ese campo."
            }
        )
    elif texto:
        parts.append({"text": f"Mensaje del jefe de bodega: {texto}"})
    else:
        raise ValueError("Se requiere texto o audio_bytes para procesar.")

    payload = {
        "system_instruction": {"parts": [{"text": SYSTEM_PROMPT}]},
        "contents": [{"parts": parts}],
        "generationConfig": {
            "temperature": 0.0,
            "responseMimeType": "application/json",
            "thinkingConfig": {"thinkingBudget": 0},
        },
    }

    ultimo_error = None
    for mod in modelos_a_probar:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{mod}:generateContent?key={api_key}"
        req = urllib.request.Request(
            url,
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=25) as resp:
                result = json.loads(resp.read().decode("utf-8"))
            raw_text = result["candidates"][0]["content"]["parts"][0]["text"]
            raw_json = json.loads(raw_text)
            return normalizar_resultado(raw_json)
        except ValueError:
            # Error de validación de negocio (dato faltante o fuera de rango): no reintentar
            raise
        except Exception as err:
            ultimo_error = err
            time.sleep(1)

    raise RuntimeError(f"Error tras reintentos con Gemini API: {ultimo_error}")


def parse_con_regex(texto: str) -> Dict[str, Any]:
    """
    Parser local de respaldo (sin costo de IA) para formatos estándar.
    """
    patron = re.compile(
        r"^\s*(IC|DP|IR)[-\s]*(\d+)\s+([A-Za-zÁÉÍÓÚáéíóúÑñ]+)"
        r"(?:\s+(\d+)\s*(?:puntos?|pts?))?"
        r"(?:\s+(\d+|-?\d+)\s*(?:error(?:es)?|err))?\s*$",
        re.IGNORECASE,
    )
    m = patron.match(texto.strip())
    if not m:
        raise ValueError(
            f"El texto '{texto}' no coincide con el patrón estándar. Configura GEMINI_API_KEY para lenguaje libre."
        )

    tipo, num, empleado, pts_esfuerzo, pts_error = m.groups()
    esfuerzo = int(pts_esfuerzo) if pts_esfuerzo is not None else 1
    error = -abs(int(pts_error)) if pts_error is not None else 0

    return normalizar_resultado(
        {
            "es_despacho": True,
            "tipo_factura": tipo.upper(),
            "numero_factura": int(num),
            "nombre_empleado": empleado,
            "puntos_esfuerzo": esfuerzo,
            "puntos_error": error,
        }
    )
