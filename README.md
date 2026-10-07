# Sistema de Liquidación y Auditoría de Bonificaciones en Bodega

**Empresa:** Intereléctricos Group SAS
**Proyecto:** Proyecto - Control de Bonificaciones Operativas
**Autor:** Mauricio Sierra – Aprendiz ADSO SENA
**Versión:** 2.0 (Arquitectura Híbrida AppSheet + Google Sheets)
**Estado:** En Producción

---

## Descripción General
El sistema BONIFICACIONES es una aplicación operativa diseñada para digitalizar y estandarizar la captura del rendimiento en la zona de despachos. Sustituye el conteo manual de remisiones por un flujo digital que desacopla la digitación en bodega del procesamiento de nómina. El sistema garantiza la equidad al separar la complejidad documental del esfuerzo físico, e integra un módulo de control de calidad mediante penalizaciones que protegen el salario base del trabajador.

## Arquitectura del Sistema
La solución opera bajo un esquema cliente-servidor en la nube:
* **Frontend (Capa de Captura):** Aplicación AppSheet ejecutada como Aplicación Web Progresiva (PWA) instalada de forma nativa en el navegador del equipo de bodega.
* **Backend (Capa de Datos y Liquidación):** Libro relacional de Google Sheets compuesto por 5 tablas maestras que actúan como base de datos y motor de cálculo de liquidación mediante fórmulas matriciales.

## Estructura de la Base de Datos
1. **EMPLEADOS:** Catálogo maestro del personal operativo.
2. **FILTRO_FECHAS:** Módulo de control de consulta dinámica.
3. **REGISTRO_DIARIO:** Tabla transaccional para el registro histórico de órdenes despachadas.
4. **CONFIGURACION:** Centralización de variables financieras (metas, bono base y matriz de escalas).
5. **RESUMEN_SEMANAL / RESUMEN_MENSUAL:** Tablas de liquidación consolidada en modo de solo lectura.

## Organización del Repositorio
* `/docs`: Documentación técnica del sistema, manuales de usuario y reglas de negocio:
  * [`INFORME_TECNICO_Y_MANUAL_DE_CONFIGURACION.md`](file:///c:/Proyectos/interelectricos-bonificaciones-bodega/docs/INFORME_TECNICO_Y_MANUAL_DE_CONFIGURACION.md)
  * [`MANUAL_DE_USUARIO_OPERATIVO.md`](file:///c:/Proyectos/interelectricos-bonificaciones-bodega/docs/MANUAL_DE_USUARIO_OPERATIVO.md)
  * [`RUNBOOK_SOPORTE_TECNICO.md`](file:///c:/Proyectos/interelectricos-bonificaciones-bodega/docs/RUNBOOK_SOPORTE_TECNICO.md)
* `/schemas`: Respaldo de configuraciones estructurales, fórmulas internas y expresiones lógicas de AppSheet ([`appsheet_config.md`](file:///c:/Proyectos/interelectricos-bonificaciones-bodega/schemas/appsheet_config.md)).
* `/templates`: Plantillas limpias de la base de datos de Google Sheets excluyendo registros reales o sensibles ([`BD_BONIFICACIONES_BODEGA_TEMPLATE.xlsx`](file:///c:/Proyectos/interelectricos-bonificaciones-bodega/templates/BD_BONIFICACIONES_BODEGA_TEMPLATE.xlsx)).

## Despliegue y Seguridad
* El sistema implementa una ventana de edición restringida a 15 minutos para correcciones inmediatas.
* La eliminación de registros se encuentra deshabilitada a nivel estructural para garantizar la trazabilidad de auditoría.
* Las credenciales, datos transaccionales de nómina y nombres reales de los trabajadores se excluyen del control de versiones mediante `.gitignore`.