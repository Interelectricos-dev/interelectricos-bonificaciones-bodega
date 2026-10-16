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
  * `ID_Empleado` (`Text`, `Key`): Identificador alfanumérico único del trabajador (ej. `B001`) o número de documento de identidad.
  * `Nombre_Completo` (`Text`, `Label`): Nombre y apellidos del empleado. Al ser una operación con un equipo reducido de personas, esta columna actúa como la etiqueta nativa (`Label`) de la tabla para desplegar directamente el nombre en listas y formularios.
  * `Activo` (`Yes/No`): Casilla de verificación booleana (`TRUE` / `FALSE`). Define vigencia laboral.

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
  * `Empleado` (`Ref` apuntando a `EMPLEADOS`): Almacena internamente el `ID_Empleado` y muestra visualmente `Nombre_Completo` (configurado como etiqueta `Label` de la tabla `EMPLEADOS`).
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
Cada fila representa un colaborador activo y se autocalcula a partir de la fila 2 sobre una matriz de 9 columnas desglosadas para garantizar máxima transparencia operativa y auditoría matemática:

#### 4.2.1. Columna A: Extracción Dinámica de Personal Activo
Genera la lista vertical de colaboradores vigentes en la empresa:
```excel
=SI.ERROR(FILTER(EMPLEADOS!A2:A; EMPLEADOS!C2:C = VERDADERO); "")
```
* `=SI.ERROR(...; "")`: Cláusula de protección y manejo de errores. En caso de que no existan colaboradores activos o la base de datos se encuentre en estado inicial de plantilla, evita que se disparen errores de cálculo `#CALC!` o `#N/A` que romperían las fórmulas en cascada de las columnas adyacentes.
* `FILTER(...)`: Función matricial dinámica que evalúa el catálogo maestro y extrae únicamente los identificadores de los colaboradores cuya columna `Activo` sea `VERDADERO` (`TRUE`). Si un empleado es desactivado, se excluye de forma automática de la liquidación sin borrar su histórico.
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

#### 4.2.3. Columna C: Puntos de Factura Acumulados
Totaliza de manera independiente los puntos devengados por concepto de lectura, líneas y complejidad documental:

* **En `RESUMEN_SEMANAL`:**
  ```excel
  =SI(A2 = ""; ""; SUMAR.SI.CONJUNTO(REGISTRO_DIARIO!$E:$E; REGISTRO_DIARIO!$C:$C; A2; REGISTRO_DIARIO!$B:$B; ">=" & FILTRO_FECHAS!$C$2; REGISTRO_DIARIO!$B:$B; "<" & (FILTRO_FECHAS!$D$2 + 1)))
  ```
* **En `RESUMEN_MENSUAL`:**
  ```excel
  =SI(A2 = ""; ""; SUMAR.SI.CONJUNTO(REGISTRO_DIARIO!$E:$E; REGISTRO_DIARIO!$C:$C; A2; REGISTRO_DIARIO!$B:$B; ">=" & FILTRO_FECHAS!$E$2; REGISTRO_DIARIO!$B:$B; "<" & (FILTRO_FECHAS!$F$2 + 1)))
  ```

* `=SI(A2 = ""; ""; ...)`: Condicional de seguridad por ausencia de empleado.
* `SUMAR.SI.CONJUNTO(...)`: Función de suma condicional con múltiples filtros:
  * `REGISTRO_DIARIO!$E:$E`: Rango de suma. Columna donde se registran los puntos por complejidad documental y cantidad de renglones de la remisión (escala de 1 a 5).
  * `REGISTRO_DIARIO!$C:$C`: Rango de criterios 1. Columna de empleados en el histórico de despachos.
  * `A2`: Criterio 1. Código identificador `ID_Empleado` a evaluar.
  * `REGISTRO_DIARIO!$B:$B`: Rango de criterios 2 y 3. Columna que contiene la marca de tiempo de auditoría (`DateTime`).
  * `">=" & FILTRO_FECHAS!$C$2` *(o `$E$2` en mensual)*: Criterio 2. Limita los registros a aquellos cuya fecha sea mayor o igual al inicio del ciclo de consulta.
  * `"<" & (FILTRO_FECHAS!$D$2 + 1)` *(o `$F$2 + 1` en mensual)*: Criterio 3. Limita los registros a aquellos cuya fecha sea menor al día final del periodo más 1 unidad. Dado que la columna B almacena fecha y hora exacta, la adición de `+ 1` asegura la inclusión de todas las transacciones realizadas hasta las 23:59:59 del último día.

