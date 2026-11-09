import logging
import os
import sys
from pathlib import Path
from typing import List, Optional
from dotenv import load_dotenv

# -----------------------------------------------------------------------------
# 1. RESOLUCIÓN DE RUTAS ABSOLUTAS (Portabilidad Task Scheduler / Cron)
# -----------------------------------------------------------------------------
SRC_DIR = Path(__file__).resolve().parent
BASE_DIR = SRC_DIR.parent

DATA_DIR = BASE_DIR / "data"
REPORTS_DIR = BASE_DIR / "reports"
CREDENTIALS_DIR = BASE_DIR / "credentials"
LOG_FILE = BASE_DIR / "app.log"

for directory in (DATA_DIR, REPORTS_DIR, CREDENTIALS_DIR):
    directory.mkdir(parents=True, exist_ok=True)

# -----------------------------------------------------------------------------
# 2. CARGA CENTRALIZADA DE VARIABLES DE ENTORNO
# -----------------------------------------------------------------------------
ENV_FILE = BASE_DIR / ".env"
if ENV_FILE.exists():
    load_dotenv(dotenv_path=ENV_FILE)
else:
    load_dotenv()  # Fallback a entorno del sistema

# -----------------------------------------------------------------------------
# 3. SISTEMA DE LOGGING DUAL (Consola + app.log)
# -----------------------------------------------------------------------------
LOG_LEVEL_STR = os.getenv("LOG_LEVEL", "INFO").upper()
LOG_LEVEL = getattr(logging, LOG_LEVEL_STR, logging.INFO)

log_formatter = logging.Formatter(
    fmt="%(asctime)s [%(levelname)s] [%(name)s]: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

root_logger = logging.getLogger()
root_logger.setLevel(LOG_LEVEL)

# Evitar duplicar handlers si config se importa múltiples veces
if not root_logger.handlers:
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(LOG_LEVEL)
    console_handler.setFormatter(log_formatter)
    root_logger.addHandler(console_handler)

    try:
        file_handler = logging.FileHandler(LOG_FILE, encoding="utf-8")
        file_handler.setLevel(LOG_LEVEL)
        file_handler.setFormatter(log_formatter)
        root_logger.addHandler(file_handler)
    except Exception as exc:
        sys.stderr.write(f"No se pudo inicializar FileHandler en {LOG_FILE}: {exc}\n")


def get_logger(name: str) -> logging.Logger:
    """Devuelve un logger configurado con el estándar del proyecto."""
    return logging.getLogger(name)


# -----------------------------------------------------------------------------
# 4. CONFIGURACIÓN TIPADA CENTRALIZADA
# -----------------------------------------------------------------------------
class Settings:
    """Configuración tipada del sistema leída desde variables de entorno."""

    # Rutas absolutas
    BASE_DIR: Path = BASE_DIR
    DATA_DIR: Path = DATA_DIR
    REPORTS_DIR: Path = REPORTS_DIR
    CREDENTIALS_DIR: Path = CREDENTIALS_DIR
    LOG_FILE: Path = LOG_FILE

    # Green API (WhatsApp)
    GREEN_HOST: str = os.getenv("GREEN_HOST", "https://7107.api.greenapi.com").rstrip("/")
    ID_INSTANCE: str = os.getenv("ID_INSTANCE", "").strip()
    API_TOKEN_INSTANCE: str = os.getenv("API_TOKEN_INSTANCE", "").strip()
    CHAT_ID_PRUEBA_RAW: str = os.getenv("CHAT_ID_PRUEBA", "").strip()

    # Gemini API
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "").strip()
    GEMINI_MODEL: str = os.getenv("GEMINI_MODEL", "gemini-3.5-flash").strip()

    # Google Sheets
    GOOGLE_SHEET_ID: str = os.getenv("GOOGLE_SHEET_ID", "").strip()
    GOOGLE_CREDENTIALS_JSON: str = os.getenv("GOOGLE_CREDENTIALS_JSON", "").strip()
    _service_account_raw: str = os.getenv("GOOGLE_SERVICE_ACCOUNT_FILE", "credentials/service_account.json").strip()

    @classmethod
    def get_service_account_path(cls) -> Path:
        """Resuelve la ruta absoluta al archivo de credenciales de Google."""
        p = Path(cls._service_account_raw)
        return p if p.is_absolute() else (cls.BASE_DIR / p)

    @classmethod
    def get_authorized_chats(cls) -> List[str]:
        """Obtiene la lista de chats de WhatsApp autorizados."""
        if not cls.CHAT_ID_PRUEBA_RAW:
            return []
        return [c.strip() for c in cls.CHAT_ID_PRUEBA_RAW.split(",") if c.strip()]


settings = Settings()

