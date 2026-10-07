# Runbook de Soporte Técnico: Sistema de Bonificaciones en Bodega

**Empresa:** Intereléctricos Group SAS  
**Proyecto:** Sistema Control de Bonificaciones Operativas en Bodega  
**Destinatarios:** Equipo de Soporte Técnico, Administrador de Sistemas y Jefatura de Operaciones  
**Versión:** 2.0 (Arquitectura Híbrida AppSheet + Google Sheets)  
**Estado:** Producción  

---

## 1. Información General del Servicio

Este documento provee los lineamientos técnicos para el mantenimiento, soporte operativo de nivel 2 y 3, diagnóstico de fallas y protocolos de contingencia del aplicativo de control de despachos y bonificaciones de Intereléctricos Group SAS.

* **Arquitectura del Sistema:** Frontend en AppSheet (PWA instalada en navegador) / Backend en Google Sheets.
* **Alojamiento de Base de Datos:** Google Drive (Carpeta corporativa: `01_SISTEMA_BONIFICACIONES`).
* **Archivo Maestro:** `BD_BONIFICACIONES_BODEGA` (Libro nativo de Google Sheets).
* **Plantilla de Respaldo:** [`BD_BONIFICACIONES_BODEGA_TEMPLATE.xlsx`](file:///c:/Proyectos/interelectricos-bonificaciones-bodega/templates/BD_BONIFICACIONES_BODEGA_TEMPLATE.xlsx).
* **Entorno de Ejecución en Bodega:** Portátil dedicado para despacho ejecutando aplicación PWA (Google Chrome / Microsoft Edge).
* **Orquestador de Sincronización:** Motor en la nube de AppSheet.
* **Propiedad y Credenciales:** Cuenta oficial del departamento de sistemas (excluida de control de versiones).

---

## 2. Matriz de Tablas y Permisos Críticos

Para garantizar la integridad y trazabilidad ante cualquier revisión de soporte:

| Tabla | Permiso en AppSheet | Gestión en Backend | Propósito Operativo |
| :--- | :---: | :---: | :--- |
| **`REGISTRO_DIARIO`** | `Adds_and_Updates` | Auditoría histórica | Registro transaccional de facturas despachadas. Eliminación deshabilitada. |
| **`EMPLEADOS`** | `Read_Only` | Google Sheets directo | Catálogo maestro de colaboradores. Altas/bajas exclusivas por el administrador. |
| **`FILTRO_FECHAS`** | `Updates_Only` | Google Sheets / AppSheet | Selector de fecha interactivo (`B2`) y motor de delimitación de fechas (`C2:F2`). |
| **`CONFIGURACION`** | *(Sin vista directa)* | Google Sheets directo | Parámetros financieros: meta base (`B2`), bono calidad (`B3`), castigo error (`B4`) y escalas salariales (`A8:C11`). |
| **`RESUMEN_SEMANAL`** | `Read_Only` | Fórmulas matriciales | Liquidación consolidada de lunes a domingo según `FILTRO_FECHAS!$C$2:$D$2`. |
| **`RESUMEN_MENSUAL`** | `Read_Only` | Fórmulas matriciales | Liquidación consolidada mensual según `FILTRO_FECHAS!$E$2:$F$2`. |

---

## 3. Procedimientos de Soporte y Resolución de Incidentes (Troubleshooting)

### Incidente 1: Corrección de un registro bloqueado por tiempo (Fuera de los 15 minutos)
* **Síntoma:** El despachador reporta un número de factura mal digitado o un empleado erróneo, pero el botón de edición (ícono de lápiz) ya desapareció en AppSheet.
* **Causa:** Regla de comportamiento `TOTALMINUTES(NOW() - [Fecha_Hora]) <= 15` cumplida para preservar auditoría.
* **Procedimiento de Solución:**
  1. El usuario operativo remite la solicitud formal a soporte indicando: **Fecha/Hora exacta**, **ID_Registro** (o Número de Factura actual), y el **valor corregido**.
  2. El Administrador de Sistemas abre el libro `BD_BONIFICACIONES_BODEGA` en Google Drive.
  3. Ingresa a la pestaña `REGISTRO_DIARIO`.
  4. Localiza la fila presionando `Ctrl + F` y buscando por el número de factura o timestamp.
  5. Enmienda el valor en la celda correspondiente (`Numero_Factura`, `Empleado`, o puntos).
  6. La aplicación en bodega reflejará la corrección en su siguiente sincronización automática.

---

### Incidente 2: Desconfiguración de botoneras táctiles (Aparecen controles `+` y `-` o teclado libre)
* **Síntoma:** En el formulario de despacho, los campos de puntos ya no muestran los botones táctiles y solicitan teclado o botones de incremento.
* **Causa:** Pérdida de metadatos de columna tras una regeneración de esquema o cambio de tipo automático en AppSheet.
* **Procedimiento de Solución:**
  1. Ingresar a la consola de administración de AppSheet.
  2. Ir a **Data > Columns > REGISTRO_DIARIO**.
  3. Verificar y restablecer la siguiente configuración estricta para cada campo:
     * **`Puntos_Factura`:**
       * `Type`: **Enum** | `Base type`: **Number** | `Input mode`: **Buttons**
       * `Values`: `1, 2, 3, 4, 5`
     * **`Puntos_Esfuerzo`:**
       * `Type`: **Enum** | `Base type`: **Number** | `Input mode`: **Buttons**
       * `Values`: `1, 2, 3, 4, 5`
     * **`Puntos_Error`:**
       * `Type`: **Enum** | `Base type`: **Number** | `Input mode`: **Buttons**
       * `Values`: `0, -1, -2, -3`
  4. Hacer clic en **Save** en la esquina superior derecha.

---

### Incidente 3: Error de esquema o sincronización ("Column mismatch / Schema error")
* **Síntoma:** Los despachadores reciben un mensaje de error bloqueante al guardar registros o la app muestra advertencia roja de sincronización.
* **Causa:** Se renombró, insertó o eliminó una columna en Google Sheets sin actualizar la definición de datos en AppSheet.
* **Procedimiento de Solución:**
  1. Verificar que las columnas en Google Sheets coincidan con la estructura canónica:
     * `REGISTRO_DIARIO`: `ID_Registro`, `Fecha_Hora`, `Empleado`, `Numero_Factura`, `Puntos_Factura`, `Puntos_Esfuerzo`, `Puntos_Error`.
     * `FILTRO_FECHAS`: `ID_Filtro`, `Fecha_Referencia`, `Semana_Inicio`, `Semana_Fin`, `Mes_Inicio`, `Mes_Fin`.
     * `RESUMEN_SEMANAL` / `RESUMEN_MENSUAL`: `ID_Empleado`, `Nombre_Empleado`, `Puntos_Factura`, `Puntos_Esfuerzo`, `Puntos_Totales`, `Bono_Productividad`, `Total_Errores`, `Bono_Calidad`, `Total_Extra_A_Pagar`.
  2. En el editor de AppSheet, ir a **Data > Tables**.
  3. Seleccionar la tabla en conflicto y hacer clic en **Regenerate Schema**.
  4. Validar que la columna virtual `Etiqueta_Empleado` en `EMPLEADOS` permanezca intacta (`CONCATENATE([ID_Empleado], " - ", [Nombre_Completo])`).
  5. Guardar los cambios (**Save**).

---

### Incidente 4: Selector de Fecha bloqueado en modo "Read-Only" en la app
* **Síntoma:** El usuario entra a la pestaña `FILTRO FECHAS`, pero el calendario no se deja editar interactivamente.
* **Causa:** Alguien escribió por error una fórmula de Google Sheets (como `=HOY()`) en la celda `B2` de la hoja `FILTRO_FECHAS`. Al detectar fórmulas de celda en el backend, AppSheet bloquea la columna automáticamente para proteger el cálculo.
* **Procedimiento de Solución:**
  1. Abrir `BD_BONIFICACIONES_BODEGA` en Google Sheets.
  2. Ir a la pestaña `FILTRO_FECHAS`.
  3. Revisar la celda `B2`: **Debe ser un valor estático de fecha**, NO una fórmula. Borrar cualquier fórmula y dejar una fecha fija (ej. la fecha actual).
  4. En AppSheet (**Data > Columns > FILTRO_FECHAS**), verificar que `Spreadsheet formula` esté en blanco, `Initial value` tenga `TODAY()` y la propiedad `Editable?` esté activa (`TRUE`).

---

### Incidente 5: Tablas de resumen vacías o con error `#N/A` generalizado
* **Síntoma:** Las vistas `RESUMEN_SEMANAL` o `RESUMEN_MENSUAL` no muestran colaboradores o exhiben error de cálculo matricial.
* **Causa:** La fórmula `=SI.ERROR(FILTER(EMPLEADOS!A2:A1000; EMPLEADOS!C2:C1000 = VERDADERO); "")` no encuentra ningún trabajador con la casilla `Activo` en `VERDADERO` / `TRUE`.
* **Procedimiento de Solución:**
  1. Abrir la pestaña `EMPLEADOS` en Google Sheets.
  2. Verificar que existan registros y que la columna `Activo` (`Columna C`) tenga casillas marcadas (`TRUE`).
  3. Verificar que los IDs de la columna `A` no tengan espacios en blanco al inicio o al final.
  4. Una vez marcado al menos un colaborador activo, las fórmulas matriciales y de consolidación por `SUMAR.SI.CONJUNTO` se restablecerán inmediatamente.

---

## 4. Procedimientos de Mantenimiento Preventivo y Rutinario

### 4.1. Alta o Baja de Personal Operativo
* **Altas:** 
  1. Ir a `EMPLEADOS` en Google Sheets.
  2. Agregar fila con nuevo `ID_Empleado` consecutivo (ej. `B-008`), `Nombre_Completo` y marcar la casilla `Activo` en `VERDADERO`.
  3. En minutos, la app de bodega lo listará en el desplegable de despacho.
* **Bajas:**
  1. **NUNCA eliminar la fila del colaborador** (rompería la integridad de los registros históricos de despacho).
  2. Desmarcar únicamente la casilla `Activo` (`FALSE`). El bodeguero desaparecerá de las liquidaciones vigentes pero su historial de despachos se mantendrá intacto para auditoría.

### 4.2. Ajuste de Parámetros de Liquidación y Metas
* Si la gerencia aprueba cambios en el esquema de bonificación:
  1. Ir a la pestaña `CONFIGURACION` en Google Sheets.
  2. Ajustar los valores en las celdas correspondientes:
     * `B2`: Meta mínima de puntos (Base: `100`).
     * `B3`: Bono base de calidad (Base: `$200.000`).
     * `B4`: Penalización por error (Base: `$40.000`).
     * `A8:C11`: Rangos y valores de la escala salarial de productividad.
  3. Los cambios entrarán en vigencia de inmediato para los ciclos que se consulten.

---

## 5. Protocolo de Contingencia por Caída de Conectividad o Servicio

1. **Falla de conexión Wi-Fi en Bodega:**
   * AppSheet cuenta con soporte offline básico en la PWA; los registros se encolarán localmente en el almacenamiento del navegador.
   * Al restablecerse la red, el despachador debe presionar el ícono de las **dos flechas circulares (Sincronizar)** en la esquina superior derecha de la aplicación.
2. **Caída total del servicio en la nube:**
   * El despachador debe llevar un registro temporal de contingencia físico (Formato impreso de remisión con Número de Factura, Bodeguero, Complejidad y Errores).
   * Al reanudarse el servicio, el despachador o soporte digita los registros en la app con la marca temporal correspondiente.
  