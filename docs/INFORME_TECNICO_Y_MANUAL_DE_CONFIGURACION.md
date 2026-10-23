# Informe Técnico y Manual de Configuración

**Proyecto:** SISTEMA DE LIQUIDACION Y AUDITORIA DE BONIFICACIONES EN BODEGA  
**Empresa:** INTERELECTRICOS GROUP SAS  
**Fecha:** 22 de Octubre de 2026  
**Autor:** Mauricio Sierra – Aprendiz ADSO SENA  
**Software:** Arquitectura Híbrida (AppSheet + Google Sheets)  

---

## 1. Alcance y Objetivo del Sistema

El sistema **BONIFICACIONES** tiene como propósito digitalizar y estandarizar la captura del rendimiento operativo en la zona de despachos de Intereléctricos Group SAS. Sustituye el conteo manual en tablero físico por un flujo digital estructurado que desacopla la digitación rápida en bodega del procedimiento financiero de nómina, asegurando:

1. **Agilidad en la captura:** Registro unificado de la calificación del despacho en un solo campo táctil de 1 a 5 puntos.
2. **Control de calidad:** Aplicación de penalizaciones sobre un fondo base de calidad garantizado sin generar saldos negativos al trabajador.
3. **Auditoría e integridad:** Almacenamiento cronológico sin eliminación de registros y restricción de edición posterior para evitar alteraciones no autorizadas.
4. **Consulta dinámica:** Visualización consolidada quincenal y mensual por empleado mediante un selector interactivo de fecha.

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
* **Función:** Centraliza la fecha de consulta y calcula de forma automática los límites temporales (quincena y mes) para alimentar a `RESUMEN_QUINCENAL` y `RESUMEN_MENSUAL`.
* **Estructura de Columnas:**
  * `ID_Filtro` (`Number`, `Key`): Valor constante `1`.
  * `Fecha_Referencia` (`Date`, `Editable`): Fecha seleccionada interactivamente por el usuario en AppSheet.
    * *Regla técnica de configuración:* En Google Sheets **no debe existir ninguna fórmula** (como `=HOY()`) en esta celda (`B2`) para evitar que AppSheet bloquee la columna como solo lectura. En AppSheet, la propiedad *Spreadsheet formula* permanece en blanco y en *Initial value* se define:
      ```text
      TODAY()
      ```
  * `Quincena_Inicio` (`Date`, Celda `C2`): Día inicial de la quincena comercial seleccionada (Día 1 o Día 16). Calculado automáticamente con la fórmula:
    ```excel
    =SI(DIA(B2) <= 15; FECHA(AÑO(B2); MES(B2); 1); FECHA(AÑO(B2); MES(B2); 16))
    ```
  * `Quincena_Fin` (`Date`, Celda `D2`): Día final de la quincena comercial seleccionada (Día 15 o último día del mes). Calculado automáticamente con la fórmula:
    ```excel
    =SI(DIA(B2) <= 15; FECHA(AÑO(B2); MES(B2); 15); FIN.MES(B2; 0))
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
  * `Puntos_Esfuerzo` (`Enum`, `Base Type: Number`): Botones numéricos `[1, 2, 3, 4, 5]`. Calificación global del despacho según complejidad y esfuerzo.
  * `Puntos_Error` (`Enum`, `Base Type: Number`): Botones numéricos `[0, -1, -2, -3]` con valor inicial `0`. Registro de penalizaciones por fallas en el despacho.

---

### 3.4. Hoja: CONFIGURACION
Centraliza las variables de nómina para que cualquier ajuste gerencial se propague sin la necesidad de modificar el código ni las fórmulas:
* **Meta base quincenal (`B2`):** `100` puntos.
* **Bono inicial de calidad (`B3`):** `$200.000`.
* **Descuento unitario por error (`B4`):** `$40.000`.
* **Matriz de Escala de Productividad Quincenal (`A8:C11`):**
  * `101` a `120` puntos → `$150.000`
  * `121` a `150` puntos → `$300.000`
  * `151` a `180` puntos → `$450.000`
  * `181` o más puntos → `$600.000`

---

## 4. Motor de Liquidación en Google Sheets

Las hojas `RESUMEN_QUINCENAL` y `RESUMEN_MENSUAL` operan como motores analíticos en modo de solo lectura (`Read_Only`). No poseen tablas de fechas independientes en su interior; en su lugar, consumen directamente los rangos calculados en la hoja `FILTRO_FECHAS`.

### 4.1. Delimitación Temporal Dinámica
En lugar de duplicar celdas de control en cada hoja de resumen, los límites de consulta se procesan de manera centralizada en la hoja `FILTRO_FECHAS`:

* **Ciclo Quincenal (`FILTRO_FECHAS!$C$2:$D$2`):**
  * `Quincena_Inicio` (`C2`): Día 1 o 16 del ciclo.
  * `Quincena_Fin` (`D2`): Día 15 o último día del mes.
* **Ciclo Mensual (`FILTRO_FECHAS!$E$2:$F$2`):**
  * `Mes_Inicio` (`E2`): Primer día del mes (`=FIN.MES(B2; -1) + 1`).
  * `Mes_Fin` (`F2`): Último día del mes (`=FIN.MES(B2; 0)`).

---

### 4.2. Lógica de Consolidación por Empleado
Cada fila representa un colaborador activo y se autocalcula a partir de la fila 2 sobre una matriz uniforme de 7 columnas:

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

#### 4.2.3. Columna C: Total Puntos Acumulados (`Total_Puntos`)
Totaliza los puntos devengados exclusivamente por calificación del despacho en el período:

* **En `RESUMEN_QUINCENAL`:**
  ```excel
  =SI(A2 = ""; ""; SUMAR.SI.CONJUNTO(REGISTRO_DIARIO!$E:$E; REGISTRO_DIARIO!$C:$C; A2; REGISTRO_DIARIO!$B:$B; ">=" & FILTRO_FECHAS!$C$2; REGISTRO_DIARIO!$B:$B; "<=" & (FILTRO_FECHAS!$D$2 + 1)))
  ```
* **En `RESUMEN_MENSUAL`:**
  ```excel
  =SI(A2 = ""; ""; SUMAR.SI.CONJUNTO(REGISTRO_DIARIO!$E:$E; REGISTRO_DIARIO!$C:$C; A2; REGISTRO_DIARIO!$B:$B; ">=" & FILTRO_FECHAS!$E$2; REGISTRO_DIARIO!$B:$B; "<=" & (FILTRO_FECHAS!$F$2 + 1)))
  ```

* `=SI(A2 = ""; ""; ...)`: Condicional de seguridad por ausencia de empleado.
* `SUMAR.SI.CONJUNTO(...)`: Función de suma condicional:
  * `REGISTRO_DIARIO!$E:$E`: Rango de suma. Columna `Puntos_Esfuerzo` donde se registra el puntaje único de despacho asignado por el despachador (1 a 5).
  * `REGISTRO_DIARIO!$C:$C`: Rango de criterios 1. Columna de empleados en el histórico de despachos.
  * `A2`: Criterio 1. Código identificador `ID_Empleado` a evaluar.
  * `REGISTRO_DIARIO!$B:$B`: Rango de criterios 2 y 3. Columna que contiene la marca de tiempo de auditoría (`DateTime`).
  * `">=" & FILTRO_FECHAS!$C$2` *(o `$E$2` en mensual)*: Criterio 2. Limita los registros a aquellos cuya fecha sea mayor o igual al inicio del ciclo de consulta.
  * `"<=" & (FILTRO_FECHAS!$D$2 + 1)` *(o `$F$2 + 1` en mensual)*: Criterio 3. Limita los registros a aquellos cuya fecha sea menor o igual al día final del periodo más 1 unidad para incluir todas las transacciones hasta las 23:59:59.

#### 4.2.4. Columna D: Bono de Productividad
Determina la retribución económica correspondiente a los puntos obtenidos evaluando la matriz escalonada:
```excel
=SI(A2 = ""; ""; SI(C2 <= CONFIGURACION!$B$2; 0; BUSCARV(C2; CONFIGURACION!$A$8:$C$11; 3; VERDADERO)))
```
* `=SI(A2 = ""; ""; ...)`: Condicional de seguridad por ausencia de empleado.
* `SI(C2 <= CONFIGURACION!$B$2; 0; ...)`: Umbral de rentabilidad operativa. Evalúa el acumulado de puntos de la celda `C2` (`Total_Puntos`) frente a la meta mínima fijada en `CONFIGURACION!$B$2` (`100` puntos). Si no se supera el umbral, asigna `$0`.
* `BUSCARV(...)` *(Búsqueda escalonada)*:
  * `C2`: Valor de entrada a calificar (`Total_Puntos`).
  * `CONFIGURACION!$A$8:$C$11`: Matriz fija de escalas salariales (`101 pts → $150.000`, `121 pts → $300.000`, `151 pts → $450.000`, `181 pts → $600.000`).
  * `3`: Indicador de la columna que devuelve el valor monetario correspondiente.
  * `VERDADERO`: Búsqueda de aproximación que localiza el escalón numérico inmediatamente inferior o igual al valor obtenido.

#### 4.2.5. Columna E: Total Errores Acumulados (`Total_Errores`)
Totaliza las penalizaciones asignadas por fallas en el despacho dentro del periodo:

* **En `RESUMEN_QUINCENAL`:**
  ```excel
  =SI(A2 = ""; ""; SUMAR.SI.CONJUNTO(REGISTRO_DIARIO!$F:$F; REGISTRO_DIARIO!$C:$C; A2; REGISTRO_DIARIO!$B:$B; ">=" & FILTRO_FECHAS!$C$2; REGISTRO_DIARIO!$B:$B; "<=" & (FILTRO_FECHAS!$D$2 + 1)))
  ```
* **En `RESUMEN_MENSUAL`:**
  ```excel
  =SI(A2 = ""; ""; SUMAR.SI.CONJUNTO(REGISTRO_DIARIO!$F:$F; REGISTRO_DIARIO!$C:$C; A2; REGISTRO_DIARIO!$B:$B; ">=" & FILTRO_FECHAS!$E$2; REGISTRO_DIARIO!$B:$B; "<=" & (FILTRO_FECHAS!$F$2 + 1)))
  ```

* `=SI(A2 = ""; ""; ...)`: Condicional de seguridad por ausencia de empleado.
* `SUMAR.SI.CONJUNTO(...)`: Función de suma condicional:
  * `REGISTRO_DIARIO!$F:$F`: Rango de la suma. Columna que registra las deducciones numéricas negativas asignadas por el despachador (`0, -1, -2, -3`).
  * `REGISTRO_DIARIO!$C:$C; A2`: Filtro por código de empleado.
  * Intervalo temporal: Filtro de contención temporal entre fecha de inicio y fecha de cierre del periodo consultado.

#### 4.2.6. Columna F: Bono de Calidad con Protección de Saldo y Umbral Mínimo
Calcula la retención del fondo de calidad asegurando que las penalizaciones no generen saldos en contra del trabajador y condicionando su cobro al cumplimiento de la meta mínima de puntos:
```excel
=SI(A2 = ""; ""; SI(C2 < CONFIGURACION!$B$2; 0; MAX(0; CONFIGURACION!$B$3 + (E2 * CONFIGURACION!$B$4))))
```
* `=SI(A2 = ""; ""; ...)`: Condicional de seguridad por ausencia de empleado.
* `SI(C2 < CONFIGURACION!$B$2; 0; ...)`: **Condición habilitadora de calidad dinámica.** Evalúa si el total de puntos alcanzado `C2` cumple o supera la meta mínima fijada en `CONFIGURACION!$B$2` (`100` puntos quincenales). Si el colaborador no alcanza la meta (`C2 < CONFIGURACION!$B$2`), se le asigna `$0`. Al igualar o superar la meta (`C2 >= CONFIGURACION!$B$2`), se liquida el bono de calidad.
* `CONFIGURACION!$B$3`: Valor base garantizado del bono de calidad (`$200.000`).
* `(E2 * CONFIGURACION!$B$4)`: **Producto del castigo.** Multiplica el acumulado de puntos de error (`E2`, que es un valor numérico negativo o cero) por la penalización unitaria fijada en `CONFIGURACION!$B$4` (`$40.000`). Al ser `E2` negativo, el signo `+` ejecuta una sustracción financiera directa (ejemplo: `$200.000 + (-2 * $40.000) = $200.000 - $80.000 = $120.000`).
* `MAX(0; ...)`: **Función de barrera o piso financiero.** Compara el saldo resultante contra 0 y devuelve el valor mayor. Evita que un exceso de equivocaciones genere descuentos sobre el salario base o saldos negativos para la empresa.

#### 4.2.7. Columna G: Total Bonificación (`Total_Bonificacion`)
Totaliza la liquidación neta a transferir o entregar en nómina al colaborador:
```excel
=SI(A2 = ""; ""; D2 + F2)
```
* `=SI(A2 = ""; ""; ...)`: Condicional de seguridad por ausencia de empleado.
* `D2`: Importe ganado por concepto de productividad (`Bono_Productividad`).
* `F2`: Importe remanente por concepto de calidad y precisión de entrega (`Bono_Calidad`).
* `+`: Adición simple que consolida el beneficio económico total devengado en el ciclo evaluado.

---

## 5. Configuración de Vistas e Interfaz (UI/UX) en AppSheet

La barra de navegación principal se compone de **cuatro accesos operativos**:

### 5.1. Vista: Formulario de Despacho (`NUEVO REGISTRO`)
* **Tipo:** `Form` en posición inicial (`first`) configurado como pantalla de registro continuo.
* **Captura:** Optimizada mediante entradas táctiles de tipo `Enum` con modo de botones (`Buttons`) para `Puntos_Esfuerzo` (1 a 5) y penalización `Puntos_Error` (0 a -3 con default `0`).
* **Campos automáticos:** `ID_Registro` y `Fecha_Hora` ocultos bajo autocomputo (`UNIQUEID()`, `NOW()`).
* **Recarga automática continua:** Configuración de `Auto re-open = ON` y `Finish view = Auto assign (Go Back)` para mantener el formulario abierto y limpio para el siguiente despacho de forma ininterrumpida.

### 5.2. Vista: Historial del Día (`HISTORIAL HOY`)
* **Tipo:** `Table` en posición central (`middle`), alimentada exclusivamente por el Slice `REGISTRO_HOY` (`[Fecha_Hora] > TODAY()`).
* **Ordenamiento:** Descendente por `Fecha_Hora` para mostrar arriba las órdenes más recientes del turno.
* **Columnas visibles:** `Numero_Factura`, `Empleado`, `Puntos_Esfuerzo` y `Puntos_Error`.

### 5.3. Vista: Resumen Consolidado (`RESUMEN`)
* **Tipo:** `Dashboard` ubicado en posición central (`middle`), con la opción *Use tabs in mobile view* activada para alternar fluidamente mediante pestañas táctiles superiores entre los reportes sin recargas:
  * Pestaña **QUINCENAL** (tabla interna en posición `Ref` con título de rango de fechas quincenal).
  * Pestaña **MENSUAL** (tabla interna en posición `Ref` con título dinámico del mes calendario en curso).
* **Columnas en vista de tabla:** `Nombre_Empleado`, `Total_Puntos`, `Total_Errores` y `Total_Bonificacion`.

### 5.4. Vista: Selector de Fecha (`SELECCIONE FECHA`)
* **Tipo:** `Detail` en posición final (`last`) con la propiedad `QuickEdit columns` habilitada para `Fecha_Referencia`.
* **Propósito:** Permite cambiar interactivamente la fecha de consulta en un solo paso directamente desde la interfaz, recalculando en tiempo real los límites de quincena y mes (`Quincena_Inicio`, `Quincena_Fin`, `Mes_Inicio`, `Mes_Fin`) que alimentan las vistas de resumen.

### 5.5. Reglas de Formato Condicional (Format Rules) en AppSheet
Para optimizar la experiencia visual del operario y alertar al supervisor sobre anomalías de forma intuitiva, se implementaron 7 reglas de formato condicional:

* **5.5.1. Acumulado de Puntos (`PUNTOS_QUINCENAL` y `PUNTOS_MENSUAL`):**
  * **Condición:** `[Total_Puntos] > 0`
  * **Formato:** Texto en Negrilla (`Bold`) de color **Azul (`blue`)** sobre la columna `Total_Puntos`.
* **5.5.2. Alerta de Penalizaciones (`ERRORES_QUINCENAL` y `ERRORES_MENSUAL`):**
  * **Condición:** `[Total_Errores] < 0`
  * **Formato:** Texto en Negrilla (`Bold`) de color **Rojo (`red`)** sobre la columna `Total_Errores`.
* **5.5.3. Recompensa Financiera (`BONOS_QUINCENAL` y `BONOS_MENSUAL`):**
  * **Condición:** Activa permanente.
  * **Formato:** Color de resalte **Verde (`green`)** con ícono `money-bill` sobre las tres columnas monetarias: `Bono_Productividad`, `Bono_Calidad` y `Total_Bonificacion`.
* **5.5.4. Identificación de Empleado Inactivo (`EMPLEADO_ACTIVO?` en `EMPLEADOS`):**
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
  Configuración de entrada en modo `Buttons` para `Puntos_Esfuerzo` (`1 a 5`) y `Puntos_Error` (`0 a -3`), acelerando la captura táctil de datos en bodega.

### 5.7. Columnas Virtuales de Filtrado por Período y Estado (AppSheet)

Para optimizar la experiencia de usuario y el drill-down analítico sin sobrecargar el libro de Google Sheets, se incorporaron las columnas virtuales nativas en AppSheet:
* **`Activo?` (Tabla `EMPLEADOS`):** Tipo `Text` con fórmula `IF([Activo], "SI", "NO")` para desplegar `"SI"` / `"NO"` en la ficha de detalle.
* **`Despachos_Quincena` (Tabla `RESUMEN_QUINCENAL`):** Tipo `List` de referencias a `REGISTRO_DIARIO`. Filtra los despachos de la quincena consultada.
* **`Despachos_Mes` (Tabla `RESUMEN_MENSUAL`):** Tipo `List` de referencias a `REGISTRO_DIARIO`. Filtra los despachos del mes consultado.
* **`Despachos_Quincena` y `Despachos_Mes` (Tabla `EMPLEADOS`):** Tipo `Number` para contabilizar métricas del colaborador en el ciclo.

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
