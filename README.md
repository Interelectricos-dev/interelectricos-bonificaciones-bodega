# Sistema de Liquidación y Auditoría de Bonificaciones en Bodega

**Empresa:** Interelectricos Group SAS  
**Proyecto:** Control de Bonificaciones Operativas en Bodega  
**Autor:** Mauricio Sierra – Aprendiz ADSO SENA  
**Versión:** 2.1 (Arquitectura Híbrida AppSheet + Bot de WhatsApp con IA + Google Sheets)  
**Estado:** En Producción  

---

## Descripción General
El sistema **BONIFICACIONES** es una solución operativa diseñada para digitalizar, agilizar y auditar en tiempo real la captura del rendimiento en la zona de despachos. Sustituye el conteo manual en papel por un flujo digital con **doble canal de captura** (aplicación móvil en AppSheet y registro conversacional por WhatsApp mediante notas de voz o texto con Inteligencia Artificial), desacoplando la digitación en bodega del procesamiento de nómina. El sistema garantiza la equidad operativa e integra un módulo de control de calidad mediante penalizaciones que protegen el salario base del trabajador.

## Arquitectura del Sistema
La solución opera bajo un esquema en la nube con dos canales de entrada sincronizados sobre una única fuente de verdad:
* **Canal 1 — Frontend Táctil (AppSheet Mobile & PWA):** Aplicación ejecutada en terminales móviles Android/iOS y computadores de mostrador para captura táctil, consulta del historial diario (`HISTORIAL HOY`) y auditoría jerárquica de liquidaciones (`LIQUIDACION`).
* **Canal 2 — Bot de WhatsApp con IA Multimodal (`/bot` en Vercel Serverless):** Microservicio en Python desplegado en Vercel que recibe notas de voz (`.ogg`) o mensajes de texto a través de **Green API**, extrae y valida los despachos (individuales o por lotes) mediante **Gemini API (`gemini-3.5-flash`)**, inserta las filas en Google Sheets y responde confirmación inmediata por WhatsApp.
* **Backend y Motor de Liquidación (Google Sheets):** Libro relacional centralizado compuesto por 5 hojas maestras que actúan como base de datos transaccional y motor de cálculo matricial en tiempo real.

## Estructura de la Base de Datos (Versión 2.0+)
1. **`EMPLEADOS`:** Catálogo maestro del personal operativo (`ID_Empleado`, `Nombre_Completo`, `Activo`).
2. **`REGISTRO_DIARIO`:** Tabla transaccional atómica de 7 columnas físicas (`ID_Registro`, `Fecha_Hora`, `Empleado`, `Tipo_Factura`, `Numero_Factura`, `Puntos_Esfuerzo`, `Puntos_Error`). Alimentada simultáneamente por AppSheet y por el Bot de WhatsApp.
3. **`BASE_HISTORICA`:** Motor matricial dinámico (`LET + MAP + LAMBDA + QUERY`) que consolida automáticamente los puntos y bonos por Año, Mes y Quincena en modo de solo lectura.
4. **`LIQUIDACION_MES`:** Tablero ejecutivo para consulta gerencial y liquidación de nómina.
5. **`CONFIGURACION`:** Centralización de parámetros financieros (meta base quincenal, fondo de calidad, penalización por error y matriz de escalas).

## Organización del Repositorio
* `/bot`: Microservicio Serverless del Bot de WhatsApp con IA:
  * [`bot/api/webhook.py`](file:///c:/Proyectos/interelectricos-bonificaciones-bodega/bot/api/webhook.py): Endpoint Serverless en Vercel (`/api/webhook`) para recepción de eventos de Green API.
  * [`bot/src/parser_ai.py`](file:///c:/Proyectos/interelectricos-bonificaciones-bodega/bot/src/parser_ai.py): Motor de extracción a JSON estricto (1 o múltiples despachos) con Gemini API.
  * [`bot/src/sheets_service.py`](file:///c:/Proyectos/interelectricos-bonificaciones-bodega/bot/src/sheets_service.py): Validación contra `EMPLEADOS` e inserción atómica por lotes en `REGISTRO_DIARIO`.
  * [`bot/src/whatsapp_service.py`](file:///c:/Proyectos/interelectricos-bonificaciones-bodega/bot/src/whatsapp_service.py): Cliente de comunicación con Green API y formateo de confirmaciones.
  * [`bot/tests/test_bot.py`](file:///c:/Proyectos/interelectricos-bonificaciones-bodega/bot/tests/test_bot.py): Consola de pruebas locales en vivo.
* `/docs`: Documentación técnica del sistema, manuales de usuario y reglas de negocio:
  * [`GUIA_INSTALACION_APP.md`](file:///c:/Proyectos/interelectricos-bonificaciones-bodega/docs/GUIA_INSTALACION_APP.md)
  * [`INFORME_TECNICO_Y_MANUAL_DE_CONFIGURACION.md`](file:///c:/Proyectos/interelectricos-bonificaciones-bodega/docs/INFORME_TECNICO_Y_MANUAL_DE_CONFIGURACION.md)
  * [`MANUAL_DE_USUARIO_OPERATIVO.md`](file:///c:/Proyectos/interelectricos-bonificaciones-bodega/docs/MANUAL_DE_USUARIO_OPERATIVO.md)
  * [`RUNBOOK_SOPORTE_TECNICO.md`](file:///c:/Proyectos/interelectricos-bonificaciones-bodega/docs/RUNBOOK_SOPORTE_TECNICO.md)
  * [`SANDBOX_PRUEBAS.md`](file:///c:/Proyectos/interelectricos-bonificaciones-bodega/docs/SANDBOX_PRUEBAS.md)
* `/schemas`: Respaldo de configuraciones estructurales, fórmulas internas y expresiones lógicas de AppSheet ([`appsheet_config.md`](file:///c:/Proyectos/interelectricos-bonificaciones-bodega/schemas/appsheet_config.md)).
* `/scripts`: Generador automatizado de documentación institucional en formato Word ([`build_docs.py`](file:///c:/Proyectos/interelectricos-bonificaciones-bodega/scripts/build_docs.py)).
* `/templates`: Plantilla limpia de la base de datos de Google Sheets excluyendo registros sensibles ([`BD_BONIFICACIONES_BODEGA_TEMPLATE.xlsx`](file:///c:/Proyectos/interelectricos-bonificaciones-bodega/templates/BD_BONIFICACIONES_BODEGA_TEMPLATE.xlsx)).
* [`CHANGELOG.md`](file:///c:/Proyectos/interelectricos-bonificaciones-bodega/CHANGELOG.md): Registro de auditoría y trazabilidad histórica de versiones y commits del proyecto.

## Despliegue y Seguridad
* El sistema en AppSheet implementa una ventana de edición restringida a 15 minutos para correcciones inmediatas y deshabilita la eliminación de registros para garantizar la trazabilidad de auditoría.
* El Bot de WhatsApp opera bajo política *Fail-Closed*, procesando únicamente los mensajes provenientes del número autorizado (`CHAT_ID_PRUEBA`) y rechazando cualquier registro con datos faltantes o fuera de rango antes de tocar Google Sheets.
* Las credenciales (`.env`, `service_account.json`) y hojas de cálculo con registros reales (`.xlsx`) se excluyen estrictamente del control de versiones mediante [`.gitignore`](file:///c:/Proyectos/interelectricos-bonificaciones-bodega/.gitignore).
