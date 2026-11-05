import json
import os
import unicodedata
import uuid
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List, Optional, Tuple, Union

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

        if (
            buscado_norm == nombre_norm
            or buscado_norm in partes
            or nombre_norm.startswith(buscado_norm)
        ):
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


def normalizar_numero_factura(val: Any) -> str:
    """Normaliza el número de factura a string limpio sin decimales (.0)."""
    s = str(val).strip()
    if s.endswith(".0"):
        s = s[:-2]
    return s


def construir_filas_registros(
    lote_datos: Union[Dict[str, Any], List[Dict[str, Any]]],
    catalogo_empleados: Optional[List[Dict[str, Any]]] = None,
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """
    Construye una lista de registros validados (1 o N despachos) con las 7 columnas físicas
    exactas de REGISTRO_DIARIO V2.0:
    [ID_Registro, Fecha_Hora, Empleado, Tipo_Factura, Numero_Factura, Puntos_Esfuerzo, Puntos_Error]
    Retorna (registros_validos, registros_incompletos_o_invalidos).
    """
    items = [lote_datos] if isinstance(lote_datos, dict) else lote_datos
    ahora_col = datetime.now(TZ_COLOMBIA).strftime("%Y-%m-%d %H:%M:%S")

    registros: List[Dict[str, Any]] = []
    incompletos: List[Dict[str, Any]] = []

    for idx, datos_json in enumerate(items, 1):
        emp_raw = datos_json.get("nombre_empleado")
        tipo_factura = str(datos_json.get("tipo_factura", "")).strip().upper()
        num_raw = datos_json.get("numero_factura")
        numero_factura = normalizar_numero_factura(num_raw) if num_raw is not None else ""

        try:
            id_empleado, nombre_oficial = resolver_empleado(
                emp_raw, catalogo_empleados
            )
        except ValueError as err_emp:
            incompletos.append(
                {
                    "indice": idx,
                    "tipo_factura": tipo_factura or None,
                    "numero_factura": numero_factura or None,
                    "nombre_empleado": emp_raw,
                    "motivo": str(err_emp).split("\n")[0],
                }
            )
            continue

        id_registro = uuid.uuid4().hex[:8]
        fila = [
            id_registro,
            ahora_col,
            id_empleado,
            tipo_factura,
            numero_factura,
            datos_json["puntos_esfuerzo"],
            datos_json["puntos_error"],
        ]
        registros.append(
            {
                "id_registro": id_registro,
                "fecha_hora": ahora_col,
                "id_empleado": id_empleado,
                "nombre_oficial": nombre_oficial,
                "factura_label": f"{tipo_factura}-{numero_factura}",
                "puntos_esfuerzo": datos_json["puntos_esfuerzo"],
                "puntos_error": datos_json["puntos_error"],
                "fila_sheets": fila,
            }
        )

    return registros, incompletos


def guardar_en_google_sheets(
    lote_datos: Union[Dict[str, Any], List[Dict[str, Any]]]
) -> Dict[str, List[Dict[str, Any]]]:
    """
    Se conecta a Google Sheets usando Service Account.
    Ejecuta un batchGet de EMPLEADOS y REGISTRO_DIARIO (columnas Empleado, Tipo_Factura, Numero_Factura)
    para validar duplicados en una sola petición HTTP de ultra-baja latencia.
    Inserta únicamente los registros nuevos (si los hay) y retorna:
    {"nuevos": [...], "duplicados": [...]}
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

    # 1. Leer catálogo EMPLEADOS y facturas existentes en 1 sola llamada de red (batchGet)
    # Columnas en REGISTRO_DIARIO: Col C (Empleado), Col D (Tipo_Factura), Col E (Numero_Factura)
    res_batch = (
        service.spreadsheets()
        .values()
        .batchGet(
            spreadsheetId=sheet_id,
            ranges=["EMPLEADOS!A2:C100", "REGISTRO_DIARIO!C2:E"],
        )
        .execute()
    )
    val_ranges = res_batch.get("valueRanges", [])
    rows_emp = val_ranges[0].get("values", []) if len(val_ranges) > 0 else []
    rows_reg = val_ranges[1].get("values", []) if len(val_ranges) > 1 else []

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

    # 2. Conjunto de facturas ya registradas por colaborador: (id_empleado, tipo_factura, numero_factura)
    existentes_set = set()
    for r in rows_reg:
        if len(r) >= 3 and r[0] and r[1] and r[2]:
            emp_id = str(r[0]).strip()
            tipo = str(r[1]).strip().upper()
            num = normalizar_numero_factura(r[2])
            existentes_set.add((emp_id, tipo, num))

    # 3. Construir filas y separar nuevos vs duplicados
    registros, incompletos_db = construir_filas_registros(
        lote_datos, empleados_records if empleados_records else None
    )

    nuevos: List[Dict[str, Any]] = []
    duplicados: List[Dict[str, Any]] = []
    vistos_en_lote = set()

    for reg in registros:
        clave = (
            str(reg["id_empleado"]).strip(),
            str(reg["fila_sheets"][3]).strip().upper(),  # Tipo_Factura
            normalizar_numero_factura(reg["fila_sheets"][4]),  # Numero_Factura
        )
        if clave in existentes_set or clave in vistos_en_lote:
            duplicados.append(reg)
        else:
            vistos_en_lote.add(clave)
            nuevos.append(reg)

    # 4. Insertar en Google Sheets solo los registros nuevos (si los hay)
    if nuevos:
        filas_a_insertar = [r["fila_sheets"] for r in nuevos]
        service.spreadsheets().values().append(
            spreadsheetId=sheet_id,
            range="REGISTRO_DIARIO!A:G",
            valueInputOption="USER_ENTERED",
            insertDataOption="INSERT_ROWS",
            body={"values": filas_a_insertar},
        ).execute()

    return {"nuevos": nuevos, "duplicados": duplicados, "incompletos": incompletos_db}
