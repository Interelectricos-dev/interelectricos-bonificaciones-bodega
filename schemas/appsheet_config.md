# Configuración Técnica de AppSheet — Sistema de Bonificaciones Bodega

> **Propósito:** Guía técnica paso a paso de toda la configuración aplicada directamente en el motor de AppSheet. No incluye fórmulas internas de Google Sheets. Cualquier persona que retome este proyecto debe poder reproducir la configuración completa siguiendo este documento en orden.

---

## Tabla de Contenidos

1. [Permisos de Tablas (Data > Tables)](#1-permisos-de-tablas)
2. [Configuración de Columnas (Data > Columns)](#2-configuración-de-columnas)
3. [Configuración de Slices (Data > Slices)](#3-configuración-de-slices)
4. [Configuración de Vistas (App > Views)](#4-configuración-de-vistas)
5. [Reglas de Comportamiento (App > Actions)](#5-reglas-de-comportamiento)
6. [Reglas de Formato Condicional (App > Format Rules)](#6-reglas-de-formato-condicional)
7. [Lista de Verificación Final](#7-lista-de-verificación-final)

---

## 1. Permisos de Tablas (Data > Tables)

*(Captura de referencia: [01_tables_permisos.png](../docs/images/appsheet_config/01_tables_permisos.png))*

Ir a **Data > Tables**. Para cada tabla configurar la propiedad **Are updates allowed?**:

| Tabla | Permiso | Razón |
| :--- | :--- | :--- |
| `EMPLEADOS` | `Read_Only` | Catálogo maestro. Solo el administrador lo modifica desde Google Sheets. |
| `REGISTRO_DIARIO` | `Adds + Updates` (Delete desmarcado) | Registro transaccional. Prohibida la eliminación por política de auditoría. |
| `FILTRO_FECHAS` | `Updates_Only` (Add y Delete desmarcados) | Tabla de un único registro de control de fecha. No se crean ni eliminan filas. |
| `RESUMEN_SEMANAL` | `Read_Only` | Calculada automáticamente por fórmulas matriciales en Google Sheets. |
| `RESUMEN_MENSUAL` | `Read_Only` | Calculada automáticamente por fórmulas matriciales en Google Sheets. |

---

## 2. Configuración de Columnas (Data > Columns)

Ir a **Data > Columns**. La cuadrícula principal de AppSheet permite configurar directamente las propiedades estándar (`TYPE`, `KEY?`, `LABEL?`, `SHOW?`, `EDITABLE?`, `REQUIRE?`, `SEARCH?` y `DISPLAY NAME`).

El apartado **Ajustes internos (✏️)** contiene **únicamente** las propiedades avanzadas que no son visibles en la cuadrícula y exigen abrir el modal de edición de la columna (icono de lápiz ✏️), tales como `Auto Compute`, `Type Details` o reglas `Valid_If`.

---

### 2.1. Tabla: `EMPLEADOS`

*(Capturas: [02_cols_empleados_01.png](../docs/images/appsheet_config/02_cols_empleados_01.png), [02_cols_empleados_02.png](../docs/images/appsheet_config/02_cols_empleados_02.png))*

#### A. Columnas base (provenientes de Google Sheets)

| NAME | TYPE | KEY? | LABEL? | SHOW? | EDITABLE? | REQUIRE? | SEARCH? | DISPLAY NAME |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :--- |
| `_RowNumber` | `Number` | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | *(vacío)* |
| `ID_Empleado` | `Text` | ☑️ | ⬜ | ☑️ | ⬜ | ⬜ | ⬜ | `ID` |
| `Nombre_Completo` | `Text` | ⬜ | ☑️ | ☑️ | ⬜ | ⬜ | ☑️ | `Nombre Completo` |
| `Activo` | `Yes/No` | ⬜ | ⬜ | ⬜ | ☑️ | ⬜ | ⬜ | *(vacío)* |

> **Notas técnicas:**
> * `Activo` se mantiene con `SHOW? = FALSE` porque el estado operativo se expone a través de la columna virtual `Estado` (`Activo?`).
> * La relación del sistema `Related REGISTRO_DIARIOs` (`List` de `Ref`) tiene configurado como Display name: `Historial de Despachos`.

#### B. Columna virtual: `Estado`

Esta columna **no existe en Google Sheets**. Se crea solo en AppSheet para mostrar `"SI"` o `"NO"` en lugar del booleano `Y/N` que genera el tipo `Yes/No`.

**Pasos:** Al final de la lista de columnas de `EMPLEADOS`, clic en **`+ Add virtual column`**.

| NAME | TYPE | KEY? | LABEL? | SHOW? | EDITABLE? | REQUIRE? | SEARCH? | DISPLAY NAME |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :--- |
| `Estado` | `Text` | ⬜ | ⬜ | ☑️ | ⬜ | ⬜ | ☑️ | `Activo?` |

> **Ajustes internos (✏️):**
> * **App formula:** `IF([Activo], "SI", "NO")`
>
> *(Resultado: En la vista de detalle del empleado, el usuario verá `SI` o `NO` en lugar de `Y` o `N`).*

---

### 2.2. Tabla: `FILTRO_FECHAS`

*(Capturas: [03_cols_filtro_fechas_01.png](../docs/images/appsheet_config/03_cols_filtro_fechas_01.png), [03_cols_filtro_fechas_02.png](../docs/images/appsheet_config/03_cols_filtro_fechas_02.png))*

| NAME | TYPE | KEY? | LABEL? | SHOW? | EDITABLE? | REQUIRE? | SEARCH? | DISPLAY NAME |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :--- |
| `_RowNumber` | `Number` | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | *(vacío)* |
| `ID_Filtro` | `Number` | ☑️ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | *(vacío)* |
| `Fecha_Referencia` | `Date` | ⬜ | ☑️ | ☑️ | ☑️ | ☑️ | ☑️ | `Seleccionar Fecha` |
| `Semana_Inicio` | `Date` | ⬜ | ⬜ | ☑️ | ⬜ | ⬜ | ⬜ | `Semana Inicio` |
| `Semana_Fin` | `Date` | ⬜ | ⬜ | ☑️ | ⬜ | ⬜ | ⬜ | `Semana Fin` |
| `Mes_Inicio` | `Date` | ⬜ | ⬜ | ☑️ | ⬜ | ⬜ | ⬜ | `Mes Inicio` |
| `Mes_Fin` | `Date` | ⬜ | ⬜ | ☑️ | ⬜ | ⬜ | ⬜ | `Mes Fin` |

> **Ajustes internos (✏️):**
> * **`Fecha_Referencia`:**
>   * **Auto Compute > Initial value:** `TODAY()`
>   * ⚠️ **Regla estricta:** La celda `B2` en Google Sheets **NO debe tener fórmula**. Debe ser una fecha estática (ej. `10/10/2026`). Si tiene fórmula de hoja de cálculo, AppSheet bloquea la edición desde la app.

---

### 2.3. Tabla: `REGISTRO_DIARIO`

*(Capturas: [04_cols_registro_diario_01.png](../docs/images/appsheet_config/04_cols_registro_diario_01.png), [04_cols_registro_diario_02.png](../docs/images/appsheet_config/04_cols_registro_diario_02.png), [07_modal_botones_puntos_01.png](../docs/images/appsheet_config/07_modal_botones_puntos_01.png), [07_modal_botones_puntos_02.png](../docs/images/appsheet_config/07_modal_botones_puntos_02.png), [07_modal_botones_puntos_03.png](../docs/images/appsheet_config/07_modal_botones_puntos_03.png))*

| NAME | TYPE | KEY? | LABEL? | SHOW? | EDITABLE? | REQUIRE? | SEARCH? | DISPLAY NAME |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :--- |
| `_RowNumber` | `Number` | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | *(vacío)* |
| `ID_Registro` | `Text` | ☑️ | ⬜ | ⬜ | ⬜ | ☑️ | ⬜ | *(vacío)* |
| `Fecha_Hora` | `DateTime` | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | *(vacío)* |
| `Empleado` | `Ref` | ⬜ | ⬜ | ☑️ | ☑️ | ☑️ | ☑️ | `Empleado` |
| `Numero_Factura` | `Text` | ⬜ | ☑️ | ☑️ | ☑️ | ☑️ | ☑️ | `N° Factura` |
| `Puntos_Factura` | `Enum` | ⬜ | ⬜ | ☑️ | ☑️ | ☑️ | ⬜ | `Puntos Factura` |
| `Puntos_Esfuerzo` | `Enum` | ⬜ | ⬜ | ☑️ | ☑️ | ☑️ | ⬜ | `Puntos Esfuerzo` |
| `Puntos_Error` | `Enum` | ⬜ | ⬜ | ☑️ | ☑️ | ☑️ | ⬜ | `Puntos Error` |

> **Ajustes internos (✏️):**
> * **`ID_Registro`:**
>   * **Auto Compute > Initial value:** `UNIQUEID()`
>
> * **`Fecha_Hora`:**
>   * **Auto Compute > Initial value:** `NOW()` *(se autocalcula al guardar sin distraer al operario)*
>
> * **`Empleado`:**
>   * **Type Details > Source table:** `EMPLEADOS`
>   * **Data Validity > Valid_If:** `SELECT(EMPLEADOS[ID_Empleado], [Activo] = TRUE)` *(filtra y muestra únicamente personal activo en el desplegable)*
>
> * **Botoneras táctiles (`Puntos_Factura`, `Puntos_Esfuerzo`, `Puntos_Error`):**
>   * **Type Details > Base type:** `Number`
>   * **Type Details > Input mode:** `Buttons` *(renderiza botones táctiles horizontales)*
>   * **Type Details > Values:**
>     * `Puntos_Factura`: `1, 2, 3, 4, 5`
>     * `Puntos_Esfuerzo`: `1, 2, 3, 4, 5`
>     * `Puntos_Error`: `0, -1, -2, -3`

---

### 2.4. Tablas: `RESUMEN_SEMANAL` y `RESUMEN_MENSUAL`

Ambas comparten la misma estructura de columnas base provenientes de Google Sheets. Configurar `RESUMEN_SEMANAL` primero y repetir el proceso idéntico para `RESUMEN_MENSUAL`.

*(Capturas: [05_cols_resumen_semanal_01.png](../docs/images/appsheet_config/05_cols_resumen_semanal_01.png), [05_cols_resumen_semanal_02.png](../docs/images/appsheet_config/05_cols_resumen_semanal_02.png), [06_cols_resumen_mensual_01.png](../docs/images/appsheet_config/06_cols_resumen_mensual_01.png), [06_cols_resumen_mensual_02.png](../docs/images/appsheet_config/06_cols_resumen_mensual_02.png))*

#### A. Columnas base (provenientes de Google Sheets)

| NAME | TYPE | KEY? | LABEL? | SHOW? | EDITABLE? | REQUIRE? | SEARCH? | DISPLAY NAME |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :--- |
| `_RowNumber` | `Number` | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | *(vacío)* |
| `ID_Empleado` | `Text` | ☑️ | ⬜ | ☑️ | ⬜ | ⬜ | ⬜ | `ID` |
| `Nombre_Empleado` | `Text` | ⬜ | ☑️ | ☑️ | ⬜ | ⬜ | ☑️ | `Empleado` |
| `Puntos_Factura` | `Number` | ⬜ | ⬜ | ☑️ | ⬜ | ⬜ | ⬜ | `Puntos Factura` |
| `Puntos_Esfuerzo` | `Number` | ⬜ | ⬜ | ☑️ | ⬜ | ⬜ | ⬜ | `Puntos Esfuerzo` |
| `Puntos_Totales` | `Number` | ⬜ | ⬜ | ☑️ | ⬜ | ⬜ | ⬜ | `Total Puntos` |
| `Bono_Productividad` | `Price` | ⬜ | ⬜ | ☑️ | ⬜ | ⬜ | ⬜ | `Bono Productividad` |
| `Total_Errores` | `Number` | ⬜ | ⬜ | ☑️ | ⬜ | ⬜ | ⬜ | `Total Errores` |
| `Bono_Calidad` | `Price` | ⬜ | ⬜ | ☑️ | ⬜ | ⬜ | ⬜ | `Bono Calidad` |
| `Total_Extra_A_Pagar` | `Price` | ⬜ | ⬜ | ☑️ | ⬜ | ⬜ | ⬜ | `Bono Neto` |

> **Ajustes internos (✏️):**
> * **Columnas monetarias (`Bono_Productividad`, `Bono_Calidad`, `Total_Extra_A_Pagar`):**
>   * **Type Details > Currency symbol:** `$`
>   * **Type Details > Decimal digits:** `0` *(ej. `$150.000`, sin centavos)*
>
> *(Nota: Todas las columnas se mantienen con EDITABLE? = FALSE y REQUIRE? = FALSE porque su cálculo es administrado en su totalidad por Google Sheets).*

#### B. Columnas virtuales de filtrado por período

*(Capturas: [08_modal_columna_virtual_01.png](../docs/images/appsheet_config/08_modal_columna_virtual_01.png), [08_modal_columna_virtual_02.png](../docs/images/appsheet_config/08_modal_columna_virtual_02.png))*

Estas columnas virtuales aseguran que al hacer clic en un empleado dentro del resumen semanal o mensual, la lista desplegable inferior filtre y muestre con exactitud los registros acotados a esa semana o mes seleccionados en `FILTRO_FECHAS`:

**1. En la tabla: `RESUMEN_SEMANAL` (`Registros_Semana`)**

Al final de la lista de columnas de `RESUMEN_SEMANAL`, clic en **`+ Add virtual column`**:

| NAME | TYPE | KEY? | LABEL? | SHOW? | EDITABLE? | REQUIRE? | SEARCH? | DISPLAY NAME |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :--- |
| `Registros_Semana` | `List` | ⬜ | ⬜ | ☑️ | ⬜ | ⬜ | ☑️ | `Registros Semanales` |

> **Ajustes internos (✏️):**
> * **App formula:**
>   ```plaintext
>   FILTER(
>     "REGISTRO_DIARIO",
>     AND(
>       [Empleado] = [_THISROW].[ID_Empleado],
>       DATE([Fecha_Hora]) >= ANY(FILTRO_FECHAS[Semana_Inicio]),
>       DATE([Fecha_Hora]) <= ANY(FILTRO_FECHAS[Semana_Fin])
>     )
>   )
>   ```
> * **Type Details > Element type:** `Ref`
> * **Type Details > Referenced table name:** `REGISTRO_DIARIO`
> * **Display > Display name:** `Registros Semanales`

**2. En la tabla: `RESUMEN_MENSUAL` (`Registros_Mes`)**

Al final de la lista de columnas de `RESUMEN_MENSUAL`, clic en **`+ Add virtual column`**:

| NAME | TYPE | KEY? | LABEL? | SHOW? | EDITABLE? | REQUIRE? | SEARCH? | DISPLAY NAME |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :--- |
| `Registros_Mes` | `List` | ⬜ | ⬜ | ☑️ | ⬜ | ⬜ | ☑️ | `Registros del Mes` |

> **Ajustes internos (✏️):**
> * **App formula:**
>   ```plaintext
>   FILTER(
>     "REGISTRO_DIARIO",
>     AND(
>       [Empleado] = [_THISROW].[ID_Empleado],
>       DATE([Fecha_Hora]) >= ANY(FILTRO_FECHAS[Mes_Inicio]),
>       DATE([Fecha_Hora]) <= ANY(FILTRO_FECHAS[Mes_Fin])
>     )
>   )
>   ```
> * **Type Details > Element type:** `Ref`
> * **Type Details > Referenced table name:** `REGISTRO_DIARIO`
> * **Display > Display name:** `Registros del Mes`

---

## 3. Configuración de Slices (Data > Slices)

*(Captura de referencia: [09_slice_registro_hoy.png](../docs/images/appsheet_config/09_slice_registro_hoy.png))*

Ir a **Data > Slices**. Se requiere crear un subconjunto de datos filtrado para mostrar únicamente los registros transaccionales del día en curso.

### Slice: `REGISTRO_HOY`

| Propiedad | Valor |
| :--- | :--- |
| **Slice name** | `REGISTRO_HOY` |
| **Source table** | `REGISTRO_DIARIO` |
| **Row filter condition** | `[Fecha_Hora] > TODAY()` |
| **Behavior** | Permite todas las operaciones permitidas en la tabla base (`Adds + Updates`). |

---

## 4. Configuración de Vistas (App > Views)

Ir a **App > Views**. La barra de navegación principal móvil tiene **4 accesos**:

| # | Nombre | Tipo | Posición | Tabla / Slice | Capturas de Referencia |
| :---: | :--- | :---: | :---: | :--- | :--- |
| 1 | `NUEVO REGISTRO` | `form` | `first` | `REGISTRO_DIARIO` | [10_view_nuevo_registro_01.png](../docs/images/appsheet_config/10_view_nuevo_registro_01.png) |
| 2 | `HISTORIAL HOY` | `table` | `middle` | `REGISTRO_HOY` (Slice) | [11_view_historial_hoy_01.png](../docs/images/appsheet_config/11_view_historial_hoy_01.png) |
| 3 | `RESUMEN` | `dashboard` | `middle` | `RESUMEN_SEMANAL` | [12_view_resumen_dashboard_01.png](../docs/images/appsheet_config/12_view_resumen_dashboard_01.png) |
| 4 | `SELECCIONE FECHA` | `detail` | `last` | `FILTRO_FECHAS` | [15_view_seleccione_fecha_01.png](../docs/images/appsheet_config/15_view_seleccione_fecha_01.png) |

---

### 4.1. Vista: `NUEVO REGISTRO`

*(Capturas: [10_view_nuevo_registro_01.png](../docs/images/appsheet_config/10_view_nuevo_registro_01.png), [10_view_nuevo_registro_02.png](../docs/images/appsheet_config/10_view_nuevo_registro_02.png), [10_view_nuevo_registro_03.png](../docs/images/appsheet_config/10_view_nuevo_registro_03.png))*

| Propiedad | Valor |
| :--- | :--- |
| **View name** | `NUEVO REGISTRO` |
| **For this data** | `REGISTRO_DIARIO` |
| **View type** | `form` |
| **Position** | `first` |
| **Column order** | `Automatic` *(renderiza Empleado, Numero_Factura, Puntos_Factura, Puntos_Esfuerzo, Puntos_Error)* |
| **Save / cancel position** | `Bottom` |
| **Finish view** | `REGISTRO_DIARIO_Form` *(al guardar, el formulario se recarga en blanco inmediatamente, listo para el siguiente despacho)* |
| **Display name** | *(vacío o `NUEVO REGISTRO`)* |
| **Icon** | `mobile-android` |

---

### 4.2. Vista: `HISTORIAL HOY`

*(Capturas: [11_view_historial_hoy_01.png](../docs/images/appsheet_config/11_view_historial_hoy_01.png), [11_view_historial_hoy_02.png](../docs/images/appsheet_config/11_view_historial_hoy_02.png), [11_view_historial_hoy_03.png](../docs/images/appsheet_config/11_view_historial_hoy_03.png))*

| Propiedad | Valor |
| :--- | :--- |
| **View name** | `HISTORIAL HOY` |
| **For this data** | `REGISTRO_HOY` (Slice que filtra los despachos del día actual) |
| **View type** | `table` |
| **Position** | `middle` |
| **Sort by** | `Fecha_Hora` — orden `Descending` |
| **Group aggregate** | `NONE` |
| **Column order** | **Manual** — agregar en este orden exacto:<br>1. `Numero_Factura`<br>2. `Empleado`<br>3. `Puntos_Factura`<br>4. `Puntos_Esfuerzo`<br>5. `Puntos_Error` |
| **Column width** | `Default` |
| **Display name** | *(vacío o `HISTORIAL HOY`)* |
| **Icon** | `history` |

---

### 4.3. Vista: `RESUMEN` (Dashboard)

Esta sección se estructura en 5 pasos. Las vistas secundarias de referencia (pasos 1 a 4) deben configurarse primero para alimentar el dashboard principal.

#### Paso 1 — Vista interna tabla semanal: `SEMANAL`

*(Capturas: [13_view_semanal_table_01.png](../docs/images/appsheet_config/13_view_semanal_table_01.png), [13_view_semanal_table_02.png](../docs/images/appsheet_config/13_view_semanal_table_02.png), [13_view_semanal_table_03.png](../docs/images/appsheet_config/13_view_semanal_table_03.png))*

| Propiedad | Valor |
| :--- | :--- |
| **View name** | `SEMANAL` |
| **For this data** | `RESUMEN_SEMANAL` |
| **View type** | `table` |
| **Position** | `ref` |
| **Column order** | **Manual** — agregar:<br>1. `Nombre_Empleado`<br>2. `Puntos_Totales`<br>3. `Total_Errores`<br>4. `Total_Extra_A_Pagar` |
| **Icon** | `list-ul` |

**Display name** *(fórmula dinámica — clic en el ícono de fórmula `fx`)*:
```
CONCATENATE(
  "SEMANAL (",
  TEXT(ANY(FILTRO_FECHAS[Fecha_Referencia]) - WEEKDAY(ANY(FILTRO_FECHAS[Fecha_Referencia])) + 2, "DD/MM/YYYY"),
  " al ",
  TEXT(ANY(FILTRO_FECHAS[Fecha_Referencia]) - WEEKDAY(ANY(FILTRO_FECHAS[Fecha_Referencia])) + 8, "DD/MM/YYYY"),
  ")"
)
```

#### Paso 2 — Vista detalle semanal: `RESUMEN_SEMANAL_Detail`

*(Capturas: [17_view_resumen_semanal_detail_01.png](../docs/images/appsheet_config/17_view_resumen_semanal_detail_01.png), [17_view_resumen_semanal_detail_02.png](../docs/images/appsheet_config/17_view_resumen_semanal_detail_02.png) — Ubicada en **SYSTEM GENERATED > RESUMEN_SEMANAL (1)**)*

| Propiedad | Valor |
| :--- | :--- |
| **View name** | `RESUMEN_SEMANAL_Detail` |
| **For this data** | `RESUMEN_SEMANAL` |
| **View type** | `detail` |
| **Position** | `ref` |
| **Display mode** | `Side-by-side` *(etiqueta a la izquierda, valor a la derecha)* |
| **Column order** | `Automatic` *(despliega las 10 columnas en orden natural: `Nombre_Empleado`, `ID_Empleado`, `Puntos_Factura`, `Puntos_Esfuerzo`, `Puntos_Totales`, `Bono_Productividad`, `Total_Errores`, `Bono_Calidad`, `Total_Extra_A_Pagar`, `Registros_Semana`)* |
| **Nested row display** | `5` |

#### Paso 3 — Vista interna tabla mensual: `MENSUAL`

*(Capturas: [14_view_mensual_table_01.png](../docs/images/appsheet_config/14_view_mensual_table_01.png), [14_view_mensual_table_02.png](../docs/images/appsheet_config/14_view_mensual_table_02.png), [14_view_mensual_table_03.png](../docs/images/appsheet_config/14_view_mensual_table_03.png))*

| Propiedad | Valor |
| :--- | :--- |
| **View name** | `MENSUAL` |
| **For this data** | `RESUMEN_MENSUAL` |
| **View type** | `table` |
| **Position** | `ref` |
| **Column order** | **Manual** — mismas 4 columnas que `SEMANAL`:<br>`Nombre_Empleado`, `Puntos_Totales`, `Total_Errores`, `Total_Extra_A_Pagar` |
| **Icon** | `list-ul` |

**Display name** *(fórmula dinámica)*:
```
CONCATENATE(
  "MENSUAL (",
  SWITCH(
    MONTH(ANY(FILTRO_FECHAS[Fecha_Referencia])),
    1, "Enero", 2, "Febrero", 3, "Marzo", 4, "Abril",
    5, "Mayo", 6, "Junio", 7, "Julio", 8, "Agosto",
    9, "Septiembre", 10, "Octubre", 11, "Noviembre", 12, "Diciembre",
    ""
  ),
  " ",
  YEAR(ANY(FILTRO_FECHAS[Fecha_Referencia])),
  ")"
)
```

#### Paso 4 — Vista detalle mensual: `RESUMEN_MENSUAL_Detail`

*(Ubicada en **SYSTEM GENERATED > RESUMEN_MENSUAL (1)**)*

Configuración análoga a `RESUMEN_SEMANAL_Detail`:
* **Display mode:** `Side-by-side`
* **Column order:** `Automatic` (despliega las métricas consolidadas del mes y la lista de despachos filtrados).
* **Nested row display:** `5`

#### Paso 5 — Dashboard principal: `RESUMEN`

*(Capturas: [12_view_resumen_dashboard_01.png](../docs/images/appsheet_config/12_view_resumen_dashboard_01.png), [12_view_resumen_dashboard_02.png](../docs/images/appsheet_config/12_view_resumen_dashboard_02.png))*

| Propiedad | Valor |
| :--- | :--- |
| **View name** | `RESUMEN` |
| **For this data** | `RESUMEN_SEMANAL` |
| **View type** | `dashboard` |
| **Position** | `middle` |
| **View entries** | 1. `SEMANAL` (`Large`)<br>2. `MENSUAL` (`Large`) |
| **Use tabs in mobile view** | `TRUE` *(activa las pestañas superiores para alternar fluidamente entre vista semanal y mensual en smartphones)* |
| **Interactive mode** | `FALSE` |
| **Display name** | *(vacío o `RESUMEN`)* |
| **Icon** | `list-alt` |

---

### 4.4. Vista: `SELECCIONE FECHA`

*(Capturas: [15_view_seleccione_fecha_01.png](../docs/images/appsheet_config/15_view_seleccione_fecha_01.png), [15_view_seleccione_fecha_02.png](../docs/images/appsheet_config/15_view_seleccione_fecha_02.png), [15_view_seleccione_fecha_03.png](../docs/images/appsheet_config/15_view_seleccione_fecha_03.png))*

| Propiedad | Valor |
| :--- | :--- |
| **View name** | `SELECCIONE FECHA` |
| **For this data** | `FILTRO_FECHAS` |
| **View type** | `detail` |
| **Position** | `last` |
| **Column order** | `Automatic` *(despliega las 5 columnas: `Fecha_Referencia`, `Semana_Inicio`, `Semana_Fin`, `Mes_Inicio`, `Mes_Fin`)* |
| **Display mode** | `Side-by-side` |
| **Quick edit columns** | `Fecha_Referencia` *(permite al usuario tocar el campo o selector de calendario y actualizar la fecha de referencia en tiempo real, recalculando automáticamente todas las vistas de resumen)* |
| **Desktop layout** | `Split view` |
| **Display name** | *(vacío o `SELECCIONE FECHA`)* |
| **Icon** | `calendar-day` |

---

### 4.5. Vista de sistema: `EMPLEADOS_Detail`

*(Capturas: [16_view_empleados_detail_01.png](../docs/images/appsheet_config/16_view_empleados_detail_01.png), [16_view_empleados_detail_02.png](../docs/images/appsheet_config/16_view_empleados_detail_02.png) — Ubicada en **SYSTEM GENERATED > EMPLEADOS (1)**)*

Se abre cuando el supervisor o usuario toca la flecha `>` en el campo `Empleado` dentro del detalle de cualquier despacho en `HISTORIAL HOY`.

| Propiedad | Valor |
| :--- | :--- |
| **View name** | `EMPLEADOS_Detail` |
| **For this data** | `EMPLEADOS` |
| **View type** | `detail` |
| **Position** | `ref` |
| **Column order** | `Automatic` *(al tener `Activo` con `SHOW? = FALSE`, AppSheet presenta de forma limpia: `Nombre_Completo`, `ID_Empleado` [ID], `Estado` [Activo? = SI/NO] y `Related REGISTRO_DIARIOs` [Historial de Despachos])* |
| **Display mode** | `Side-by-side` |
| **Nested row display** | `5` |

**Resultado visual en la app móvil:**
```
Nombre Completo    Empleado 3
ID                 1003
Activo?            SI

Historial de Despachos (9)
N° Factura   Empleado     Puntos Factura
FAC-73310    Empleado 3   5
FAC-65201    Empleado 3   2
...
```

---

## 5. Reglas de Comportamiento (App > Actions)

*(Captura: [18_action_bloqueo_15min.png](../docs/images/appsheet_config/18_action_bloqueo_15min.png))*

### Restricción de edición: tabla `REGISTRO_DIARIO`

Ir a **App > Actions > REGISTRO_DIARIO > acción del sistema `Edit`**.

* **Objetivo:** Garantizar la integridad y auditoría de la bodega, impidiendo que un operario modifique un despacho pasados 15 minutos de su creación.
* **Do this:** `App: edit this row`
* **Desktop behavior:** `Open a form`
* **Position:** `Primary`
* **Campo:** `Behavior > Only if this condition is true`
* **Condición:**
  ```
  TOTALMINUTES(NOW() - [Fecha_Hora]) <= 15
  ```
* **Efecto operativo:** El botón de edición (ícono de lápiz ✏️) permanece habilitado durante los primeros 15 minutos posteriores a la creación del registro. Cumplido este lapso, el sistema oculta automáticamente el botón, congelando el registro en modo Solo Lectura inalterable.

---

## 6. Reglas de Formato Condicional (App > Format Rules)

*(Capturas: [19_format_rules_lista_01.png](../docs/images/appsheet_config/19_format_rules_lista_01.png) a [19_format_rules_lista_08.png](../docs/images/appsheet_config/19_format_rules_lista_08.png))*

Ir a **App > Format Rules**. Existen 7 reglas activas configuradas para resaltar visualmente el desempeño y las alertas:

| Rule Name | For this data | Condition | Format these columns | Icon | Visual Format / Color |
| :--- | :--- | :--- | :--- | :---: | :--- |
| `EMPLEADO_INACTIVO` | `EMPLEADOS` | `[Activo] = FALSE` | `Nombre_Completo` | *(ninguno)* | Color de texto: `orange` + Estilo: *Cursiva (Italics)* |
| `PUNTOS_TOTALES_SEMANAL` | `RESUMEN_SEMANAL` | `[Puntos_Totales] > 0` | `Puntos_Totales` | *(ninguno)* | Color de texto: `blue` + Negrilla (Bold) |
| `ERRORES_TOTALES_SEMANAL` | `RESUMEN_SEMANAL` | `[Total_Errores] < 0` | `Total_Errores` | *(ninguno)* | Color de texto: `red` + Negrilla (Bold) |
| `BONOS_SEMANAL` | `RESUMEN_SEMANAL` | *(vacío / siempre activo)* | `Bono_Productividad`<br>`Bono_Calidad`<br>`Total_Extra_A_Pagar` | `money-bill` | Color de resalte (Highlight): `green` |
| `PUNTOS_TOTALES_MENSUAL` | `RESUMEN_MENSUAL` | `[Puntos_Totales] > 0` | `Puntos_Totales` | *(ninguno)* | Color de texto: `blue` + Negrilla (Bold) |
| `ERRORES_TOTALES_MENSUAL` | `RESUMEN_MENSUAL` | `[Total_Errores] < 0` | `Total_Errores` | *(ninguno)* | Color de texto: `red` + Negrilla (Bold) |
| `BONOS_MENSUAL` | `RESUMEN_MENSUAL` | *(vacío / siempre activo)* | `Bono_Productividad`<br>`Bono_Calidad`<br>`Total_Extra_A_Pagar` | `money-bill` | Color de resalte (Highlight): `green` |

---

## 7. Lista de Verificación Final

Antes del despliegue masivo o entrega a los operarios, cotejar cada punto contra la app real:

- [ ] **Google Sheets:** La celda `B2` de `FILTRO_FECHAS` contiene una fecha estática inicial sin fórmulas volátiles.
- [ ] **Google Sheets:** La celda `B2` de `CONFIGURACION` tiene la meta mínima de puntos (100) para otorgar el Bono de Calidad.
- [ ] **Slice `REGISTRO_HOY`:** Filtra con precisión `[Fecha_Hora] > TODAY()` para listar exclusivamente la jornada en curso.
- [ ] **Historial del Día:** La vista `HISTORIAL HOY` ordena los despachos de forma descendente (`Fecha_Hora`).
- [ ] **Detalle con Filtro de Período:** En el detalle de `RESUMEN_SEMANAL` o `RESUMEN_MENSUAL`, la lista desplegable inferior muestra los despachos acotados al período de la fecha seleccionada en `SELECCIONE FECHA`.
- [ ] **Columna `Estado`:** En el detalle del empleado muestra `"SI"` o `"NO"`.
- [ ] **Formulario:** `N° Factura` es obligatorio; los botones de puntos (`1` a `5`) y errores (`0` a `-3`) responden tácticamente.
- [ ] **Finish view:** Al guardar un despacho, el formulario se recarga automáticamente en blanco (`REGISTRO_DIARIO_Form`).
- [ ] **Restricción 15 min:** El lápiz ✏️ permite correcciones durante 15 minutos; transcurrido este tiempo desaparece.
- [ ] **Dashboard `RESUMEN`:** Navegación móvil por pestañas (`SEMANAL` y `MENSUAL`) con títulos dinámicos de rango de fechas.
- [ ] **Formato condicional:** Puntos en azul, errores en rojo, bonos con ícono `money-bill` verde, y empleados inactivos en naranja cursiva.
- [ ] **Empleado inactivo:** No figura en la lista desplegable de operarios al crear nuevos registros.
