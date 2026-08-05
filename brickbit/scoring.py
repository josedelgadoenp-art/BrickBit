"""Motor de scoring: Fit x Intención -> prioridad.

score_final = 0.4 * fit + 0.6 * intencion

- fit:        qué tan parecido es el lead al cliente ideal (0-100, viene del lead).
- intencion:  suma de pesos de señales con decaimiento exponencial por recencia
              (vida media configurable), pasada por una curva saturante para que
              una sola señal fuerte no dispare la alarma pero varias señales
              recientes sí. Una señal de hace 45 días vale la mitad que una de
              hoy: vendemos "quién necesita comprar HOY".

Prioridad: A (>= UMBRAL_A) contactar hoy · B (>= UMBRAL_B) esta semana · C nutrir.
"""

import math
from datetime import datetime

import pandas as pd

from . import config


def _decaimiento(fecha_senal: str, ahora: datetime) -> float:
    try:
        dt = datetime.strptime(fecha_senal[:19], "%Y-%m-%d %H:%M:%S")
    except (ValueError, TypeError):
        return 1.0
    dias = max((ahora - dt).days, 0)
    return math.pow(0.5, dias / config.SENAL_VIDA_MEDIA_DIAS)


def score_intencion(senales_lead: pd.DataFrame, ahora: datetime | None = None) -> float:
    """Suma ponderada por recencia de las señales, con saturación diminishing.

    total=100 (una señal fuerte y fresca) -> ~50; total=200 -> ~75; total=300 -> ~88.
    Así la prioridad A exige acumulación de señales recientes, no una sola.
    """
    ahora = ahora or datetime.now()
    total = 0.0
    for _, s in senales_lead.iterrows():
        info = config.SENALES.get(s["tipo"])
        if not info:
            continue
        total += info["peso"] * _decaimiento(s["fecha"], ahora)
    return round(100.0 * (1.0 - math.pow(0.5, total / 100.0)), 1)


def prioridad(score: float) -> str:
    if score >= config.UMBRAL_A:
        return "A"
    if score >= config.UMBRAL_B:
        return "B"
    return "C"


def calcular_scores(leads: pd.DataFrame, senales: pd.DataFrame) -> pd.DataFrame:
    """Devuelve leads con columnas: intencion, score, prioridad, senales_labels, cross_sell."""
    ahora = datetime.now()
    if leads.empty:
        return leads.assign(intencion=[], score=[], prioridad=[], senales_labels=[], cross_sell=[])

    por_lead = dict(tuple(senales.groupby("lead_id"))) if not senales.empty else {}

    intenciones, labels, cross = [], [], []
    for lead_id in leads["id"]:
        s = por_lead.get(lead_id, pd.DataFrame(columns=["tipo", "fecha"]))
        intenciones.append(score_intencion(s, ahora))
        tipos = list(s["tipo"]) if not s.empty else []
        labels.append(", ".join(config.SENALES[t]["label"] for t in tipos if t in config.SENALES))
        cross.append(any(config.SENALES.get(t, {}).get("cross_sell") for t in tipos))

    out = leads.copy()
    out["intencion"] = intenciones
    out["score"] = (0.4 * out["fit_score"] + 0.6 * out["intencion"]).round(1)
    out["prioridad"] = out["score"].map(prioridad)
    out["senales_labels"] = labels
    out["cross_sell"] = cross
    return out.sort_values("score", ascending=False)
