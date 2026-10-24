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
| `RESUMEN_QUINCENAL`<br>`RESUMEN_MENSUAL` | `Read_Only` | Calculadas automáticamente por fórmulas matriciales en Google Sheets. |

---

## 2. Configuración de Columnas (Data > Columns)

Ir a **Data > Columns**. La cuadrícula principal de AppSheet permite configurar directamente las propiedades estándar (`TYPE`, `KEY?`, `LABEL?`, `SHOW?`, `EDITABLE?`, `REQUIRE?`, `SEARCH?` y `DISPLAY NAME`).

El apartado **Ajustes internos** contiene **únicamente** las propiedades avanzadas que no son visibles en la cuadrícula y exigen abrir el modal de edición de la columna (icono de lápiz en el editor), tales como `Auto Compute`, `Type Details` o reglas `Valid_If`.

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
> * `Activo` se mantiene con `SHOW? = FALSE` porque el estado operativo se expone a través de la columna virtual `Activo?`.
> * La relación del sistema `Related REGISTRO_DIARIOs` (`List` de `Ref`) tiene configurado como Display name: `Historial de Despachos`.

#### B. Columnas virtuales en `EMPLEADOS`

Estas columnas **no existen en Google Sheets**. Se crean en AppSheet mediante el botón **`+ Add virtual column`** al final de la tabla:

| NAME | TYPE | KEY? | LABEL? | SHOW? | EDITABLE? | REQUIRE? | SEARCH? | DISPLAY NAME |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :--- |
| `Activo?` | `Text` | ⬜ | ⬜ | ☑️ | ⬜ | ⬜ | ☑️ | `Activo?` |
| `Despachos_Quincena` | `Number` | ⬜ | ⬜ | ☑️ | ⬜ | ⬜ | ⬜ | `Despachos Quincena` |
| `Despachos_Mes` | `Number` | ⬜ | ⬜ | ☑️ | ⬜ | ⬜ | ⬜ | `Despachos Mes` |

> **Ajustes internos:**
> * **`Activo?`:**
>   * **App formula:** `IF([Activo], "SI", "NO")`
> * **`Despachos_Quincena`:**
>   * **App formula:**
>     ```appsheet
>     COUNT(
>       FILTER(
>         "REGISTRO_DIARIO",
>         AND(
>           [Empleado] = [_THISROW].[ID_Empleado],
>           DATE([Fecha_Hora]) >= INDEX(FILTRO_FECHAS[Quincena_Inicio], 1),
>           DATE([Fecha_Hora]) <= INDEX(FILTRO_FECHAS[Quincena_Fin], 1)
>         )
>       )
>     )
>     ```
> * **`Despachos_Mes`:**
>   * **App formula:**
>     ```appsheet
>     COUNT(
>       FILTER(
>         "REGISTRO_DIARIO",
>         AND(
>           [Empleado] = [_THISROW].[ID_Empleado],
>           DATE([Fecha_Hora]) >= INDEX(FILTRO_FECHAS[Mes_Inicio], 1),
>           DATE([Fecha_Hora]) <= INDEX(FILTRO_FECHAS[Mes_Fin], 1)
>         )
>       )
>     )
>     ```

---

### 2.2. Tabla: `FILTRO_FECHAS`

*(Capturas: [03_cols_filtro_fechas_01.png](../docs/images/appsheet_config/03_cols_filtro_fechas_01.png), [03_cols_filtro_fechas_02.png](../docs/images/appsheet_config/03_cols_filtro_fechas_02.png))*

| NAME | TYPE | KEY? | LABEL? | SHOW? | EDITABLE? | REQUIRE? | SEARCH? | DISPLAY NAME |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :--- |
| `_RowNumber` | `Number` | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | *(vacío)* |
| `ID_Filtro` | `Number` | ☑️ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | *(vacío)* |
| `Fecha_Referencia` | `Date` | ⬜ | ☑️ | ☑️ | ☑️ | ☑️ | ☑️ | `Seleccionar Fecha` |
| `Quincena_Inicio` | `Date` | ⬜ | ⬜ | ☑️ | ⬜ | ⬜ | ⬜ | `Quincena Inicio` |
| `Quincena_Fin` | `Date` | ⬜ | ⬜ | ☑️ | ⬜ | ⬜ | ⬜ | `Quincena Fin` |
| `Mes_Inicio` | `Date` | ⬜ | ⬜ | ☑️ | ⬜ | ⬜ | ⬜ | `Mes Inicio` |
| `Mes_Fin` | `Date` | ⬜ | ⬜ | ☑️ | ⬜ | ⬜ | ⬜ | `Mes Fin` |