#### 4.2.4. Columna D: Puntos de Esfuerzo Físico Acumulados
Totaliza de manera independiente los puntos devengados por desgaste corporal, cortes de cable y maniobras logísticas de carga pesada:

* **En `RESUMEN_SEMANAL`:**
  ```excel
  =SI(A2 = ""; ""; SUMAR.SI.CONJUNTO(REGISTRO_DIARIO!$F:$F; REGISTRO_DIARIO!$C:$C; A2; REGISTRO_DIARIO!$B:$B; ">=" & FILTRO_FECHAS!$C$2; REGISTRO_DIARIO!$B:$B; "<" & (FILTRO_FECHAS!$D$2 + 1)))
  ```
* **En `RESUMEN_MENSUAL`:**
  ```excel
  =SI(A2 = ""; ""; SUMAR.SI.CONJUNTO(REGISTRO_DIARIO!$F:$F; REGISTRO_DIARIO!$C:$C; A2; REGISTRO_DIARIO!$B:$B; ">=" & FILTRO_FECHAS!$E$2; REGISTRO_DIARIO!$B:$B; "<" & (FILTRO_FECHAS!$F$2 + 1)))
  ```

* `=SI(A2 = ""; ""; ...)`: Condicional de seguridad por ausencia de empleado.
* `SUMAR.SI.CONJUNTO(...)`: Función de suma condicional:
  * `REGISTRO_DIARIO!$F:$F`: Rango de suma. Columna donde se registran los puntos asociados al desgaste físico y maniobras logísticas (cortes, peso, uso de montacargas).
  * Argumentos restantes (`REGISTRO_DIARIO!$C:$C`, `A2`, `REGISTRO_DIARIO!$B:$B`, fechas de inicio y fin): Idénticos a la columna C para garantizar consistencia estricta en el empleado y el intervalo de fechas auditado.

#### 4.2.5. Columna E: Puntos Totales Acumulados
Consolida la sumatoria directa entre el volumen documental procesado y el esfuerzo físico realizado:
```excel
=SI(A2 = ""; ""; C2 + D2)
```
* `=SI(A2 = ""; ""; ...)`: Condicional de seguridad por ausencia de empleado.
* `C2`: Total de puntos acumulados por volumen de facturas (`Puntos_Factura`).
* `D2`: Total de puntos acumulados por desgaste físico (`Puntos_Esfuerzo`).
* `+`: Operador aritmético simple. Evita la sobrecarga de fórmulas repetidas y otorga total transparencia analítica a los supervisores y trabajadores para auditar el origen exacto de su puntuación.

#### 4.2.6. Columna F: Bono de Productividad
Determina la retribución económica correspondiente a los puntos obtenidos evaluando la matriz escalonada:
```excel
=SI(A2 = ""; ""; SI(E2 <= CONFIGURACION!$B$2; 0; BUSCARV(E2; CONFIGURACION!$A$8:$C$11; 3; VERDADERO)))
```
* `=SI(A2 = ""; ""; ...)`: Condicional de seguridad por ausencia de empleado.
* `SI(E2 <= CONFIGURACION!$B$2; 0; ...)`: Umbral de rentabilidad operativa. Evalúa el acumulado de puntos de la celda `E2` frente a la meta mínima fijada en `CONFIGURACION!$B$2` (`100` puntos). Si no se supera el umbral, asigna `$0`.
* `BUSCARV(...)` *(Búsqueda escalonada)*:
  * `E2`: Valor de entrada a calificar (`Puntos_Totales`).
  * `CONFIGURACION!$A$8:$C$11`: Matriz fija de escalas salariales (`101 pts → $150.000`, `121 pts → $300.000`, `151 pts → $450.000`, `181 pts → $600.000`).
  * `3`: Indicador de la columna que devuelve el valor monetario correspondiente.
  * `VERDADERO`: Búsqueda de aproximación. Al estar ordenada de forma ascendente, localiza el escalón numérico inmediatamente inferior o igual al valor obtenido.

#### 4.2.7. Columna G: Total Errores Acumulados
Totaliza las penalizaciones asignadas por fallas en el despacho dentro del periodo:

* **En `RESUMEN_SEMANAL`:**
  ```excel
  =SI(A2 = ""; ""; SUMAR.SI.CONJUNTO(REGISTRO_DIARIO!$G:$G; REGISTRO_DIARIO!$C:$C; A2; REGISTRO_DIARIO!$B:$B; ">=" & FILTRO_FECHAS!$C$2; REGISTRO_DIARIO!$B:$B; "<" & (FILTRO_FECHAS!$D$2 + 1)))
  ```
