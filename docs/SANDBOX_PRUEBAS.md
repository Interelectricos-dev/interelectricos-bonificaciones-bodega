# Sandbox de Pruebas y Evolución del Sistema de Bonificaciones

**Proyecto:** Sistema de Liquidación y Auditoría de Bonificaciones en Bodega  
**Entorno:** Aplicación de Pruebas / Sandbox (No productivo)  
**Fecha de Inicio de Pruebas:** 23 de Octubre de 2026  
**Objetivo:** Evaluar la viabilidad operativa y la experiencia de usuario (UX) al separar la captura del tipo de documento y el consecutivo numérico en el formulario de despacho.

---

## 1. Justificación y Análisis de la Experiencia Operativa (UX)

### Situación Anterior (Producción Actual)
* **Campo:** `Numero_Factura` de tipo `Text`.
* **Comportamiento:** El despachador debe teclear manualmente letras, guiones y números (ejemplo: `IR-12345`).
* **Limitación:** El teclado del celular se abre en modo alfanumérico completo, aumentando el tiempo de digitación y el riesgo de errores tipográficos en bodega.

### Propuesta en Evaluación (Entorno de Pruebas)
* **Paso 1 (Botonera):** Selección táctil en un toque del tipo de comprobante (`IR`, `IC`, `NCR`, etc.) mediante botones `Enum`.
* **Paso 2 (Teclado Numérico Puro):** Campo `Numero_Factura` configurado como `Number`, levantando automáticamente el teclado numérico de dígitos grandes en el teléfono móvil.
* **Paso 3 (Consolidación Visual):** Columna virtual `Factura_Completa` que concatena ambos valores para visualización y auditoría.

---

## 2. Definición de la Columna `LABEL`: ¿Por qué usar una Columna Virtual?

### El problema de usar `Numero_Factura` como LABEL:
Si se deja `Numero_Factura` como `LABEL? = TRUE`:
1. En el historial, detalles y listas solo aparecerá el número (ejemplo: `123`).
2. **Ambigüedad operativa:** Al existir múltiples tipos de comprobantes, pueden coincidir en el mismo número consecutivo (ej. `IR 123` frente a `IC 123`). Un operario o supervisor no sabría a qué serie corresponde el despacho a simple vista.

### La Solución Técnica Recomendada:
Crear una **Columna Virtual** llamada `Factura_Completa` y configurarla como el **`LABEL` oficial de `REGISTRO_DIARIO`**:

* **¿Por qué?**
  * Toda lista, tarjeta, historial de despachos o relación mostrará siempre la identificación humana completa e inequívoca: `IR-123`.
  * La búsqueda por lupa (`Search? = TRUE`) permitirá encontrar el registro buscando tanto por `"IR-123"` como solo por el número `"123"`.
  * Google Sheets permanece optimizado almacenando los campos atómicos (`Tipo_Documento` en columna G y `Numero_Factura` en columna D).

---

## 3. Especificación Técnica de Configuración en AppSheet (Pruebas)

### A. Columna Física en Google Sheets (Hoja `REGISTRO_DIARIO`)
* **Columna G:** `Tipo_Documento` *(ubicada al final de la tabla para no desplazar columnas A a F ni alterar fórmulas en hojas de resumen)*.

### B. Configuración de Columnas en AppSheet (`Data > Columns > REGISTRO_DIARIO`)

| Columna | Tipo | KEY? | LABEL? | SHOW? | EDITABLE? | REQUIRE? | SEARCH? | Configuración Clave |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :--- |
| `Tipo_Documento` | `Enum` | ⬜ | ⬜ | ☑️ | ☑️ | ☑️ | ⬜ | **Base type:** `Text`<br>**Input mode:** `Buttons`<br>**Values:** `IR, IC, NCR`<br>**Initial value:** `"IR"` |
| `Numero_Factura` | `Number` | ⬜ | ⬜ | ☑️ | ☑️ | ☑️ | ☑️ | **Type:** `Number`<br>Dispara teclado numérico directo. |
| `Factura_Completa` *(Virtual)* | `Text` | ⬜ | ☑️ | ☑️ | ⬜ | ⬜ | ☑️ | **App formula:**<br>`[Tipo_Documento] & "-" & [Numero_Factura]`<br>**Display name:** `Factura` |