> **Ajustes internos:**
> * **`ID_Filtro`:**
>   * **Auto Compute > Initial value:** `1`
> * **`Fecha_Referencia`:**
>   * **Auto Compute > Initial value:** `TODAY()`
>   * **Regla estricta:** La celda `B2` en Google Sheets **NO debe tener fórmula**. Debe ser una fecha estática (ej. `22/10/2026`). Si tiene fórmula de hoja de cálculo, AppSheet bloquea la edición desde la app móvil.

---

### 2.3. Tabla: `REGISTRO_DIARIO` (Formulario Optimizado — Solo Columnas Físicas)

*(Capturas: [04_cols_registro_diario_01.png](../docs/images/appsheet_config/04_cols_registro_diario_01.png), [04_cols_registro_diario_02.png](../docs/images/appsheet_config/04_cols_registro_diario_02.png))*

Esta tabla cuenta **exclusivamente con sus 6 columnas físicas** provenientes de Google Sheets. **No requiere ninguna columna virtual**.

| NAME | TYPE | KEY? | LABEL? | SHOW? | EDITABLE? | REQUIRE? | SEARCH? | DISPLAY NAME |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :--- |
| `_RowNumber` | `Number` | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | *(vacío)* |
| `ID_Registro` | `Text` | ☑️ | ⬜ | ⬜ | ⬜ | ☑️ | ⬜ | *(vacío)* |
| `Fecha_Hora` | `DateTime` | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | *(vacío)* |
| `Empleado` | `Ref` | ⬜ | ⬜ | ☑️ | ☑️ | ☑️ | ☑️ | `Empleado` |
| `Numero_Factura` | `Text` | ⬜ | ☑️ | ☑️ | ☑️ | ☑️ | ☑️ | `N° Factura` |
| `Puntos_Esfuerzo` | `Enum` | ⬜ | ⬜ | ☑️ | ☑️ | ☑️ | ⬜ | `Puntaje Despacho` |
| `Puntos_Error` | `Enum` | ⬜ | ⬜ | ☑️ | ☑️ | ☑️ | ⬜ | `Puntos Error` |

> **Ajustes internos:**
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
> * **Botonera de Puntaje único de Despacho (`Puntos_Esfuerzo`):**
>   * **Type Details > Base type:** `Number`
>   * **Type Details > Input mode:** `Buttons`
>   * **Type Details > Values:** `1, 2, 3, 4, 5`
>   * **Display Name:** `Puntaje Despacho`
>
> * **Botonera de Penalizaciones (`Puntos_Error`):**
>   * **Type Details > Base type:** `Number`
>   * **Type Details > Input mode:** `Buttons`
>   * **Type Details > Values:** `0, -1, -2, -3`
>   * **Auto Compute > Initial value:** `0` *(por defecto el despacho no tiene error; el operario no tiene que tocarlo si el despacho fue correcto)*

---

### 2.4. Tablas: `RESUMEN_QUINCENAL` y `RESUMEN_MENSUAL`

Ambas tablas exponen en AppSheet las mismas 7 columnas visibles de liquidación consolidada calculadas en Google Sheets. 

En `RESUMEN_MENSUAL`, la liquidación corresponde a la **suma financiera exacta de lo devengado en la Quincena 1 (días 1 al 15) más la Quincena 2 (días 16 al fin de mes)**. Para garantizar este desglose sin distorsionar las escalas quincenales, la hoja en Google Sheets contiene 8 columnas auxiliares de cálculo analítico (`H:O`) que en AppSheet se mantienen con `SHOW? = FALSE`.

#### A. Columnas base (provenientes de Google Sheets)

