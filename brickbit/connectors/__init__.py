"""Conectores de ingesta: convierten fuentes externas en señales de intención.

Cada conector expone una función `ingestar(conn, **opciones) -> ResultadoIngesta`
y se registra aquí para que la UI y los jobs programados lo descubran.

Contrato que todo conector debe cumplir:
  1. **Idempotente** — correrlo dos veces no duplica leads ni señales. La
     deduplicación vive en índices únicos de la base (origen, origen_id).
  2. **Degradación limpia** — si la fuente no responde, devuelve un resultado
     con `error` poblado en lugar de lanzar excepción; la app sigue viva.
  3. **Trazable** — cada señal guarda de qué fuente y con qué folio se creó.
"""

from .base import ResultadoIngesta
from . import permisos_cdmx

CONECTORES = {
    "permisos_cdmx": {
        "label": "🏗️ Permisos de construcción CDMX",
        "modulo": permisos_cdmx,
        "senal": "permiso_construccion",
        "descripcion": (
            "Manifestaciones de construcción registradas ante las alcaldías de CDMX. "
            "Cada folio nuevo es un desarrollador con proyecto activo y presupuesto aprobado."
        ),
    },
}

__all__ = ["CONECTORES", "ResultadoIngesta", "permisos_cdmx"]
