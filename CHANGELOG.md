# Historial de Cambios y Auditoría del Proyecto (CHANGELOG)

**Empresa:** Interelectricos Group SAS  
**Proyecto:** Sistema de Liquidación y Auditoría de Bonificaciones en Bodega  
**Responsable:** Mauricio Sierra – Aprendiz ADSO SENA  

Todos los cambios notables a nivel arquitectónico, funcional, documental y de seguridad de este proyecto quedan registrados en este archivo para fines de auditoría técnica y trazabilidad.

---

## [Versión 2.2] — 2026-11-04 a 2026-11-05
### Robustez Operativa: Antiduplicados por Colaborador, Tolerancia a Fallos Parciales, Ensamblado Numérico Universal y Mapeo Fonético de Facturas

* **Nuevas Funcionalidades (`feat`) y Resiliencia (`fix`):**
  * **Reintentos Exponenciales ante Fallos de Google Sheets (`503/500/429`):** Política de reintentos (*exponential backoff*) en `bot/src/sheets_service.py` tanto para lectura (`batchGet`) como inserción (`append`). Si los servidores de Google Sheets experimentan un micro-corte temporal (`503 Service Unavailable`), el microservicio reintenta automáticamente con esperas progresivas (1.5s, 3s, 6s) hasta 4 veces antes de arrojar error, garantizando cero interrupciones para el despachador.
  * **Ensamblado Numérico Estructural Universal (Sin Rangos Fijos - Opción B):** Reemplazo de los rangos cerrados (ej. `104xxx`, `36xxx`) en el prompt del modelo multimodal (`bot/src/parser_ai.py`) por reglas universales de ensamblado en español: concatenación exacta por bloques/parejas (*"diez cuarenta y nueve cincuenta y ocho"* $\rightarrow$ `104958`), preservación de dígitos repetidos (*"treinta y seis seis cero cero"* $\rightarrow$ `36600`) y cantidades continuas. Garantiza escalabilidad indefinida ante cualquier consecutivo futuro (`108xxx`, `125xxx`, `2xxxxx`).
  * **Mapeo Fonético y Homófonos de Facturación:** Reconocimiento auditivo tolerante a ruido de bodega y modismos en audios de WhatsApp:
    * `IC` (Factura de contado): *"IC"*, *"ICE"*, *"EC"*, *"Ais"*, *"I ce"*, *"I-C"*, *"contado"*.
    * `DP` (Factura de tirilla blanca - contado): *"DP"*, *"DePe"*, *"Pepe"*, *"BP"*, *"TP"*, *"Bete"*, *"D-P"*, *"tirilla"*.
    * `IR` (Factura de remisión crédito): *"IR"*, *"ER"*, *"YR"*, *"Ye-erre"*, *"I-erre"*, *"I-R"*, *"remisión"*, *"crédito"*.
  * **Blindaje del Término Genérico "Factura":** En la empresa todas las entregas son facturas; se instruye a Gemini que la palabra *"factura"* jamás se mapee por defecto a `IC`. Si falta la sigla o naturaleza, se clasifica como incompleto (`null`).
  * **Tolerancia a Fallos Parciales en Lotes:** Si en un audio o texto con múltiples despachos alguno carece de datos críticos (ej. falta auxiliar o tipo de factura), el bot **no cancela la tanda completa**: guarda inmediatamente todos los registros válidos en Google Sheets y notifica al final qué factura puntual requiere reenvío (`bot/src/sheets_service.py`, `bot/src/whatsapp_service.py`).
  * **Filtro Antiduplicados por Colaborador en Memoria (`batchGet`):** Control cruzado `(ID_Empleado, Tipo_Factura, Numero_Factura)` que descarta comprobantes repetidos dictados al mismo auxiliar en el mismo audio o registrados previamente en la hoja, pero permitiendo pedidos compartidos entre diferentes auxiliares.
  * **Consola de Pruebas con Escucha Dual (`bot/tests/test_bot.py`):** Arquitectura híbrida que combina la cola de Green API con sondeo de historial saliente reciente (`lastOutgoingMessages`), habilitando pruebas en vivo en el chat personal ("Mensajes a ti mismo") sin bloqueos de servidor.
* **Mantenimiento y Documentación (`docs`):**
  * **Sección 6.3 en Runbook (`docs/RUNBOOK_SOPORTE_TECNICO.md`):** Protocolo técnico de mantenimiento del Prompt ante altas/bajas de auxiliares de bodega y creación de nuevos prefijos de factura.
  * **Alineación Comercial en Manual Operativo e Informe Técnico:** Estandarización de `IC` (contado), `DP` (tirilla blanca) e `IR` (remisión crédito) en toda la suite documental, con regeneración de archivos `.docx` institucionales.

