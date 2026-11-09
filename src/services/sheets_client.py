import json
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from src.config import settings, get_logger
from src.services.dispatch_analyzer import EMPLEADOS_FALLBACK, normalizar_numero_factura

logger = get_logger("sheets_client")


class SheetsClient:
    """Capa de integración con la API de Google Sheets v4 con tolerancia a fallos."""

    SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]

    def __init__(
        self,
        sheet_id: Optional[str] = None,
        credentials_file: Optional[Path] = None,
        credentials_json: Optional[str] = None,
    ) -> None:
        self.sheet_id = (sheet_id or settings.GOOGLE_SHEET_ID).strip()
        self.credentials_file = credentials_file or settings.get_service_account_path()
        self.credentials_json = credentials_json or settings.GOOGLE_CREDENTIALS_JSON
        self._service = None

    def _obtener_servicio(self):
        """Inicializa el cliente de Google Sheets con las credenciales configuradas."""
        if self._service is not None:
            return self._service

        if not self.sheet_id or self.sheet_id == "PENDIENTE_PEGAR_AQUI":
            raise ValueError("GOOGLE_SHEET_ID no está configurado en el archivo .env")

        if self.credentials_json:
            creds = service_account.Credentials.from_service_account_info(
                json.loads(self.credentials_json), scopes=self.SCOPES
            )
        elif self.credentials_file and self.credentials_file.exists():
            creds = service_account.Credentials.from_service_account_file(
                str(self.credentials_file), scopes=self.SCOPES
            )
        else:
            raise FileNotFoundError(
                f"No se encontraron credenciales de Google Service Account en '{self.credentials_file}' "
                "ni en GOOGLE_CREDENTIALS_JSON."
            )

        self._service = build("sheets", "v4", credentials=creds, cache_discovery=False)
        return self._service

    def _ejecutar_con_reintentos(self, peticion: Any, max_intentos: int = 4, delay_inicial: float = 1.5) -> Any:
        """Ejecuta una petición con política de reintentos exponenciales ante 429, 500, 503, etc."""
        delay = delay_inicial
        ultimo_error = None

        for intento in range(1, max_intentos + 1):
            try:
                return peticion.execute()
            except HttpError as err:
                status = getattr(err.resp, "status", None)
                ultimo_error = err
                if status in (429, 500, 502, 503, 504) and intento < max_intentos:
                    logger.warning("Error HTTP %s en Google Sheets (intento %d/%d). Reintentando en %.1fs...", status, intento, max_intentos, delay)
                    time.sleep(delay)
                    delay *= 2
                    continue
                raise
            except (TimeoutError, OSError) as net_err:
                ultimo_error = net_err
                if intento < max_intentos:
                    logger.warning("Error de red en Google Sheets (intento %d/%d): %s. Reintentando en %.1fs...", intento, max_intentos, net_err, delay)
                    time.sleep(delay)
                    delay *= 2
                    continue
                raise

        raise ultimo_error

    def obtener_catalogo_y_existentes(self) -> Tuple[List[Dict[str, Any]], Set[Tuple[str, str, str]]]:
        """
        Recupera el catálogo de EMPLEADOS y las claves de facturas ya registradas en REGISTRO_DIARIO.
        Si la red o el servicio cloud fallan, conmuta de forma no bloqueante al catálogo de contingencia.
        """
        try:
            service = self._obtener_servicio()
            req_batch = service.spreadsheets().values().batchGet(
                spreadsheetId=self.sheet_id,
                ranges=["EMPLEADOS!A2:C100", "REGISTRO_DIARIO!C2:E"],
            )
            res_batch = self._ejecutar_con_reintentos(req_batch)
            val_ranges = res_batch.get("valueRanges", [])

            rows_emp = val_ranges[0].get("values", []) if len(val_ranges) > 0 else []
            rows_reg = val_ranges[1].get("values", []) if len(val_ranges) > 1 else []

            catalogo_empleados: List[Dict[str, Any]] = []
            for r in rows_emp:
                if len(r) >= 2 and r[0] and r[1]:
                    activo_val = r[2] if len(r) >= 3 else "TRUE"
                    catalogo_empleados.append(
                        {
                            "ID_Empleado": str(r[0]).strip(),
                            "Nombre_Completo": str(r[1]).strip(),
                            "Activo": activo_val,
                        }
                    )

            existentes_set: Set[Tuple[str, str, str]] = set()
            for r in rows_reg:
                if len(r) >= 3 and r[0] and r[1] and r[2]:
                    emp_id = str(r[0]).strip()
                    tipo = str(r[1]).strip().upper()
                    num = normalizar_numero_factura(r[2])
                    existentes_set.add((emp_id, tipo, num))

            logger.info(
                "Catálogo sincronizado: %d empleados, %d registros históricos para antiduplicados.",
                len(catalogo_empleados),
                len(existentes_set),
            )
            return catalogo_empleados, existentes_set

        except Exception as exc:
            logger.warning(
                "ADVERTENCIA DE RESILIENCIA: No fue posible consultar Google Sheets (%s). "
                "Operando con catálogo de respaldo local en modo no bloqueante.",
                exc,
            )
            return EMPLEADOS_FALLBACK, set()

    def insertar_filas_registro_diario(self, filas: List[List[Any]]) -> int:
        """Inserta por lotes atómicos filas en la hoja REGISTRO_DIARIO."""
        if not filas:
            return 0

        service = self._obtener_servicio()
        req_append = service.spreadsheets().values().append(
            spreadsheetId=self.sheet_id,
            range="REGISTRO_DIARIO!A:G",
            valueInputOption="USER_ENTERED",
            insertDataOption="INSERT_ROWS",
            body={"values": filas},
        )
        self._ejecutar_con_reintentos(req_append)
        logger.info("Se insertaron exitosamente %d filas en REGISTRO_DIARIO.", len(filas))
        return len(filas)