---

## 4. Bitácora de Pruebas y Resultados Observados

| Fecha | Prueba Ejecutada | Resultado Esperado | Resultado Observado | Estado |
| :---: | :--- | :--- | :--- | :---: |
| 23/10/2026 | Inserción de Columna G en Sheets | No alterar fórmulas de `RESUMEN_QUINCENAL` | Verificado. Ninguna fórmula de resumen se movió ni afectó. | Exitoso |
| 23/10/2026 | Configuración de `LABEL` | Resolver duplicidad de números entre tipos de factura | Verificado con columna virtual `Factura_Completa` como LABEL. | Exitoso |
| 24/10/2026 | Auditoría de liquidación en `RESUMEN_MENSUAL` (400 registros) | Consolidar bonos mensuales como la suma exacta de Q1 + Q2 independiente | Identificado desfase por acumulación de puntos mensuales sobre escala quincenal. Se implementaron columnas auxiliares H:O para desglosar Q1 y Q2 y totalizar en A:G. Regenerate Schema ejecutado y columnas ocultas. Resultados exactos ($150k prod, $120k cal). | Exitoso |
| 26/10/2026 | Diseño de Escala Dinámica en `CONFIGURACION` | Que al cambiar la Meta Base (`B2`), los tramos de puntos se recalculen solos | Fórmulas relativas evaluadas (`$B$2 + 1`, `$B$2 + 20`, etc.). Verificada compatibilidad total con `BUSCARV(..., TRUE)` en `RESUMEN_QUINCENAL` y `RESUMEN_MENSUAL` sin tocar ninguna fórmula de liquidación. | Documentado para Sandbox |
| 26/10/2026 | Calibración Financiera y Escala de Puntos (Salario Mínimo) | Definir montos y escalas acordes a Ley 1393/2010 (Regla del 40%) y flujo real de bodega | Identificado que la escala actual ($800k quincenal) duplica el SMLV y colapsa ante la UGPP. Diseñada propuesta con tope quincenal de $250k (~35% SMLV), tramos de 50 pts por sobre-esfuerzo y protocolo para incorporar las IR. | Documentado para Decisión Gerencial |
| 27/10/2026 | Arquitectura de Liquidación Dinámica y Dashboard Ejecutivo | Automatizar la liquidación quincenal y mensual con cero filas manuales y cero redundancias en `REGISTRO_DIARIO` | Creado motor en memoria en `BASE_HISTORICA` con `LET` + `MAP` + `QUERY` generando Quincenas (Q1/Q2) y Meses (1..12). Se eliminaron columnas calculadas repetitivas en `REGISTRO_DIARIO` (vuelve a 7 columnas puras). Creado Dashboard interactivo `LIQUIDACION_MES` con selectores dinámicos y valores en pesos ($). | Validado en Sandbox |
| 27/10/2026 | Centralización de Vistas en AppSheet y Depuración de Tablas | Unificar vistas de consulta en una sola pantalla ejecutiva (`Liquidación`) y retirar dependencias frágiles | Conectada `BASE_HISTORICA` a AppSheet con drill-down (Año > Mes > Quincena). Se eliminaron las vistas y tablas obsoletas `RESUMEN_QUINCENAL`, `RESUMEN_MENSUAL` y `FILTRO_FECHAS`. Se sanearon y eliminaron las columnas virtuales `Despachos_Quincena` y `Despachos_Mes` en `EMPLEADOS`, eliminando errores de sincronización y acelerando la app. Calibrada Meta Base en 300 pts. | Exitoso en Sandbox |

---

## 5. Propuesta Técnica: Escala de Productividad Dinámica (Vinculada a Meta Base)

