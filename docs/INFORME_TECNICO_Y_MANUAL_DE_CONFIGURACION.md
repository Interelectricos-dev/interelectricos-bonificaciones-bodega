# Informe Técnico y Manual de Configuración

**Proyecto:** SISTEMA DE LIQUIDACION Y AUDITORIA DE BONIFICACIONES EN BODEGA  
**Empresa:** INTERELECTRICOS GROUP SAS  
**Fecha:** 01 de Octubre de 2026  
**Autor:** Mauricio Sierra – Aprendiz ADSO SENA  
**Software:** Arquitectura Híbrida (AppSheet + Google Sheets)  

---

## 1. Alcance y Objetivo del Sistema

El sistema **BONIFICACIONES** tiene como propósito digitalizar y estandarizar la captura del rendimiento operativo en la zona de despachos de Intereléctricos Group SAS. Sustituye el conteo manual en tablero físico por un flujo digital estructurado que desacopla la digitación rápida en bodega del procedimiento financiero de nómina, asegurando:

1. **Equidad en la medición:** Separación estricta entre la complejidad de lectura/conteo de la factura y el desgaste físico real (cortes cables, cargas pesadas, manejo de maquinaria, etc.).
2. **Control de calidad:** Aplicación de penalizaciones sobre un fondo base de calidad sin generar saldos negativos al trabajador.
3. **Auditoría e integridad:** Almacenamiento cronológico sin eliminación de registros y restricción de edición posterior para evitar alteraciones no autorizadas.
4. **Consulta dinámica:** Visualización consolidada semanal y mensual por empleado mediante un selector de una sola fecha.

---

## 2. Arquitectura General y Flujo de Información

La solución opera bajo un esquema cliente-servidor en la nube:

* **2.1. Capa de Captura (Frontend):** Aplicación AppSheet ejecutada como Aplicación Web Progresiva (PWA) en el navegador del equipo de bodega.
* **2.2. Capa de Datos y Procesamiento (Backend):** Libro de Google Sheets que actúa como base de datos relacional y motor de cálculo de liquidación.

---

## 3. Diccionario y Modelo de Base de Datos

El libro de Google Sheets se compone de cinco tablas estructuradas:

### 3.1. Hoja: EMPLEADOS
* **Permiso en AppSheet:** `Read_Only`
* **Función:** Control centralizado del personal operativo. Las altas, bajas y modificaciones son realizadas exclusivamente por el administrador en la hoja de cálculo para evitar alteraciones a mitad de ciclo de pago.
* **Estructura:**
  * `ID_Empleado` (`Text`, `Key`): Identificador alfanumérico único del trabajador (ej. `B001`) o puede guardar el número de documento del empleado.
  * `Nombre_Completo` (`Text`): Nombre y apellidos del empleado.
  * `Activo` (`Yes/No`): Casilla de verificación booleana (`TRUE` / `FALSE`). Define vigencia laboral.
  * `Etiqueta_Empleado` (Columna Virtual en AppSheet, `Label`): Concatenación utilizada en menús desplegables para facilitar la selección visual guardando únicamente el identificador clave:
    ```text
    CONCATENATE([ID_Empleado], " - ", [Nombre_Completo])
    ```

---

### 3.2. Hoja: FILTRO_FECHAS
* **Permiso en AppSheet:** `Updates_Only`
* **Función:** Centraliza la fecha de consulta y calcula de forma automática los límites temporales (semana y mes) para alimentar a `RESUMEN_SEMANAL` y `RESUMEN_MENSUAL`.
* **Estructura de Columnas:**
  * `ID_Filtro` (`Text`, `Key`): Valor constante `1`.
  * `Fecha_Referencia` (`Date`, `Editable`): Fecha seleccionada interactivamente por el usuario en AppSheet.
    * *Regla técnica de configuración:* En Google Sheets **no debe existir ninguna fórmula** (como `=HOY()`) en esta celda (`B2`) para evitar que AppSheet bloquee la columna como solo lectura. En AppSheet, la propiedad *Spreadsheet formula* permanece en blanco y en *Initial value* se define:
      ```text
      TODAY()
      ```
  * `Semana_Inicio` (`Date`, Celda `C2`): Lunes de la semana seleccionada. Calculado automáticamente con la fórmula:
    ```excel
    =B2 - DIASEM(B2; 2) + 1
    ```
  * `Semana_Fin` (`Date`, Celda `D2`): Domingo de la semana seleccionada. Calculado automáticamente con la fórmula:
    ```excel
    =C2 + 6
    ```
  * `Mes_Inicio` (`Date`, Celda `E2`): Primer día del mes seleccionado. Calculado automáticamente con la fórmula:
    ```excel
    =FIN.MES(B2; -1) + 1
    ```
  * `Mes_Fin` (`Date`, Celda `F2`): Último día del mes seleccionado. Calculado automáticamente con la fórmula:
    ```excel
    =FIN.MES(B2; 0)
    ```

