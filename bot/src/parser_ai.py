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

CONTEXTO OPERATIVO Y NOMENCLATURA DE INTERELÉCTRICOS:
1. "IC": Facturas de venta.
   - Formato habitual: 6 dígitos en la serie 104xxx o 105xxx (ej. 104958, 104996, 105000).
   - Variaciones fonéticas: Si Luis dice "ICE", "EC" o "I-C", mapea siempre a "IC".
   - Armado de números en bloques: Si Luis dice "diez cuarenta y nueve cincuenta y ocho", debes concatenar: 10 + 49 + 58 = 104958. NUNCA omitas el "diez" inicial ni lo reduzcas a 4 dígitos.
2. "DP": Despachos de bodega / traslados.
   - Formato habitual: 5 dígitos en la serie 35xxx o 36xxx (ej. 36567, 36600, 36625).
   - Armado de dígitos repetidos: Si Luis dice "treinta y seis seis cero cero", debes extraer 36600. NUNCA reduzcas los dos seis a uno solo (no es 3600, es 36600). Si dice "treinta y seis seiscientos", es 36600.
3. "IR": Remisiones / Devoluciones.
   - Formato habitual: 5 dígitos en la serie 47xxx o 48xxx (ej. 48494, 48515, 48530).
   - Variaciones fonéticas: Si Luis pronuncia "ER", "YR" o "I-R", mapea siempre a "IR".

AGRUPACIÓN POR COLABORADOR:
- Si Luis dice "Para Edward: ...", "Anota a Edward: ...", o menciona un auxiliar y a continuación lista varios comprobantes, ASIGNA ESE MISMO AUXILIAR A TODOS ESOS DESPACHOS hasta que se mencione a otro auxiliar diferente. Luis no necesita repetir el nombre en cada factura.

AUXILIARES ACTIVOS DE BODEGA:
- "Edward", "Sneider", "Fabian", "Sergio", "Estebi".

PUNTOS:
- puntos_esfuerzo: entero del 1 al 5. Si omitió decir los puntos de esfuerzo, asigna 1 por defecto.
- puntos_error: entero del 0 al -3 (SIEMPRE negativo o 0). Si no menciona errores, asigna 0 por defecto.
  (Si dice "1 error" -> -1, "2 errores" -> -2, "3 errores" -> -3).

REGLAS DE SEGURIDAD CRÍTICAS (CERO INVENCIÓN DE DATOS):
- NUNCA inventes números ni nombres que no se hayan dicho en el audio o texto.
- Si en algún despacho particular falta el tipo de factura, el número o el auxiliar, pon null en ese campo específico.
- Si el mensaje NO es un reporte de despacho (ej. "hola", "ya voy", ruido vacío), devuelve "es_despacho": false y "despachos": [].

Formato JSON obligatorio de respuesta:
{
  "es_despacho": true,
  "despachos": [
    {
      "tipo_factura": "IC",
      "numero_factura": 104958,
      "nombre_empleado": "Edward",
      "puntos_esfuerzo": 3,
      "puntos_error": 0
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
        faltantes.append("tipo de factura (IC, DP o IR)")
    elif tipo not in ("IC", "DP", "IR"):
        faltantes.append(
            f"tipo de factura válido (se entendió '{tipo}', pero solo existe IC, DP o IR)"
        )

    num_raw = item.get("numero_factura")
    numero: Optional[int] = None
    if num_raw is None or str(num_raw).strip().upper() in ("", "NULL", "NONE"):
        faltantes.append("número de factura")
    else:
        try:
            numero = int(num_raw)
            if numero <= 0:
                faltantes.append("número de factura positivo")
        except (ValueError, TypeError):
            faltantes.append(f"número de factura numérico (se recibió '{num_raw}')")

    nombre_raw = item.get("nombre_empleado")
    nombre = str(nombre_raw).strip() if nombre_raw is not None else ""
    if not nombre or nombre.upper() in ("NULL", "NONE"):
        faltantes.append(
            "nombre del auxiliar (Edward, Sneider, Fabian, Sergio o Estebi)"
        )

    if faltantes:
        lista_str = ", ".join(faltantes)
        raise ValueError(f"{prefijo}falta {lista_str}.")

    try:
        esfuerzo = int(
            item.get("puntos_esfuerzo")
            if item.get("puntos_esfuerzo") is not None
            else 1
        )
    except (ValueError, TypeError):
        raise ValueError(f"{prefijo}los puntos de esfuerzo deben ser un número del 1 al 5.")
    if esfuerzo < 1 or esfuerzo > 5:
        raise ValueError(
            f"{prefijo}puntos de esfuerzo fuera de rango ({esfuerzo}). Solo se permite de 1 a 5."
        )

    try:
        error = int(
            item.get("puntos_error") if item.get("puntos_error") is not None else 0
        )
    except (ValueError, TypeError):
        raise ValueError(f"{prefijo}los puntos de error deben ser entre 0 y 3.")
    if error > 0:
        error = -error
    if error < -3 or error > 0:
        raise ValueError(
            f"{prefijo}puntos de error fuera de rango ({error}). Solo se permite 0, -1, -2 o -3."
        )

    return {
        "tipo_factura": tipo,
        "numero_factura": numero,
        "nombre_empleado": nombre,
        "puntos_esfuerzo": esfuerzo,
        "puntos_error": error,
    }


def normalizar_lote_resultado(data: Any) -> Dict[str, Any]:
    """
    Seguro de validación tolerante a fallos parciales.
    Separa los despachos en:
    - 'validos': despachos con todos los campos correctos, listos para guardar.
    - 'incompletos': despachos a los que les faltó algún dato crítico (factura, colaborador),
      conservando la información disponible para notificar a Luis con precisión quirúrgica
      y que solo tenga que reenviar los omitidos.
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

    validos: List[Dict[str, Any]] = []
    incompletos: List[Dict[str, Any]] = []

    for idx, item in enumerate(lista_cruda, start=1):
        try:
            despacho_limpio = normalizar_un_despacho(
                item, indice=idx if len(lista_cruda) > 1 else 0
            )
            validos.append(despacho_limpio)
        except ValueError as e:
            tipo = item.get("tipo_factura")
            num = item.get("numero_factura")
            emp = item.get("nombre_empleado")
            motivo = str(e)
            if ":" in motivo:
                motivo = motivo.split(":", 1)[1].strip()

            incompletos.append(
                {
                    "indice": idx,
                    "tipo_factura": str(tipo).strip().upper() if tipo and str(tipo).upper() != "NULL" else None,
                    "numero_factura": num if num and str(num).upper() not in ("NULL", "NONE") else None,
                    "nombre_empleado": str(emp).strip() if emp and str(emp).upper() != "NULL" else None,
                    "motivo": motivo,
                }
            )

    return {"validos": validos, "incompletos": incompletos}


def parse_con_gemini(
    texto: Optional[str] = None,
    audio_bytes: Optional[bytes] = None,
    mime_type: str = "audio/ogg",
) -> Dict[str, Any]:
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