### A. Justificación
Actualmente, la tabla de escalas en la hoja `CONFIGURACION` (`A8:B11`) contiene números estáticos quemados (`101 a 120`, `121 a 150`, etc.). Si la administración decide cambiar la **Meta Base Quincenal** de `100` a `200` o `250` puntos, un operario o administrador tendría que modificar manualmente las 8 celdas de rangos, aumentando el riesgo de errores tipográficos que dañarían el `BUSCARV` de nómina.

### B. Especificación de Fórmulas Dinámicas en `CONFIGURACION`

Al convertir los límites de los tramos en fórmulas relativas ancladas a la celda `B2` (`Meta Base Quincenal`), cualquier cambio en la meta recalcula instantáneamente toda la matriz de bonificaciones:

| Fila | Columna A (`DESDE`) | Columna B (`HASTA`) | Columna C (`BONO($)`) | Propósito / Comportamiento |
| :---: | :--- | :--- | :---: | :--- |
| **8** | `=$B$2 + 1` | `=$B$2 + 20` | `$150.000` | **Tramo 1:** Inicia 1 punto arriba de la meta, con ancho de 20 pts. |
| **9** | `=B8 + 1` | `=$B$2 + 50` | `$300.000` | **Tramo 2:** Inicia tras el tramo 1, con tope en meta + 50 pts. |
| **10** | `=B9 + 1` | `=$B$2 + 80` | `$450.000` | **Tramo 3:** Inicia tras el tramo 2, con tope en meta + 80 pts. |
| **11** | `=B10 + 1` | `"o más"` | `$600.000` | **Tramo 4:** Inicia tras el tramo 3, tope máximo de bonificación. |

### C. Simulación de Comportamiento

* **Escenario Actual (Meta Base `B2 = 100`):**
  * Tramo 1: `101` a `120` $\rightarrow$ $150.000
  * Tramo 2: `121` a `150` $\rightarrow$ $300.000
  * Tramo 3: `151` a `180` $\rightarrow$ $450.000
  * Tramo 4: `181` o más $\rightarrow$ $600.000

* **Escenario de Ajuste (Meta Base `B2 = 200`):**
  * Tramo 1: `201` a `220` $\rightarrow$ $150.000
  * Tramo 2: `221` a `250` $\rightarrow$ $300.000
  * Tramo 3: `251` a `280` $\rightarrow$ $450.000
  * Tramo 4: `281` o más $\rightarrow$ $600.000

### D. Impacto Técnico en el Sistema
* **Cero cambios en `RESUMEN_QUINCENAL` y `RESUMEN_MENSUAL`:**
  Las hojas de liquidación usan `=BUSCARV(C2; CONFIGURACION!$A$8:$C$11; 3; VERDADERO)`. Al usar coincidencia aproximada (`VERDADERO`), el motor de Google Sheets lee los nuevos límites dinámicos sin necesidad de editar ninguna fórmula de liquidación.
* **Integridad garantizada:** La condición de seguridad previa `=SI(C2 <= CONFIGURACION!$B$2; 0; ...)` garantiza que nadie reciba bono si no supera la nueva meta.

---

## 6. Propuesta de Calibración Financiera y Escalas de Puntos (Alineación Salario Mínimo)

### 6.1. Marco Legal y Fiscal: La Regla del 40% (Ley 1393 de 2010 / UGPP)
En Colombia, los pagos laborales no constitutivos de salario (bonificaciones por mera liberalidad o metas operativas) **no pueden exceder el 40% de la remuneración total mensual del colaborador**.
* Si el bono excede ese 40%, el excedente debe cotizar obligatoriamente a seguridad social (salud, pensión y ARL), generando sobrecostos imprevistos o sanciones de la UGPP.
* Para un operario con Salario Mínimo Legal Vigente (~$1.300.000 a $1.400.000 básico), el **tope máximo mensual seguro de bonificaciones** debe situarse entre **$450.000 y $500.000** (es decir, un máximo quincenal de **$225.000 a $250.000** sumando calidad y productividad).

