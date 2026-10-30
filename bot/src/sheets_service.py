import json
import os
import unicodedata
import uuid
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List, Optional, Tuple

# Catálogo local por defecto (tomado de BD_BONIFICACIONES_BODEGA.xlsx) para pruebas sin conexión
EMPLEADOS_DEFAULT = [
    {"ID_Empleado": "1001", "Nombre_Completo": "Sneider Villanueva", "Activo": True},
    {"ID_Empleado": "1002", "Nombre_Completo": "Edward Sanchez", "Activo": True},
    {"ID_Empleado": "1003", "Nombre_Completo": "Fabian Ortiz", "Activo": True},
    {"ID_Empleado": "1004", "Nombre_Completo": "Sergio Ricardo Ballesteros", "Activo": True},
    {"ID_Empleado": "1005", "Nombre_Completo": "Estebi Sanchez", "Activo": True},
]

TZ_COLOMBIA = timezone(timedelta(hours=-5))


def _quitar_acentos(texto: str) -> str:
    return "".join(
        c
        for c in unicodedata.normalize("NFD", texto.lower().strip())
        if unicodedata.category(c) != "Mn"
    )


def resolver_empleado(
    nombre_buscado: str, catalogo: Optional[List[Dict[str, Any]]] = None
) -> Tuple[str, str]:
    """
    Cruza el nombre dicho por Luis (ej. 'Edward') contra la tabla EMPLEADOS
    (filtrando solo Activo = True) y devuelve (ID_Empleado, Nombre_Completo).
    """
    lista = catalogo if catalogo is not None else EMPLEADOS_DEFAULT
    buscado_norm = _quitar_acentos(nombre_buscado)

    for emp in lista:
        activo = emp.get("Activo", True)
        if str(activo).upper() in ("FALSE", "FALSO", "NO", "0"):
            continue
        nombre_completo = str(emp.get("Nombre_Completo", "")).strip()
        if not nombre_completo:
            continue
        nombre_norm = _quitar_acentos(nombre_completo)
        partes = nombre_norm.split()

        if buscado_norm == nombre_norm or buscado_norm in partes or nombre_norm.startswith(buscado_norm):
            return str(emp["ID_Empleado"]), nombre_completo

    nombres_disponibles = [
        str(e.get("Nombre_Completo", "")).strip()
        for e in lista
        if str(e.get("Activo", True)).upper() not in ("FALSE", "FALSO", "NO", "0")
        and str(e.get("Nombre_Completo", "")).strip()
    ]
    raise ValueError(
        f"El auxiliar '{nombre_buscado}' no existe o está inactivo en la hoja EMPLEADOS.\n"
        f"👷 Auxiliares activos: {', '.join(nombres_disponibles)}"
    )


def construir_fila_registro(
    datos_json: Dict[str, Any],
    catalogo_empleados: Optional[List[Dict[str, Any]]] = None,
) -> Dict[str, Any]:
    """
    Construye el diccionario exacto con las 7 columnas físicas de REGISTRO_DIARIO V2.0:
    [ID_Registro, Fecha_Hora, Empleado, Tipo_Factura, Numero_Factura, Puntos_Esfuerzo, Puntos_Error]
    """
    id_empleado, nombre_oficial = resolver_empleado(
        datos_json["nombre_empleado"], catalogo_empleados
    )
    id_registro = uuid.uuid4().hex[:8]
    ahora_col = datetime.now(TZ_COLOMBIA).strftime("%Y-%m-%d %H:%M:%S")

    fila = [
        id_registro,
        ahora_col,
        id_empleado,
        datos_json["tipo_factura"],
        datos_json["numero_factura"],
        datos_json["puntos_esfuerzo"],
        datos_json["puntos_error"],
    ]

    return {
        "id_registro": id_registro,
        "fecha_hora": ahora_col,
        "id_empleado": id_empleado,
        "nombre_oficial": nombre_oficial,
        "factura_label": f"{datos_json['tipo_factura']}-{datos_json['numero_factura']}",
        "fila_sheets": fila,
    }


def guardar_en_google_sheets(datos_json: Dict[str, Any]) -> Dict[str, Any]:
    """
    Se conecta a Google Sheets usando Service Account (soporta google-api-python-client
    ya instalado en tu venv o gspread), lee EMPLEADOS en vivo e inserta la fila en REGISTRO_DIARIO.
    """
    from google.oauth2 import service_account
    from googleapiclient.discovery import build

    sheet_id = os.getenv("GOOGLE_SHEET_ID", "").strip()
    if not sheet_id or sheet_id == "PENDIENTE_PEGAR_AQUI":
        raise RuntimeError("Falta configurar GOOGLE_SHEET_ID en bot/.env")

    creds_json_env = os.getenv("GOOGLE_CREDENTIALS_JSON", "").strip()
    creds_file = os.getenv("GOOGLE_SERVICE_ACCOUNT_FILE", "").strip()
    scopes = ["https://www.googleapis.com/auth/spreadsheets"]

    if creds_json_env:
        creds = service_account.Credentials.from_service_account_info(
            json.loads(creds_json_env), scopes=scopes
        )
    elif creds_file and os.path.exists(creds_file):
        creds = service_account.Credentials.from_service_account_file(
            creds_file, scopes=scopes
        )
    else:
        raise FileNotFoundError(
            f"No se encontró el archivo de credenciales de Google: '{creds_file}'"
        )

    service = build("sheets", "v4", credentials=creds)

    # 1. Leer catálogo EMPLEADOS en vivo
    res_emp = (
        service.spreadsheets()
        .values()
        .get(spreadsheetId=sheet_id, range="EMPLEADOS!A2:C100")
        .execute()
    )
    rows_emp = res_emp.get("values", [])
    empleados_records = []
    for r in rows_emp:
        if len(r) >= 2 and r[0] and r[1]:
            activo_val = r[2] if len(r) >= 3 else "TRUE"
            empleados_records.append(
                {
                    "ID_Empleado": str(r[0]).strip(),
                    "Nombre_Completo": str(r[1]).strip(),
                    "Activo": activo_val,
                }
            )

    # 2. Construir fila validada
    registro = construir_fila_registro(
        datos_json, empleados_records if empleados_records else None
    )

    # 3. Hacer append en REGISTRO_DIARIO
    service.spreadsheets().values().append(
        spreadsheetId=sheet_id,
        range="REGISTRO_DIARIO!A:G",
        valueInputOption="USER_ENTERED",
        insertDataOption="INSERT_ROWS",
        body={"values": [registro["fila_sheets"]]},
    ).execute()

    return registro
