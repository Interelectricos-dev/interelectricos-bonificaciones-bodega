# Sistema de Liquidación y Auditoría de Bonificaciones en Bodega

**Empresa:** Interelectricos Group SAS  
**Proyecto:** Control de Bonificaciones Operativas en Bodega  
**Autor:** Mauricio Sierra – Aprendiz ADSO SENA  
**Versión:** 2.3 (Arquitectura Modular Desacoplada SRP por Servicios + Bot Multimodal + AppSheet + Google Sheets)  
**Estado:** En Producción  

---

## 1. Descripción General
El sistema **BONIFICACIONES** es una solución operativa diseñada para digitalizar, agilizar y auditar en tiempo real la captura del rendimiento en la zona de despachos de Intereléctricos Group SAS. Sustituye el conteo manual en papel por un flujo digital con **doble canal de captura** (aplicación móvil en AppSheet y bot conversacional por WhatsApp mediante notas de voz o texto con Inteligencia Artificial), desacoplando la digitación en bodega del procesamiento de nómina.

---

## 2. Arquitectura de Software Desacoplada (SRP)

El backend de procesamiento opera bajo una arquitectura modular desacoplada por servicios, aplicando estrictamente el **Principio de Responsabilidad Única (SRP)**:

```
├── .env                          # Variables de entorno reales (excluido en .gitignore)
├── .env.example                  # Plantilla documentada con ejemplos de cada variable
├── .gitignore                    # Protección de credenciales, temporales, venv y logs
├── main.py                       # Orquestador declarativo y delgado (~80 líneas)
├── requirements.txt              # Dependencias fijadas con versiones mínimas
├── README.md                     # Documentación técnica, arquitectura y guía de despliegue
├── data/                         # Capa de insumos / plantillas (*.example)
├── reports/                      # Artefactos y reportes generados dinámicamente (.gitkeep)
├── credentials/                  # Llaves privadas/JSON de Google (ignorado en Git, .gitkeep)
├── docs/                         # Documentación viva (Manual Operativo, Runbook, CHANGELOG)
├── tests/                        # Suite de pruebas unitarias automatizadas
├── api/                          # Endpoints HTTP Serverless (Vercel)
│   └── webhook.py                # Controlador HTTP desacoplado
└── src/
    ├── __init__.py
    ├── config.py                 # Centralización de configuración, paths absolutos y logging dual
    └── services/                 # Módulos especializados por responsabilidad técnica
        ├── __init__.py
        ├── gemini_client.py      # Capa de integración con API de Google Gemini (texto/audio)
        ├── green_api_client.py   # Capa de integración con Green API (WhatsApp)
        ├── sheets_client.py      # Capa de integración con Google Sheets API (lectura/escritura)
        ├── dispatch_parser.py    # Capa de ingesta, lectura y extracción de payloads crudos
        ├── dispatch_analyzer.py  # Reglas de negocio puras (validaciones, rangos, deduplicación)
        └── dispatch_exporter.py  # Formateo de presentación WhatsApp y reportes de auditoría
```

### Capas y Responsabilidades Técnicas

1. **Orquestador Delgado (`main.py`):**
   - No contiene lógica matemática ni llamadas HTTP directas.
   - Secuencia declarativamente el flujo: `GeminiClient` ➔ `DispatchParser` ➔ `DispatchAnalyzer` ➔ `SheetsClient` ➔ `DispatchExporter`.
2. **Capa de Reglas de Negocio Puras (`src/services/dispatch_analyzer.py`):**
   - Sin dependencias de red, librerías de presentación ni frameworks externos.
   - Valida siglas de factura autorizadas (`IC`, `DP`, `IR`), rangos de esfuerzo (1 a 5) y errores (0 a -3).
   - Resuelve auxiliares mediante coincidencia fonética/sin acentos contra el catálogo de activos.
   - Detecta y aísla duplicados contra el historial y el mismo lote.
   - Ensambla las 7 columnas físicas del registro atómico de `REGISTRO_DIARIO`.
3. **Capa de Clientes / Integración (`src/services/*_client.py`):**
   - Encapsulan autenticación, reintentos exponenciales (ante errores 429, 500, 503) y timeouts.
   - Si la API externa cambia de versión o endpoint, las reglas de negocio no se alteran.
4. **Capa de Ingesta y Estructuración (`src/services/dispatch_parser.py`):**
   - Extrae el contenido de webhooks y desensambla el JSON multimodal devuelto por la IA.
5. **Capa de Formateo y Presentación (`src/services/dispatch_exporter.py`):**
   - Formatea respuestas estéticas en Markdown enriquecido para WhatsApp y genera reportes JSON en `reports/`.
6. **Configuración Centralizada (`src/config.py`):**
   - Resuelve todas las rutas mediante `BASE_DIR = Path(__file__).resolve().parent.parent`.
   - Inicializa el sistema de logs dual escribiendo a la vez en consola y en `app.log`.

---

## 3. Despliegue y Ejecución

### Requisitos Previos
* Python 3.10 o superior.
* Archivo de entorno `.env` configurado a partir de `.env.example`.
* Credenciales de Google Sheets (`service_account.json` dentro de `credentials/` o `GOOGLE_CREDENTIALS_JSON`).

### Instalación de Dependencias
```bash
python -m venv .venv
# En Windows:
.venv\Scripts\activate
# En Linux/macOS:
source .venv/bin/activate

pip install -r requirements.txt
```

### Modos de Ejecución

1. **Ejecución Local / Tarea Programada (Orquestador CLI):**
   ```bash
   python main.py "Para Edward: Factura IC 104958 3 puntos esfuerzo"
   ```

2. **Modo Escucha en Vivo de WhatsApp (Sondeo continuo para pruebas):**
   ```bash
   python bot/tests/test_bot.py
   ```

3. **Ejecución de Pruebas Unitarias:**
   ```bash
   python -m unittest tests/test_services.py
   ```

4. **Despliegue Serverless en Vercel:**
   - Endpoint: `/api/webhook`
   - Configurado en `bot/vercel.json` apuntando al controlador desacoplado.
