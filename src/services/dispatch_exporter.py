import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional
from src.config import settings, get_logger

logger = get_logger("dispatch_exporter")


class DispatchExporter:
    """Capa de formateo, presentación y generación de artefactos y reportes finales."""

    @staticmethod
    def describir_incompleto(inc: Dict[str, Any]) -> str:
        """Construye una descripción legible y pedagógica de un despacho con datos omitidos."""
        tipo = inc.get("tipo_factura")
        num = inc.get("numero_factura")
        emp = inc.get("nombre_empleado")
        motivo = inc.get("motivo", "Datos incompletos")

        if tipo and num and not emp:
            return f"Factura *{tipo}-{num}*: falta el nombre del auxiliar"
        if emp and (not num or not tipo):
            return f"Auxiliar *{emp}*: falta el número o serie de factura"
        if tipo and num and emp:
            return f"Factura *{tipo}-{num}* ({emp}): {motivo}"
        return f"Despacho #{inc.get('indice', '?')}: {motivo}"

    @classmethod
    def formatear_mensaje_whatsapp(
        cls,
        nuevos: List[Dict[str, Any]],
        duplicados: Optional[List[Dict[str, Any]]] = None,
        incompletos: Optional[List[Dict[str, Any]]] = None,
    ) -> str:
        """
        Genera el mensaje final de confirmación estructurado con formato enriquecido para WhatsApp.
        """
        duplicados = duplicados or []
        incompletos = incompletos or []
        lineas: List[str] = []

        # Caso 1: Cero registros nuevos guardados
        if not nuevos:
            if duplicados and not incompletos:
                lineas.append("⚠️ *Aviso de duplicidad:*")
                lineas.append("Los siguientes despachos ya estaban registrados previamente:")
                for d in duplicados:
                    lineas.append(f"• *{d['nombre_oficial']}*: {d['factura_label']}")
                return "\n".join(lineas)

            if incompletos and not duplicados:
                lineas.append("⚠️ *No se pudo registrar ningún despacho por datos incompletos:*")
                for inc in incompletos:
                    lineas.append(f"• {cls.describir_incompleto(inc)}")
                lineas.append("\n💡 *Por favor reenvía el mensaje o audio indicando los datos faltantes.*")
                lineas.append("👉 *Ejemplo:* `IC104958 Edward 3 puntos`")
                return "\n".join(lineas)

            if incompletos and duplicados:
                lineas.append("⚠️ *Ningún despacho nuevo registrado:*")
                lineas.append("\n*Omitidos por duplicidad:*")
                for d in duplicados:
                    lineas.append(f"• *{d['nombre_oficial']}*: {d['factura_label']}")
                lineas.append("\n*Omitidos por datos incompletos:*")
                for inc in incompletos:
                    lineas.append(f"• {cls.describir_incompleto(inc)}")
                lineas.append("\n💡 *Por favor reenvía únicamente los despachos incompletos.*")
                return "\n".join(lineas)

            return "ℹ️ *No se procesaron despachos en este mensaje.*"

        # Caso 2: Exactamente 1 despacho nuevo
        if len(nuevos) == 1:
            r = nuevos[0]
            lineas.append(
                "✅ *¡Despacho registrado con éxito!*\n"
                f"📄 *Documento:* {r['factura_label']}\n"
                f"👷 *Auxiliar:* {r['nombre_oficial']} (ID: {r['id_empleado']})\n"
                f"⚡ *Esfuerzo:* {r['puntos_esfuerzo']} pts | "
                f"⚠️ *Errores:* {r['puntos_error']}\n"
                f"🕒 *Hora:* {r['fecha_hora']} (ID: `{r['id_registro']}`)"
            )
        # Caso 3: Múltiples despachos nuevos en bloque
        else:
            lineas.append(f"✅ *¡{len(nuevos)} despachos registrados en bloque!*")
            for idx, r in enumerate(nuevos, start=1):
                lineas.append(
                    f"{idx}. *{r['factura_label']}* — {r['nombre_oficial']} "
                    f"({r['puntos_esfuerzo']} pts | {r['puntos_error']} err)"
                )
            lineas.append(f"🕒 *Hora:* {nuevos[0]['fecha_hora']}")

        # Avisos adicionales en lotes mixtos
        if duplicados:
            lineas.append("\n⚠️ *Omitidos por duplicidad (ya registrados previamente):*")
            for d in duplicados:
                lineas.append(f"• *{d['nombre_oficial']}*: {d['factura_label']}")

        if incompletos:
            lineas.append("\n⚠️ *Omitidos por datos incompletos (requieren reenvío):*")
            for inc in incompletos:
                lineas.append(f"• {cls.describir_incompleto(inc)}")
            lineas.append(
                f"\n💡 *Los {len(nuevos)} despachos válidos ya quedaron guardados.* "
                "Por favor reenvía únicamente los omitidos."
            )

        return "\n".join(lineas)

    @staticmethod
    def formatear_error_operativo(mensaje_error: str) -> str:
        """Formatea un mensaje de error operacional para ser devuelto por WhatsApp."""
        return (
            f"⚠️ *No se pudo registrar en Google Sheets:*\n{mensaje_error}\n\n"
            "💡 *Ejemplo individual:* `IC104958 Edward 3 puntos`\n"
            "💡 *Ejemplo en bloque:* `Para Edward: IC 104958 3 puntos, DP 36600 2 puntos`"
        )

    @staticmethod
    def exportar_reporte_auditoria_json(
        datos_procesados: Dict[str, Any], prefijo: str = "lote_despachos"
    ) -> Optional[Path]:
        """Exporta un artefacto JSON en reports/ (o /tmp en Vercel) para trazabilidad y auditoría."""
        import os
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        directorio = Path("/tmp") if os.getenv("VERCEL") else settings.REPORTS_DIR
        archivo_salida = directorio / f"{prefijo}_{timestamp}.json"
        try:
            with open(archivo_salida, "w", encoding="utf-8") as f:
                json.dump(datos_procesados, f, indent=2, ensure_ascii=False)
            logger.info("Reporte de auditoría generado en: %s", archivo_salida)
            return archivo_salida
        except Exception as exc:
            logger.debug("No se persistió reporte JSON en entorno serverless: %s", exc)
            return None