---

## [Versión 2.1] — 2026-10-30
### Integración de Captura Automatizada por WhatsApp con IA Multimodal (Serverless)

* **Nuevas Funcionalidades (`feat`):**
  * **Bot de WhatsApp (`/bot`):** Nuevo canal de entrada que coexiste en tiempo real con AppSheet escribiendo sobre la misma tabla transaccional `REGISTRO_DIARIO` en Google Sheets.
  * **Procesamiento Multimodal con Gemini API (`gemini-3.5-flash`):** Extracción estructurada en JSON a partir de **notas de voz (`.ogg`)** o **mensajes de texto** en lenguaje natural enviados por el jefe de bodega (`bot/src/parser_ai.py`).
  * **Registro Individual y por Bloques (Lotes):** Capacidad de procesar tanto 1 despacho suelto (`"IC 2021 Edward 2 puntos 1 error"`) como múltiples despachos acumulados en un solo audio o texto, ejecutando una única lectura del catálogo `EMPLEADOS` y una única inserción masiva (`batch append`) en `REGISTRO_DIARIO` (`bot/src/sheets_service.py`).
  * **Despliegue Serverless en Vercel (`bot/api/webhook.py`):** Función en la nube con ejecución bajo demanda (costo $0 y aislamiento total de la red interna y del Windows Server corporativo).
* **Seguridad y Validaciones (`fix`):**
  * **Bloqueo Estricto por Remitente (*Fail-Closed*):** Restricción en `webhook.py` y `test_bot.py` para procesar y responder exclusivamente al número autorizado configurado en `CHAT_ID_PRUEBA`, ignorando cualquier conversación normal o de terceros en el WhatsApp corporativo.
  * **Seguro de Integridad de Datos (Cero Invención):** Regla estricta en el prompt del modelo y validador local que bloquea la escritura en Google Sheets si falta el tipo de comprobante (`IC`, `DP`, `IR`), el consecutivo numérico, el auxiliar activo o si los puntos están fuera de rango (`1..5` esfuerzo, `0..-3` error), notificando por WhatsApp el motivo exacto.

---

## [Versión 2.0] — 2026-10-22 a 2026-10-29
### Refactorización Arquitectónica: Motor Matricial Quincenal y Ergonomía Móvil

* **Modelo de Datos y Liquidación (`feat` / `fix`):**
  * **Migración a Liquidación Quincenal (`BASE_HISTORICA`):** Sustitución de las tablas rígidas `FILTRO_FECHAS`, `RESUMEN_QUINCENAL` y `RESUMEN_MENSUAL` por una única matriz dinámica en memoria gobernada por `LET + MAP + LAMBDA + QUERY` en Google Sheets.
  * **Tablero Ejecutivo (`LIQUIDACION_MES`):** Consolidación mensual y quincenal con cálculo automático de bonos productivos y de calidad blindados bajo la normativa UGPP (Ley 1393 de 2010).
  * **Unificación de Puntaje de Despacho:** Simplificación de la calificación operativa en `Puntos_Esfuerzo` (`1` a `5`) y `Puntos_Error` (`0` a `-3`).
* **Interfaz Móvil en AppSheet (`feat` / `fix`):**
  * **Separación Ergonómica del Comprobante:** División física entre `Tipo_Factura` (botonera `IC, DP, IR`) y `Numero_Factura` (`Number` con apertura directa del teclado numérico en móvil), unificados visualmente mediante la columna virtual `Factura` (`[Tipo_Factura] & "-" & [Numero_Factura]`).
  * **Flujo de Captura Continua (`Auto re-open`):** Configuración de `NUEVO REGISTRO` como vista de inicio (`Starting view`) con reapertura automática tras guardar.
  * **Navegación Drill-Down (`Año > Mes > Quincena`):** Consulta jerárquica en la vista `LIQUIDACION` sin selectores manuales de calendario.
* **Documentación y Manuales (`docs`):**
  * Sincronización integral de `INFORME_TECNICO_Y_MANUAL_DE_CONFIGURACION.md`, `MANUAL_DE_USUARIO_OPERATIVO.md`, `RUNBOOK_SOPORTE_TECNICO.md`, `schemas/appsheet_config.md` y `SANDBOX_PRUEBAS.md` con capturas reales V2.0 y generador automatizado `scripts/build_docs.py` compatible con Microsoft Word y WPS Office.

