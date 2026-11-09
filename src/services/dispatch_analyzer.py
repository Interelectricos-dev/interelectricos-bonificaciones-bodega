import unicodedata
import uuid
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List, Optional, Set, Tuple

# Constantes de dominio puro
TIPOS_FACTURA_VALIDOS = ("IC", "DP", "IR")
PUNTOS_ESFUERZO_MIN = 1
PUNTOS_ESFUERZO_MAX = 5
PUNTOS_ERROR_MIN = -3
PUNTOS_ERROR_MAX = 0
TZ_COLOMBIA = timezone(timedelta(hours=-5))

# Catálogo de respaldo local para operación en contingencia / offline
EMPLEADOS_FALLBACK: List[Dict[str, Any]] = [
    {"ID_Empleado": "1001", "Nombre_Completo": "Sneider Villanueva", "Activo": True},
    {"ID_Empleado": "1002", "Nombre_Completo": "Edward Sanchez", "Activo": True},
    {"ID_Empleado": "1003", "Nombre_Completo": "Fabian Ortiz", "Activo": True},
    {"ID_Empleado": "1004", "Nombre_Completo": "Sergio Ricardo Ballesteros", "Activo": True},
    {"ID_Empleado": "1005", "Nombre_Completo": "Estebi Sanchez", "Activo": True},
]


def normalizar_texto(texto: str) -> str:
    """Elimina acentos y convierte a minúsculas para comparaciones fonéticas robustas."""
    return "".join(
        c
        for c in unicodedata.normalize("NFD", str(texto).lower().strip())
        if unicodedata.category(c) != "Mn"
    )


def normalizar_numero_factura(val: Any) -> str:
    """Normaliza el número de factura a cadena sin decimales residuales (.0)."""
    s = str(val).strip()
    if s.endswith(".0"):
        s = s[:-2]
    return s


def validar_un_despacho(item: Dict[str, Any], indice: int = 1) -> Dict[str, Any]:
    """
    Regla de negocio pura: Valida exhaustivamente los campos de un despacho individual.
    Lanza ValueError con descripción amigable si incumple las reglas.
    """
    prefijo = f"Despacho #{indice}: " if indice > 0 else ""
    faltantes: List[str] = []

    # 1. Validación de Tipo de Factura
    tipo_raw = item.get("tipo_factura")
    tipo = str(tipo_raw).strip().upper() if tipo_raw is not None else ""
    if not tipo or tipo in ("NULL", "NONE"):
        faltantes.append("tipo de factura (IC, DP o IR)")
    elif tipo not in TIPOS_FACTURA_VALIDOS:
        faltantes.append(
            f"tipo de factura válido (recibido '{tipo}', pero solo existe IC, DP o IR)"
        )

    # 2. Validación de Número de Factura
    num_raw = item.get("numero_factura")
    numero_limpio: Optional[str] = None
    if num_raw is None or str(num_raw).strip().upper() in ("", "NULL", "NONE"):
        faltantes.append("número de factura")
    else:
        try:
            num_int = int(float(str(num_raw).strip()))
            if num_int <= 0:
                faltantes.append("número de factura positivo")
            else:
                numero_limpio = str(num_int)
        except (ValueError, TypeError):
            faltantes.append(f"número de factura numérico (recibido '{num_raw}')")

    # 3. Validación de Auxiliar
    nombre_raw = item.get("nombre_empleado")
    nombre = str(nombre_raw).strip() if nombre_raw is not None else ""
    if not nombre or nombre.upper() in ("NULL", "NONE"):
        faltantes.append("nombre del auxiliar asignado")

    if faltantes:
        raise ValueError(f"{prefijo}falta {', '.join(faltantes)}.")

    # 4. Validación de Puntos de Esfuerzo (1 a 5)
    try:
        esfuerzo = int(item.get("puntos_esfuerzo") if item.get("puntos_esfuerzo") is not None else 1)
    except (ValueError, TypeError):
        raise ValueError(f"{prefijo}los puntos de esfuerzo deben ser numéricos (1 a 5).")

    if esfuerzo < PUNTOS_ESFUERZO_MIN or esfuerzo > PUNTOS_ESFUERZO_MAX:
        raise ValueError(
            f"{prefijo}puntos de esfuerzo ({esfuerzo}) fuera de rango [{PUNTOS_ESFUERZO_MIN} - {PUNTOS_ESFUERZO_MAX}]."
        )

    # 5. Validación de Puntos de Error (0 a -3)
    try:
        error = int(item.get("puntos_error") if item.get("puntos_error") is not None else 0)
    except (ValueError, TypeError):
        raise ValueError(f"{prefijo}los puntos de error deben ser numéricos (0 a -3).")

    if error > 0:
        error = -error  # Invertir signo positivo dictado por el usuario ("1 error" -> -1)

    if error < PUNTOS_ERROR_MIN or error > PUNTOS_ERROR_MAX:
        raise ValueError(
            f"{prefijo}puntos de error ({error}) fuera de rango [{PUNTOS_ERROR_MIN} a {PUNTOS_ERROR_MAX}]."
        )

    return {
        "tipo_factura": tipo,
        "numero_factura": numero_limpio,
        "nombre_empleado": nombre,
        "puntos_esfuerzo": esfuerzo,
        "puntos_error": error,
    }


