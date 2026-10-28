# Configuración Técnica de AppSheet — Sistema de Bonificaciones Bodega (Versión 2.0)

> **Propósito:** Guía técnica exhaustiva paso a paso de toda la configuración aplicada directamente en el motor de AppSheet. Refleja la arquitectura optimizada V2.0 basada en la tabla centralizada `BASE_HISTORICA`, separación ergonómica de comprobantes (`Tipo_Documento` y teclado numérico), columna virtual `Hora`, y navegación nativa por drill-down temporal. Cualquier persona que retome este proyecto debe poder reproducir la configuración completa siguiendo este documento en orden.

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
   - 4.3. [Vista LIQUIDACIÓN (Drill-Down Jerárquico)](#43-vista-liquidación-drill-down-jerárquico)
   - 4.4. [Vistas de Detalle del Sistema](#44-vistas-de-detalle-del-sistema)
5. [Ajustes Globales y Pantalla de Inicio (Settings)](#5-ajustes-globales-y-pantalla-de-inicio-settings)
6. [Reglas de Comportamiento (App > Actions)](#6-reglas-de-comportamiento-app--actions)
7. [Reglas de Formato Condicional (App > Format Rules)](#7-reglas-de-formato-condicional-app--format-rules)
8. [Matriz de Evolución: Versión 1.0 vs. Versión 2.0](#8-matriz-de-evolución-versión-10-vs-versión-20)
9. [Lista de Verificación Final](#9-lista-de-verificación-final)

---

## 1. Permisos de Tablas (Data > Tables)

Ir a **Data > Tables**. Para cada tabla configurar la propiedad **Are updates allowed?**:

| Tabla | Permiso | Razón Operativa y de Seguridad |
| :--- | :--- | :--- |
| `EMPLEADOS` | `Read_Only` | Catálogo maestro de personal. Solo el administrador o RRHH lo modifica desde Google Sheets. |
| `REGISTRO_DIARIO` | `Adds + Updates`<br>*(Delete desmarcado)* | Registro transaccional en caliente. Prohibida la eliminación directa por política de auditoría. |
| `BASE_HISTORICA` | `Read_Only` | Matriz histórica consolidada calculada automáticamente en Google Sheets (`LET` + `QUERY`). |

> **Nota de Arquitectura V2.0:**  
> Las tablas `FILTRO_FECHAS`, `RESUMEN_QUINCENAL` y `RESUMEN_MENSUAL` de la V1.0 fueron **retiradas y eliminadas**. Toda la auditoría quincenal y mensual histórica ahora es administrada en AppSheet de manera unificada y en tiempo real a través de `BASE_HISTORICA`.

---

## 2. Configuración de Columnas (Data > Columns)

Ir a **Data > Columns**. La cuadrícula principal de AppSheet permite configurar directamente las propiedades estándar (`TYPE`, `KEY?`, `LABEL?`, `SHOW?`, `EDITABLE?`, `REQUIRE?`, `SEARCH?` y `DISPLAY NAME`).

El apartado **Ajustes internos** contiene las propiedades avanzadas accesibles al abrir el modal de edición de la columna (icono de lápiz en el editor), tales como `Auto Compute`, `Type Details` o reglas `Valid_If`.

---

### 2.1. Tabla: `EMPLEADOS`

#### A. Columnas base (provenientes de Google Sheets)

| NAME | TYPE | KEY? | LABEL? | SHOW? | EDITABLE? | REQUIRE? | SEARCH? | DISPLAY NAME |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :--- |
| `_RowNumber` | `Number` | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | *(vacío)* |
| `ID_Empleado` | `Text` | ☑️ | ⬜ | ☑️ | ⬜ | ⬜ | ⬜ | `ID` |
| `Nombre_Completo` | `Text` | ⬜ | ☑️ | ☑️ | ⬜ | ⬜ | ☑️ | `Nombre Completo` |
| `Activo` | `Yes/No` | ⬜ | ⬜ | ⬜ | ☑️ | ⬜ | ⬜ | *(vacío)* |

> **Notas técnicas:**
> * `Activo` se mantiene con `SHOW? = FALSE` porque el estado operativo se expone a través de la columna virtual `Activo?`.
> * La relación del sistema `Related REGISTRO_DIARIOs` (`List` de `Ref`) tiene configurado como Display name: `Historial de Despachos`.

#### B. Columnas virtuales en `EMPLEADOS`

Se crea en AppSheet mediante el botón **`+ Add virtual column`** al final de la tabla:

| NAME | TYPE | KEY? | LABEL? | SHOW? | EDITABLE? | REQUIRE? | SEARCH? | DISPLAY NAME |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| `Activo?` | `Text` | ⬜ | ⬜ | ☑️ | ⬜ | ⬜ | ☑️ | `Activo?` |

> **Ajustes internos:**
> * **`Activo?`:**
>   * **App formula:** `IF([Activo], "SI", "NO")`
>
> **Saneamiento V2.0:** Se eliminaron las columnas virtuales `Despachos_Quincena` y `Despachos_Mes`. No son necesarias ya que las bonificaciones se liquidan por puntos y su cálculo generaba llamadas pesadas e incompatibilidad con el retiro de `FILTRO_FECHAS`.

---

### 2.2. Tabla: `REGISTRO_DIARIO` (Formulario Optimizado)

Esta tabla transaccional implementa la separación ergonómica entre comprobante y número consecutivo, disparando el teclado numérico puro en el móvil, y agrega la columna virtual de hora para auditoría inmediata.

#### A. Columnas físicas (Google Sheets: 7 columnas)

| NAME | TYPE | KEY? | LABEL? | SHOW? | EDITABLE? | REQUIRE? | SEARCH? | DISPLAY NAME |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :--- |
| `_RowNumber` | `Number` | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | *(vacío)* |
| `ID_Registro` | `Text` | ☑️ | ⬜ | ⬜ | ⬜ | ☑️ | ⬜ | *(vacío)* |
| `Fecha_Hora` | `DateTime` | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | *(vacío)* |
| `Empleado` | `Ref` | ⬜ | ⬜ | ☑️ | ☑️ | ☑️ | ☑️ | `Empleado` |
| `Tipo_Documento` | `Enum` | ⬜ | ⬜ | ☑️ | ☑️ | ☑️ | ⬜ | `Tipo Comprobante` |
| `Numero_Factura` | `Number` | ⬜ | ⬜ | ☑️ | ☑️ | ☑️ | ☑️ | `N° Consecutivo` |
| `Puntos_Esfuerzo` | `Enum` | ⬜ | ⬜ | ☑️ | ☑️ | ☑️ | ⬜ | `Puntaje Despacho` |
| `Puntos_Error` | `Enum` | ⬜ | ⬜ | ☑️ | ☑️ | ☑️ | ⬜ | `Puntos Error` |

#### B. Columnas virtuales en `REGISTRO_DIARIO`

| NAME | TYPE | KEY? | LABEL? | SHOW? | EDITABLE? | REQUIRE? | SEARCH? | DISPLAY NAME |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :--- |
| `Factura_Completa` | `Text` | ⬜ | ☑️ | ☑️ | ⬜ | ⬜ | ☑️ | `Factura` |
| `Hora` | `Text` | ⬜ | ⬜ | ☑️ | ⬜ | ⬜ | ⬜ | `Hora` |

> **Ajustes internos:**
> * **`ID_Registro`:**
>   * **Auto Compute > Initial value:** `UNIQUEID()`
>
> * **`Fecha_Hora`:**
>   * **Auto Compute > Initial value:** `NOW()` *(se autocalcula al guardar sin distraer al operario)*
>
> * **`Hora` (Columna Virtual):**
>   * **App formula:** `TEXT([Fecha_Hora], "H:MM AM/PM")`
>   * **SHOW?**: `TRUE` *(se ubica de primera en la tabla `HISTORIAL HOY` para facilitar el seguimiento cronológico)*
>
> * **`Empleado`:**
>   * **Type Details > Source table:** `EMPLEADOS`
>   * **Data Validity > Valid_If:** `SELECT(EMPLEADOS[ID_Empleado], [Activo] = TRUE)` *(muestra únicamente personal activo en el desplegable)*
>
> * **`Tipo_Documento`:**
>   * **Type Details > Base type:** `Text`
>   * **Type Details > Input mode:** `Buttons`
>   * **Type Details > Values:** `IR, IC, DP` *(o los tipos de remisión y factura definidos por la empresa)*
>   * **Auto Compute > Initial value:** `"IC"`
>
> * **`Numero_Factura`:**
>   * **Type:** `Number` *(dispara teclado numérico directo en Android/iOS)*
>
> * **`Factura_Completa` (Columna Virtual):**
>   * **App formula:** `[Tipo_Documento] & "-" & [Numero_Factura]`
>   * **LABEL?**: `TRUE` *(identificador humano unificado en listados y detalles: ej. `IC-2140`)*
>
> * **Botonera de Puntaje de Despacho (`Puntos_Esfuerzo`):**
>   * **Type Details > Base type:** `Number`
>   * **Type Details > Input mode:** `Buttons`
>   * **Type Details > Values:** `1, 2, 3, 4, 5`
>   * **Display Name:** `Puntaje Despacho`
>
> * **Botonera de Penalizaciones (`Puntos_Error`):**
>   * **Type Details > Base type:** `Number`
>   * **Type Details > Input mode:** `Buttons`
>   * **Type Details > Values:** `0, -1, -2, -3`
>   * **Auto Compute > Initial value:** `0` *(por defecto el despacho no tiene error)*

---

### 2.3. Tabla: `BASE_HISTORICA` (Motor de Liquidación)

Esta tabla se alimenta de la hoja `BASE_HISTORICA` en Google Sheets (generada por la fórmula matricial `LET` + `QUERY` en segundo plano).

#### A. Columnas base (provenientes de Google Sheets: 10 columnas)

| NAME | TYPE | KEY? | LABEL? | SHOW? | EDITABLE? | REQUIRE? | SEARCH? | DISPLAY NAME |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :--- |
| `_RowNumber` | `Number` | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | *(vacío)* |
| `Año` | `Number` | ⬜ | ⬜ | ☑️ | ⬜ | ⬜ | ☑️ | `Año` |
| `Mes` | `Number` | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | *(oculto: 1..12)* |
| `Quincena` | `Text` | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | *(oculto: Q1/Q2)* |
| `ID_Empleado` | `Ref` | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | `ID Empleado` |
| `Nombre` | `Text` | ⬜ | ☑️ | ☑️ | ⬜ | ⬜ | ☑️ | `Empleado` |
| `Pts_Esfuerzo` | `Number` | ⬜ | ⬜ | ☑️ | ⬜ | ⬜ | ⬜ | `Puntos Esfuerzo` |
| `Pts_Error` | `Number` | ⬜ | ⬜ | ☑️ | ⬜ | ⬜ | ⬜ | `Puntos Error` |
| `Bono Productivo` | `Price` | ⬜ | ⬜ | ☑️ | ⬜ | ⬜ | ⬜ | `Bono Productividad` |
| `Bono Calidad` | `Price` | ⬜ | ⬜ | ☑️ | ⬜ | ⬜ | ⬜ | `Bono Calidad` |
| `Total BONO` | `Price` | ⬜ | ⬜ | ☑️ | ⬜ | ⬜ | ☑️ | `Total Bonificación` |

#### B. Columnas virtuales en `BASE_HISTORICA`

| NAME | TYPE | KEY? | LABEL? | SHOW? | EDITABLE? | REQUIRE? | SEARCH? | DISPLAY NAME |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :--- |
| `ID_Liquidacion` | `Text` | ☑️ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | *(vacío)* |
| `Mes_Nombre` | `Text` | ⬜ | ⬜ | ☑️ | ⬜ | ⬜ | ☑️ | `Mes` |
| `Quincena_Nombre` | `Text` | ⬜ | ⬜ | ☑️ | ⬜ | ⬜ | ☑️ | `Quincena` |

> **Ajustes internos de `BASE_HISTORICA`:**
> * **`ID_Liquidacion` (Clave Primaria Virtual):**
>   * **App formula:** `CONCATENATE([Año], "-", [Mes], "-", [Quincena], "-", [ID_Empleado])`
>   * **KEY?**: `TRUE` *(garantiza un identificador único por colaborador y quincena)*
>
> * **`Año`:**
>   * **Type Details > Show thousands separator:** `FALSE` *(evita mostrar `2,026` con coma)*
>
> * **`Mes_Nombre` (Columna Virtual):**
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
>   * **App formula:**
>     ```appsheet
>     IF([Quincena] = "Q1", "1ra Quincena", "2da Quincena") & " · " & [Mes_Nombre] & " " & [Año]
>     ```
>   * *Produce encabezados legibles: `1ra Quincena · Octubre 2026` o `2da Quincena · Octubre 2026`.*
>
> * **`ID_Empleado`:**
>   * **Type Details > Source table:** `EMPLEADOS`
>
> * **Columnas Monetarias (`Bono Productivo`, `Bono Calidad`, `Total BONO`):**
>   * **Type Details > Currency symbol:** `$`
>   * **Type Details > Decimal digits:** `0` *(ej. `$200.000`)*
>
> * **Columnas `EDITABLE?`:** Todas en `FALSE` *(datos consolidados calculados en la hoja de cálculo)*.

---

## 3. Configuración de Slices (Data > Slices)

Ir a **Data > Slices**. Se utiliza un único slice para filtrar en tiempo real los despachos de la jornada:

### Slice: `REGISTRO_HOY`

| Propiedad | Valor |
| :--- | :--- |
| **Slice name** | `REGISTRO_HOY` |
| **Source table** | `REGISTRO_DIARIO` |
| **Row filter condition** | `[Fecha_Hora] > TODAY()` |
| **Slice actions** | Hereda las acciones permitidas de la tabla (`Adds + Updates`). |

---

## 4. Configuración de Vistas (App > Views)

La barra de navegación principal móvil consta de **3 vistas limpias y directas ordenadas por la propiedad Position**:

| # | Nombre de Vista | Tipo | Posición (`Position`) | Tabla / Slice | Icono |
| :---: | :--- | :---: | :---: | :--- | :--- |
| 1 | `NUEVO REGISTRO` | `form` | `first` | `REGISTRO_DIARIO` | `mobile-android` / `plus-circle` |
| 2 | `HISTORIAL HOY` | `table` | `middle` | `REGISTRO_HOY` (Slice) | `history` |
| 3 | `Liquidación` | `table` | `last` | `BASE_HISTORICA` | `file-invoice` |

---

### 4.1. Vista: `NUEVO REGISTRO`

| Propiedad | Configuración | Justificación / Comportamiento |
| :--- | :--- | :--- |
| **View name** | `NUEVO REGISTRO` | Nombre de la vista en el editor. |
| **For this data** | `REGISTRO_DIARIO` | Tabla transaccional de captura. |
| **View type** | `form` | Formulario de captura. |
| **Position** | `first` | Primer botón en la barra de navegación inferior. |
| **Form style** | `Side by side` | **Escritorio:** Organiza etiquetas al lado de los campos, haciendo el formulario más compacto en altura sin necesidad de scroll.<br>**Celular:** Se adapta automáticamente en formato vertical (nombre arriba, campo o botones debajo). |
| **Column order** | **Manual**:<br>1. `Empleado`<br>2. `Tipo_Documento`<br>3. `Numero_Factura`<br>4. `Puntos_Esfuerzo`<br>5. `Puntos_Error` | Orden ergonómico de captura rápida. |
| **Save / cancel position** | `Bottom` | Botones de confirmación al pie de pantalla. |
| **Auto re-open** | `ON` | El formulario se recarga automáticamente tras guardar para agilizar la captura masiva sin salir de la vista. |
| **Finish view** | `Auto assign (Go Back)` | Al pulsar Cancel regresa a la vista previa. |
| **Display name** | `NUEVO REGISTRO` | Etiqueta visible en el menú. |
| **Icon** | `mobile-android` | Ícono representativo. |

---

### 4.2. Vista: `HISTORIAL HOY`

| Propiedad | Configuración |
| :--- | :--- |
| **View name** | `HISTORIAL HOY` |
| **For this data** | `REGISTRO_HOY` (Slice de despachos de hoy) |
| **View type** | `table` |
| **Position** | `middle` |
| **Sort by** | `Fecha_Hora` — orden `Descending` *(los despachos más recientes aparecen arriba)* |
| **Group aggregate** | `NONE` |
| **Column order** | **Manual** — en este orden exacto:<br>1. `Hora`<br>2. `Factura_Completa`<br>3. `Empleado`<br>4. `Puntos_Esfuerzo`<br>5. `Puntos_Error` |
| **Column width** | `Wide` *(asegura que las columnas de hora, factura y operario no se trunquen)* |
| **Display name** | `HISTORIAL HOY` |
| **Icon** | `history` |

---

### 4.3. Vista: `Liquidación` (Drill-Down Jerárquico)

Esta vista reemplaza completamente los antiguos dashboards quincenales y mensuales, permitiendo consultar cualquier período de la historia con navegación táctil nativa.

| Propiedad | Configuración |
| :--- | :--- |
| **View name** | `Liquidación` |
| **For this data** | `BASE_HISTORICA` |
| **View type** | `table` |
| **Position** | `last` |
| **Group by** | 1. `Año` — `Descending`<br>2. `Mes_Nombre` — `Descending`<br>3. `Quincena_Nombre` — `Ascending` |
| **Sort by** | `Pts_Esfuerzo` — `Descending` *(ordena a los colaboradores de mayor a menor esfuerzo en la quincena)* |
| **Group aggregate** | `Total BONO` $\rightarrow$ `SUM` *(opcional, muestra el total a pagar en el encabezado de cada quincena)* |
| **Column order** | **Manual**:<br>1. `Nombre`<br>2. `Pts_Esfuerzo`<br>3. `Pts_Error`<br>4. `Total BONO` |
| **Column width** | `Wide` *(despliegue amplio y cómodo de los nombres y valores monetarios)* |
| **Display name** | `Liquidación` |
| **Icon** | `file-invoice` |

> **Comportamiento UX en Celular (Drill-Down Progresivo):**
> 1. En la pantalla móvil de ancho reducido, AppSheet no muestra toda la jerarquía en un solo pantallazo. En su lugar, presenta el primer nivel de agrupación: **Año** (ej. `2026`).
> 2. Al tocar el año, la aplicación profundiza al segundo nivel: **Mes** (ej. `Octubre`).
> 3. Al tocar el mes, se abre la tabla quincenal segmentada por `1ra Quincena` y `2da Quincena`, mostrando cada colaborador ordenado de mayor a menor esfuerzo con sus puntos y su bono neto.
> 4. Al estar en la tabla final, la lupa de búsqueda permite filtrar instantáneamente por nombre de colaborador.
> *(En escritorio o tablet, la vista muestra la tabla completa con el árbol jerárquico desplegado).*

---

### 4.4. Vistas de Detalle del Sistema

#### A. Vista de detalle: `BASE_HISTORICA_Detail`
*(Ubicada en **SYSTEM GENERATED > BASE_HISTORICA (1)**)*

Se abre al tocar cualquier colaborador dentro de la tabla de liquidación:
* **View type:** `detail`
* **Header column:** `None` *(elimina la tarjeta gigante superior)*.
* **Display name (Fórmula dinámica):** `[Quincena_Nombre]` *(ubica el período directamente en la miga de pan o barra de título superior de la ventana: ej. `1ra Quincena · Octubre 2026`)*.
* **Column order:**
  1. `Nombre`
  2. `Pts_Esfuerzo`
  3. `Pts_Error`
  4. `Bono Productivo`
  5. `Bono Calidad`
  6. `Total BONO`

#### B. Vista de detalle: `REGISTRO_DIARIO_Detail`
*(Ubicada en **SYSTEM GENERATED > REGISTRO_DIARIO (1)**)*

Se abre al tocar un despacho en `HISTORIAL HOY`:
* **View type:** `detail`
* **Column order:** `Automatic` (muestra `Fecha_Hora`, `Factura_Completa`, `Empleado`, `Puntos_Esfuerzo`, `Puntos_Error`).
* **Display name:** `Detalle del Despacho`

#### C. Vista de detalle: `EMPLEADOS_Detail`
*(Ubicada en **SYSTEM GENERATED > EMPLEADOS (1)**)*

Se abre al tocar la flecha `>` en el nombre de un empleado:
* **View type:** `detail`
* **Column order:** `Automatic` (muestra `Nombre_Completo`, `ID_Empleado`, `Activo?` y `Related REGISTRO_DIARIOs`).
* **Display name:** `Ficha del Colaborador`

---

## 5. Ajustes Globales y Pantalla de Inicio (Settings)

Para garantizar la máxima agilidad operativa en los teléfonos de bodega:

1. Ir a **Settings > General** (o **App > Views > View Options**):
   * **Starting view:** Seleccionar `NUEVO REGISTRO`.
   * **Propósito:** Cada vez que el despachador abre la app en el celular o la recarga, el sistema se posiciona directamente en el formulario listo para digitar la siguiente factura, ahorrando clics.
2. Ir a **Settings > Theme & Brand**:
   * **Primary color:** Azul corporativo (`#1A73E8`) o color institucional de Intereléctricos.
   * **Logo / App Name:** `Bonificaciones Bodega`.

---

## 6. Reglas de Comportamiento (App > Actions)

### Restricción de edición a 15 minutos: tabla `REGISTRO_DIARIO`

Ir a **App > Actions > REGISTRO_DIARIO > acción del sistema `Edit`**:

* **Objetivo:** Permitir corrección inmediata de errores tipográficos en bodega sin comprometer la auditoría posterior.
* **Do this:** `App: edit this row`
* **Display name:** `Editar Despacho`
* **Desktop behavior:** `Open a form`
* **Position:** `Primary`
* **Behavior > Only if this condition is true:**
  ```appsheet
  TOTALMINUTES(NOW() - [Fecha_Hora]) <= 15
  ```
* **Efecto operativo:** El icono de lápiz permanece activo durante los primeros 15 minutos de creado el registro. Tras cumplirse este tiempo, el sistema oculta automáticamente el botón de edición, congelando la fila de manera inalterable.

---

## 7. Reglas de Formato Condicional (App > Format Rules)

Ir a **App > Format Rules**. Existen **3 reglas activas** configuradas para la tabla `BASE_HISTORICA` (se retiró la regla de empleado activo dado que la app filtra operativamente y solo muestra colaboradores activos con registros de despacho):

| Rule Name | For this data | Format these columns | Condition (Fórmula de Activación) | Formato Visual / Resalte |
| :--- | :--- | :--- | :--- | :--- |
| **`Puntos`** | `BASE_HISTORICA` | `Pts_Esfuerzo` | `[Pts_Esfuerzo] >= 300` | Color: `#1A73E8` (Azul) + Negrilla (`Bold = TRUE`) + Ícono: `star` |
| **`Errores`** | `BASE_HISTORICA` | `Pts_Error` | `[Pts_Error] < 0` | Color: `#D93025` (Rojo) + Negrilla (`Bold = TRUE`) + Ícono: `error_outline` |
| **`Bonos`** | `BASE_HISTORICA` | `Total BONO` | `[Total BONO] > 0` | Ícono: `usd-circle` con Color `#188038` (Verde) + Número en Negrilla (`Bold = TRUE`) con color de texto base |

### Solución Técnica para la Condición de `Bonos`:
En AppSheet, las Format Rules evalúan condiciones a **nivel de fila**. Al seleccionar múltiples columnas en *Format these columns* (por ejemplo `Bono Productivo`, `Bono Calidad` y `Total BONO`), la condición define cuándo se activa el formato:

1. **Si la regla aplica a `Total BONO` (Recomendado):**
   * **Condición:**
     ```appsheet
     [Total BONO] > 0
     ```
   * En la tabla de `Liquidación` solo se muestra `Total BONO`, por lo que el ícono `usd-circle` verde y la negrilla solo se mostrarán en los colaboradores que efectivamente ganaron dinero en la quincena.
2. **Si deseas que en la vista de detalle se resalten las 3 columnas:**
   * Si en *Format these columns* agregas `Bono Productivo`, `Bono Calidad` y `Total BONO` con la condición `[Total BONO] > 0`, las 3 celdas se resaltarán si el total es mayor a cero.
   * **Nota importante:** Si un colaborador sacó `$0` en Calidad pero `$150.000` en Productividad, con una regla única el `$0` también recibiría el icono verde porque la fila cumple `[Total BONO] > 0`. Si se desea que **estrictamente nunca aparezca ícono verde sobre un `$0`**, la solución estándar en AppSheet es mantener la regla **`Bonos`** apuntando exclusivamente a `Total BONO`, o crear una mini-regla específica por columna (`[Bono Productivo] > 0`, etc.).

---

## 8. Matriz de Evolución: Versión 1.0 vs. Versión 2.0

Para fines de trazabilidad y auditoría de desarrollo, la siguiente matriz sintetiza los cambios estructurales aplicados al sistema:

| Componente | Versión 1.0 (Anterior) | Versión 2.0 (Actual Optimizada) | Justificación Técnica del Cambio |
| :--- | :--- | :--- | :--- |
| **Captura de Factura** | Un solo campo de texto `Numero_Factura` (`Text`). Digitaba `IR-12345` a mano. | Separación en `Tipo_Documento` (`Enum` botones) + `Numero_Factura` (`Number`). | Activa el teclado numérico puro en el celular, reduciendo tiempos y errores en bodega. |
| **LABEL de Registro** | `Numero_Factura` como LABEL físico. | Columna virtual `Factura_Completa` (`[Tipo_Documento] & "-" & [Numero_Factura]`). | Resuelve ambigüedad visual en registros que compartan número pero diferente tipo (`IR-100` vs `IC-100`). |
| **Columna Virtual `Hora`** | No existía (solo `Fecha_Hora` completa oculta). | `TEXT([Fecha_Hora], "H:MM AM/PM")` mostrada de primera en `HISTORIAL HOY`. | Permite a Luis y los despachadores revisar cronológicamente los despachos del día de un vistazo. |
| **Estilo de Formulario** | `Standard` vertical extenso. | `Form style = Side by side`. | Compacto en altura en pantalla de escritorio; adaptación táctil fluida en celular. |
| **Ancho de Columnas** | `Default`. | `Column width = Wide` en todas las tablas. | Evita el truncamiento de textos en nombres, números de factura y valores en pesos. |
| **Orden en Liquidación** | Por nombre alfabético. | `Sort by = Pts_Esfuerzo` (`Descending`). | Destaca en los primeros lugares a los colaboradores con mayor productividad quincenal. |
| **Icono de Liquidación** | `list-alt` / `calculator`. | `file-invoice`. | Identidad gráfica alineada al concepto de comprobante y pago de nómina. |
| **Tablas Satélites de Resumen** | `RESUMEN_QUINCENAL` y `RESUMEN_MENSUAL` calculadas por fórmulas estáticas en Sheets. | **Retiradas**. Reemplazadas por la tabla única `BASE_HISTORICA`. | Elimina redundancia, desincronización y hojas intermedias frágiles. |
| **Control de Fechas** | Tabla física `FILTRO_FECHAS` que obligaba a tocar un calendario interactivo. | **Retirada**. Drill-down nativo por `Año > Mes > Quincena` en AppSheet. | Elimina la necesidad de cambiar celdas de control. Historial perpetuo navegable con un toque. |
| **Rendimiento de `EMPLEADOS`** | Columnas virtuales `Despachos_Quincena` y `Despachos_Mes` con `COUNT(FILTER(...))`. | **Retiradas**. Se conserva solo `Activo?`. | Acelera drásticamente la sincronización móvil al eliminar consultas circulares sobre fechas. |
| **Estructura de Vistas** | 4 accesos: Nuevo Registro, Historial Hoy, Resumen (Dashboard) y Seleccione Fecha. | 3 accesos: `NUEVO REGISTRO` (`first`), `HISTORIAL HOY` (`middle`) y `Liquidación` (`last`). | Interfaz minimalista y enfocada, reduciendo la carga cognitiva del usuario. |
| **Pantalla de Inicio** | Abría por defecto en la vista predeterminada de navegación. | `Starting view = NUEVO REGISTRO` configurado en `Settings > General`. | Al abrir la app, entra directamente al formulario de despacho para agilidad total. |

---

## 9. Lista de Verificación Final

Antes del despliegue masivo en bodega, cotejar cada punto contra la app real en AppSheet:

- [ ] **Hoja `BASE_HISTORICA`:** Contiene en `A1` la fórmula matricial `LET` + `QUERY` generando Año, Mes, Quincena, ID_Empleado, Puntos y Errores; y de `G1` a `J1` las columnas de nombres y liquidación en pesos ($).
- [ ] **Hoja `CONFIGURACION`:** Celda `B3` tiene la Meta Base Quincenal (300 pts) y la matriz de bonos por tramos calibrada.
- [ ] **Formulario de Registro (`NUEVO REGISTRO`):**
  - Configurado en `Position = first` y con `Form style = Side by side`.
  - `Tipo_Documento` despliega botones táctiles (`IR`, `IC`, `DP` con default `"IC"`).
  - `Numero_Factura` despliega el teclado numérico del teléfono.
  - `Factura_Completa` aparece como título representativo (`LABEL`) en listas e historial.
  - `Auto re-open = ON` mantiene el formulario listo en blanco tras pulsar "Save".
- [ ] **Apertura de la App:** Al iniciar la aplicación, abre directamente en el formulario de `NUEVO REGISTRO` (`Starting view`).
- [ ] **Historial del Día (`HISTORIAL HOY`):**
  - Configurado en `Position = middle` y con `Column width = Wide`.
  - Ordenado por `Fecha_Hora` descendente.
  - Columnas ordenadas: `Hora`, `Factura_Completa`, `Empleado`, `Puntos_Esfuerzo`, `Puntos_Error`.
  - Botón de edición (lápiz) desaparece automáticamente tras 15 minutos de creado el registro.
- [ ] **Vista `Liquidación`:**
  - Configurada en `Position = last`, icono `file-invoice` y con `Column width = Wide`.
  - Ordenada por `Pts_Esfuerzo` descendente (de mayor a menor esfuerzo).
  - En celular navega fluidamente por drill-down: `Año` $\rightarrow$ `Mes` $\rightarrow$ Tabla quincenal.
  - La tabla quincenal muestra únicamente `Nombre`, `Pts_Esfuerzo`, `Pts_Error` y `Total BONO`.
- [ ] **Detalle de Colaborador:**
  - Al presionar una fila en `Liquidación`, el encabezado grande desaparece (`Header column = None`).
  - La miga de pan o barra de título muestra claramente la quincena consultada (`Display name = [Quincena_Nombre]`).
  - Muestra el desglose de `Bono Productivo`, `Bono Calidad` y `Total BONO` en formato moneda ($) sin decimales.
- [ ] **Format Rules (`BASE_HISTORICA`):**
  - **`Puntos`:** `[Pts_Esfuerzo] >= 300` en azul con estrella y negrilla.
  - **`Errores`:** `[Pts_Error] < 0` en rojo con icono de advertencia y negrilla.
  - **`Bonos`:** Condición `[Total BONO] > 0` con icono `usd-circle` verde `#188038` y negrilla en color base.
- [ ] **Colaboradores Inactivos:** No figuran en el desplegable de operarios al ingresar nuevos registros (`Valid_If`).