* **En `RESUMEN_MENSUAL`:**
  ```excel
  =SI(A2 = ""; ""; SUMAR.SI.CONJUNTO(REGISTRO_DIARIO!$G:$G; REGISTRO_DIARIO!$C:$C; A2; REGISTRO_DIARIO!$B:$B; ">=" & FILTRO_FECHAS!$E$2; REGISTRO_DIARIO!$B:$B; "<" & (FILTRO_FECHAS!$F$2 + 1)))
  ```

* `=SI(A2 = ""; ""; ...)`: Condicional de seguridad por ausencia de empleado.
* `SUMAR.SI.CONJUNTO(...)`: Función de suma condicional:
  * `REGISTRO_DIARIO!$G:$G`: Rango de la suma. Columna que registra las deducciones numéricas negativas asignadas por el despachador (`0, -1, -2, -3`).
  * `REGISTRO_DIARIO!$C:$C; A2`: Filtro por código de empleado.
  * `REGISTRO_DIARIO!$B:$B; ">=" & ...; REGISTRO_DIARIO!$B:$B; "<" & (... + 1)`: Filtro de contención temporal entre fecha de inicio y fecha de cierre del periodo consultado.

#### 4.2.8. Columna H: Bono de Calidad con Protección de Saldo y Umbral Mínimo
Calcula la retención del fondo de calidad asegurando que las penalizaciones no generen saldos en contra del trabajador y condicionando su cobro al cumplimiento de la meta mínima de puntos:
```excel
=SI(A2 = ""; ""; SI(E2 < CONFIGURACION!$B$2; 0; MAX(0; CONFIGURACION!$B$3 + (G2 * CONFIGURACION!$B$4))))
```
* `=SI(A2 = ""; ""; ...)`: Condicional de seguridad por ausencia de empleado.
* `SI(E2 < CONFIGURACION!$B$2; 0; ...)`: **Condición habilitadora de calidad dinámica.** Evalúa si el total de puntos alcanzado `E2` cumple o supera la meta mínima fijada en `CONFIGURACION!$B$2` (por defecto `100` puntos o el valor calibrado tras la prueba piloto). Si el colaborador no alcanza la meta (`E2 < CONFIGURACION!$B$2`), se le asigna `$0`. Al igualar o superar la meta (`E2 >= CONFIGURACION!$B$2`), se liquida el bono de calidad.
* `CONFIGURACION!$B$3`: Valor base garantizado del bono de calidad (`$200.000`).
* `(G2 * CONFIGURACION!$B$4)`: **Producto del castigo.** Multiplica el acumulado de puntos de error (`G2`, que es un valor numérico negativo o cero) por la penalización unitaria fijada en `CONFIGURACION!$B$4` (`$40.000`). Al ser `G2` negativo, el signo `+` ejecuta una sustracción financiera directa (ejemplo: `$200.000 + (-2 * $40.000) = $200.000 - $80.000 = $120.000`).
* `MAX(0; ...)`: **Función de barrera o piso financiero.** Compara el saldo resultante contra 0 y devuelve el valor mayor. Evita que un exceso de equivocaciones genere descuentos sobre el salario base o saldos negativos para la empresa.

#### 4.2.9. Columna I: Total Extra a Pagar
Totaliza la liquidación neta a transferir o entregar en efectivo al colaborador:
```excel
=SI(A2 = ""; ""; F2 + H2)
```
* `=SI(A2 = ""; ""; ...)`: Condicional de seguridad por ausencia de empleado.
* `F2`: Importe ganado por concepto de productividad física y volumen (`Bono_Productividad`).
* `H2`: Importe remanente por concepto de calidad y precisión de entrega (`Bono_Calidad`).
* `+`: Adición simple que consolida el beneficio económico total devengado en el ciclo evaluado.

---

## 5. Configuración de Vistas e Interfaz (UI/UX) en AppSheet

La barra de navegación principal se compone de **cuatro accesos operativos**:

### 5.1. Vista: Formulario de Despacho (`NUEVO REGISTRO`)
* **Tipo:** `Form` en posición inicial (`first`) configurado como pantalla de registro continuo.
* **Captura:** Optimizada mediante entradas táctiles de tipo `Enum` con modo de botones (`Buttons`) para calificaciones de 1 a 5 y selección relacional (`Ref`) para empleados activos.
* **Campos automáticos:** `ID_Registro` y `Fecha_Hora` ocultos bajo autocomputo (`UNIQUEID()`, `NOW()`).
* **Recarga automática:** Configuración de `Finish view = REGISTRO_DIARIO_Form` para limpiar y dejar el formulario listo para el siguiente despacho inmediatamente al guardar.