### 6.2. Comparativa Financiera: Configuración Actual vs. Propuesta Calibrada

| Componente | Configuración Actual (En Producción) | Propuesta Calibrada (Salario Mínimo) | Justificación de Negocio |
| :--- | :---: | :---: | :--- |
| **Bono Base Calidad (Quincenal)** | **$200.000** | **$70.000** | Fondo base quincenal proporcional (~5% del salario mensual). |
| **Penalización por Error** | -$40.000 / error | -$15.000 / error | Al 4to o 5to error pierde el bono de calidad sin tocar el sueldo base. |
| **Productividad - Tramo 1** | $150.000 | **$50.000** | Reconocimiento inicial por cruzar la meta (+~7% básico). |
| **Productividad - Tramo 2** | $300.000 | **$90.000** | Rendimiento medio-alto constante (+~13% básico). |
| **Productividad - Tramo 3** | $450.000 | **$130.000** | Alto desempeño quincenal (+~19% básico). |
| **Productividad - Tramo 4 (Tope)** | $600.000 | **$180.000** | Tope máximo por sobre-esfuerzo (+~26% básico). |
| **Tope Máximo Quincenal (Prod + Cal)** | **$800.000** | **$250.000** | Máximo devengado en 15 días. |
| **Tope Máximo Mensual (Prod + Cal)** | **$1.600.000** *(Supera el 100% del SMLV)* | **$500.000** *(~35% del SMLV)* | **100% blindado ante la regla del 40% de la UGPP.** |

### 6.3. Justificación de los Rangos de Puntos: ¿Por qué ensanchar los tramos?
1. **La Meta como frontera (`Meta + 1`):** 
   * Se descarta la creación de un "tope muerto" entre la meta y el primer bono. Si la meta es 200, el bono debe arrancar en 201 para evitar frustración en el trabajador.
2. **Ensanchar los tramos de 20 a 50 puntos:**
   * En AppSheet, el promedio real por despacho es de **2.6 puntos de esfuerzo**.
   * Un tramo de solo 20 puntos se consigue con apenas **7 u 8 despachos** (2 horas de trabajo), haciendo que los operarios alcancen el tope en la primera semana.
   * Tramos de **50 puntos** representan entre **18 y 20 despachos adicionales** (~2 días completos de sobre-esfuerzo sostenido), manteniendo la motivación durante toda la quincena.

#### Matriz de Escala Recomendada (Ejemplo con Meta Base = 200 pts):
* **Hasta 200 pts:** $0 *(Cumplimiento básico contractual cubierto por el salario mínimo)*.
* **201 a 250 pts (+50 pts):** **$50.000** *(Tramo 1)*
* **251 a 300 pts (+50 pts):** **$90.000** *(Tramo 2)*
* **301 a 350 pts (+50 pts):** **$130.000** *(Tramo 3)*
* **351 pts o más:** **$180.000** *(Tramo 4 - Tope Máximo)*

### 6.4. Protocolo de Acción ante la Llegada de las Remisiones (`IR`)
Cuando el jefe de despacho entregue los datos de las facturas tipo remisión (`IR`):
1. **Consolidación:** Ingresar los valores en la columna `G` (`IR`) de la tabla de septiembre.
2. **Cálculo del Mix Total:** Determinar el porcentaje definitivo de participación (`% IC`, `% DP`, `% IR`).
3. **Simulación Cruzada:**
   * Evaluar cuántos puntos totales acumulan Beto, Edward y Sneider sumando las `IR`.
   * Contrastar si la Meta Base Quincenal óptima debe ser de **200, 220 o 250 puntos** para que el 70% del equipo alcance al menos el Tramo 1 o 2.
4. **Presentación Gerencial:** Entregar al jefe de despacho el comparativo financiero (Costo actual vs Costo calibrado) para su aprobación final.

---

## 7. Arquitectura de Liquidación Dinámica y Dashboard Ejecutivo

