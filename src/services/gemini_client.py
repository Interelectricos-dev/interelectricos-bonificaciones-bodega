import base64
import json
import time
import urllib.error
import urllib.request
from typing import Optional
from src.config import settings, get_logger

logger = get_logger("gemini_client")

SYSTEM_PROMPT = """Eres el motor de extracción de datos de la bodega de Intereléctricos Group SAS.
Tu tarea es analizar el mensaje de texto o nota de voz enviado por el jefe de bodega (Luis) y extraer UNO o MÚLTIPLES registros de facturas en formato JSON estricto.

NOMENCLATURA Y TIPOS DE FACTURA (MAPEO FONÉTICO OBLIGATORIO):
En Intereléctricos TODOS los comprobantes son facturas. Existen únicamente 3 tipos de factura autorizados:
1. "IC" (Factura de contado):
   - Mapea a "IC" si Luis pronuncia la sigla o si la IA la transcribe como:
     "IC", "ICE", "EC", "Ais", "I ce", "I-C", o si menciona explícitamente "factura de contado".
2. "DP" (Factura de tirilla blanca - contado):
   - Mapea a "DP" si Luis pronuncia la sigla o si la IA la transcribe como:
     "DP", "DePe", "Pepe", "BP", "TP", "Bete", "D-P", o si menciona "tirilla" o "tirilla blanca".
3. "IR" (Factura de remisión crédito):
   - Mapea a "IR" si Luis pronuncia la sigla o si la IA la transcribe como:
     "IR", "ER", "YR", "Ye-erre", "I-erre", "I-R", o si menciona "remisión" o "crédito".

REGLA CRÍTICA SOBRE LA PALABRA "FACTURA":
- La palabra genérica "factura" aplica a los 3 tipos (IC, DP, IR). NUNCA asumas que por decir "factura" se trata de "IC".
- Si en un registro se dice un número de factura pero NO se logra distinguir si es IC, DP o IR, asigna "tipo_factura": null.

REGLAS DE ENSAMBLADO NUMÉRICO (SIN RANGOS FIJOS, APLICA A CUALQUIER CONSECUTIVO):
Luis puede dictar los números de las facturas de diversas formas. Reconstruye el número exacto según estas pautas:
A. Dictado por bloques / pares de dos dígitos:
   Concatena exactamente cada par pronunciado. Ejemplos:
   - "diez cuarenta y nueve cincuenta y ocho" -> 10 + 49 + 58 = 104958.
   - "doce setenta y cuatro cero dos" -> 12 + 74 + 02 = 127402.
   - "veinte treinta y cinco cuarenta" -> 20 + 35 + 40 = 203540.
   NUNCA omitas el primer par ni reduzcas dígitos.
B. Dictado con dígitos repetidos o combinados:
   - "treinta y seis seis cero cero" -> 36 + 6 + 0 + 0 = 36600 (NUNCA reduzcas a 3600).
   - "cuarenta y ocho ocho cinco dos" -> 48 + 8 + 5 + 2 = 48852.
C. Dictado corrido / cantidad estándar:
   - "ciento cuatro mil novecientos cincuenta y ocho" -> 104958.
   - "treinta y seis mil seiscientos" -> 36600.
NUNCA inventes ceros ni recortes cifras que fueron expresamente pronunciadas.

AGRUPACIÓN POR COLABORADOR:
- Si Luis dice "Para Edward: ...", "Anota a Edward: ...", o menciona un auxiliar y a continuación lista varias facturas, ASIGNA ESE MISMO AUXILIAR A TODAS ESAS FACTURAS hasta que se mencione a otro auxiliar diferente. Luis no necesita repetir el nombre en cada comprobante.

AUXILIARES ACTIVOS DE BODEGA:
- "Edward", "Sneider", "Fabian", "Sergio", "Estebi".

PUNTOS:
- puntos_esfuerzo: entero del 1 al 5. Si omitió decir los puntos de esfuerzo, asigna 1 por defecto.
- puntos_error: entero del 0 al -3 (SIEMPRE negativo o 0). Si no menciona errores, asigna 0 por defecto.
  (Si dice "1 error" -> -1, "2 errores" -> -2, "3 errores" -> -3).

REGLAS DE SEGURIDAD CRÍTICAS (CERO INVENCIÓN DE DATOS):
- NUNCA inventes números ni nombres que no se hayan dicho en el audio o texto.
- Si en alguna factura particular falta el tipo de factura, el número o el auxiliar, pon null en ese campo específico.
- Si el mensaje NO es un reporte de despachos/facturas (ej. "hola", "ya voy", ruido vacío), devuelve "es_despacho": false y "despachos": [].

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


class GeminiClient:
    """Capa de integración y consumo con Gemini API (Google AI Studio)."""

    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None) -> None:
        self.api_key = (api_key or settings.GEMINI_API_KEY).strip()
        self.model = (model or settings.GEMINI_MODEL).strip()
        if not self.api_key or self.api_key == "PENDIENTE_PEGAR_AQUI":
            raise ValueError("GEMINI_API_KEY no está configurada en las variables de entorno.")

    def extraer_despachos_raw(
        self,
        texto: Optional[str] = None,
        audio_bytes: Optional[bytes] = None,
        mime_type: str = "audio/ogg",
    ) -> str:
        """
        Envía texto o audio a Gemini API con tolerancia a fallos y rotación de modelos.
        Retorna la respuesta cruda en JSON como string.
        """
        if not texto and not audio_bytes:
            raise ValueError("Se requiere al menos texto o audio_bytes para consultar Gemini.")

        parts = []
        if audio_bytes:
            b64_audio = base64.b64encode(audio_bytes).decode("ascii")
            clean_mime = mime_type.split(";")[0].strip()
            parts.append({"inline_data": {"mime_type": clean_mime, "data": b64_audio}})
            parts.append(
                {
                    "text": (
                        "Escucha esta nota de voz del jefe de bodega y extrae todos los despachos mencionados "
                        "en el arreglo JSON 'despachos'. Si falta algún dato en un despacho, pon null en ese campo."
                    )
                }
            )
        else:
            parts.append({"text": f"Mensaje del jefe de bodega: {texto}"})

        payload = {
            "system_instruction": {"parts": [{"text": SYSTEM_PROMPT}]},
            "contents": [{"parts": parts}],
            "generationConfig": {
                "temperature": 0.0,
                "responseMimeType": "application/json",
                "thinkingConfig": {"thinkingBudget": 0},
            },
        }

        modelos = [self.model, "gemini-3-flash-preview", "gemini-3.5-flash"]
        modelos_unicos = list(dict.fromkeys(modelos))
        ultimo_error: Optional[Exception] = None

        for mod in modelos_unicos:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{mod}:generateContent?key={self.api_key}"
            req = urllib.request.Request(
                url,
                data=json.dumps(payload).encode("utf-8"),
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            try:
                logger.info("Consultando Gemini API con modelo '%s'...", mod)
                with urllib.request.urlopen(req, timeout=25) as resp:
                    res_json = json.loads(resp.read().decode("utf-8"))
                raw_text = res_json["candidates"][0]["content"]["parts"][0]["text"]
                return raw_text
            except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError, OSError) as err:
                ultimo_error = err
                logger.warning("Fallo al consultar modelo '%s': %s. Reintentando...", mod, err)
                time.sleep(1.0)

        logger.error("Todos los intentos con Gemini API fallaron: %s", ultimo_error)
        raise RuntimeError(f"Error de conexión tras reintentos con Gemini API: {ultimo_error}")