---

## [Versión 1.0] — 2026-10-05 a 2026-10-16
### Lanzamiento Inicial del Sistema de Bonificaciones (AppSheet + Google Sheets)

* Diseño inicial del libro relacional `BD_BONIFICACIONES_BODEGA` y plantilla limpia `templates/BD_BONIFICACIONES_BODEGA_TEMPLATE.xlsx`.
* Implementación de la ventana de auditoría de 15 minutos para edición de registros (`TOTALMINUTES(NOW() - [Fecha_Hora]) <= 15`) y bloqueo estructural de eliminaciones (`Deletes` deshabilitado).
* Creación de la guía de instalación móvil (`GUIA_INSTALACION_APP.md`) con código QR y manuales operativos iniciales.

---

## Registro Histórico de Commits (Auditoría Git)

| Fecha | Commit | Tipo | Descripción del Cambio |
| :---: | :---: | :---: | :--- |
| `2026-11-05` | `6dc72e9` | `feat(bot)` | Ensamblado numérico universal sin rangos, mapeo fonético de facturas y escucha dual en test |
| `2026-11-04` | `6baf820` | `feat(bot)` | Tolerancia a fallos parciales, agrupación por colaborador y afinamiento fonético de nomenclaturas |
| `2026-11-04` | `6b26b93` | `docs` | Optimizar maquetación docx, corregir marca Interelectricos y estructurar galerías y estilos |
| `2026-11-03` | `1da6054` | `feat` | Validación antiduplicados por colaborador en AppSheet, Bot de WhatsApp y documentación |
| `2026-10-30` | `e7c5504` | `fix(bot)` | Restringir respuesta del bot únicamente al chat autorizado (*Fail-Closed*) |
| `2026-10-30` | `a2e2c2c` | `feat(bot)` | Soportar registro de despachos por lotes en un solo audio o texto |
| `2026-10-30` | `bf4153a` | `feat(bot)` | Integrar bot de WhatsApp con Gemini API y Google Sheets para registro de despachos |
| `2026-10-29` | `62c30b7` | `docs` | Actualizar manual operativo V2 con nuevas capturas y corregir maquetación `.docx` para WPS |
| `2026-10-28` | `bad0f6f` | `docs` | Sincronizar manual operativo, informe técnico y runbook a arquitectura V2.0 |
| `2026-10-28` | `526fe94` | `docs(images)` | Actualizar capturas V2 y sincronizar esquema con app real |
| `2026-10-28` | `9731a1e` | `docs(appsheet)` | Actualizar configuración técnica V2.0 y consolidar sandbox de pruebas |
| `2026-10-24` | `984089d` | `fix(liquidacion)` | Corregir consolidación mensual por quincenas y detallar fórmulas analíticas |
| `2026-10-23` | `8fe41ef` | `fix(appsheet)` | Documentar recarga continua con `Auto re-open` y alinear manuales |
| `2026-10-22` | `f4827fc` | `feat(modelo)` | Migrar a liquidación quincenal y unificar puntaje único de despacho |
| `2026-10-16` | `57ebdca` | `docs(appsheet)` | Estandarizar *display names* en español para vistas y acciones |
| `2026-10-16` | `5e3850a` | `style(images)` | Integrar marco gris carbón en capturas para compatibilidad con GitHub |
| `2026-10-15` | `75a1c93` | `style(docs)` | Oscurecer bordes de imágenes para mayor contraste |
| `2026-10-15` | `1a1eba5` | `docs` | Formalizar estilo, agregar bordes a imágenes y actualizar enlace de instalación |
| `2026-10-15` | `8b1e2a0` | `docs` | Optimizar tamaño de imágenes en manuales y sincronizar vistas de la app |
| `2026-10-15` | `f3ef9c5` | `docs` | Sincronizar `appsheet_config` con app real, regla de meta mínima y capturas |
| `2026-10-08` | `ffe4bb6` | `docs` | Actualizar manual técnico y guías operativas |
| `2026-10-07` | `5e1faba` | `feat` | Desagregar puntos de factura y esfuerzo en hojas de resumen y actualizar documentación |
| `2026-10-05` | `e1a20cb` | `docs` | Alinear fórmulas de filtro de fechas y valores monetarios con plantilla Excel |
| `2026-10-05` | `eacc086` | `feat` | Documentación técnica y operativa, esquemas AppSheet y plantilla inicial |

