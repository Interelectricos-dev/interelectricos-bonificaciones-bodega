import json
import unittest
from pathlib import Path

from src.config import settings
from src.services.dispatch_analyzer import (
    normalizar_numero_factura,
    procesar_y_estructurar_registros,
    resolver_empleado,
    segregar_despachos_lote,
    validar_un_despacho,
)
from src.services.dispatch_exporter import DispatchExporter
from src.services.dispatch_parser import DispatchParser


class TestDispatchArchitecture(unittest.TestCase):
    """Pruebas unitarias de la arquitectura desacoplada por servicios."""

    def test_rutas_absolutas_config(self):
        """Verifica que las rutas en config.py sean absolutas y existan las carpetas requeridas."""
        self.assertTrue(settings.BASE_DIR.is_absolute())
        self.assertTrue(settings.DATA_DIR.is_absolute())
        self.assertTrue(settings.REPORTS_DIR.is_absolute())
        self.assertTrue(settings.CREDENTIALS_DIR.is_absolute())
        self.assertTrue(settings.DATA_DIR.exists())
        self.assertTrue(settings.REPORTS_DIR.exists())
        self.assertTrue(settings.CREDENTIALS_DIR.exists())

    def test_parser_ai_response_valida(self):
        """Verifica ingesta y estructuración de respuestas JSON de la IA."""
        payload_json = json.dumps(
            {
                "es_despacho": True,
                "despachos": [
                    {
                        "tipo_factura": "IC",
                        "numero_factura": 104958,
                        "nombre_empleado": "Edward",
                        "puntos_esfuerzo": 3,
                        "puntos_error": 0,
                    }
                ],
            }
        )
        resultado = DispatchParser.parse_ai_json_response(payload_json)
        self.assertEqual(len(resultado), 1)
        self.assertEqual(resultado[0]["numero_factura"], 104958)

    def test_parser_mensaje_no_despacho(self):
        """Verifica que los mensajes que no son despachos lancen la excepción controlada."""
        payload_json = json.dumps({"es_despacho": False, "despachos": []})
        with self.assertRaises(ValueError) as ctx:
            DispatchParser.parse_ai_json_response(payload_json)
        self.assertIn("NO_ES_DESPACHO", str(ctx.exception))

    def test_analizador_reglas_despacho_individual(self):
        """Verifica las reglas de negocio en la validación individual."""
        # Caso válido con normalización
        datos = {
            "tipo_factura": "ic",
            "numero_factura": "104958.0",
            "nombre_empleado": "Edward",
            "puntos_esfuerzo": 4,
            "puntos_error": 1,  # Debe forzar signo negativo
        }
        res = validar_un_despacho(datos)
        self.assertEqual(res["tipo_factura"], "IC")
        self.assertEqual(res["numero_factura"], "104958")
        self.assertEqual(res["puntos_error"], -1)

        # Caso tipo factura inválido
        datos_err = datos.copy()
        datos_err["tipo_factura"] = "FACTURA_X"
        with self.assertRaises(ValueError):
            validar_un_despacho(datos_err)

        # Caso esfuerzo fuera de rango
        datos_esf = datos.copy()
        datos_esf["puntos_esfuerzo"] = 6
        with self.assertRaises(ValueError):
            validar_un_despacho(datos_esf)

    def test_analizador_resolucion_empleados_fonetica(self):
        """Verifica resolución flexible de nombres con acentos y variaciones."""
        id_emp, nombre = resolver_empleado("fabián")
        self.assertEqual(id_emp, "1003")
        self.assertEqual(nombre, "Fabian Ortiz")

        id_emp, nombre = resolver_empleado("Sneider")
        self.assertEqual(id_emp, "1001")
        self.assertEqual(nombre, "Sneider Villanueva")

        with self.assertRaises(ValueError):
            resolver_empleado("EmpleadoInexistente")

    def test_analizador_segregacion_y_duplicados(self):
        """Verifica segregación de fallos parciales y deduplicación contra existentes."""
        lote = [
            {"tipo_factura": "IC", "numero_factura": 2001, "nombre_empleado": "Edward", "puntos_esfuerzo": 3, "puntos_error": 0},
            {"tipo_factura": "DP", "numero_factura": 2002, "nombre_empleado": "Edward", "puntos_esfuerzo": 2, "puntos_error": 0},
            {"tipo_factura": None, "numero_factura": 2003, "nombre_empleado": "Edward"},  # Incompleto
        ]
        segregados = segregar_despachos_lote(lote)
        self.assertEqual(len(segregados["validos"]), 2)
        self.assertEqual(len(segregados["incompletos"]), 1)

        existentes = {("1002", "IC", "2001")}
        analisis = procesar_y_estructurar_registros(segregados["validos"], existentes_set=existentes)
        self.assertEqual(len(analisis["duplicados"]), 1)
        self.assertEqual(len(analisis["nuevos"]), 1)
        # Comprobar estructura de 7 columnas físicas para REGISTRO_DIARIO
        fila_7 = analisis["nuevos"][0]["fila_sheets"]
        self.assertEqual(len(fila_7), 7)
        self.assertEqual(fila_7[2], "1002")  # ID_Empleado
        self.assertEqual(fila_7[3], "DP")    # Tipo
        self.assertEqual(fila_7[4], "2002")  # Numero

    def test_exportador_formateo_mensajes(self):
        """Verifica presentación estética de confirmación en WhatsApp."""
        nuevos = [
            {
                "factura_label": "IC-104958",
                "nombre_oficial": "Edward Sanchez",
                "id_empleado": "1002",
                "puntos_esfuerzo": 3,
                "puntos_error": 0,
                "fecha_hora": "2026-11-09 10:00:00",
                "id_registro": "test1234",
            }
        ]
        msg = DispatchExporter.formatear_mensaje_whatsapp(nuevos=nuevos)
        self.assertIn("✓ *DESPACHO REGISTRADO*", msg)
        self.assertIn("• *Factura:* IC-104958", msg)
        self.assertIn("• *Hora:* 2026-11-09 10:00", msg)


if __name__ == "__main__":
    unittest.main()

