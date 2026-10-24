# Sandbox de Pruebas: Desacoplamiento de Tipo y Número de Factura

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
