# Esquemas y Configuraciones Nativas de AppSheet

Este documento sirve como respaldo técnico de las expresiones lógicas, configuraciones de columnas y comportamientos de interfaz definidos directamente en el motor de AppSheet. No incluye las fórmulas de Google Sheets.

---

## 1. Permisos de Tablas (Table Settings)

* **REGISTRO_DIARIO:** `Adds_and_Updates` (Eliminación bloqueada por auditoría).
* **EMPLEADOS:** `Read_Only` (Altas y bajas se gestionan directamente en Google Sheets).
* **FILTRO_FECHAS:** `Updates_Only` (Solo permite modificar la fecha de referencia).
* **RESUMEN_SEMANAL / RESUMEN_MENSUAL:** `Read_Only` (Hojas calculadas por fórmulas matriciales).

---

## 2. Configuraciones de Columnas (Data > Columns)

### Tabla: EMPLEADOS
* **Columnas Físicas:**
  * `ID_Empleado` (`Text`, `Key`): Identificador único de cada colaborador.
  * `Nombre_Completo` (`Text`, `Label`):
    * **Objetivo:** Etiqueta nativa visual para menús desplegables y selecciones en formularios (`Ref`). Dado que son máximo 5 colaboradores con nombres distintos, muestra de forma limpia únicamente el nombre del trabajador sin requerir columnas virtuales de concatenación.
    * **Propiedades:** `Label` activado (`TRUE`).
  * `Activo` (`Yes/No`): Control de vigencia laboral.

---

### Tabla: FILTRO_FECHAS

* **Columnas de la Tabla:**
  * `ID_Filtro` (`Text`, `Key`): Identificador único (valor fijo `1`).
  * `Fecha_Referencia` (`Date`, `Editable`):
    * **Objetivo:** Fijar por defecto el día en curso permitiendo al usuario modificarla interactivamente para filtrar reportes.
    * **Propiedades:** `Editable?` activado (`TRUE`).
    * **Initial Value:**
      ```text
      TODAY()
      ```
    * **Regla estricta:** En Google Sheets la celda `B2` no debe llevar fórmula de hoja de cálculo para evitar bloqueo en AppSheet.
  * `Semana_Inicio`, `Semana_Fin`, `Mes_Inicio`, `Mes_Fin` (`Date`, `Read_Only`):
    * **Objetivo:** Columnas calculadas automáticamente por fórmulas en Google Sheets (`WEEKDAY` / `EOMONTH`) para delimitar las ventanas temporales que consumen `RESUMEN_SEMANAL` y `RESUMEN_MENSUAL`.
    * **Propiedades:** `Editable?` desactivado (`FALSE`).

---

### Tabla: REGISTRO_DIARIO

* **Columna: `ID_Registro`**
  * **Objetivo:** Clave primaria única generada automáticamente.
  * **Propiedades:** `Key` activado (`TRUE`), `Show?` desactivado (`FALSE`).
  * **Initial Value:**
    ```text
    UNIQUEID()
    ```

* **Columna: `Fecha_Hora`**
  * **Objetivo:** Estampa de tiempo exacta de captura.
  * **Propiedades:** `Show?` desactivado (`FALSE`).
  * **Initial Value:**
    ```text
    NOW()
    ```

* **Columna: `Empleado`**
  * **Objetivo:** Vincular el registro con el catálogo maestro de trabajadores activos.
  * **Tipo:** `Ref` hacia la tabla `EMPLEADOS`.

* **Configuración de Botoneras (`Puntos_Factura`, `Puntos_Esfuerzo`, `Puntos_Error`)**  
  Para garantizar que se inserten números puros en Google Sheets pero el usuario interactúe con botones táctiles amigables, los tres campos comparten la siguiente configuración estricta:
  * **Type:** `Enum`
  * **Base Type:** `Number`
  * **Input Mode:** `Buttons`
  * **Valores permitidos:**
    * `Puntos_Factura`: `1, 2, 3, 4, 5`
    * `Puntos_Esfuerzo`: `1, 2, 3, 4, 5`
    * `Puntos_Error`: `0, -1, -2, -3`

---

## 3. Reglas de Comportamiento (Behavior)

### Acción: Edit (Tabla `REGISTRO_DIARIO`)

* **Objetivo:** Restringir la modificación de un registro una vez superados los 15 minutos desde su creación.
* **Condición (`Only if this condition is true`):**
  ```text
  TOTALMINUTES(NOW() - [Fecha_Hora]) <= 15
  ```

---

## 4. Títulos Dinámicos de Vistas (UX > Views)

Fórmulas asignadas a la propiedad **Display Name** de las vistas de reporte para que actualicen su título según la fecha elegida en el selector (`FILTRO_FECHAS`).

### Vista: `RESUMEN_SEMANAL`
* **Display Name:**
  ```text
  CONCATENATE(
    "SEMANAL (", 
    TEXT(ANY(FILTRO_FECHAS[Fecha_Referencia]) - WEEKDAY(ANY(FILTRO_FECHAS[Fecha_Referencia])) + 2, "DD/MM/YYYY"), 
    " al ", 
    TEXT(ANY(FILTRO_FECHAS[Fecha_Referencia]) - WEEKDAY(ANY(FILTRO_FECHAS[Fecha_Referencia])) + 8, "DD/MM/YYYY"), 
    ")"
  )
  ```

### Vista: `RESUMEN_MENSUAL`
* **Display Name:**
  ```text
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