---

### 3.3. Hoja: REGISTRO_DIARIO
* **Permiso en AppSheet:** `Adds_and_Updates`
* **Función:** Registro histórico de cada orden o factura despachada.
* **Estructura:**
  * `ID_Registro` (`Text`, `Key`): Oculto (`Show? = False`), autogenerado mediante la fórmula `UNIQUEID()`.
  * `Fecha_Hora` (`DateTime`): Oculto (`Show? = False`), marca temporal automática generada mediante `NOW()`.
  * `Empleado` (`Ref` apuntando a `EMPLEADOS`): Guarda `ID_Empleado` y muestra visualmente `Etiqueta_Empleado`.
  * `Numero_Factura` (`Text`): Número del documento impreso auditado. Campo obligatorio (`Require? = True`).
  * `Puntos_Factura` (`Enum`, `Base Type: Number`): Botones numéricos `[1, 2, 3, 4, 5]`. Evalúa la complejidad documental y conteo de referencias.
  * `Puntos_Esfuerzo` (`Enum`, `Base Type: Number`): Botones numéricos `[1, 2, 3, 4, 5]`. Evalúa el desgaste corporal y maniobras logísticas (cortes, peso, repeticiones).
  * `Puntos_Error` (`Enum`, `Base Type: Number`): Botones numéricos `[0, -1, -2, -3]`. Registro de penalizaciones por fallas en el despacho.

---

### 3.4. Hoja: CONFIGURACION
Centraliza las variables de nómina para que cualquier ajuste gerencial se propague sin la necesidad de modificar el código ni las fórmulas:
* **3.4.1. Meta base semanal (`B2`):** `100` puntos.
* **3.4.2. Bono inicial de calidad (`B3`):** `$200.000`.
* **3.4.3. Descuento unitario por error (`B4`):** `$40.000`.
* **3.4.4. Matriz de Escala de Productividad (`A8:C11`):**
  * `101` a `120` puntos → `$150.000`
  * `121` a `150` puntos → `$300.000`
  * `151` a `180` puntos → `$450.000`
  * `181` o más puntos → `$600.000`

---

## 4. Motor de Liquidación en Google Sheets

Las hojas `RESUMEN_SEMANAL` y `RESUMEN_MENSUAL` operan como motores analíticos en modo de solo lectura (`Read_Only`). No poseen tablas de fechas independientes en su interior; en su lugar, consumen directamente los rangos calculados en la hoja `FILTRO_FECHAS`.

### 4.1. Delimitación Temporal Dinámica
En lugar de duplicar celdas de control en cada hoja de resumen, los límites de consulta se procesan de manera centralizada en la hoja `FILTRO_FECHAS`:

* **Ciclo Semanal (`FILTRO_FECHAS!$C$2:$D$2`):**
  * `Semana_Inicio` (`C2`): Lunes del ciclo (`=B2 - DIASEM(B2; 2) + 1`).
  * `Semana_Fin` (`D2`): Domingo del ciclo (`=C2 + 6`).
* **Ciclo Mensual (`FILTRO_FECHAS!$E$2:$F$2`):**
  * `Mes_Inicio` (`E2`): Primer día del mes (`=FIN.MES(B2; -1) + 1`).
  * `Mes_Fin` (`F2`): Último día del mes (`=FIN.MES(B2; 0)`).

---

### 4.2. Lógica de Consolidación por Empleado
Cada fila representa un colaborador activo y se autocalcula a partir de la fila 2:

#### 4.2.1. Columna A: Extracción Dinámica de Personal Activo
Genera la lista vertical de colaboradores vigentes en la empresa:
```excel
=SI.ERROR(FILTER(EMPLEADOS!A2:A1000; EMPLEADOS!C2:C1000 = VERDADERO); "")
```
* `FILTER(...)`: Función matricial dinámica que evalúa el rango de personal y retorna únicamente los IDs donde `Activo = TRUE`. Si un colaborador es desactivado, desaparece automáticamente de las liquidaciones vigentes sin alterar el histórico transaccional.
* `SI.ERROR(..., "")`: Previene errores visuales (`#N/A` o `#CALC!`) en caso de no haber empleados activos.

