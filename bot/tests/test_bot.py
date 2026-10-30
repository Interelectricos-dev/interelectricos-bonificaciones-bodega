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
    Escucha de forma continua la cola de Green API.
    Soporta tanto 1 despacho individual como múltiples despachos en un mismo audio/texto.
    Para detenerlo: presiona Ctrl + C en la terminal.
    """
    wa = GreenAPIService()

    print("🧹 Limpiando notificaciones antiguas pendientes en la cola...", flush=True)
    limpiadas = 0
    while wa.recibir_notificacion_cola(borrar_al_leer=True) is not None:
        limpiadas += 1
    if limpiadas:
        print(f"   ({limpiadas} notificaciones antiguas descartadas)", flush=True)

    print("\n" + "=" * 70, flush=True)
    print("🎧 BOT ESCUCHANDO WHATSAPP EN VIVO (Presiona Ctrl + C para salir)", flush=True)
    print("📱 Soporta 1 despacho suelto o BLOQUES de varios despachos en 1 audio/texto", flush=True)
    print("   • Individual: 'IC 2021 Edward 2 puntos 1 error'", flush=True)
    print("   • En bloque:  'IC 2021 Edward 2 puntos, DP 3040 Sneider 3 puntos'", flush=True)
    print("=" * 70, flush=True)

    try:
        while True:
            try:
                body = wa.recibir_notificacion_cola(borrar_al_leer=True)
            except Exception as e:
                print(f"⚠️ Error consultando cola: {e}", flush=True)
                time.sleep(2)
                continue

            if not body:
                time.sleep(2)
                continue

            chat_id, texto, audio_url = wa.extraer_contenido_webhook(body)
            if not chat_id or (not texto and not audio_url):
                continue

            # Ignorar los mensajes de respuesta que envía el propio bot
            if texto and texto.startswith(("✅", "⚠️")):
                continue

            print("\n" + "-" * 65, flush=True)
            print(f"📥 ¡Nuevo mensaje recibido del chat {chat_id}!", flush=True)
            try:
                if audio_url:
                    print("🎙️ Tipo: NOTA DE VOZ -> Descargando audio desde Green API...", flush=True)
                    audio_bytes, mime_type = wa.descargar_archivo(audio_url)
                    print(f"🤖 Analizando audio ({len(audio_bytes)} bytes) con Gemini API...", flush=True)
                    lote_despachos = parse_con_gemini(audio_bytes=audio_bytes, mime_type=mime_type)
                else:
                    print(f"💬 Tipo: TEXTO -> '{texto}'", flush=True)
                    print("🤖 Analizando texto con Gemini API...", flush=True)
                    lote_despachos = parse_con_gemini(texto=texto)

                print(f"\n1️⃣ DESPACHOS EXTRAÍDOS POR GEMINI ({len(lote_despachos)}):", flush=True)
                print(json.dumps(lote_despachos, indent=2, ensure_ascii=False), flush=True)

                print("\n2️⃣ GUARDANDO EN GOOGLE SHEETS (REGISTRO_DIARIO)...", flush=True)
                registros = guardar_en_google_sheets(lote_despachos)
                for r in registros:
                    print("   ✅ Fila insertada:", r["fila_sheets"], flush=True)

                confirmacion = formatear_mensaje_confirmacion(registros)
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
                        "💡 *Ejemplo individual:* `IC2021 Edward 2 puntos 1 error`\n"
                        "💡 *Ejemplo por bloque:* `IC2021 Edward 2 puntos, DP3040 Sneider 3 puntos`",
                    )
                except Exception:
                    pass
    except KeyboardInterrupt:
        print("\n👋 Bot detenido manualmente por el usuario.", flush=True)


if __name__ == "__main__":
    cargar_env(BOT_DIR / ".env")
    escuchar_whatsapp_continuo()