def resolver_empleado(
    nombre_buscado: str, catalogo: Optional[List[Dict[str, Any]]] = None
) -> Tuple[str, str]:
    """
    Cruza el nombre en memoria contra el catálogo de empleados activos.
    Retorna (ID_Empleado, Nombre_Completo).
    Lanza ValueError si el colaborador no existe o está inactivo.
    """
    lista = catalogo if catalogo is not None else EMPLEADOS_FALLBACK
    buscado_norm = normalizar_texto(nombre_buscado)

    for emp in lista:
        activo = emp.get("Activo", True)
        if str(activo).upper() in ("FALSE", "FALSO", "NO", "0"):
            continue
        nombre_completo = str(emp.get("Nombre_Completo", "")).strip()
        if not nombre_completo:
            continue

        nombre_norm = normalizar_texto(nombre_completo)
        partes = nombre_norm.split()

        if (
            buscado_norm == nombre_norm
            or buscado_norm in partes
            or nombre_norm.startswith(buscado_norm)
        ):
            return str(emp["ID_Empleado"]), nombre_completo

    activos = [
        str(e.get("Nombre_Completo", "")).strip()
        for e in lista
        if str(e.get("Activo", True)).upper() not in ("FALSE", "FALSO", "NO", "0")
        and str(e.get("Nombre_Completo", "")).strip()
    ]
    raise ValueError(
        f"El auxiliar '{nombre_buscado}' no existe o está inactivo. Auxiliares activos: {', '.join(activos)}"
    )


def segregar_despachos_lote(despachos_crudos: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
    """
    Segrega un lote de despachos en 'validos' e 'incompletos' aplicando tolerancia a fallos parciales.
    """
    validos: List[Dict[str, Any]] = []
    incompletos: List[Dict[str, Any]] = []

    for idx, item in enumerate(despachos_crudos, start=1):
        try:
            limpio = validar_un_despacho(item, indice=idx if len(despachos_crudos) > 1 else 0)
            validos.append(limpio)
        except ValueError as exc:
            motivo = str(exc)
            if ":" in motivo:
                motivo = motivo.split(":", 1)[1].strip()
            incompletos.append(
                {
                    "indice": idx,
                    "tipo_factura": item.get("tipo_factura"),
                    "numero_factura": item.get("numero_factura"),
                    "nombre_empleado": item.get("nombre_empleado"),
                    "motivo": motivo,
                }
            )

    return {"validos": validos, "incompletos": incompletos}


def procesar_y_estructurar_registros(
    despachos_validos: List[Dict[str, Any]],
    catalogo_empleados: Optional[List[Dict[str, Any]]] = None,
    existentes_set: Optional[Set[Tuple[str, str, str]]] = None,
    fecha_referencia: Optional[str] = None,
) -> Dict[str, List[Dict[str, Any]]]:
    """
    Regla de negocio nuclear:
    1. Resuelve IDs de empleados contra el catálogo.
    2. Identifica y separa duplicados contra el historial y el mismo lote.
    3. Construye la fila física estándar de 7 columnas para REGISTRO_DIARIO V2.0:
       [ID_Registro, Fecha_Hora, Empleado, Tipo_Factura, Numero_Factura, Puntos_Esfuerzo, Puntos_Error]
    """
    ahora = fecha_referencia or datetime.now(TZ_COLOMBIA).strftime("%Y-%m-%d %H:%M:%S")
    existentes = existentes_set or set()

    nuevos: List[Dict[str, Any]] = []
    duplicados: List[Dict[str, Any]] = []
    incompletos: List[Dict[str, Any]] = []
    vistos_en_lote: Set[Tuple[str, str, str]] = set()

    for idx, d in enumerate(despachos_validos, start=1):
        nombre_emp = d.get("nombre_empleado", "")
        try:
            id_empleado, nombre_oficial = resolver_empleado(nombre_emp, catalogo_empleados)
        except ValueError as err_res:
            incompletos.append(
                {
                    "indice": idx,
                    "tipo_factura": d.get("tipo_factura"),
                    "numero_factura": d.get("numero_factura"),
                    "nombre_empleado": nombre_emp,
                    "motivo": str(err_res),
                }
            )
            continue

        tipo = str(d["tipo_factura"]).strip().upper()
        numero = normalizar_numero_factura(d["numero_factura"])
        clave = (id_empleado, tipo, numero)

        id_registro = uuid.uuid4().hex[:8]
        fila_7_cols = [
            id_registro,
            ahora,
            id_empleado,
            tipo,
            numero,
            d["puntos_esfuerzo"],
            d["puntos_error"],
        ]

        registro_objeto = {
            "id_registro": id_registro,
            "fecha_hora": ahora,
            "id_empleado": id_empleado,
            "nombre_oficial": nombre_oficial,
            "factura_label": f"{tipo}-{numero}",
            "puntos_esfuerzo": d["puntos_esfuerzo"],
            "puntos_error": d["puntos_error"],
            "fila_sheets": fila_7_cols,
        }

        if clave in existentes or clave in vistos_en_lote:
            duplicados.append(registro_objeto)
        else:
            vistos_en_lote.add(clave)
            nuevos.append(registro_objeto)

    return {
        "nuevos": nuevos,
        "duplicados": duplicados,
        "incompletos": incompletos,
    }

