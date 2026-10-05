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
* **Función:** Almacena una única fecha de referencia para sincronizar las vistas temporales.
* **Estructura:**
  * `ID_Filtro` (`Text`, `Key`): Valor constante `1`.
  * `Fecha_Referencia` (`Date`, `Editable`): Fecha seleccionada por el supervisor.
* **Regla técnica de configuración:** En Google Sheets **no debe existir ninguna fórmula** (como `=HOY()`) en esta celda para evitar que AppSheet bloquee la columna como solo lectura. En AppSheet, la propiedad *Spreadsheet formula* permanece en blanco y en *Initial value* se define:
  ```text
  TODAY()
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
* **3.4.2. Bono base de calidad (`B3`):** `$200`.
* **3.4.3. Deducción unitaria por error (`B4`):** `$40`.
* **3.4.4. Matriz de Escala de Productividad (`A8:C11`):**
  * `101` a `120` puntos → `$150`
  * `121` a `150` puntos → `$300`
  * `151` a `180` puntos → `$450`
  * `181` a más puntos → `$600`

---

## 4. Motor de Liquidación en Google Sheets

Las hojas `RESUMEN_SEMANAL` y `RESUMEN_MENSUAL` operan como motores analíticos en modo de solo lectura (`Read_Only`).

### 4.1. Delimitación Temporal Dinámica
El bloque selector en ambas hojas lee la fecha centralizada en `FILTRO_FECHAS` y calcula de forma automática los límites del ciclo:

#### 4.1.1. En Resumen Semanal (Celdas `I2:J4`)
* **Fecha de referencia (`J2`):**
  ```excel
  =FILTRO_FECHAS!$B$2
  ```
* **Inicio de semana - Lunes (`J3`):**
  ```excel
  =J2 - DIASEM(J2; 2) + 1
  ```
* **Fin de semana - Domingo (`J4`):**
  ```excel
  =J3 + 6
  ```

#### 4.1.2. En Resumen Mensual (Celdas `I2:J4`)
* **Fecha de referencia (`J2`):**
  ```excel
  =FILTRO_FECHAS!$B$2
  ```
* **Inicio de mes (`J3`):**
  ```excel
  =FIN.MES(J2; -1) + 1
  ```
* **Fin de mes (`J4`):**
  ```excel
  =FIN.MES(J2; 0)
  ```

---

### 4.2. Lógica de Consolidación por Empleado
Cada fila representa un colaborador activo y se autocalcula a partir de la fila 2:

#### 4.2.1. Columna A: Extracción Dinámica de Personal Activo
Genera la lista vertical de colaboradores vigentes en la empresa:
```excel
=FILTER(EMPLEADOS!A2:A; EMPLEADOS!C2:C = VERDADERO)
```
* `FILTER(...)`: Función matricial dinámica que evalúa un rango y retorna únicamente las filas que cumplen una condición lógica establecida.
* `EMPLEADOS!A2:A`: Rango de retorno. Apunta a la columna `ID_Empleado` de la tabla maestra.
* `EMPLEADOS!C2:C = VERDADERO`: Criterio de validación. Evalúa la columna booleana `Activo`. Si un colaborador es desactivado, desaparece automáticamente de las liquidaciones vigentes sin eliminar su registro en el histórico transaccional.

#### 4.2.2. Columna B: Nombre del Empleado
Recupera la denominación textual asociada al identificador para facilitar la lectura del reporte:
```excel
=SI(A2 = ""; ""; BUSCARV(A2; EMPLEADOS!$A:$B; 2; FALSO))
```
* `=SI(A2 = ""; ""; ...)`: Condicional de seguridad por ausencia de empleado.
* `BUSCARV(...)`: Función de búsqueda vertical exacta.
  * `A2`: Valor buscado (`ID_Empleado`).
  * `EMPLEADOS!$A:$B`: Matriz de consulta fijada en la tabla maestra.
  * `2`: Indicador de la columna que extrae el `Nombre_Completo`.
  * `FALSO`: Parámetro de coincidencia exacta obligatoria.

#### 4.2.3. Columna C: Puntos Totales Acumulados
Consolida la sumatoria de complejidad documental y desgaste físico generados por el trabajador dentro de la ventana de fechas:
```excel
=SI(A2 = ""; ""; SUMAR.SI.CONJUNTO(REGISTRO_DIARIO!$E:$E; REGISTRO_DIARIO!$C:$C; A2; REGISTRO_DIARIO!$B:$B; ">=" & $J$3; REGISTRO_DIARIO!$B:$B; "<" & ($J$4 + 1)) + SUMAR.SI.CONJUNTO(REGISTRO_DIARIO!$F:$F; REGISTRO_DIARIO!$C:$C; A2; REGISTRO_DIARIO!$B:$B; ">=" & $J$3; REGISTRO_DIARIO!$B:$B; "<" & ($J$4 + 1)))
```
* **Primer `SUMAR.SI.CONJUNTO(...)` (Puntos por Factura):**
  * `REGISTRO_DIARIO!$E:$E`: Rango de suma. Columna donde se registran los puntos por complejidad de lectura de la remisión (escala de 1 a 5).
  * `REGISTRO_DIARIO!$C:$C`: Rango de criterios 1. Columna de empleados en el histórico de despachos.
  * `A2`: Criterio 1. Código identificador (`ID_Empleado`) a evaluar.
  * `REGISTRO_DIARIO!$B:$B`: Rango de criterios 2 y 3. Columna que contiene la marca de tiempo de auditoría (`DateTime`).
  * `">=" & $J$3`: Criterio 2. Limita los registros a aquellos cuya fecha sea mayor o igual al inicio del ciclo (Lunes en semanal / Día 1 en mensual).
  * `"<" & ($J$4 + 1)`: Criterio 3. Limita los registros a aquellos cuya fecha sea menor al día final del periodo más 1 unidad. Dado que la columna B almacena hora exacta, la adición de `+ 1` asegura la inclusión de todas las transacciones realizadas hasta las `23:59:59` del último día.
* **Operador `+`:** Concatena aritméticamente la sumatoria de esfuerzo cognitivo con la de esfuerzo físico.
* **Segundo `SUMAR.SI.CONJUNTO(...)` (Puntos por Esfuerzo Físico):**
  * `REGISTRO_DIARIO!$F:$F`: Rango de suma. Columna de desgaste físico y maniobras logísticas (cortes, peso).
  * **Argumentos restantes:** Idénticos al primer bloque para garantizar consistencia en el empleado y el intervalo de fechas.

#### 4.2.4. Columna D: Bono de Productividad
Determina la retribución económica correspondiente a los puntos obtenidos:
```excel
=SI(A2 = ""; ""; SI(C2 <= CONFIGURACION!$B$2; 0; BUSCARV(C2; CONFIGURACION!$A$8:$C$11; 3; VERDADERO)))
```
* `=SI(A2 = ""; ""; ...)`: Condicional de seguridad por ausencia de empleado.
* `SI(C2 <= CONFIGURACION!$B$2; 0; ...)`: Umbral de rentabilidad operativa. Evalúa el acumulado de puntos de la celda `C2` frente a la meta mínima fijada en `CONFIGURACION!$B$2` (100 puntos). Si no se supera el umbral, asigna `$0`.
* `BUSCARV(...)` (Búsqueda escalonada):
  * `C2`: Valor de entrada a calificar (`Puntos Totales`).
  * `CONFIGURACION!$A$8:$C$11`: Matriz fija de escalas salariales (`101 pts → $150`, `121 pts → $300`, `151 pts → $450`, `181 pts → $600`).
  * `3`: Indicador de la columna que devuelve el valor monetario correspondiente.
  * `VERDADERO`: Búsqueda de aproximación. Al estar ordenada de forma ascendente, localiza el escalón numérico inmediatamente inferior o igual al valor obtenido.

#### 4.2.5. Columna E: Total Errores Acumulados
Totaliza las penalizaciones asignadas por fallas en el despacho dentro del periodo:
```excel
=SI(A2 = ""; ""; SUMAR.SI.CONJUNTO(REGISTRO_DIARIO!$G:$G; REGISTRO_DIARIO!$C:$C; A2; REGISTRO_DIARIO!$B:$B; ">=" & $J$3; REGISTRO_DIARIO!$B:$B; "<" & ($J$4 + 1)))
```
* `REGISTRO_DIARIO!$G:$G`: Rango de la suma. Columna que registra las deducciones numéricas negativas asignadas por el despachador (`0, -1, -2, -3`).
* `REGISTRO_DIARIO!$C:$C; A2`: Filtro por código de empleado.
* `REGISTRO_DIARIO!$B:$B; ">=" & $J$3; REGISTRO_DIARIO!$B:$B; "<" & ($J$4 + 1)`: Filtro de contención temporal entre fecha de inicio y fecha de cierre del periodo.

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