### 7.1. Diagnóstico de Eficiencia y Normalización
Para evitar la duplicación de datos y la sobrecarga de fórmulas fijas en hojas satélites, se diseñó un modelo desacoplado en dos capas:
1. **Eliminación de Redundancia en `REGISTRO_DIARIO`:** Se mantiene la tabla transaccional limpia con sus 7 columnas atómicas originales (`ID_Registro`, `Fecha_Hora`, `Empleado`, `Tipo_Factura`, `Numero_Factura`, `Puntos_Esfuerzo`, `Puntos_Error`). Se descarta almacenar columnas físicas repetitivas de "Quincena" o "Mes" que duplicarían miles de cadenas idénticas.
2. **Generación al Vuelo en Memoria:** Las dimensiones temporales (`Quincena` como `Q1` o `Q2`, y `Mes` numérico real 1..12) se calculan en la memoria de ejecución durante la consulta de agregación.

---

### 7.2. Especificación Técnica de las Hojas

#### A. Hoja `BASE_HISTORICA` (Motor de Datos en Segundo Plano - Oculta)
* **Celda A1 (Generador Matricial Dinámico):**
```excel
=LET(
  fechas, REGISTRO_DIARIO!B2:B, 
  quincenas, MAP(fechas, LAMBDA(f, IF(f="", "", IF(DAY(f)<=15, "Q1", "Q2")))), 
  meses, MAP(fechas, LAMBDA(f, IF(f="", "", MONTH(f)))), 
  QUERY(
    {REGISTRO_DIARIO!A2:G, quincenas, meses}, 
    "SELECT YEAR(Col2), Col9, Col8, Col3, SUM(Col6), SUM(Col7) 
     WHERE Col1 IS NOT NULL 
     GROUP BY YEAR(Col2), Col9, Col8, Col3 
     ORDER BY YEAR(Col2) DESC, Col9 DESC, Col8 ASC 
     LABEL YEAR(Col2) 'Año', Col9 'Mes', Col8 'Quincena', Col3 'ID_Empleado', SUM(Col6) 'Pts_Esfuerzo', SUM(Col7) 'Pts_Error'"
  )
)
```
* **Columnas Calculadas de Liquidación Financiera:**
  * **G1 (`Nombre`):** `=MAP(D2:INDEX(D:D, COUNTA(D:D)), LAMBDA(id, IF(id="", "", IFERROR(VLOOKUP(id, EMPLEADOS!A:B, 2, FALSE), id))))`
  * **H1 (`Bono Productivo`):** `=MAP(E2:INDEX(E:E, COUNTA(D:D)), LAMBDA(pts, IF(pts="", "", IF(pts < CONFIGURACION!$B$3, 0, IF(pts < (CONFIGURACION!$B$3 + 50), CONFIGURACION!$C$9, IF(pts < (CONFIGURACION!$B$3 + 100), CONFIGURACION!$C$10, IF(pts < (CONFIGURACION!$B$3 + 150), CONFIGURACION!$C$11, CONFIGURACION!$C$12)))))))`
  * **I1 (`Bono Calidad`):** Condicionado al cumplimiento de la meta base (`E < CONFIGURACION!$B$3` $\rightarrow$ `$0`):
    `=MAP(E2:INDEX(E:E, COUNTA(D:D)), F2:INDEX(F:F, COUNTA(D:D)), LAMBDA(pts, err, IF(pts="", "", IF(pts < CONFIGURACION!$B$3, 0, MAX(0, CONFIGURACION!$B$4 + (err * CONFIGURACION!$B$5))))))`
  * **J1 (`Total BONO`):** `=MAP(H2:INDEX(H:H, COUNTA(D:D)), I2:INDEX(I:I, COUNTA(D:D)), LAMBDA(prod, cal, IF(prod="", "", prod + cal)))`

---