### 5.2. Vista: Historial del Día (`HISTORIAL HOY`)
* **Tipo:** `Table` en posición central (`middle`), alimentada exclusivamente por el Slice `REGISTRO_HOY` (`[Fecha_Hora] > TODAY()`).
* **Ordenamiento:** Descendente por `Fecha_Hora` para mostrar arriba las órdenes más recientes del turno.
* **Columnas visibles:** `Numero_Factura`, `Empleado`, `Puntos_Factura`, `Puntos_Esfuerzo` y `Puntos_Error`.

### 5.3. Vista: Resumen Consolidado (`RESUMEN`)
* **Tipo:** `Dashboard` ubicado en posición central (`middle`), con la opción *Use tabs in mobile view* activada para alternar fluidamente mediante pestañas táctiles superiores entre los reportes sin recargas:
  * Pestaña **SEMANAL** (tabla interna en posición `Ref` con título de rango de fechas de lunes a domingo).
  * Pestaña **MENSUAL** (tabla interna en posición `Ref` con título dinámico del mes calendario en curso).

### 5.4. Vista: Selector de Fecha (`SELECCIONE FECHA`)
* **Tipo:** `Detail` en posición final (`last`) con la propiedad `QuickEdit columns` habilitada para `Fecha_Referencia`.
* **Propósito:** Permite cambiar interactivamente la fecha de consulta en un solo paso directamente desde la interfaz, recalculando en tiempo real los límites de semana y mes (`Semana_Inicio`, `Semana_Fin`, `Mes_Inicio`, `Mes_Fin`) que alimentan las vistas de resumen.

### 5.5. Reglas de Formato Condicional (Format Rules) en AppSheet
Para optimizar la experiencia visual del operario y alertar al supervisor sobre anomalías de forma intuitiva, se implementaron 7 reglas de formato condicional:

* **5.5.1. Acumulado de Puntos (`PUNTOS_TOTALES_SEMANAL` y `PUNTOS_TOTALES_MENSUAL`):**
  * **Condición:** `[Puntos_Totales] > 0`
  * **Formato:** Texto en Negrilla (`Bold`) de color **Azul (`blue`)** sobre la columna `Puntos_Totales`.
* **5.5.2. Alerta de Penalizaciones (`ERRORES_TOTALES_SEMANAL` y `ERRORES_TOTALES_MENSUAL`):**
  * **Condición:** `[Total_Errores] < 0`
  * **Formato:** Texto en Negrilla (`Bold`) de color **Rojo (`red`)** sobre la columna `Total_Errores`.
* **5.5.3. Recompensa Financiera (`BONOS_SEMANAL` y `BONOS_MENSUAL`):**
  * **Condición:** Activa permanente.
  * **Formato:** Color de resalte **Verde (`green`)** con ícono `money-bill` sobre las tres columnas monetarias: `Bono_Productividad`, `Bono_Calidad` y `Total_Extra_A_Pagar`.
* **5.5.4. Identificación de Empleado Inactivo (`EMPLEADO_INACTIVO` en `EMPLEADOS`):**
  * **Condición:** `[Activo] = FALSE`
  * **Formato:** Texto en color **Naranja (`orange`)** con estilo Cursiva (`Italic`) sobre `Nombre_Completo`. Mantiene la legibilidad del nombre para auditorías y consultas históricas sin generar confusión visual.

### 5.6. Validaciones y Comportamiento de Campos (Valid_If / Show_If)

* **5.6.1. Filtro de Selección de Personal Activo:**
  En la columna `Empleado` de `REGISTRO_DIARIO`, la regla `Valid_If` restringe la lista desplegable únicamente a colaboradores con estado activo:
  ```text
  SELECT(EMPLEADOS[ID_Empleado], [Activo] = TRUE)
  ```
* **5.6.2. Obligatoriedad de Número de Factura:**
  Configuración `Require? = TRUE` para evitar registros huérfanos sin documento auditado.
* **5.6.3. Uso de Botones de Selección Rápida (`Enum`):**
  Configuración de entrada en modo `Buttons` para `Puntos_Factura` (`1 a 5`), `Puntos_Esfuerzo` (`1 a 5`) y `Puntos_Error` (`0 a -3`), acelerando la captura táctil de datos en bodega.

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
