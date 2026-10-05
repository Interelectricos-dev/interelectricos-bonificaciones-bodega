# Manual de Usuario Operativo: Sistema Bonificaciones

**Proyecto:** SISTEMA CONTROL DE BONIFICACIONES EN BODEGA  
**Empresa:** INTERELECTRICOS GROUP SAS  
**Fecha:** 03 de Octubre de 2026  
**Autor:** Mauricio Sierra – Aprendiz ADSO SENA  
**Destinatarios:** Despachador de mostrador, Supervisores de Bodega y Jefatura de Operaciones  

---

## 1. Introducción y Propósito

El aplicativo **BONIFICACIONES** es la herramienta digital oficial para auditar y registrar el desempeño de alistamiento de pedidos en bodega. Sustituye el antiguo conteo por rayas en tablero, garantizando que a cada colaborador se le reconozca tanto el volumen de referencias procesadas como el esfuerzo físico real (cortes, cargas pesadas, uso de maquinaria, etc.), protegiendo la calidad del despacho.

---

## 2. Acceso e Inicio de la Aplicación en el Portátil

El sistema opera como una aplicación de escritorio independiente en el computador de bodega, sin necesidad de abrir pestañas convencionales de navegador.

```text
Barra de Tareas de Windows
          ↓
Clic en Ícono “BONIFICACIONES”
          ↓
Pantalla Directa de Despacho
```

> **Nota visual:** Ícono de la aplicación anclado en la barra de tareas de Windows y ventana inicial sin barra de direcciones URL.

1. **Encendido:** Encienda el equipo de bodega y verifique la conexión a la red Wi-Fi de la empresa.
2. **Acceso directo:** En la barra de tareas inferior de Windows, localice y haga un solo clic sobre el ícono de **BONIFICACIONES**.
3. **Inicio de sesión:** La aplicación iniciará sesión de forma persistente con la cuenta autorizada de bodega y abrirá directamente la pantalla de captura.

---

## 3. Flujo Diario de Registro de Despacho

Cada vez que un bodeguero entregue un pedido alistado junto con la factura física para su revisión, el despachador registrará la información siguiendo estos pasos secuenciales:

> **Formulario de captura rápida:** Campos `Empleado`, `Numero_Factura` y las tres botoneras numéricas táctiles.

### 3.1. Seleccionar al Colaborador
Toque el campo **Empleado** y elija al bodeguero responsable en la lista desplegable. El sistema mostrará la etiqueta legible (ej. `B-001 - Carlos Gomez`) y asociará internamente su identificador de control.

### 3.2. Digitar el Número de Factura
En la casilla **N° Factura**, ingrese el consecutivo numérico o alfanumérico impreso en la orden (aplica por igual para documentos `IC`, `DP` o `IR`).

### 3.3. Asignar Puntos de Factura
Presione un botón del **1 al 5** evaluando únicamente el volumen de líneas y tiempo de lectura documental del pedido:
* **1 pts:** Factura simple con pocos artículos o referencias.
* **2 - 4 pts:** Pedidos de tamaño medio con múltiples referencias.
* **5 pts:** Factura extensa con alta densidad de renglones que requiere conteo riguroso.

### 3.4. Asignar Puntos de Esfuerzo Físico
Presione un botón del **1 al 5** evaluando el desgaste corporal y maniobras requeridas:
* **1 pts:** Sin esfuerzo extra, mercancía ubicada en estanterías bajas.
* **2 - 4 pts:** Pedidos que requirieron cortes de cable conductor, mangueras o cargue de tubería pesada.
* **5 pts:** Maniobras complejas de carga pesada de bobinas industriales o uso del montacargas.

### 3.5. Asignar Puntos de Error
Audite la mercancía física contra la factura antes de empacar y marque la casilla correspondiente:
* **0 pts:** Despacho exacto y conforme, sin anomalías.
* **-1 pts:** Leve subsanable (ej. olvido de un ítem menor o conteo impreciso).
* **-2 pts:** Dos errores leves detectados en la misma orden.
* **-3 pts:** Falta crítica (corte erróneo de cable conductor o equivocación que cause devolución formal).

### 3.6. Guardar y Continuar
Presione el botón **SAVE (Guardar)**. Los datos se sincronizan inmediatamente en la nube y el formulario se limpiará de forma automática para recibir el siguiente alistamiento.

---

## 4. Corrección de Errores y Ventana de Seguridad

El sistema cuenta con un mecanismo de autocorrección temporal para subsanar descuidos de digitación sin comprometer la auditoría.

* **Dentro de los primeros 15 minutos:** Si el despachador nota que digitó mal el número de factura o seleccionó un empleado equivocado, puede abrir el registro reciente, pulsar el botón del lápiz (**Editar**), enmendar el dato y guardar.
* **Cumplidos los 15 minutos:** La acción de edición se oculta y el registro queda bloqueado en modo de solo lectura. Si se requiere un cambio posterior, se deberá remitir la solicitud formal al Administrador del Sistema con el número de factura y la justificación del ajuste.
* **Eliminaciones:** Por directriz de auditoría, ningún usuario operativo tiene permisos para eliminar registros del sistema.

---

## 5. Consulta Dinámica de Totales y Liquidación

Los supervisores y bodegueros pueden consultar el avance de productividad y calidad sin necesidad de acceder a hojas de cálculo complejas.

### 5.1. Pestaña RESUMEN (Dashboard)
* **SEMANAL:** Consolida los puntos acumulados por cada trabajador de lunes a domingo para la semana consultada, mostrando el bono de productividad alcanzado y el bono de calidad resultante.
* **MENSUAL:** Presenta el consolidado acumulado desde el primer hasta el último día del mes en curso.

### 5.2. Consultar Periodos Anteriores (Selector de Fecha)
1. Diríjase a la pestaña **FILTRO FECHAS**.
2. Toque el selector de calendario y escoja cualquier día correspondiente a la semana o mes que desea auditar.
3. Al regresar a **RESUMEN**, las tablas actualizarán automáticamente sus cálculos y títulos dinámicos con base en dicha fecha.

---

## 6. Resumen Rápido de Parámetros Económicos

Para facilitar la resolución de dudas operativas a los trabajadores de bodega:

* **Meta Base de Productividad:** 100 puntos semanales (cubiertos por el salario ordinario). A partir del punto 101 se liquidan bonos escalonados ($150, $300, $450 ó $600).
* **Bono de Calidad:** Bolsa inicial de $200. Cada punto de error reportado descuenta $40 de dicha bolsa.
* **Protección de Salario:** El bono de calidad cuenta con piso de $0; nunca genera saldos en contra ni deducciones del sueldo fijo.
