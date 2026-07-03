"""Prima Viva: suscripción dinámica cuya prima baja con hábitos verificados.

El seguro deja de ser un precio fijo anual y se convierte en un sistema vivo:
wearables, telemática de manejo y prevención verificable reducen la prima
mes a mes. Aquí los datos se simulan con controles; en producción vendrían
de APIs de wearables (Apple Health, Google Fit) y telemática vehicular.
"""

from __future__ import annotations

import numpy as np
import streamlit as st

from core.simulator import prima_mensual_estimada

DESCUENTO_MAX = 0.25   # tope regulatorio demo: -25% de prima

DEFAULT_HABITOS = {
    "pasos": 6_000,          # pasos diarios promedio
    "sueno": 6.5,            # horas de sueño
    "manejo_brusco": 25,     # % de frenadas/aceleraciones bruscas (telemática)
    "chequeo_anual": False,  # chequeo médico preventivo verificado
    "sin_tabaco": True,      # racha sin fumar verificada
    "racha_semanas": 4,      # semanas cumpliendo metas de hábitos
}


def habitos() -> dict:
    st.session_state.setdefault("habitos", dict(DEFAULT_HABITOS))
    return st.session_state["habitos"]


def score_habitos(h: dict) -> float:
    """Score de vitalidad verificada 0–100."""
    s = 0.0
    s += min(h["pasos"] / 10_000, 1.2) * 30          # movimiento
    s += max(0, 1 - abs(h["sueno"] - 7.5) / 3) * 20  # sueño óptimo ~7.5h
    s += (1 - h["manejo_brusco"] / 100) * 20         # manejo suave
    s += 15 if h["chequeo_anual"] else 0
    s += 15 if h["sin_tabaco"] else 0
    return float(np.clip(s, 0, 100))


def descuento_actual(score: float, racha_semanas: int) -> float:
    """Fracción de descuento: el score define el techo, la racha lo consolida."""
    techo = DESCUENTO_MAX * (score / 100)
    consolidacion = min(racha_semanas / 26, 1.0)     # 6 meses para consolidar
    return techo * consolidacion


def prima_base_paquete(perfil: dict, cobertura: dict) -> float:
    """Prima mensual del paquete activo; si no hay escudos, cotiza el paquete Vital completo."""
    c = dict(cobertura)
    if not any(c[k] for k in ("gmm", "vida", "retiro", "patrimonio")):
        c.update(gmm=True, vida=True, patrimonio=True)
    primas = prima_mensual_estimada(perfil, c)
    primas.pop("retiro", None)   # el aporte de ahorro no se descuenta, no es costo
    return float(sum(primas.values()))


def proyeccion_12_meses(prima_base: float, score: float, racha_actual: int) -> tuple[list, list]:
    """(meses, primas) si el usuario mantiene sus hábitos 12 meses más."""
    meses = list(range(13))
    primas = []
    for m in meses:
        d = descuento_actual(score, racha_actual + m * 4)
        primas.append(prima_base * (1 - d))
    return meses, primas
