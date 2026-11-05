import json
import os
import sys
import time
from pathlib import Path

# Permitir importar desde bot/src
BOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BOT_DIR))

from src.parser_ai import parse_con_gemini
from src.sheets_service import guardar_en_google_sheets
from src.whatsapp_service import GreenAPIService, formatear_mensaje_confirmacion


def cargar_env(env_path: Path) -> None:
    """Carga variables del archivo .env."""
    if env_path.exists():
        for line in env_path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                os.environ[k.strip()] = v.strip()


def escuchar_whatsapp_continuo() -> None:
    """
    Escucha de forma continua mensajes entrantes y notas de voz de WhatsApp.
    Soporta recepción por cola de Green API y sondeo directo para pruebas personales ("Mensajes a ti mismo").
    Para detenerlo: presiona Ctrl + C en la terminal.
    """
    wa = GreenAPIService()

    print("\n" + "=" * 70, flush=True)
    print("🎧 BOT ESCUCHANDO WHATSAPP EN VIVO (Presiona Ctrl + C para salir)", flush=True)
    print("📱 Soporta 1 despacho suelto o BLOQUES de varios despachos en 1 audio/texto", flush=True)
    print("   • Individual: 'IC 2021 Edward 2 puntos 1 error'", flush=True)
    print("   • En bloque:  'IC 2021 Edward 2 puntos, DP 3040 Sneider 3 puntos'", flush=True)
    print("=" * 70, flush=True)

    # Inicializar registro de mensajes ya procesados para no duplicar historial
    procesados = set()
    try:
        historial_inicial = wa.obtener_ultimos_mensajes(minutos=15)
        for m in historial_inicial:
            mid = m.get("idMessage")
            if mid:
                procesados.add(mid)
    except Exception:
        pass

    chat_autorizado = os.getenv("CHAT_ID_PRUEBA", "").strip()
    lista_chats = [c.strip() for c in chat_autorizado.split(",") if c.strip()]

    try:
        while True:
            mensajes_a_procesar = []

            # 1. Intentar por cola normal de Green API
            try:
                body = wa.recibir_notificacion_cola(borrar_al_leer=True)
                if body:
                    cid, txt, aurl = wa.extraer_contenido_webhook(body)
                    if cid:
                        mensajes_a_procesar.append(("queue", cid, txt, aurl))
            except Exception:
                pass

            # 2. Sondeo directo de historial reciente (cubre chats propios "Mensaje a ti mismo")
            try:
                recientes = wa.obtener_ultimos_mensajes(minutos=2)
                for item in recientes:
                    mid = item.get("idMessage")
                    if not mid or mid in procesados:
                        continue
                    if item.get("sendByApi", False):
                        procesados.add(mid)
                        continue

                    cid = item.get("chatId")
                    txt = item.get("textMessage")
                    aurl = item.get("downloadUrl") if item.get("typeMessage") in ("audioMessage", "voiceMessage") else None

                    if cid and (txt or aurl):
                        procesados.add(mid)
                        mensajes_a_procesar.append((mid, cid, txt, aurl))
            except Exception:
                pass

            if not mensajes_a_procesar:
                time.sleep(1.5)
                continue

            for item_msg in mensajes_a_procesar:
                _, chat_id, texto, audio_url = item_msg

                # SEGURO DE PRIVACIDAD ESTRICTO: Solo escuchar chats autorizados
                if not lista_chats or chat_id not in lista_chats:
                    continue

                # Ignorar mensajes de confirmación generados por el bot
                if texto and texto.startswith(("✅", "⚠️", "🤖")):
                    continue

                print("\n" + "-" * 65, flush=True)
                print(f"📥 ¡Nuevo mensaje recibido del chat {chat_id}!", flush=True)
                try:
                    if audio_url:
                        print("🎙️ Tipo: NOTA DE VOZ -> Descargando audio desde Green API...", flush=True)
                        audio_bytes, mime_type = wa.descargar_archivo(audio_url)
                        print(f"🤖 Analizando audio ({len(audio_bytes)} bytes) con Gemini API...", flush=True)
                        resultado_parse = parse_con_gemini(audio_bytes=audio_bytes, mime_type=mime_type)
                    else:
                        print(f"💬 Tipo: TEXTO -> '{texto}'", flush=True)
                        print("🤖 Analizando texto con Gemini API...", flush=True)
                        resultado_parse = parse_con_gemini(texto=texto)

                    despachos_validos = resultado_parse.get("validos", [])
                    despachos_incompletos = resultado_parse.get("incompletos", [])

                    print(f"\n1️⃣ DESPACHOS VÁLIDOS ({len(despachos_validos)}):", flush=True)
                    print(json.dumps(despachos_validos, indent=2, ensure_ascii=False), flush=True)
                    if despachos_incompletos:
                        print(f"⚠️ DESPACHOS INCOMPLETOS ({len(despachos_incompletos)}):", flush=True)
                        print(json.dumps(despachos_incompletos, indent=2, ensure_ascii=False), flush=True)

                    nuevos = []
                    duplicados = []
                    if despachos_validos:
                        print("\n2️⃣ GUARDANDO EN GOOGLE SHEETS (REGISTRO_DIARIO)...", flush=True)
                        resultado = guardar_en_google_sheets(despachos_validos)
                        nuevos = resultado["nuevos"]
                        duplicados = resultado["duplicados"]
                        despachos_incompletos.extend(resultado.get("incompletos", []))
                        for r in nuevos:
                            print("   ✅ Fila insertada:", r["fila_sheets"], flush=True)
                        for d in duplicados:
                            print("   ⚠️ Omitido por duplicidad:", d["fila_sheets"], flush=True)

                    confirmacion = formatear_mensaje_confirmacion(nuevos, duplicados, incompletos=despachos_incompletos)
                    print("\n3️⃣ ENVIANDO CONFIRMACIÓN A WHATSAPP...", flush=True)
                    wa.enviar_mensaje(chat_id, confirmacion)
                    print("   ✅ ¡Confirmación enviada! Esperando el siguiente mensaje...", flush=True)

                except Exception as err:
                    msg_err = str(err)
                    if "NO_ES_DESPACHO" in msg_err:
                        print("ℹ️ Mensaje conversacional ignorado (no es un despacho).", flush=True)
                        continue
                    print(f"❌ Error validando despacho: {msg_err}", flush=True)
                    try:
                        wa.enviar_mensaje(
                            chat_id,
                            f"⚠️ *No se pudo registrar en Google Sheets:*\n{msg_err}\n\n"
                            "💡 *Ejemplo individual:* `IC104958 Edward 3 puntos`\n"
                            "💡 *Ejemplo por bloque:* `Para Edward: IC 104958 3 puntos, DP 36600 2 puntos`",
                        )
                    except Exception:
                        pass
    except KeyboardInterrupt:
        print("\n👋 Bot detenido manualmente por el usuario.", flush=True)


if __name__ == "__main__":
    cargar_env(BOT_DIR / ".env")
    escuchar_whatsapp_continuo()