#### B. Hoja `LIQUIDACION_MES` (Dashboard Ejecutivo de Consulta)
* **Barra de Control Superior:**
  * `A2`: Año (`2025`, `2026`, `2027`)
  * `B2`: Mes (`Enero`, `Febrero`, ..., `Octubre`, `Noviembre`, `Diciembre`)
  * `C2`: Número de Mes automático mediante `SWITCH(LOWER(TRIM(B2)), "enero", 1, ..., "octubre", 10, ...)`
  * `D2`: Selector de Quincena (`TODAS`, `Q1`, `Q2`)
* **Fórmula de Consulta en Celda A5:**
```excel
=IFERROR(
  QUERY(
    BASE_HISTORICA!A2:J, 
    "SELECT Col3, Col4, Col7, Col5, Col6, Col8, Col9, Col10 
     WHERE Col1 = " & A2 & " AND Col2 = " & C2 & 
     IF(OR(UPPER(D2)="TODAS", D2=""), "", " AND Col3 = '" & D2 & "'")
  ), 
  "No hay registros para este período seleccionado"
)
```
* **Comportamiento:** Extrae instantáneamente solo las quincenas y colaboradores del período seleccionado, presentando Quincena, ID, Nombre, Puntos, Errores y los tres rubros en pesos ($) reales listos para pago de nómina.

---

## 8. Implementación en AppSheet: Vista de Bonificaciones y Experiencia de Usuario (UX)

### 8.1. Especificación del Modelo de Datos (`Data > Columns > BASE_HISTORICA`)

| Columna | Tipo | KEY? | LABEL? | SHOW? | EDITABLE? | SEARCH? | Configuración Clave / App Formula |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :--- |
| `ID_Liquidacion` *(Virtual)* | `Text` | ☑️ | ⬜ | ⬜ | ⬜ | ⬜ | `CONCATENATE([Año], "-", [Mes], "-", [Quincena], "-", [ID_Empleado])` |
| `Año` | `Number` | ⬜ | ⬜ | ☑️ | ⬜ | ☑️ | Formato número entero sin separador de miles. |
| `Mes` | `Number` | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | Oculto (1..12). |
| `Mes_Nombre` *(Virtual)* | `Text` | ⬜ | ⬜ | ☑️ | ⬜ | ☑️ | `SWITCH([Mes], 1, "Enero", 2, "Febrero", 3, "Marzo", 4, "Abril", 5, "Mayo", 6, "Junio", 7, "Julio", 8, "Agosto", 9, "Septiembre", 10, "Octubre", 11, "Noviembre", 12, "Diciembre", "")` |
| `Quincena` | `Text` | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | Código base (`Q1` / `Q2`). |
| `Quincena_Nombre` *(Virtual)* | `Text` | ⬜ | ⬜ | ☑️ | ⬜ | ☑️ | `IF([Quincena] = "Q1", "1ra Quincena", "2da Quincena") & " · " & [Mes_Nombre] & " " & [Año]` *(Ejemplo: `1ra Quincena · Octubre 2026`)*. |
| `ID_Empleado` | `Number` | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ID numérico del colaborador. |
| `Nombre` | `Text` | ⬜ | ☑️ | ☑️ | ⬜ | ☑️ | **LABEL oficial de la tabla**. |
| `Pts_Esfuerzo` | `Number` | ⬜ | ⬜ | ☑️ | ⬜ | ⬜ | Entero. |
| `Pts_Error` | `Number` | ⬜ | ⬜ | ☑️ | ⬜ | ⬜ | Entero (con valores negativos). |
| `Bono Productivo` | `Price` | ⬜ | ⬜ | ☑️ | ⬜ | ⬜ | Currency: COP ($), sin decimales. |
| `Bono Calidad` | `Price` | ⬜ | ⬜ | ☑️ | ⬜ | ⬜ | Currency: COP ($), sin decimales. |
| `Total BONO` | `Price` | ⬜ | ⬜ | ☑️ | ⬜ | ☑️ | Currency: COP ($), sin decimales. |

---

### 8.2. Especificación de Vistas (UX / Navigation)