#### 4.2.2. Columna B: Nombre del Empleado
Recupera la denominación textual asociada al identificador para facilitar la lectura del reporte:
```excel
=SI(A2 = ""; ""; BUSCARV(A2; EMPLEADOS!$A:$B; 2; FALSO))
```
* `=SI(A2 = ""; ""; ...)`: Condicional de seguridad por ausencia de empleado.
* `BUSCARV(...)`: Función de búsqueda vertical exacta.
  * `A2`: Valor buscado (`ID_Empleado`).
  * `EMPLEADOS!$A:$B`: Matriz de consulta fijada en la tabla maestra.
  * `2`: Indicador de columna que extrae el `Nombre_Completo`.
  * `FALSO`: Parámetro de coincidencia exacta obligatoria.

#### 4.2.3. Columna C: Puntos Totales Acumulados
Consolida la sumatoria de complejidad documental y desgaste físico generados por el trabajador dentro de la ventana de fechas.

* **En `RESUMEN_SEMANAL` (apunta a `FILTRO_FECHAS!$C$2` y `$D$2`):**
  ```excel
  =SI(A2 = ""; ""; SUMAR.SI.CONJUNTO(REGISTRO_DIARIO!$E:$E; REGISTRO_DIARIO!$C:$C; A2; REGISTRO_DIARIO!$B:$B; ">=" & FILTRO_FECHAS!$C$2; REGISTRO_DIARIO!$B:$B; "<" & (FILTRO_FECHAS!$D$2 + 1)) + SUMAR.SI.CONJUNTO(REGISTRO_DIARIO!$F:$F; REGISTRO_DIARIO!$C:$C; A2; REGISTRO_DIARIO!$B:$B; ">=" & FILTRO_FECHAS!$C$2; REGISTRO_DIARIO!$B:$B; "<" & (FILTRO_FECHAS!$D$2 + 1)))
  ```

* **En `RESUMEN_MENSUAL` (apunta a `FILTRO_FECHAS!$E$2` y `$F$2`):**
  ```excel
  =SI(A2 = ""; ""; SUMAR.SI.CONJUNTO(REGISTRO_DIARIO!$E:$E; REGISTRO_DIARIO!$C:$C; A2; REGISTRO_DIARIO!$B:$B; ">=" & FILTRO_FECHAS!$E$2; REGISTRO_DIARIO!$B:$B; "<" & (FILTRO_FECHAS!$F$2 + 1)) + SUMAR.SI.CONJUNTO(REGISTRO_DIARIO!$F:$F; REGISTRO_DIARIO!$C:$C; A2; REGISTRO_DIARIO!$B:$B; ">=" & FILTRO_FECHAS!$E$2; REGISTRO_DIARIO!$B:$B; "<" & (FILTRO_FECHAS!$F$2 + 1)))
  ```

* **Desglose de argumentos:**
  * `REGISTRO_DIARIO!$E:$E` / `$F:$F`: Rangos de suma para `Puntos_Factura` y `Puntos_Esfuerzo` respectivamente.
  * `REGISTRO_DIARIO!$C:$C; A2`: Filtro por código del trabajador.
  * `REGISTRO_DIARIO!$B:$B; ">=" & ...`: Limita los registros a marcas de tiempo mayores o iguales al inicio del ciclo.
  * `REGISTRO_DIARIO!$B:$B; "<" & (... + 1)`: Limita los registros a marcas de tiempo menores al día de fin más 1 unidad. Al contener la columna B hora exacta (`DateTime`), la adición de `+ 1` asegura incluir todas las transacciones hasta las `23:59:59` del último día.

#### 4.2.4. Columna D: Bono de Productividad
Determina la retribución económica correspondiente a los puntos obtenidos evaluando la matriz escalonada:
```excel
=SI(A2 = ""; ""; SI(C2 <= CONFIGURACION!$B$2; 0; BUSCARV(C2; CONFIGURACION!$A$8:$C$11; 3; VERDADERO)))
```
* `SI(C2 <= CONFIGURACION!$B$2; 0; ...)`: Evalúa el acumulado frente a la meta mínima de `100` puntos (`CONFIGURACION!$B$2`). Si no se supera, asigna `$0`.
* `BUSCARV(C2; CONFIGURACION!$A$8:$C$11; 3; VERDADERO)`: Búsqueda por aproximación sobre la escala salarial ordenada (`101 pts → $150.000`, `121 pts → $300.000`, `151 pts → $450.000`, `181 pts → $600.000`).

#### 4.2.5. Columna E: Total Errores Acumulados
Totaliza las penalizaciones asignadas por fallas en el despacho dentro del periodo evaluado:

* **En `RESUMEN_SEMANAL`:**
  ```excel
  =SI(A2 = ""; ""; SUMAR.SI.CONJUNTO(REGISTRO_DIARIO!$G:$G; REGISTRO_DIARIO!$C:$C; A2; REGISTRO_DIARIO!$B:$B; ">=" & FILTRO_FECHAS!$C$2; REGISTRO_DIARIO!$B:$B; "<" & (FILTRO_FECHAS!$D$2 + 1)))
  ```

