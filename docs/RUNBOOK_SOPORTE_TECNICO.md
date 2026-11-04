# Runbook de Soporte Técnico: Sistema de Bonificaciones en Bodega

**Empresa:** Interelectricos Group SAS  
**Proyecto:** Sistema Control de Bonificaciones Operativas en Bodega  
**Destinatarios:** Equipo de Soporte Técnico, Administrador de Sistemas y Jefatura de Operaciones  
**Versión:** 2.0 (Arquitectura Centralizada con Base Histórica Dinámica y Drill-Down)  
**Estado:** Producción  

---

## 1. Información General del Servicio

Este documento provee los lineamientos técnicos para el mantenimiento, soporte operativo de nivel 2 y 3, diagnóstico de fallas y protocolos de contingencia del aplicativo de control de despachos y bonificaciones de Interelectricos Group SAS.

* **Arquitectura del Sistema:** Frontend en AppSheet (PWA instalada en navegador y app nativa móvil) / Backend en Google Sheets.
* **Alojamiento de Base de Datos:** Google Drive (Carpeta corporativa: `01_SISTEMA_BONIFICACIONES`).
* **Archivo Maestro:** `BD_BONIFICACIONES_BODEGA` (Libro nativo de Google Sheets).
* **Plantilla de Respaldo:** [`BD_BONIFICACIONES_BODEGA_TEMPLATE.xlsx`](file:///c:/Proyectos/interelectricos-bonificaciones-bodega/templates/BD_BONIFICACIONES_BODEGA_TEMPLATE.xlsx).
* **Guía Canónica de Configuración AppSheet:** [`schemas/appsheet_config.md`](file:///c:/Proyectos/interelectricos-bonificaciones-bodega/schemas/appsheet_config.md).
* **Manual Técnico de Arquitectura:** [`docs/INFORME_TECNICO_Y_MANUAL_DE_CONFIGURACION.md`](file:///c:/Proyectos/interelectricos-bonificaciones-bodega/docs/INFORME_TECNICO_Y_MANUAL_DE_CONFIGURACION.md).
* **Entorno de Ejecución en Bodega:** Teléfonos móviles Android dedicados para despachadores y terminal de mostrador (PWA en Google Chrome / Microsoft Edge).
* **Orquestador de Sincronización:** Motor en la nube de AppSheet.
* **Propiedad y Credenciales:** Cuenta oficial del departamento de sistemas (excluida de control de versiones).

---

## 2. Matriz de Tablas y Permisos Críticos

Para garantizar la integridad y trazabilidad ante cualquier revisión de soporte:

| Tabla | Permiso en AppSheet | Gestión en Backend | Propósito Operativo |
| :--- | :---: | :---: | :--- |
| **`REGISTRO_DIARIO`** | `Updates, Adds`<br>*(Deletes desmarcado)* | Auditoría histórica atómica | Registro transaccional en caliente de comprobantes despachados. Eliminación bloqueada. |
| **`EMPLEADOS`** | `Read-only` | Google Sheets directo | Catálogo maestro de colaboradores. Altas y bajas exclusivas por el administrador. |
| **`BASE_HISTORICA`** | `Read-only` | Fórmulas matriciales automáticas | Matriz histórica consolidada calculada al vuelo (`LET` + `MAP` + `QUERY`). Alimenta la vista `LIQUIDACION`. |
| **`CONFIGURACION`** | *(Sin vista en AppSheet)* | Google Sheets directo | Parámetros financieros: Meta base (`B3`), fondo calidad (`B4`), castigo error (`B5`) y matriz de tramos (`A8:C12`). |
| **`LIQUIDACION_MES`** | *(Sin vista en AppSheet)* | Google Sheets directo | Dashboard ejecutivo para consulta y exportación de nóminas quincenales y mensuales. |

> **Nota de Soporte V2.0:**  
> Las tablas `FILTRO_FECHAS`, `RESUMEN_QUINCENAL` y `RESUMEN_MENSUAL` de la V1.0 fueron **retiradas y eliminadas definitivamente**. No deben existir en la consola de AppSheet ni en el libro de Google Sheets.

---

## 3. Procedimientos de Soporte y Resolución de Incidentes (Troubleshooting)

---

### Incidente 1: Corrección de un registro bloqueado por tiempo (Fuera de los 15 minutos)
* **Síntoma:** El despachador reporta un número de factura mal digitado, una serie errónea o un empleado equivocado, pero el botón de edición (ícono de lápiz) ya desapareció en AppSheet.
* **Causa:** Regla de comportamiento `TOTALMINUTES(NOW() - [Fecha_Hora]) <= 15` cumplida para preservar auditoría.
* **Procedimiento de Solución:**
  1. El usuario operativo remite la solicitud formal a soporte indicando: **Fecha/Hora exacta**, **ID_Registro** (o Número de Factura actual), y el **valor corregido**.
  2. El Administrador de Sistemas abre el libro `BD_BONIFICACIONES_BODEGA` en Google Drive.
  3. Ingresa a la pestaña `REGISTRO_DIARIO`.
  4. Localiza la fila presionando `Ctrl + F` y buscando por el consecutivo numérico (`Numero_Factura`), la serie (`Tipo_Factura`) o el timestamp.
  5. Enmienda el valor en la celda correspondiente:
     * Columna C: `Empleado` (ID del colaborador).
     * Columna D: `Numero_Factura` (Consecutivo numérico puro).
     * Columna E: `Puntos_Esfuerzo` (1 a 5).
     * Columna F: `Puntos_Error` (0 a -3).
     * Columna G: `Tipo_Factura` (`IC`, `DP` o `IR`).
  6. **Efecto Inmediato:** La corrección impactará automáticamente en segundos la hoja `BASE_HISTORICA` (recalculando puntos y bonos) y se reflejará en la aplicación móvil en su siguiente sincronización.

---

### Incidente 2: Desconfiguración de botoneras táctiles o teclado numérico
* **Síntoma:** En el formulario de despacho, el campo `Numero_Factura` abre el teclado alfanumérico completo en vez del teclado numérico, o los puntos/errores aparecen como casillas de texto libre.
* **Causa:** Pérdida de metadatos de columna tras una regeneración de esquema o cambio de tipo automático en AppSheet.
* **Procedimiento de Solución:**
  1. Ingresar a la consola de administración de AppSheet.
  2. Ir a **Data > Columns > REGISTRO_DIARIO**.
  3. Verificar y restablecer la siguiente configuración estricta para cada campo:
     * **`Tipo_Factura`:**
       * `Type`: **Enum** | `Base type`: **Text** | `Input mode`: **Buttons**
       * `Values`: `IC, DP, IR`
       * `Display name`: `Tipo Factura`
     * **`Numero_Factura`:**
       * `Type`: **Number** *(dispara el teclado numérico de dígitos grandes en el celular)*
       * `Require?`: `TRUE` (marcado)
       * `Display name`: `N° Factura`
     * **`Puntos_Esfuerzo`:**
       * `Type`: **Enum** | `Base type`: **Number** | `Input mode`: **Buttons**
       * `Values`: `1, 2, 3, 4, 5`
       * `Require?`: `TRUE` (marcado)
       * `Display name`: `Puntos Esfuerzo`
     * **`Puntos_Error`:**
       * `Type`: **Enum** | `Base type`: **Number** | `Input mode`: **Buttons**
       * `Values`: `0, -1, -2, -3`
       * `Initial value`: `0`
       * `Require?`: `TRUE` (marcado)
       * `Display name`: `Puntos Error`
  4. Verificar las columnas virtuales:
     * **`Factura`:** Fórmula `[Tipo_Factura] & "-" & [Numero_Factura]`, `LABEL? = TRUE`, `SEARCH? = TRUE`.
     * **`Hora`:** Fórmula `TEXT([Fecha_Hora], "H:MM AM/PM")`, `SHOW? = TRUE`, `SEARCH? = TRUE`.
  5. Hacer clic en **Save** en la esquina superior derecha.

---

### Incidente 3: Error de esquema o sincronización ("Column mismatch / Schema error")
* **Síntoma:** Los despachadores reciben un mensaje de error bloqueante al guardar registros o la app muestra advertencia roja de sincronización.
* **Causa:** Se renombró, insertó o eliminó una columna en Google Sheets sin actualizar la definición de datos en AppSheet.
* **Procedimiento de Solución:**
  1. Verificar que las columnas en Google Sheets coincidan exactamente con la estructura canónica V2.0:
     * `EMPLEADOS`: `ID_Empleado`, `Nombre_Completo`, `Activo`.
     * `REGISTRO_DIARIO`: `ID_Registro`, `Fecha_Hora`, `Empleado`, `Numero_Factura`, `Puntos_Esfuerzo`, `Puntos_Error`, `Tipo_Factura`.
     * `BASE_HISTORICA`: `Año`, `Mes`, `Quincena`, `ID_Empleado`, `Pts_Esfuerzo`, `Pts_Error`, `Nombre`, `Bono Productivo`, `Bono Calidad`, `Total BONO`.
  2. En el editor de AppSheet, ir a **Data > Tables**.
  3. Seleccionar la tabla en conflicto y hacer clic en **Regenerate Schema**.
  4. Validar propiedades críticas tras la regeneración:
     * En `EMPLEADOS`: `Nombre_Completo` con `LABEL? = TRUE`, `Activo` con `SHOW? = FALSE`. Verificar que la virtual `Activo?` se conserve y que **NO existan** las virtuales obsoletas `Despachos_Quincena` o `Despachos_Mes`.
     * En `REGISTRO_DIARIO`: `Factura` con `LABEL? = TRUE`.
     * En `BASE_HISTORICA`: `ID_Liquidacion` con `KEY? = TRUE` y `SHOW? = TRUE`. `Nombre` con `LABEL? = TRUE`.
  5. Guardar los cambios (**Save**).

---

### Incidente 4: Error de desbordamiento en matriz dinámica (`BASE_HISTORICA`) — Error `#REF!`
* **Síntoma:** En Google Sheets, la hoja `BASE_HISTORICA` muestra `#REF!` en la celda `A1` con el mensaje: *"Array result was not expanded because it would overwrite data in..."*, o la vista `LIQUIDACION` en AppSheet aparece vacía.
* **Causa:** Un usuario escribió manualmente en las filas inferiores de `BASE_HISTORICA` (en el rango `A2:F`), interrumpiendo el espacio de derrame de la fórmula matricial `LET` + `QUERY` en `A1`.
* **Procedimiento de Solución:**
  1. Abrir `BD_BONIFICACIONES_BODEGA` en Google Sheets.
  2. Ir a la pestaña `BASE_HISTORICA`.
  3. Seleccionar el rango desde la fila 2 hacia abajo en las columnas A a F (`A2:F`) y presionar **Supr** (Delete) para limpiar cualquier contenido estático escrito por error.
  4. Verificar que la celda `A1` conserve intacta la fórmula matricial canónica:
     ```excel
     =LET(
       fechas; REGISTRO_DIARIO!B2:B; 
       quincenas; MAP(fechas; LAMBDA(f; SI(f=""; ""; SI(DIA(f)<=15; "Q1"; "Q2")))); 
       meses; MAP(fechas; LAMBDA(f; SI(f=""; ""; MES(f)))); 
       QUERY(
         {REGISTRO_DIARIO!A2:G\ quincenas\ meses}; 
         "SELECT YEAR(Col2), Col9, Col8, Col3, SUM(Col6), SUM(Col7) 
          WHERE Col1 IS NOT NULL 
          GROUP BY YEAR(Col2), Col9, Col8, Col3 
          ORDER BY YEAR(Col2) DESC, Col9 DESC, Col8 ASC 
          LABEL YEAR(Col2) 'Año', Col9 'Mes', Col8 'Quincena', Col3 'ID_Empleado', SUM(Col6) 'Pts_Esfuerzo', SUM(Col7) 'Pts_Error'"
       )
     )
     ```
  5. Una vez despejado el rango, la matriz se expandirá automáticamente repoblando todo el histórico quincenal.

---

### Incidente 5: Un empleado activo no figura en la tabla de liquidación quincenal
* **Síntoma:** Luis o el auxiliar preguntan por qué un empleado que está activo en la empresa no aparece en la tabla de `LIQUIDACION` de una quincena específica.
* **Causa:** **Comportamiento esperado del sistema V2.0.** A diferencia de las hojas rígidas de la V1.0 que listaban a todos los trabajadores con ceros, el motor matricial `QUERY` de la V2.0 opera bajo optimización analítica y agrupa exclusivamente los colaboradores que registraron al menos un despacho en el período consultado. Si un empleado no alistó pedidos (por vacaciones, incapacidad u otras funciones), no genera fila en esa quincena.
* **Procedimiento de Explicación / Solución:**
  1. Aclarar al usuario que la tabla de liquidación es un reporte de rendimiento por despacho: solo muestra personal con operaciones reales.
  2. Si el colaborador sí despachó pero no figura, verificar que sus despachos en `REGISTRO_DIARIO` tengan la fecha dentro de la quincena correspondiente y que su nombre haya sido seleccionado correctamente en el campo `Empleado`.

---

### Incidente 6: Usuario bloqueado por permisos de cuenta ("Access Denied / Not Authorized")
* **Síntoma:** Al abrir el acceso directo en el celular o iniciar sesión con Google, el usuario recibe un mensaje indicando que no cuenta con autorización para acceder a la aplicación.
* **Causa:** El aplicativo se encuentra configurado con control de acceso por lista blanca y el correo del colaborador no ha sido dado de alta en la consola de usuarios.
* **Procedimiento de Solución:**
  1. El colaborador remite formalmente a soporte su dirección de correo corporativa o autorizada.
  2. El Administrador de Sistemas ingresa al editor de AppSheet con las credenciales maestras.
  3. Accede al apartado **Users** (o **Share App**).
  4. Agrega la dirección de correo en la lista de usuarios autorizados con rol estándar (`User`) y guarda los cambios.
  5. En caso de que la directriz gerencial sea mantener el acceso libre provisional en bodega sin autenticación obligatoria, verificar la política en los ajustes de seguridad de la app.

---

### Incidente 7: El formulario de despacho se cierra tras guardar un registro
* **Síntoma:** Al guardar un despacho, la aplicación vuelve a la vista de historial o al menú principal, obligando al despachador a presionar nuevamente `NUEVO REGISTRO` para el siguiente alistamiento.
* **Causa:** La opción `Auto re-open` está desactivada (`OFF`) o `Finish view` tiene una asignación de redirección no estándar.
* **Procedimiento de Solución:**
  1. Ingresar al editor de AppSheet.
  2. Ir a **Views > NUEVO REGISTRO**.
  3. Activar el switch **Auto re-open** (en posición `ON` / azul).
  4. En el campo **Finish view**, seleccionar **`Auto assign (Go Back)`**.
  5. Verificar que en **Settings > Views > General**, la propiedad **`Starting view`** tenga asignado **`NUEVO REGISTRO`**.
  6. Guardar los cambios (**Save**). Con esto el formulario se mantendrá abierto indefinidamente tras cada guardado hasta que el usuario pulse conscientemente *Cancel*.

---

### Incidente 8: El sistema rechaza un número de factura ("Esta factura ya fue registrada previamente para este colaborador")
* **Síntoma:** En AppSheet, al ingresar el número de factura, la casilla se resalta en rojo y muestra el mensaje `⚠️ Esta factura ya fue registrada previamente para este colaborador`. En WhatsApp, el bot responde que la factura fue omitida por duplicidad.
* **Causa:** La regla de negocio antiduplicados `(Empleado + Tipo_Factura + Numero_Factura)` detectó que dicho documento ya fue cargado previamente para ese mismo operario en la hoja `REGISTRO_DIARIO`.
* **Procedimiento de Diagnóstico y Soporte:**
  1. **Verificar en `HISTORIAL HOY`:** En la app móvil, ir a `HISTORIAL HOY` y filtrar por el número de factura. Validar la hora y el auxiliar al que le fue acreditada originalmente.
  2. **Caso de Doble Registro Accidental:** Si el despachador o Luis intentó guardarla dos veces (por ejemplo, doble clic al guardar en AppSheet o reenvío de nota de voz de días anteriores), la validación operó correctamente protegiendo el puntaje. Indicar al operario que la factura ya está contabilizada y no requiere reenvío.
  3. **Caso de Error Tipográfico en el Número:** Si el auxiliar digitó un número por equivocación y ahora coincide con una factura vieja, confrontar el documento físico impreso y digitar el número consecutivo real.
  4. **Caso de Pedido Compartido Legítimo:** Si la factura fue alistada entre dos colaboradores distintos (ej. cables por Edward y aparamenta por Sneider), recordar al usuario que **el sistema sí permite registrar la misma factura seleccionando al otro colaborador**. El bloqueo aplica única y exclusivamente cuando se intenta repetir para el *mismo* auxiliar.
  5. **Corrección Administrativa de Excepción:** Si un registro antiguo tenía el número equivocado y bloquea una factura legítima del día, el Administrador de Sistemas puede corregir el consecutivo erróneo en la celda correspondiente de `REGISTRO_DIARIO` en Google Sheets. Al sincronizar la app, el bloqueo quedará liberado de inmediato.

---

## 4. Procedimientos de Mantenimiento Preventivo y Rutinario

### 4.1. Alta o Baja de Personal Operativo
* **Altas:** 
  1. Ir a `EMPLEADOS` en Google Sheets.
  2. Agregar fila con nuevo `ID_Empleado` consecutivo, `Nombre_Completo` y marcar la casilla `Activo` en `VERDADERO` (`TRUE`).
  3. En minutos, la app de bodega lo listará automáticamente en el desplegable de despacho (`Valid_If`).
* **Bajas:**
  1. **NUNCA eliminar la fila del colaborador** (rompería la integridad de los registros históricos de despacho).
  2. Desmarcar únicamente la casilla `Activo` (`FALSE`). El auxiliar desaparecerá de inmediato del formulario de captura para nuevos despachos, pero su historial transaccional de meses pasados permanecerá intacto para auditoría y pago de liquidaciones.

### 4.2. Calibración de Parámetros de Liquidación y Metas
Si la Gerencia General aprueba modificaciones en el esquema de compensación o la meta base:
1. Ir a la pestaña `CONFIGURACION` en Google Sheets.
2. Ajustar los valores en las celdas correspondientes:
   * `B3`: **Meta Base Quincenal** (Base configurada: `300` puntos).
   * `B4`: **Bono Calidad Quincenal** (Base configurada: `$100.000` quincenales).
   * `B5`: **Descuento Unitario por Error** (Base configurada: `$20.000` por cada punto de error).
   * `A9:C12`: **Escala de Productividad** en números cerrados (`301-350` → `$50.000`, `351-400` → `$100.000`, `401-450` → `$150.000`, `451 o más` → `$200.000`, alcanzando un bono neto máximo de `$300.000` quincenales sumando calidad).
3. **Efecto Inmediato:** Los cambios se propagan de forma instantánea a toda la hoja `BASE_HISTORICA` y al dashboard `LIQUIDACION_MES` sin necesidad de tocar ninguna fórmula matricial ni código de programación.

---

## 5. Protocolo de Contingencia por Caída de Conectividad o Servicio

1. **Falla de conexión Wi-Fi / Datos móviles en Bodega:**
   * AppSheet cuenta con soporte offline nativo en la app móvil y en la PWA. Los despachos registrados se encolarán de manera segura en el almacenamiento local del dispositivo.
   * El operario puede continuar despachando normalmente.
   * Al restablecerse la red, el despachador debe presionar el ícono de las **dos flechas circulares (Sincronizar)** en la esquina superior derecha para vaciar la cola de envíos hacia Google Sheets.
2. **Caída total del servicio en la nube (Incidente Mayor):**
   * El despachador debe llevar un registro temporal de contingencia físico en planilla de papel (Serie de Factura, Número de Consecutivo, Colaborador, Puntos de Esfuerzo 1-5, Errores).
   * Al reanudarse el servicio en la nube, el personal de bodega o soporte digita los registros en la app con la marca temporal correspondiente para garantizar su incorporación a la liquidación de la quincena.


---

## 6. Soporte y Mantenimiento del Bot de WhatsApp (`/bot` — Vercel + Green API + Gemini)

### 6.1. Cambio o Adición del Número Autorizado (`CHAT_ID_PRUEBA`)
Por política de seguridad (*Fail-Closed*), el bot procesa exclusivamente los mensajes que provengan del número configurado en `CHAT_ID_PRUEBA`. Para actualizarlo en producción:
1. Ingresar a **Vercel** → Proyecto `interelectricos-bonificaciones-bodega` → **Environment Variables**.
2. Localizar la variable **`CHAT_ID_PRUEBA`**, hacer clic en **`⋯` > Edit** y colocar el número en formato internacional de WhatsApp (`573XXXXXXXXX@c.us`). Si se desean autorizar dos números simultáneamente, separarlos por coma (`573134040002@c.us,573XXXXXXXXX@c.us`).
3. Guardar los cambios (**Save**), ir a la pestaña **Deployments** y seleccionar **Redeploy** sobre el último despliegue activo.

### 6.2. Diagnóstico cuando el Bot de WhatsApp no responde
1. **Verificar estado de la función en Vercel:** Abrir `https://interelectricos-bonificaciones-bode.vercel.app/api/webhook` en el navegador. Debe retornar `{"status": "ok", "service": "Bot WhatsApp Bonificaciones Bodega - Interelectricos"}`.
2. **Verificar sesión QR en Green API:** Si el teléfono físico de Sistemas permaneció más de 14 días continuos apagado o sin conexión a internet, ingresar al panel de Green API (`idInstance: 710722740631`) y verificar que el estado sea `authorized` y que `webhookUrl` apunte a `https://interelectricos-bonificaciones-bode.vercel.app/api/webhook`.
3. **Pruebas desde consola local:** Para depurar el flujo en tiempo real desde un computador de soporte, ejecutar `python -X utf8 bot/tests/test_bot.py`.
