import base64
import json
import os
import re
import time
import urllib.error
import urllib.request
from typing import Any, Dict, List, Optional

SYSTEM_PROMPT = """Eres el motor de extracción de datos de la bodega de Intereléctricos Group SAS.
Tu tarea es analizar el mensaje de texto o nota de voz enviado por el jefe de bodega (Luis) y extraer UNO o MÚLTIPLES despachos en formato JSON estricto.

REGLAS DE SEGURIDAD CRÍTICAS (CERO INVENCIÓN DE DATOS):
- NUNCA inventes ni adivines números de factura o nombres que no se hayan dicho en el mensaje o audio.
- Si el mensaje NO es un reporte de despacho (ej. "hola", "ya voy", ruido vacío), devuelve "es_despacho": false y "despachos": [].
- Si el usuario menciona varios despachos para un mismo empleado (ej. "Para Edward: IC 2021 2 puntos y DP 3050 1 punto"), asigna ese mismo empleado a cada uno de esos despachos.
- Si en algún despacho falta el tipo de factura, el número de factura o el nombre del empleado, pon null en ese campo específico.

Reglas de cada objeto dentro de "despachos":
1. tipo_factura: Serie del documento. Solo puede ser "IC", "DP" o "IR" (en mayúsculas), o null si no se mencionó.
2. numero_factura: Número entero del documento (ej. 2021), o null si no se mencionó.
3. nombre_empleado: Nombre del auxiliar mencionado (ej. "Edward", "Sneider", "Fabian", "Sergio", "Estebi"), o null si no se mencionó.
4. puntos_esfuerzo: Número entero entre 1 y 5. Si omitió decir los puntos de esfuerzo, asigna 1 por defecto.
5. puntos_error: Número entero entre 0 y -3 (SIEMPRE negativo o 0).
   - Si NO menciona errores para ese despacho, asigna 0.
   - Si menciona "1 error", asigna -1. Si menciona "2 errores", asigna -2. Si menciona "3 errores", asigna -3.

Formato JSON obligatorio de respuesta:
{
  "es_despacho": true,
  "despachos": [
    {
      "tipo_factura": "IC",
      "numero_factura": 2021,
      "nombre_empleado": "Edward",
      "puntos_esfuerzo": 2,
      "puntos_error": -1
    }
  ]
}"""


def normalizar_un_despacho(item: Dict[str, Any], indice: int = 1) -> Dict[str, Any]:
    """Valida un despacho individual dentro del lote."""
    prefijo = f"Despacho #{indice}: " if indice > 0 else ""
    faltantes: List[str] = []

    tipo_raw = item.get("tipo_factura")
    tipo = str(tipo_raw).strip().upper() if tipo_raw is not None else ""
    if not tipo or tipo == "NULL":
        faltantes.append("Tipo de factura (IC, DP o IR)")
    elif tipo not in ("IC", "DP", "IR"):
        faltantes.append(
            f"Tipo de factura válido (se entendió '{tipo}', pero solo existe IC, DP o IR)"
        )

    num_raw = item.get("numero_factura")
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

    nombre_raw = item.get("nombre_empleado")
    nombre = str(nombre_raw).strip() if nombre_raw is not None else ""
    if not nombre or nombre.upper() in ("NULL", "NONE"):
        faltantes.append(
            "Nombre del auxiliar (Edward, Sneider, Fabian, Sergio o Estebi)"
        )

    if faltantes:
        lista_str = ", ".join(faltantes)
        raise ValueError(f"{prefijo}Falta {lista_str}.")

    try:
        esfuerzo = int(
            item.get("puntos_esfuerzo")
            if item.get("puntos_esfuerzo") is not None
            else 1
        )
    except (ValueError, TypeError):
        raise ValueError(f"{prefijo}Los puntos de esfuerzo deben ser un número del 1 al 5.")
    if esfuerzo < 1 or esfuerzo > 5:
        raise ValueError(
            f"{prefijo}Puntos de esfuerzo fuera de rango ({esfuerzo}). Solo se permite de 1 a 5."
        )

    try:
        error = int(
            item.get("puntos_error") if item.get("puntos_error") is not None else 0
        )
    except (ValueError, TypeError):
        raise ValueError(f"{prefijo}Los puntos de error deben ser entre 0 y 3.")
    if error > 0:
        error = -error
    if error < -3 or error > 0:
        raise ValueError(
            f"{prefijo}Puntos de error fuera de rango ({error}). Solo se permite 0, -1, -2 o -3."
        )

    return {
        "tipo_factura": tipo,
        "numero_factura": numero,
        "nombre_empleado": nombre,
        "puntos_esfuerzo": esfuerzo,
        "puntos_error": error,
    }


def normalizar_lote_resultado(data: Any) -> List[Dict[str, Any]]:
    """
    Seguro de validación para 1 o múltiples despachos.
    Si algún despacho del bloque tiene datos incompletos, detiene el guardado
    e informa exactamente cuál falló.
    """
    if isinstance(data, dict):
        if data.get("es_despacho") is False:
            raise ValueError(
                "NO_ES_DESPACHO: El mensaje o audio no es un registro de despacho."
            )
        if "despachos" in data and isinstance(data["despachos"], list):
            lista_cruda = data["despachos"]
        else:
            lista_cruda = [data]
    elif isinstance(data, list):
        lista_cruda = data
    else:
        raise ValueError("Formato de respuesta inesperado del analizador.")

    if not lista_cruda:
        raise ValueError(
            "NO_ES_DESPACHO: No se detectaron despachos en el mensaje."
        )

    errores: List[str] = []
    despachos_limpios: List[Dict[str, Any]] = []

    for idx, item in enumerate(lista_cruda, start=1):
        try:
            despachos_limpios.append(
                normalizar_un_despacho(item, indice=idx if len(lista_cruda) > 1 else 0)
            )
        except ValueError as e:
            errores.append(str(e))

    if errores:
        raise ValueError("\n• ".join([""] + errores).lstrip())

    return despachos_limpios


def parse_con_gemini(
    texto: Optional[str] = None,
    audio_bytes: Optional[bytes] = None,
    mime_type: str = "audio/ogg",
) -> List[Dict[str, Any]]:
    """
    Llama a la API de Gemini en Google AI Studio y devuelve una lista de 1 o N despachos
    validados a partir de un mensaje de texto o nota de voz (.ogg).
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
                "text": (
                    "Escucha esta nota de voz del jefe de bodega y extrae todos los despachos mencionados "
                    "en el arreglo JSON 'despachos'. Si falta algún dato en un despacho, pon null en ese campo."
                )
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
            return normalizar_lote_resultado(raw_json)
        except ValueError:
            raise
        except Exception as err:
            ultimo_error = err
            time.sleep(1)

    raise RuntimeError(f"Error tras reintentos con Gemini API: {ultimo_error}")