* **En `RESUMEN_MENSUAL`:**
  ```excel
  =SI(A2 = ""; ""; SUMAR.SI.CONJUNTO(REGISTRO_DIARIO!$G:$G; REGISTRO_DIARIO!$C:$C; A2; REGISTRO_DIARIO!$B:$B; ">=" & FILTRO_FECHAS!$E$2; REGISTRO_DIARIO!$B:$B; "<" & (FILTRO_FECHAS!$F$2 + 1)))
  ```
* `REGISTRO_DIARIO!$G:$G`: Rango de suma de deducciones negativas (`0, -1, -2, -3`).

#### 4.2.6. Columna F: Bono de Calidad con Protección de Saldo
Calcula la retención del fondo de calidad asegurando que las penalizaciones no generen saldos en contra del trabajador:
```excel
=SI(A2 = ""; ""; MAX(0; CONFIGURACION!$B$3 + (E2 * CONFIGURACION!$B$4)))
```
* `=SI(A2 = ""; ""; ...)`: Condicional de seguridad por ausencia de empleado.
* `CONFIGURACION!$B$3`: Valor base garantizado del bono de calidad (`$200`).
* `(E2 * CONFIGURACION!$B$4)`: Producto del castigo. Multiplica el acumulado de puntos de error (`E2`, que es un valor numérico negativo o cero) por la penalización unitaria fijada en `CONFIGURACION!$B$4` (`$40`). Al ser `E2` negativo, el signo `+` ejecuta una sustracción financiera directa (ejemplo: `200 + (-2 * 40) = 200 - 80 = $120`).
* `MAX(0; ...)`: Función de barrera o piso financiero. Compara el saldo resultante contra `0` y devuelve el valor mayor. Evita que un exceso de equivocaciones genere descuentos sobre el salario base o saldos negativos para la empresa.

#### 4.2.7. Columna G: Total Extra a Pagar
Totaliza la liquidación neta a transferir o entregar en efectivo al colaborador:
```excel
=SI(A2 = ""; ""; D2 + F2)
```
* `=SI(A2 = ""; ""; ...)`: Condicional de seguridad por ausencia de empleado.
* `D2`: Importe ganado por concepto de productividad física y volumen.
* `F2`: Importe remanente por concepto de calidad y precisión de entrega.
* `+`: Adición simple que consolida el beneficio económico total devengado en el ciclo evaluado.

---

## 5. Configuración de Vistas e Interfaz (UI/UX) en AppSheet

La navegación se compone de tres accesos principales:

### 5.1. Vista: Formulario de Despacho
* **Tipo:** `Form` configurado como pantalla de inicio.
* **Captura:** Optimizada mediante entradas de tipo `Enum` con modo de botones (`Buttons`) para calificaciones de 1 a 5 y selección relacional (`Ref`) para empleados activos.
* **Campos automáticos:** `ID_Registro` y `Fecha_Hora` ocultos bajo autocomputo (`UNIQUEID()`, `NOW()`).

### 5.2. Vista: Selector de Fecha
* **Tipo:** `Detail` con la propiedad `QuickEdit columns` habilitada para el campo `Fecha_Referencia`.
* **Propósito:** Permite la actualización de fechas sin ingresar a la edición estructural de la tabla.

### 5.3. Vista: Resumen (Dashboard Unificado)
* **Tipo:** `Dashboard` ubicado en la barra central de navegación, con la opción *Use tabs in mobile view* activada para alternar entre reportes sin recargas de página. Contiene las vistas internas en posición `Ref`:
  * En la vista **Semanal**
  * En la vista **Mensual**

---

## 6. Políticas de Seguridad, Integridad y Auditoría

### 6.1. Ventana de Edición Restringida (15 minutos)
Configurada en la acción del sistema `Edit` de `REGISTRO_DIARIO` bajo la regla de comportamiento:
```text
TOTALMINUTES(NOW() - [Fecha_Hora]) <= 15
```
Otorga un margen para subsanar errores de digitación inmediatos. Superado el umbral temporal, el registro queda congelado para preservar la trazabilidad de auditoría.

### 6.2. Inhabilitación de Eliminaciones (Deletes)
Permisos estructurales de tabla limitados a adición y actualización (`Adds_and_Updates`), garantizando la preservación histórica de cada transacción.

### 6.3. Segregación de Roles en Gestión de Personal
Tabla `EMPLEADOS` bloqueada en modo de solo lectura (`Read_Only`) en la interfaz de usuario. Altas y bajas son administradas exclusivamente por personal autorizado directamente en Google Sheets.
