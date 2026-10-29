# Configuración Técnica de AppSheet — Sistema de Bonificaciones Bodega (Versión 2.0)

> **Propósito:** Guía técnica exhaustiva paso a paso de toda la configuración aplicada directamente en el motor de AppSheet. Refleja fielmente la arquitectura optimizada V2.0 verificada contra las capturas reales de la aplicación (`docs/images/appsheet_config_v2/`), incluyendo la tabla centralizada `BASE_HISTORICA`, separación ergonómica de comprobantes (`Tipo_Factura` y teclado numérico), columna virtual `Hora`, y navegación nativa por drill-down temporal. Cualquier persona que retome este proyecto debe poder reproducir la configuración completa siguiendo este documento en orden.

---

## Tabla de Contenidos

1. [Permisos de Tablas (Data > Tables)](#1-permisos-de-tablas)
2. [Configuración de Columnas (Data > Columns)](#2-configuración-de-columnas)
   - 2.1. [Tabla EMPLEADOS](#21-tabla-empleados)
   - 2.2. [Tabla REGISTRO_DIARIO (Formulario Optimizado)](#22-tabla-registro_diario-formulario-optimizado)
   - 2.3. [Tabla BASE_HISTORICA (Motor de Liquidación)](#23-tabla-base_historica-motor-de-liquidación)
3. [Configuración de Slices (Data > Slices)](#3-configuración-de-slices)
4. [Configuración de Vistas (App > Views)](#4-configuración-de-vistas)
   - 4.1. [Vista NUEVO REGISTRO](#41-vista-nuevo-registro)
   - 4.2. [Vista HISTORIAL HOY](#42-vista-historial-hoy)
   - 4.3. [Vista LIQUIDACION (Drill-Down Jerárquico)](#43-vista-liquidacion-drill-down-jerárquico)
   - 4.4. [Vistas de Detalle del Sistema](#44-vistas-de-detalle-del-sistema)
5. [Ajustes Globales y Pantalla de Inicio (Settings)](#5-ajustes-globales-y-pantalla-de-inicio-settings)
6. [Reglas de Comportamiento (App > Actions)](#6-reglas-de-comportamiento-app--actions)
7. [Reglas de Formato Condicional (App > Format Rules)](#7-reglas-de-formato-condicional-app--format-rules)
8. [Matriz de Evolución: Versión 1.0 vs. Versión 2.0](#8-matriz-de-evolución-versión-10-vs-versión-20)
9. [Galería de Pantallas Operativas (Simulador y Celular)](#9-galería-de-pantallas-operativas-simulador-y-celular)
10. [Lista de Verificación Final](#10-lista-de-verificación-final)

---

## 1. Permisos de Tablas (Data > Tables)

*(Captura de referencia: [01_tables_permisos.png](../docs/images/appsheet_config_v2/01_tables_permisos.png))*

Ir a **Data > Tables**. Para cada tabla configurar la propiedad **Are updates allowed?**:

| Tabla | Permiso | Razón Operativa y de Seguridad |
| :--- | :--- | :--- |
| `EMPLEADOS` | `Read-only` | Catálogo maestro de personal. Solo el administrador o RRHH lo modifica desde Google Sheets. |
| `REGISTRO_DIARIO` | `Updates, Adds`<br>*(Deletes desmarcado)* | Registro transaccional en caliente. Prohibida la eliminación directa por política de auditoría. |
| `BASE_HISTORICA` | `Read-only` | Matriz histórica consolidada calculada automáticamente en Google Sheets (`LET` + `QUERY`). |

> **Nota de Arquitectura V2.0:**  
> Las tablas `FILTRO_FECHAS`, `RESUMEN_QUINCENAL` y `RESUMEN_MENSUAL` de la V1.0 fueron **retiradas y eliminadas**. Toda la auditoría quincenal y mensual histórica ahora es administrada en AppSheet de manera unificada y en tiempo real a través de `BASE_HISTORICA`. Las tablas auxiliares de Sheets `CONFIGURACION` y `LIQUIDACION_MES` no se cargan a AppSheet.

---

## 2. Configuración de Columnas (Data > Columns)

Ir a **Data > Columns**. La cuadrícula principal de AppSheet permite configurar directamente las propiedades estándar (`TYPE`, `KEY?`, `LABEL?`, `SHOW?`, `EDITABLE?`, `REQUIRE?`, `SEARCH?` y `DISPLAY NAME`).

El apartado **Ajustes internos** contiene las propiedades avanzadas accesibles al abrir el modal de edición de la columna (icono de lápiz en el editor), tales como `Auto Compute`, `Type Details` o reglas `Valid_If`.

---

### 2.1. Tabla: `EMPLEADOS`

*(Capturas: [02_cols_empleados_01.png](../docs/images/appsheet_config_v2/02_cols_empleados_01.png), [02_cols_empleados_02.png](../docs/images/appsheet_config_v2/02_cols_empleados_02.png))*

#### A. Columnas base (provenientes de Google Sheets)

| NAME | TYPE | KEY? | LABEL? | SHOW? | EDITABLE? | REQUIRE? | SEARCH? | DISPLAY NAME |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :--- |
| `_RowNumber` | `Number` | - | - | - | - | - | - | *(vacío)* |
| `ID_Empleado` | `Text` | Sí | - | Sí | - | - | - | `ID` |
| `Nombre_Completo` | `Text` | - | Sí | Sí | - | - | Sí | `Nombre Completo` |
| `Activo` | `Yes/No` | - | - | - | Sí | - | - | *(vacío)* |

> **Notas técnicas:**
> * `Activo` se mantiene con `SHOW? = FALSE` porque el estado operativo se expone a través de la columna virtual `Activo?`.
> * La relación del sistema `Related REGISTRO_DIARIOs` (`List` de `Ref`) tiene configurado como Display name: `Historial de Despachos` y `SEARCH? = TRUE`.

#### B. Columnas virtuales en `EMPLEADOS`

| NAME | TYPE | KEY? | LABEL? | SHOW? | EDITABLE? | REQUIRE? | SEARCH? | DISPLAY NAME |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :--- |
| `Activo?` | `Text` | - | - | Sí | - | - | Sí | `Activo?` |

> **Ajustes internos:**
> * **`Activo?`:**
>   * **App formula:** `IF([Activo], "SI", "NO")`
>
> **Saneamiento V2.0:** Se eliminaron las columnas virtuales `Despachos_Quincena` y `Despachos_Mes`. No son necesarias ya que las bonificaciones se liquidan por puntos y su cálculo generaba llamadas pesadas e incompatibilidad con el retiro de `FILTRO_FECHAS`.

---

### 2.2. Tabla: `REGISTRO_DIARIO` (Formulario Optimizado)

*(Capturas de columnas: [03_cols_registro_diario_01.png](../docs/images/appsheet_config_v2/03_cols_registro_diario_01.png), [03_cols_registro_diario_02.png](../docs/images/appsheet_config_v2/03_cols_registro_diario_02.png))*  
*(Modales: [05_modal_tipo_documento_01.png](../docs/images/appsheet_config_v2/05_modal_tipo_documento_01.png), [06_modal_col_hora_01.png](../docs/images/appsheet_config_v2/06_modal_col_hora_01.png), [07_modal_col_factura_completa_01.png](../docs/images/appsheet_config_v2/07_modal_col_factura_completa_01.png))*

Esta tabla transaccional implementa la separación ergonómica entre comprobante (`Tipo_Factura`) y número consecutivo (`Numero_Factura`), disparando el teclado numérico puro en el móvil, y agrega las columnas virtuales `Factura` (como `LABEL`) y `Hora`.

#### A. Columnas físicas (Google Sheets: 7 columnas)

| NAME | TYPE | KEY? | LABEL? | SHOW? | EDITABLE? | REQUIRE? | SEARCH? | INITIAL VALUE | DISPLAY NAME |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :--- | :--- |
| `_RowNumber` | `Number` | - | - | - | - | - | - | *(vacío)* | *(vacío)* |
| `ID_Registro` | `Text` | Sí | - | - | - | Sí | - | `UNIQUEID()` | *(vacío)* |
| `Fecha_Hora` | `DateTime` | - | - | - | - | - | - | `NOW()` | *(vacío)* |
| `Empleado` | `Ref` | - | - | Sí | Sí | Sí | Sí | *(vacío)* | `Empleado` |
| `Tipo_Factura` | `Enum` | - | - | Sí | Sí | - | - | *(vacío)* | `Tipo Factura` |
| `Numero_Factura` | `Number` | - | - | Sí | Sí | Sí | - | *(vacío)* | `N° Factura` |
| `Puntos_Esfuerzo` | `Enum` | - | - | Sí | Sí | Sí | - | *(vacío)* | `Puntos Esfuerzo` |
| `Puntos_Error` | `Enum` | - | - | Sí | Sí | Sí | - | `0` | `Puntos Error` |

#### B. Columnas virtuales en `REGISTRO_DIARIO`

| NAME | TYPE | KEY? | LABEL? | SHOW? | EDITABLE? | REQUIRE? | SEARCH? | FORMULA | DISPLAY NAME |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :--- | :--- |
| `Factura` | `Text` | - | Sí | Sí | - | - | Sí | `[Tipo_Factura] & "-" & [Numero_Factura]` | `Factura` |
| `Hora` | `Text` | - | - | Sí | - | - | Sí | `TEXT([Fecha_Hora], "H:MM AM/PM")` | `Hora` |

> **Ajustes internos de `REGISTRO_DIARIO`:**
> * **`ID_Registro`:**
>   * **Auto Compute > Initial value:** `UNIQUEID()`
>
> * **`Fecha_Hora`:**
>   * **Auto Compute > Initial value:** `NOW()` *(se autocalcula al guardar sin distraer al operario)*
>
> * **`Empleado`:**
>   * **Type Details > Source table:** `EMPLEADOS`
>   * **Data Validity > Valid_If:** `SELECT(EMPLEADOS[ID_Empleado], [Activo] = TRUE)` *(muestra únicamente personal activo en el desplegable)*
>
> * **`Tipo_Factura`:**
>   * **Type Details > Base type:** `Text`
>   * **Type Details > Input mode:** `Buttons`
>   * **Type Details > Values:** `IC, DP, IR`
>   * **Display Name:** `Tipo Factura`
>
> * **`Numero_Factura`:**
>   * **Type:** `Number` *(dispara automáticamente el teclado numérico directo en Android/iOS)*
>   * **Display Name:** `N° Factura`
>
> * **`Factura` (Columna Virtual):**
>   * **App formula:** `[Tipo_Factura] & "-" & [Numero_Factura]`
>   * **LABEL?**: `TRUE` *(identificador humano unificado en listados y detalles: ej. `DP-36278` o `IR-48351`)*
>   * **SEARCH?**: `TRUE`
>
> * **`Hora` (Columna Virtual):**
>   * **App formula:** `TEXT([Fecha_Hora], "H:MM AM/PM")`
>   * **SEARCH?**: `TRUE`
>   * *Se ubica en primer lugar en la tabla `HISTORIAL HOY` para agilizar la auditoría cronológica diaria.*
>
> * **Botonera de Puntaje de Despacho (`Puntos_Esfuerzo`):**
>   * **Type Details > Base type:** `Number`
>   * **Type Details > Input mode:** `Buttons`
>   * **Type Details > Values:** `1, 2, 3, 4, 5`
>   * **Display Name:** `Puntos Esfuerzo`
>
> * **Botonera de Penalizaciones (`Puntos_Error`):**
>   * **Type Details > Base type:** `Number`
>   * **Type Details > Input mode:** `Buttons`
>   * **Type Details > Values:** `0, -1, -2, -3`
>   * **Auto Compute > Initial value:** `0` *(por defecto el despacho no tiene error)*
>   * **Display Name:** `Puntos Error`

---

### 2.3. Tabla: `BASE_HISTORICA` (Motor de Liquidación)

*(Capturas de columnas: [04_cols_base_historica_01.png](../docs/images/appsheet_config_v2/04_cols_base_historica_01.png), [04_cols_base_historica_02.png](../docs/images/appsheet_config_v2/04_cols_base_historica_02.png))*  
*(Modal ID_Liquidacion: [08_modal_id_liquidacion_01.png](../docs/images/appsheet_config_v2/08_modal_id_liquidacion_01.png), [08_modal_id_liquidacion_02.png](../docs/images/appsheet_config_v2/08_modal_id_liquidacion_02.png))*

Esta tabla se alimenta de la hoja `BASE_HISTORICA` en Google Sheets (generada por la fórmula matricial `LET` + `QUERY` en segundo plano).

#### A. Columnas base (provenientes de Google Sheets: 10 columnas)

| NAME | TYPE | KEY? | LABEL? | SHOW? | EDITABLE? | REQUIRE? | SEARCH? | DISPLAY NAME |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :--- |
| `_RowNumber` | `Number` | - | - | - | - | - | - | *(vacío)* |
| `Año` | `Number` | - | - | Sí | - | - | Sí | *(vacío)* |
| `Mes` | `Number` | - | - | - | - | - | - | *(oculto: 1..12)* |
| `Quincena` | `Text` | - | - | - | - | - | - | *(oculto: Q1/Q2)* |
| `ID_Empleado` | `Number` | - | - | Sí | - | - | - | `ID` |
| `Nombre` | `Text` | - | Sí | Sí | - | - | Sí | `Nombre` |
| `Pts_Esfuerzo` | `Number` | - | - | Sí | - | - | - | `Puntos Esfuerzo` |
| `Pts_Error` | `Number` | - | - | Sí | - | - | - | `Puntos Error` |
| `Bono Productivo` | `Price` | - | - | Sí | - | - | - | *(vacío)* |
| `Bono Calidad` | `Price` | - | - | Sí | - | - | - | *(vacío)* |
| `Total BONO` | `Price` | - | - | Sí | - | - | - | *(vacío)* |

#### B. Columnas virtuales en `BASE_HISTORICA`

| NAME | TYPE | KEY? | LABEL? | SHOW? | EDITABLE? | REQUIRE? | SEARCH? | FORMULA | DISPLAY NAME |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :--- | :--- |
| `ID_Liquidacion` | `Text` | Sí | - | Sí | - | - | - | `CONCATENATE([Año], "-", [Mes], "-", [Quincena], "-", [ID_Empleado])` | *(vacío)* |
| `Mes_Nombre` | `Text` | - | - | Sí | - | - | Sí | `SWITCH([Mes], 1, "Enero", 2, "Febrero", ..., 12, "Diciembre", "")` | `"Mes"` |
| `Quincena_Nombre` | `Text` | - | - | Sí | - | - | Sí | `IF([Quincena] = "Q1", "1ra Quincena", "2da Quincena") & " · " & [Mes_Nombre] & " " & [Año]` | `Quincena` |

> **Ajustes internos de `BASE_HISTORICA`:**
> * **`ID_Liquidacion` (Clave Primaria Virtual):**
>   * **App formula:** `CONCATENATE([Año], "-", [Mes], "-", [Quincena], "-", [ID_Empleado])`
>   * **KEY?**: `TRUE` *(garantiza un identificador único por colaborador y quincena)*
>   * **SHOW?**: `TRUE`
>
> * **`Año`:**
>   * **Type Details > Show thousands separator:** `FALSE` *(evita mostrar `2,026` con coma)*
>   * **SEARCH?**: `TRUE`
>
> * **`Mes_Nombre` (Columna Virtual):**
>   * **Display Name:** `"Mes"`
>   * **SEARCH?**: `TRUE`
>   * **App formula:**
>     ```appsheet
>     SWITCH(
>       [Mes],
>       1, "Enero", 2, "Febrero", 3, "Marzo", 4, "Abril",
>       5, "Mayo", 6, "Junio", 7, "Julio", 8, "Agosto",
>       9, "Septiembre", 10, "Octubre", 11, "Noviembre", 12, "Diciembre",
>       ""
>     )
>     ```
>
> * **`Quincena_Nombre` (Columna Virtual):**
>   * **Display Name:** `Quincena`
>   * **SEARCH?**: `TRUE`
>   * **App formula:**
>     ```appsheet
>     IF([Quincena] = "Q1", "1ra Quincena", "2da Quincena") & " · " & [Mes_Nombre] & " " & [Año]
>     ```
>   * *Produce encabezados legibles: `1ra Quincena · Octubre 2026` o `2da Quincena · Octubre 2026`.*
>
> * **Columnas Monetarias (`Bono Productivo`, `Bono Calidad`, `Total BONO`):**
>   * **Type Details > Currency symbol:** `$`
>   * **Type Details > Decimal digits:** `0` *(ej. `$300.000`)*
>
> * **Columnas `EDITABLE?`:** Todas en `FALSE` *(datos calculados por el motor de hoja de cálculo)*.

---

## 3. Configuración de Slices (Data > Slices)

*(Captura de referencia: [09_slice_registro_hoy.png](../docs/images/appsheet_config_v2/09_slice_registro_hoy.png))*

Ir a **Data > Slices**. Se utiliza un único slice para filtrar en tiempo real los despachos de la jornada:

### Slice: `REGISTRO_HOY`

| Propiedad | Valor |
| :--- | :--- |
| **Slice name** | `REGISTRO_HOY` |
| **Source table** | `REGISTRO_DIARIO` |
| **Row filter condition** | `[Fecha_Hora] > TODAY()` |
| **Slice actions** | `Auto assign` |
| **Update mode** | `Updates`, `Adds` (`Deletes` desmarcado) |

---

## 4. Configuración de Vistas (App > Views)

La barra de navegación principal móvil consta de **3 vistas limpias y directas ordenadas por la propiedad Position**:

| # | Nombre de Vista | Tipo | Posición (`Position`) | Tabla / Slice | Icono |
| :---: | :--- | :---: | :---: | :--- | :--- |
| 1 | `NUEVO REGISTRO` | `form` | `first` | `REGISTRO_DIARIO` | `mobile-android` |
| 2 | `HISTORIAL HOY` | `table` | `middle` | `REGISTRO_HOY` (Slice) | `history` |
| 3 | `LIQUIDACION` | `table` | `last` | `BASE_HISTORICA` | `file-invoice` |

---

### 4.1. Vista: `NUEVO REGISTRO`

*(Capturas: [10_view_nuevo_registro_01.png](../docs/images/appsheet_config_v2/10_view_nuevo_registro_01.png), [10_view_nuevo_registro_02.png](../docs/images/appsheet_config_v2/10_view_nuevo_registro_02.png), [10_view_nuevo_registro_03.png](../docs/images/appsheet_config_v2/10_view_nuevo_registro_03.png))*

| Propiedad | Configuración | Justificación / Comportamiento |
| :--- | :--- | :--- |
| **View name** | `NUEVO REGISTRO` | Nombre de la vista en el editor. |
| **For this data** | `REGISTRO_DIARIO` | Tabla transaccional de captura. |
| **View type** | `form` | Formulario de captura. |
| **Position** | `first` | Primer botón en la barra de navegación inferior. |
| **Page style** | `Automatic` | Flujo estándar de formulario. |
| **Form style** | `Side-by-side` | **Escritorio:** Muestra etiquetas al lado de los campos para mayor compactación.<br>**Celular:** Se adapta verticalmente mostrando la etiqueta arriba y el campo o botonera debajo. |
| **Column order** | `Automatic` | Renderiza de forma natural los campos editables (`Empleado`, `Tipo_Factura`, `Numero_Factura`, `Puntos_Esfuerzo`, `Puntos_Error`). |
| **Save / cancel position** | `Bottom` | Botones de confirmación al pie de pantalla. |
| **Auto re-open** | `ON` | El formulario se recarga automáticamente tras guardar para agilizar la captura masiva sin salir de la vista. |
| **Finish view** | `Auto assign (Go Back)` | Al pulsar Cancel regresa a la vista previa. |
| **Icon** | `mobile-android` | Ícono del menú inferior. |

---

### 4.2. Vista: `HISTORIAL HOY`

*(Capturas: [11_view_historial_hoy_01.png](../docs/images/appsheet_config_v2/11_view_historial_hoy_01.png), [11_view_historial_hoy_02.png](../docs/images/appsheet_config_v2/11_view_historial_hoy_02.png))*

| Propiedad | Configuración |
| :--- | :--- |
| **View name** | `HISTORIAL HOY` |
| **For this data** | `REGISTRO_HOY` (Slice de despachos de hoy) |
| **View type** | `table` |
| **Position** | `middle` |
| **Sort by** | `Fecha_Hora` — orden `Descending` *(los despachos más recientes aparecen arriba)* |
| **Group aggregate** | `NONE` |
| **Column order** | **Manual** — en este orden exacto:<br>1. `Hora`<br>2. `Factura`<br>3. `Empleado`<br>4. `Puntos_Esfuerzo`<br>5. `Puntos_Error` |
| **Column width** | `Wide` *(asegura que las columnas de hora, factura y operario no se trunquen)* |
| **Icon** | `history` |

---

### 4.3. Vista: `LIQUIDACION` (Drill-Down Jerárquico)

*(Capturas: [12_view_liquidacion_01.png](../docs/images/appsheet_config_v2/12_view_liquidacion_01.png), [12_view_liquidacion_02.png](../docs/images/appsheet_config_v2/12_view_liquidacion_02.png))*

Esta vista reemplaza completamente los antiguos dashboards quincenales y mensuales, permitiendo consultar cualquier período de la historia con navegación táctil nativa.

| Propiedad | Configuración |
| :--- | :--- |
| **View name** | `LIQUIDACION` |
| **For this data** | `BASE_HISTORICA` |
| **View type** | `table` |
| **Position** | `last` |
| **Group by** | 1. `Año` — `Descending`<br>2. `Mes_Nombre` — `Descending`<br>3. `Quincena_Nombre` — `Ascending` |
| **Sort by** | `Pts_Esfuerzo` — `Descending` *(ordena a los colaboradores de mayor a menor esfuerzo en la quincena)* |
| **Group aggregate** | `NONE` |
| **Column order** | **Manual**:<br>1. `Nombre`<br>2. `Pts_Esfuerzo`<br>3. `Pts_Error`<br>4. `Total BONO` |
| **Column width** | `Wide` *(despliegue amplio y cómodo de los nombres y valores monetarios)* |
| **Icon** | `file-invoice` |

> **Comportamiento UX en Celular (Drill-Down Progresivo):**
> 1. En la pantalla móvil de ancho reducido, AppSheet presenta inicialmente el primer nivel de agrupación: **Año** (ej. `2026`).
> 2. Al tocar el año, la aplicación profundiza al segundo nivel: **Mes** (ej. `Octubre`).
> 3. Al tocar el mes, se abre la tabla quincenal segmentada por `1ra Quincena` y `2da Quincena`, mostrando cada colaborador ordenado de mayor a menor esfuerzo con sus puntos y su bono neto.
> 4. Al estar en la tabla final, la lupa de búsqueda permite filtrar instantáneamente por nombre de colaborador.
> *(En escritorio o tablet, la vista muestra la tabla completa con el árbol jerárquico desplegado).*

---

### 4.4. Vistas de Detalle del Sistema

#### A. Vista de detalle: `BASE_HISTORICA_Detail`
*(Capturas: [13_view_base_historica_detail_01.png](../docs/images/appsheet_config_v2/13_view_base_historica_detail_01.png), [13_view_base_historica_detail_02.png](../docs/images/appsheet_config_v2/13_view_base_historica_detail_02.png))*

Se abre al tocar cualquier colaborador dentro de la tabla de liquidación:
* **View type:** `detail`
* **Header columns:** Ninguna (`None` / desmarcado) *(elimina la tarjeta gigante repetitiva superior)*.
* **Display name (Fórmula dinámica):** `[Quincena_Nombre]` *(ubica el período directamente en la barra de navegación superior o miga de pan: ej. `1ra Quincena · Octubre 2026`)*.
* **Display mode:** `Side-by-side`
* **Column order:** `Automatic` (renderiza `Nombre`, `ID_Empleado`, `Pts_Esfuerzo`, `Pts_Error`, `Bono Productivo`, `Bono Calidad`, `Total BONO`).

---

## 5. Ajustes Globales y Pantalla de Inicio (Settings)

*(Captura de referencia: [09b_settings_starting_view.png](../docs/images/appsheet_config_v2/09b_settings_starting_view.png))*

Para garantizar la máxima agilidad operativa en los teléfonos de bodega:

1. Ir a **Settings > Views > General**:
   * **Starting view:** Seleccionar `NUEVO REGISTRO`.
   * **Propósito:** Cada vez que el despachador abre la app en el celular o la recarga, el sistema se posiciona directamente en el formulario listo para digitar el siguiente despacho sin clics adicionales.
2. Ir a **Settings > Theme & Brand**:
   * **Primary color:** Azul corporativo (`#1A73E8`).
   * **App Name:** `BONIFICACIONES`.

---

## 6. Reglas de Comportamiento (App > Actions)

*(Captura de referencia: [14_action_bloqueo_15min.png](../docs/images/appsheet_config_v2/14_action_bloqueo_15min.png))*

### Restricción de edición a 15 minutos: tabla `REGISTRO_DIARIO`

Ir a **App > Actions > REGISTRO_DIARIO > acción del sistema `Edit`**:

* **Objetivo:** Permitir corrección inmediata de errores tipográficos en bodega sin comprometer la auditoría posterior.
* **Do this:** `App: edit this row`
* **Desktop behavior:** `Open a form`
* **Position:** `Primary`
* **Behavior > Only if this condition is true:**
  ```appsheet
  TOTALMINUTES(NOW() - [Fecha_Hora]) <= 15
  ```
* **Efecto operativo:** El icono de lápiz permanece activo durante los primeros 15 minutos de creado el registro. Tras cumplirse este tiempo, el sistema oculta automáticamente el botón de edición, congelando la fila de manera inalterable.

---

## 7. Reglas de Formato Condicional (App > Format Rules)

*(Capturas: [15_format_rules_lista.png](../docs/images/appsheet_config_v2/15_format_rules_lista.png), [16_format_rule_bonos.png](../docs/images/appsheet_config_v2/16_format_rule_bonos.png))*

Ir a **App > Format Rules**. Existen **3 reglas activas** configuradas para la tabla `BASE_HISTORICA`:

| Rule Name | For this data | Format these columns | Condition (Fórmula de Activación) | Formato Visual / Resalte |
| :--- | :--- | :--- | :--- | :--- |
| **`Puntos`** | `BASE_HISTORICA` | `Pts_Esfuerzo` | `[Pts_Esfuerzo] >= 300` | Text Color: `#1A73E8` (Azul) + Negrilla (`Bold = TRUE`) |
| **`Errores`** | `BASE_HISTORICA` | `Pts_Error` | `[Pts_Error] < 0` | Text Color: `#D93025` (Rojo) + Negrilla (`Bold = TRUE`) |
| **`Bonos`** | `BASE_HISTORICA` | `Bono Productivo`, `Bono Calidad`, `Total BONO` | `[Total BONO] > 0` | Ícono: `usd-circle` con Highlight Color `#188038` (Verde) + Número en Negrilla (`Bold = TRUE`) con color de texto base |

> **Comportamiento Verificado en Pantalla Real:**  
> Gracias a la condición `[Total BONO] > 0`, en la tabla quincenal solo reciben el ícono `usd-circle` verde y la negrilla los colaboradores que efectivamente ganaron dinero (ej. Edward Sanchez con `$300.000`). Quienes tienen `$0` se muestran limpios sin ícono de dinero.

---

## 8. Matriz de Evolución: Versión 1.0 vs. Versión 2.0

Para fines de trazabilidad y auditoría de desarrollo, la siguiente matriz sintetiza los cambios estructurales aplicados al sistema:

| Componente | Versión 1.0 (Anterior) | Versión 2.0 (Actual Optimizada) | Justificación Técnica del Cambio |
| :--- | :--- | :--- | :--- |
| **Captura de Factura** | Un solo campo de texto `Numero_Factura` (`Text`). Digitaba `IR-12345` a mano. | Separación en `Tipo_Factura` (`Enum` botones) + `Numero_Factura` (`Number`). | Activa el teclado numérico puro en el celular, reduciendo tiempos y errores en bodega. |
| **LABEL de Registro** | `Numero_Factura` como LABEL físico. | Columna virtual `Factura` (`[Tipo_Factura] & "-" & [Numero_Factura]`). | Resuelve ambigüedad visual en registros que compartan número pero diferente tipo (`IR-100` vs `IC-100`). |
| **Columna Virtual `Hora`** | No existía (solo `Fecha_Hora` completa oculta). | `TEXT([Fecha_Hora], "H:MM AM/PM")` mostrada de primera en `HISTORIAL HOY`. | Permite a Luis y los despachadores revisar cronológicamente los despachos del día de un vistazo. |
| **Estilo de Formulario** | `Standard` vertical extenso. | `Form style = Side-by-side`. | Compacto en altura en pantalla de escritorio; adaptación táctil fluida en celular. |
| **Ancho de Columnas** | `Default`. | `Column width = Wide` en todas las tablas. | Evita el truncamiento de textos en nombres, números de factura y valores en pesos. |
| **Orden en Liquidación** | Por nombre alfabético. | `Sort by = Pts_Esfuerzo` (`Descending`). | Destaca en los primeros lugares a los colaboradores con mayor productividad quincenal. |
| **Icono de Liquidación** | `list-alt` / `calculator`. | `file-invoice`. | Identidad gráfica alineada al concepto de comprobante y pago de nómina. |
| **Tablas Satélites de Resumen** | `RESUMEN_QUINCENAL` y `RESUMEN_MENSUAL` calculadas por fórmulas estáticas en Sheets. | **Retiradas**. Reemplazadas por la tabla única `BASE_HISTORICA`. | Elimina redundancia, desincronización y hojas intermedias frágiles. |
| **Control de Fechas** | Tabla física `FILTRO_FECHAS` que obligaba a tocar un calendario interactivo. | **Retirada**. Drill-down nativo por `Año > Mes > Quincena` en AppSheet. | Elimina la necesidad de cambiar celdas de control. Historial perpetuo navegable con un toque. |
| **Rendimiento de `EMPLEADOS`** | Columnas virtuales `Despachos_Quincena` y `Despachos_Mes` con `COUNT(FILTER(...))`. | **Retiradas**. Se conserva solo `Activo?`. | Acelera drásticamente la sincronización móvil al eliminar consultas circulares sobre fechas. |
| **Estructura de Vistas** | 4 accesos: Nuevo Registro, Historial Hoy, Resumen (Dashboard) y Seleccione Fecha. | 3 accesos: `NUEVO REGISTRO` (`first`), `HISTORIAL HOY` (`middle`) y `LIQUIDACION` (`last`). | Interfaz minimalista y enfocada, reduciendo la carga cognitiva del usuario. |
| **Pantalla de Inicio** | Abría por defecto en la vista predeterminada de navegación. | `Starting view = NUEVO REGISTRO` configurado en `Settings > Views > General`. | Al abrir la app, entra directamente al formulario de despacho para agilidad total. |

---

## 9. Galería de Pantallas Operativas (Simulador y Celular)

Las siguientes capturas corresponden al funcionamiento real de la aplicación en los dispositivos móviles de bodega:

* **Formulario de Despacho:** [17_app_pantalla_formulario.jpg](../docs/images/appsheet_config_v2/17_app_pantalla_formulario.jpg) — Captura del formulario en Android con botonera de `Tipo Factura` (`IC`, `DP`, `IR`), consecutivo numérico y selectores de puntos y penalizaciones.
* **Historial Diario en Vivo:** [18_app_pantalla_historial.jpg](../docs/images/appsheet_config_v2/18_app_pantalla_historial.jpg) — Tabla `HISTORIAL HOY` mostrando despachos ordenados por hora (`12:57 p. m.`), código de factura concatenado (`DP-36278`, `IR-48351`) y operario.
* **Navegación Drill-Down:** [19_app_pantalla_liquidacion_mes.jpg](../docs/images/appsheet_config_v2/19_app_pantalla_liquidacion_mes.jpg) — Pantalla de selección de Mes (`Octubre >`).
* **Tabla Quincenal Consolidada:** [20_app_pantalla_liquidacion_tabla_01.jpg](../docs/images/appsheet_config_v2/20_app_pantalla_liquidacion_tabla_01.jpg), [20_app_pantalla_liquidacion_tabla_02.jpg](../docs/images/appsheet_config_v2/20_app_pantalla_liquidacion_tabla_02.jpg) — Tabla final dividida por quincenas (`1ra Quincena · Octubre 2026` y `2da Quincena · Octubre 2026`), ordenando colaboradores por puntos de esfuerzo y resaltando en verde con ícono `usd-circle` a quienes superaron la meta (`Edward Sanchez: 455 pts -> $300.000`).

---

## 10. Lista de Verificación Final

Antes del despliegue masivo en bodega, cotejar cada punto contra la app real en AppSheet:

- [ ] **Hoja `BASE_HISTORICA`:** Contiene en `A1` la fórmula matricial `LET` + `QUERY` generando Año, Mes, Quincena, ID_Empleado, Puntos y Errores; y de `G1` a `J1` las columnas de nombres y liquidación en pesos ($).
- [ ] **Hoja `CONFIGURACION`:** Celda `B3` tiene la Meta Base Quincenal (300 pts) y la matriz de bonos por tramos calibrada.
- [ ] **Formulario de Registro (`NUEVO REGISTRO`):**
  - Configurado en `Position = first` y con `Form style = Side-by-side`.
  - `Tipo_Factura` despliega botones táctiles (`IC`, `DP`, `IR`).
  - `Numero_Factura` despliega el teclado numérico del teléfono.
  - `Factura` aparece como título representativo (`LABEL`) en listas e historial.
  - `Auto re-open = ON` mantiene el formulario listo en blanco tras pulsar "Save".
- [ ] **Apertura de la App:** Al iniciar la aplicación, abre directamente en el formulario de `NUEVO REGISTRO` (`Starting view`).
- [ ] **Historial del Día (`HISTORIAL HOY`):**
  - Configurado en `Position = middle` y con `Column width = Wide`.
  - Ordenado por `Fecha_Hora` descendente.
  - Columnas ordenadas: `Hora`, `Factura`, `Empleado`, `Puntos_Esfuerzo`, `Puntos_Error`.
  - Botón de edición (lápiz) desaparece automáticamente tras 15 minutos de creado el registro.
- [ ] **Vista `LIQUIDACION`:**
  - Configurada en `Position = last`, icono `file-invoice` y con `Column width = Wide`.
  - Ordenada por `Pts_Esfuerzo` descendente (de mayor a menor esfuerzo).
  - En celular navega fluidamente por drill-down: `Año` $\rightarrow$ `Mes` $\rightarrow$ Tabla quincenal.
  - La tabla quincenal muestra únicamente `Nombre`, `Pts_Esfuerzo`, `Pts_Error` y `Total BONO`.
- [ ] **Detalle de Colaborador:**
  - Al presionar una fila en `LIQUIDACION`, el encabezado grande desaparece (`Header columns = None`).
  - La miga de pan o barra de título muestra claramente la quincena consultada (`Display name = [Quincena_Nombre]`).
  - Muestra el desglose de `Bono Productivo`, `Bono Calidad` y `Total BONO` en formato moneda ($) sin decimales.
- [ ] **Format Rules (`BASE_HISTORICA`):**
  - **`Puntos`:** `[Pts_Esfuerzo] >= 300` con texto azul `#1A73E8` y negrilla.
  - **`Errores`:** `[Pts_Error] < 0` con texto rojo `#D93025` y negrilla.
  - **`Bonos`:** Condición `[Total BONO] > 0` con icono `usd-circle` verde `#188038` y negrilla en color base.
- [ ] **Colaboradores Inactivos:** No figuran en el desplegable de operarios al ingresar nuevos registros (`Valid_If`).