| NAME | TYPE | KEY? | LABEL? | SHOW? | EDITABLE? | REQUIRE? | SEARCH? | DISPLAY NAME |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :--- |
| `_RowNumber` | `Number` | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | *(vacío)* |
| `ID_Empleado` | `Ref` | ☑️ | ⬜ | ☑️ | ⬜ | ⬜ | ⬜ | `ID` |
| `Nombre_Empleado` | `Text` | ⬜ | ☑️ | ☑️ | ⬜ | ⬜ | ☑️ | `Empleado` |
| `Total_Puntos` | `Number` | ⬜ | ⬜ | ☑️ | ⬜ | ⬜ | ⬜ | `Total Puntos` |
| `Bono_Productividad` | `Price` | ⬜ | ⬜ | ☑️ | ⬜ | ⬜ | ⬜ | `Bono Productividad` |
| `Total_Errores` | `Number` | ⬜ | ⬜ | ☑️ | ⬜ | ⬜ | ⬜ | `Total Errores` |
| `Bono_Calidad` | `Price` | ⬜ | ⬜ | ☑️ | ⬜ | ⬜ | ⬜ | `Bono Calidad` |
| `Total_Bonificacion` | `Price` | ⬜ | ⬜ | ☑️ | ⬜ | ⬜ | ⬜ | `Bono Neto` |

#### A.1. Columnas auxiliares de auditoría quincenal (Exclusivas de `RESUMEN_MENSUAL`)
*Las siguientes 8 columnas físicas existen en Google Sheets (`H:O`) para desglosar la liquidación de cada quincena y se configuran en AppSheet con `SHOW? = FALSE`:*
* `Puntos_Q1` (`Number`), `Bono_Prod_Q1` (`Price`), `Errores_Q1` (`Number`), `Bono_Cal_Q1` (`Price`).
* `Puntos_Q2` (`Number`), `Bono_Prod_Q2` (`Price`), `Errores_Q2` (`Number`), `Bono_Cal_Q2` (`Price`).

> **Ajustes internos:**
> * **`ID_Empleado`:**
>   * **Type Details > Source table:** `EMPLEADOS`
> * **Columnas monetarias (`Bono_Productividad`, `Bono_Calidad`, `Total_Bonificacion` y auxiliares):**
>   * **Type Details > Currency symbol:** `$`
>   * **Type Details > Decimal digits:** `0` *(ej. `$150.000`, sin centavos)*
>
> *(Nota: Todas las columnas se mantienen con EDITABLE? = FALSE y REQUIRE? = FALSE porque su cálculo es administrado en su totalidad por las fórmulas de Google Sheets).*

#### B. Columnas virtuales de filtrado por período (Listas interactivas de facturas)

Estas columnas despliegan la tabla interactiva inferior con cada una de las facturas que el colaborador despachó en el ciclo al abrir su vista de detalle:

| NAME | TYPE | KEY? | LABEL? | SHOW? | EDITABLE? | REQUIRE? | SEARCH? | DISPLAY NAME |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :--- |
| `Despachos_Quincena`<br>*(en RESUMEN_QUINCENAL)* | `List` | ⬜ | ⬜ | ☑️ | ⬜ | ⬜ | ⬜ | `Despachos Quincena` |
| `Despachos_Mes`<br>*(en RESUMEN_MENSUAL)* | `List` | ⬜ | ⬜ | ☑️ | ⬜ | ⬜ | ⬜ | `Despachos Mes` |

> **Ajustes internos:**
> * **`Despachos_Quincena` (en `RESUMEN_QUINCENAL`):**
>   * **Type Details > Element type:** `Ref`
>   * **Type Details > Referenced table name:** `REGISTRO_DIARIO`
>   * **App formula:**
>     ```appsheet
>     FILTER(
>       "REGISTRO_DIARIO",
>       AND(
>         [Empleado] = [_THISROW].[ID_Empleado],
>         DATE([Fecha_Hora]) >= INDEX(FILTRO_FECHAS[Quincena_Inicio], 1),
>         DATE([Fecha_Hora]) <= INDEX(FILTRO_FECHAS[Quincena_Fin], 1)
>       )
>     )
>     ```
> * **`Despachos_Mes` (en `RESUMEN_MENSUAL`):**
>   * **Type Details > Element type:** `Ref`
>   * **Type Details > Referenced table name:** `REGISTRO_DIARIO`
>   * **App formula:**
>     ```appsheet
>     FILTER(
>       "REGISTRO_DIARIO",
>       AND(
>         [Empleado] = [_THISROW].[ID_Empleado],
>         DATE([Fecha_Hora]) >= INDEX(FILTRO_FECHAS[Mes_Inicio], 1),
>         DATE([Fecha_Hora]) <= INDEX(FILTRO_FECHAS[Mes_Fin], 1)
>       )
>     )
>     ```