#### A. Vista Principal (`Bonificaciones`)
* **Data Source:** `BASE_HISTORICA`
* **View Type:** `Table`
* **Group by:**
  1. `Año` (Descending)
  2. `Mes_Nombre` (Ascending)
  3. `Quincena_Nombre` (Ascending)
* **Column Order (Pantalla Limpia - Revelación Progresiva):**
  1. `Nombre`
  2. `Pts_Esfuerzo`
  3. `Pts_Error`
  4. `Total BONO`
* **Sort by:** `Nombre` (Ascending)

#### B. Vista Detalle (`BASE_HISTORICA_Detail`)
* **Header:** Columna virtual `Quincena_Nombre` como encabezado principal destacado.
* **Column Order (Desglose Auditoría):**
  1. `Nombre`
  2. `Pts_Esfuerzo`
  3. `Pts_Error`
  4. `Bono Productivo`
  5. `Bono Calidad`
  6. `Total BONO`

---

### 8.3. Reglas de Formato Visual (Format Rules)

Para resaltar visualmente el desempeño operativo en AppSheet (`App > Format Rules`):

1. **Meta de Productividad Cumplida (Azul):**
   * **Target data:** `BASE_HISTORICA`
   * **Target columns:** `Pts_Esfuerzo`
   * **Condition:** `[Pts_Esfuerzo] >= 100` *(o `[Pts_Esfuerzo] >= INDEX(CONFIGURACION[Meta Base Quincenal], 1)`)*
   * **Format:** Text Color `#1A73E8` (Azul corporativo), `Bold = TRUE`, Icono `star` o `check_circle`.

2. **Alertas de Calidad / Errores (Rojo):**
   * **Target data:** `BASE_HISTORICA`
   * **Target columns:** `Pts_Error`
   * **Condition:** `[Pts_Error] < 0`
   * **Format:** Text Color `#D93025` (Rojo advertencia), `Bold = TRUE`, Icono `error_outline` o `warning`.

3. **Bono Ganado / Dinero a Pagar (Verde):**
   * **Target data:** `BASE_HISTORICA`
   * **Target columns:** `Total BONO`
   * **Condition:** `[Total BONO] > 0`
   * **Format:** Text Color `#188038` (Verde éxito), `Bold = TRUE`, Icono `payments` o `monetization_on`.

---

### 8.4. Desacoplamiento de Tablas Satélites y Saneamiento de `EMPLEADOS`

Para lograr una arquitectura escalable y de alto rendimiento en AppSheet, se ejecutaron las siguientes acciones de saneamiento en el modelo de datos:

1. **Retiro de Tablas Satélites Obsoletas:**
   * Se eliminaron las vistas y tablas `RESUMEN_QUINCENAL`, `RESUMEN_MENSUAL` y `FILTRO_FECHAS`.
   * **Justificación:** Estas hojas dependían de fechas estáticas forzadas manualmente y fórmulas `SUMIFS` pesadas. Toda la reportería histórica y ejecutiva quedó consolidada en la tabla única `BASE_HISTORICA` (en AppSheet) y `LIQUIDACION_MES` (en Google Sheets).

2. **Eliminación de Columnas Virtuales en `EMPLEADOS`:**
   * Se borraron las columnas virtuales `Despachos_Quincena` y `Despachos_Mes` de la tabla `EMPLEADOS`.
   * **Justificación Técnica:**
     * **Eliminación de dependencias rotas:** Ambas columnas calculaban conteos referenciando la tabla `FILTRO_FECHAS`, arrojando errores al retirarla.
     * **Optimización de rendimiento:** Cada subconsulta `COUNT(SELECT(...))` en columnas virtuales ralentizaba el tiempo de sincronización móvil.
     * **Alineación con el modelo de compensación:** Las bonificaciones se liquidan por **Puntos de Esfuerzo** y no por conteo de facturas. El desempeño real se audita de forma nativa desde la vista centralizada de `Liquidación`.



