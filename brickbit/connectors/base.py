"""Utilidades compartidas por los conectores de ingesta."""

import json
import math
import re
import unicodedata
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from datetime import datetime

from .. import config


@dataclass
class ResultadoIngesta:
    """Resumen de una corrida de conector. Nunca lanza: los fallos van en `error`."""

    fuente: str
    registros_leidos: int = 0
    leads_nuevos: int = 0
    leads_actualizados: int = 0
    senales_nuevas: int = 0
    duplicados_omitidos: int = 0
    descartados: int = 0
    modo: str = "desconocido"          # "api" | "fixture"
    error: str | None = None
    avisos: list[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return self.error is None

    def resumen(self) -> str:
        if self.error:
            return f"❌ {self.fuente}: {self.error}"
        return (
            f"✅ {self.fuente} ({self.modo}): {self.registros_leidos} registros leídos · "
            f"{self.leads_nuevos} leads nuevos · {self.leads_actualizados} actualizados · "
            f"{self.senales_nuevas} señales · {self.duplicados_omitidos} duplicados omitidos · "
            f"{self.descartados} descartados"
        )


# ---------------------------------------------------------------------------
# Normalización de texto y fechas
# ---------------------------------------------------------------------------

def sin_acentos(texto: str) -> str:
    """'Álvaro Obregón' -> 'alvaro obregon'. Para comparar claves, no para mostrar."""
    if not texto:
        return ""
    descompuesto = unicodedata.normalize("NFKD", str(texto))
    return "".join(c for c in descompuesto if not unicodedata.combining(c)).lower().strip()


def clave_normalizada(texto: str) -> str:
    """Clave estable para deduplicar nombres: sin acentos, sin puntuación, sin dobles espacios.

    'Constructora Bosque Real, S.A. de C.V.' y 'CONSTRUCTORA BOSQUE REAL SA DE CV'
    colapsan a la misma clave, que es lo que evita crear el mismo desarrollador dos veces.
    """
    base = sin_acentos(texto)
    base = re.sub(r"\b(s\.?a\.?p?\.?i?\.?|de|c\.?v\.?|s\.?\s?de\s?r\.?l\.?)\b", " ", base)
    base = re.sub(r"[^a-z0-9ñ ]+", " ", base)
    return re.sub(r"\s+", " ", base).strip()


def titulo(texto: str) -> str:
    """Normaliza MAYÚSCULAS de registros oficiales a una forma presentable."""
    limpio = re.sub(r"\s+", " ", str(texto or "")).strip()
    if not limpio:
        return ""
    return limpio.title() if limpio.isupper() else limpio


_FORMATOS_FECHA = (
    "%Y-%m-%dT%H:%M:%S", "%Y-%m-%d %H:%M:%S", "%Y-%m-%d",
    "%d/%m/%Y", "%d-%m-%Y", "%Y/%m/%d", "%d/%m/%y",
)


def parse_fecha(valor) -> datetime | None:
    """Los datasets oficiales mezclan formatos de fecha; probamos los comunes."""
    if valor in (None, "", "NULL"):
        return None
    texto = str(valor).strip().replace("Z", "")
    for fmt in _FORMATOS_FECHA:
        try:
            return datetime.strptime(texto[:len(datetime.now().strftime(fmt))], fmt)
        except ValueError:
            continue
    try:  # último recurso: ISO con microsegundos u offset
        return datetime.fromisoformat(texto.split("+")[0])
    except ValueError:
        return None


def a_float(valor) -> float | None:
    """Convierte '1,234.50' o ' 45 ' a float; None si no es numérico."""
    if valor in (None, "", "NULL"):
        return None
    try:
        return float(str(valor).replace(",", "").strip())
    except ValueError:
        return None


# ---------------------------------------------------------------------------
# Geolocalización a zonas BrickBit
# ---------------------------------------------------------------------------

def _haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    r = 6371.0
    dlat, dlon = math.radians(lat2 - lat1), math.radians(lon2 - lon1)
    a = (math.sin(dlat / 2) ** 2
         + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2) ** 2)
    return 2 * r * math.asin(math.sqrt(a))


def zona_mas_cercana(lat: float | None, lon: float | None,
                     radio_max_km: float = 4.0) -> tuple[str | None, float | None]:
    """Asigna el punto a la zona BrickBit más cercana dentro del radio.

    Devuelve (zona, distancia_km). Fuera del radio devuelve (None, distancia):
    un permiso en Milpa Alta no debe caer en Polanco solo por ser el menos lejano.
    """
    if lat is None or lon is None:
        return None, None
    if not (18.9 <= lat <= 19.8 and -99.4 <= lon <= -98.8):  # fuera del Valle de México
        return None, None

    mejor, mejor_dist = None, float("inf")
    for nombre, datos in config.ZONAS_CDMX.items():
        d = _haversine_km(lat, lon, datos["lat"], datos["lon"])
        if d < mejor_dist:
            mejor, mejor_dist = nombre, d
    return (mejor if mejor_dist <= radio_max_km else None), round(mejor_dist, 2)


# ---------------------------------------------------------------------------
# Cliente HTTP mínimo (stdlib: sin dependencias nuevas)
# ---------------------------------------------------------------------------

class ErrorFuente(Exception):
    """La fuente externa no se pudo consultar. El conector lo captura y degrada."""


def get_json(url: str, timeout: int = 20, intentos: int = 3) -> dict:
    """GET con reintentos y backoff. Lanza ErrorFuente con un mensaje legible."""
    ultimo = ""
    for intento in range(intentos):
        try:
            peticion = urllib.request.Request(
                url, headers={"User-Agent": "BrickBit/0.1 (conector datos abiertos)"}
            )
            with urllib.request.urlopen(peticion, timeout=timeout) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            ultimo = f"HTTP {e.code} al consultar la fuente"
            if e.code < 500:  # 4xx no se reintenta: la petición está mal formada
                break
        except urllib.error.URLError as e:
            ultimo = f"sin conexión con la fuente ({e.reason})"
        except (TimeoutError, json.JSONDecodeError, OSError) as e:
            ultimo = f"respuesta ilegible o timeout ({type(e).__name__})"
        if intento < intentos - 1:
            import time
            time.sleep(2 ** intento)
    raise ErrorFuente(ultimo or "fallo desconocido al consultar la fuente")