---

## 3. Configuración de Slices (Data > Slices)

Ir a **Data > Slices**. Se requiere crear un subconjunto de datos filtrado para mostrar únicamente los registros transaccionales del día en curso:

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

| # | Nombre | Tipo | Posición | Tabla / Slice |
| :---: | :--- | :---: | :---: | :--- |
| 1 | `NUEVO REGISTRO` | `form` | `first` | `REGISTRO_DIARIO` |
| 2 | `HISTORIAL HOY` | `table` | `middle` | `REGISTRO_HOY` (Slice) |
| 3 | `RESUMEN` | `dashboard` | `middle` | *(no aplica — contenedor de vistas)* |
| 4 | `SELECCIONE FECHA` | `detail` | `last` | `FILTRO_FECHAS` |

---

### 4.1. Vista: `NUEVO REGISTRO`

| Propiedad | Valor |
| :--- | :--- |
| **View name** | `NUEVO REGISTRO` |
| **For this data** | `REGISTRO_DIARIO` |
| **View type** | `form` |
| **Position** | `first` |
| **Column order** | `Automatic` *(renderiza Empleado, Numero_Factura, Puntos_Esfuerzo, Puntos_Error)* |
| **Save / cancel position** | `Bottom` |
| **Auto re-open** | `ON` *(activado para recarga continua del formulario sin límite de despachos)* |
| **Finish view** | `Auto assign (Go Back)` *(al guardar, Auto re-open mantiene el formulario en blanco; al dar Cancel regresa a la vista previa)* |
| **Display name** | `NUEVO REGISTRO` |
| **Icon** | `mobile-android` |

---

### 4.2. Vista: `HISTORIAL HOY`

| Propiedad | Valor |
| :--- | :--- |
| **View name** | `HISTORIAL HOY` |
| **For this data** | `REGISTRO_HOY` (Slice de despachos del día) |
| **View type** | `table` |
| **Position** | `middle` |
| **Sort by** | `Fecha_Hora` — orden `Descending` |
| **Group aggregate** | `NONE` |
| **Column order** | **Manual** — en este orden exacto:<br>1. `Numero_Factura`<br>2. `Empleado`<br>3. `Puntos_Esfuerzo`<br>4. `Puntos_Error` |
| **Column width** | `Default` |
| **Display name** | `HISTORIAL HOY` |
| **Icon** | `history` |

#### Vista de sistema detalle: `REGISTRO_DIARIO_Detail`
*(Ubicada en **SYSTEM GENERATED > REGISTRO_DIARIO (1)**)*

Se despliega automáticamente al presionar cualquier fila dentro de `HISTORIAL HOY`:
* **View type:** `detail`
* **Column order:** `Automatic` (muestra `Fecha_Hora`, `Empleado`, `Numero_Factura`, `Puntos_Esfuerzo`, `Puntos_Error`).
* **Display name:** `Detalle del Despacho`

---

### 4.3. Vista: `RESUMEN` (Dashboard Quincenal y Mensual)

#### Paso 1 — Vistas internas de tabla: `QUINCENAL` y `MENSUAL`

| Propiedad | Configuración `QUINCENAL` | Configuración `MENSUAL` |
| :--- | :--- | :--- |
| **For this data** | `RESUMEN_QUINCENAL` | `RESUMEN_MENSUAL` |
| **View type** | `table` | `table` |
| **Position** | `ref` | `ref` |
| **Sort by** | `Total_Bonificacion` (Descending) | `Total_Bonificacion` (Descending) |
| **Column order** | Manual: `Nombre_Empleado`, `Total_Puntos`, `Total_Errores`, `Total_Bonificacion` | Manual: `Nombre_Empleado`, `Total_Puntos`, `Total_Errores`, `Total_Bonificacion` |
| **Icon** | `list-ul` | `list-ul` |

* **Display name dinámico `QUINCENAL` (fórmula `fx`):**
  ```appsheet
  CONCATENATE(
    "QUINCENAL (",
    TEXT(INDEX(FILTRO_FECHAS[Quincena_Inicio], 1), "DD/MM/YYYY"),
    " al ",
    TEXT(INDEX(FILTRO_FECHAS[Quincena_Fin], 1), "DD/MM/YYYY"),
    ")"
  )
  ```

* **Display name dinámico `MENSUAL` (fórmula `fx`):**
  ```appsheet
  CONCATENATE(
    "MENSUAL (",
    SWITCH(
      MONTH(INDEX(FILTRO_FECHAS[Fecha_Referencia], 1)),
      1, "Enero", 2, "Febrero", 3, "Marzo", 4, "Abril",
      5, "Mayo", 6, "Junio", 7, "Julio", 8, "Agosto",
      9, "Septiembre", 10, "Octubre", 11, "Noviembre", 12, "Diciembre",
      ""
    ),
    " ",
    YEAR(INDEX(FILTRO_FECHAS[Fecha_Referencia], 1)),
    ")"
  )
  ```

#### Paso 2 — Vistas de detalle del sistema: `RESUMEN_QUINCENAL_Detail` y `RESUMEN_MENSUAL_Detail`
*(Ubicadas en **SYSTEM GENERATED**)*
* **View type:** `detail`
* **Display mode:** `Side-by-side`
* **Nested row display:** `5`
* **Column order:** `Automatic` (despliega las métricas consolidadas y la lista filtrada de despachos del período).

#### Paso 3 — Dashboard principal: `RESUMEN`

| Propiedad | Valor |
| :--- | :--- |
| **View name** | `RESUMEN` |
| **View type** | `dashboard` |
| **Position** | `middle` |
| **View entries** | 1. `QUINCENAL` (`Large`)<br>2. `MENSUAL` (`Large`) |
| **Use tabs in mobile view** | `TRUE` *(activa pestañas superiores para alternar fluidamente entre quincenal y mensual)* |
| **Interactive mode** | `FALSE` |
| **Display name** | `RESUMEN` |
| **Icon** | `list-alt` |

---

### 4.4. Vista: `SELECCIONE FECHA`

| Propiedad | Valor |
| :--- | :--- |
| **View name** | `SELECCIONE FECHA` |
| **For this data** | `FILTRO_FECHAS` |
| **View type** | `detail` |
| **Position** | `last` |
| **Column order** | `Automatic` *(despliega: `Fecha_Referencia`, `Quincena_Inicio`, `Quincena_Fin`, `Mes_Inicio`, `Mes_Fin`)* |
| **Display mode** | `Side-by-side` |
| **Quick edit columns** | `Fecha_Referencia` *(permite tocar el calendario y cambiar la fecha de referencia en tiempo real)* |
| **Desktop layout** | `Split view` |
| **Display name** | `SELECCIONE FECHA` |
| **Icon** | `calendar-day` |

---

### 4.5. Vista de sistema: `EMPLEADOS_Detail`
*(Ubicada en **SYSTEM GENERATED > EMPLEADOS (1)**)*

Se abre cuando el supervisor toca la flecha `>` en el campo `Empleado` dentro del detalle de un despacho.
* **View type:** `detail`
* **Display mode:** `Side-by-side`
* **Column order:** `Automatic` (despliega `Nombre_Completo`, `ID_Empleado`, `Activo?`, `Despachos_Quincena`, `Despachos_Mes`, y `Related REGISTRO_DIARIOs`).
* **Display name:** `Ficha del Colaborador`

---

## 5. Reglas de Comportamiento (App > Actions)

### Restricción de edición a 15 minutos: tabla `REGISTRO_DIARIO`

Ir a **App > Actions > REGISTRO_DIARIO > acción del sistema `Edit`**:

* **Objetivo:** Impedir que un operario modifique un despacho pasados 15 minutos de su creación.
* **Do this:** `App: edit this row`
* **Display name:** `Editar Despacho`
* **Desktop behavior:** `Open a form`
* **Position:** `Primary`
* **Behavior > Only if this condition is true:**
  ```appsheet
  TOTALMINUTES(NOW() - [Fecha_Hora]) <= 15
  ```
* **Efecto operativo:** El botón de edición (ícono de lápiz) permanece habilitado durante los primeros 15 minutos posteriores a la creación del registro. Cumplido este lapso, el sistema oculta automáticamente el botón, congelando el registro en modo Solo Lectura inalterable.

---

## 6. Reglas de Formato Condicional (App > Format Rules)

Ir a **App > Format Rules**. Existen 7 reglas activas configuradas:

| Rule Name | For this data | Condition | Format these columns | Formato Visual / Resalte |
| :--- | :--- | :--- | :--- | :--- |
| `EMPLEADO_ACTIVO?` | `EMPLEADOS` | `[Activo] = FALSE` | `Nombre_Completo` | Color: `orange` + Estilo: *Cursiva (Italics)* |
| `PUNTOS_QUINCENAL`<br>`PUNTOS_MENSUAL` | `RESUMEN_QUINCENAL`<br>`RESUMEN_MENSUAL` | `[Total_Puntos] > 0` | `Total_Puntos` | Color: `blue` + Negrilla (Bold) |
| `ERRORES_QUINCENAL`<br>`ERRORES_MENSUAL` | `RESUMEN_QUINCENAL`<br>`RESUMEN_MENSUAL` | `[Total_Errores] < 0` | `Total_Errores` | Color: `red` + Negrilla (Bold) |
| `BONOS_QUINCENAL`<br>`BONOS_MENSUAL` | `RESUMEN_QUINCENAL`<br>`RESUMEN_MENSUAL` | *(vacío / siempre activo)* | `Bono_Productividad`<br>`Bono_Calidad`<br>`Total_Bonificacion` | Ícono: `money-bill` + Resalte (Highlight): `green` |

---

## 7. Lista de Verificación Final

Antes del despliegue masivo o entrega a los operarios, cotejar cada punto contra la app real:

- [ ] **Google Sheets:** La celda `B2` de `FILTRO_FECHAS` contiene una fecha estática inicial sin fórmulas volátiles.
- [ ] **Google Sheets:** La celda `B2` de `CONFIGURACION` tiene la meta mínima de puntos (100) para otorgar el Bono de Calidad quincenal.
- [ ] **Slice `REGISTRO_HOY`:** Filtra con precisión `[Fecha_Hora] > TODAY()` para listar exclusivamente la jornada en curso.
- [ ] **Historial del Día:** La vista `HISTORIAL HOY` ordena los despachos de forma descendente (`Fecha_Hora`).
- [ ] **Detalle con Filtro de Período:** En el detalle de `RESUMEN_QUINCENAL` o `RESUMEN_MENSUAL`, la lista desplegable inferior muestra los despachos acotados al período de la fecha seleccionada en `SELECCIONE FECHA`.
- [ ] **Columna `Activo?`:** En el detalle del empleado muestra `"SI"` o `"NO"`.
- [ ] **Formulario:** `N° Factura` es obligatorio; los botones de puntos (`1` a `5`) y errores (`0` a `-3` con default `0`) responden tácticamente en un solo toque.
- [ ] **Recarga continua:** Con `Auto re-open` activo y `Finish view = Auto assign (Go Back)`, el formulario se recarga continuamente en blanco tras cada guardado para despachos masivos.
- [ ] **Restricción 15 min:** El botón de edición permite correcciones durante 15 minutos; transcurrido este tiempo desaparece.
- [ ] **Dashboard `RESUMEN`:** Navegación móvil por pestañas (`QUINCENAL` y `MENSUAL`) con títulos dinámicos de rango de fechas.
- [ ] **Formato condicional:** Reglas `PUNTOS_QUINCENAL` (azul sobre `Total_Puntos`), `ERRORES_QUINCENAL` (rojo sobre `Total_Errores`), `BONOS_QUINCENAL` (verde sobre `Total_Bonificacion`), `PUNTOS_MENSUAL` (azul), `ERRORES_MENSUAL` (rojo), `BONOS_MENSUAL` (verde) y `EMPLEADO_ACTIVO?` (naranja cursiva).
- [ ] **Empleado inactivo:** No figura en la lista desplegable de operarios al crear nuevos registros.
