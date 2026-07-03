"""Gemelo Familiar: fusión de dos gemelos digitales en un hogar.

Simula el hogar completo y el análisis de supervivencia cruzado: qué pasa
con la economía familiar si falta cualquiera de los dos titulares, y qué
suma asegurada cierra cada brecha.
"""

from __future__ import annotations

import streamlit as st

DEFAULT_PAREJA = {
    "nombre": "",
    "edad": 32,
    "ingreso_mensual": 25_000.0,
    "gastos_aportados": 0.0,       # gasto extra que agrega al hogar
    "fumador": False,
    "salud_general": "Buena",
    "activo": False,
}


def pareja() -> dict:
    return st.session_state.setdefault("pareja", dict(DEFAULT_PAREJA))


def perfil_hogar(p: dict, pj: dict) -> dict:
    """Perfil fusionado del hogar para el simulador Monte Carlo."""
    hogar = dict(p)
    hogar["nombre"] = f"{p['nombre'] or 'Titular'} + {pj['nombre'] or 'Pareja'}"
    hogar["ingreso_mensual"] = p["ingreso_mensual"] + pj["ingreso_mensual"]
    hogar["gastos_mensuales"] = p["gastos_mensuales"] + max(pj["gastos_aportados"], 0)
    # el riesgo biológico del hogar toma el peor perfil de los dos
    if pj["fumador"]:
        hogar["fumador"] = True
    orden = ["Excelente", "Buena", "Regular", "Delicada"]
    if orden.index(pj["salud_general"]) > orden.index(p["salud_general"]):
        hogar["salud_general"] = pj["salud_general"]
    return hogar


def analisis_supervivencia(p: dict, pj: dict, cobertura: dict) -> list[dict]:
    """Brecha económica si falta cada miembro, y suma asegurada sugerida."""
    gastos_hogar = p["gastos_mensuales"] + max(pj["gastos_aportados"], 0)
    ahorro = p["ahorro_actual"]
    suma_activa = cobertura["suma_vida"] if cobertura["vida"] else 0.0
    resultados = []
    for quien, ingreso, con_seguro in (
        (p["nombre"] or "Titular", p["ingreso_mensual"], suma_activa),
        (pj["nombre"] or "Pareja", pj["ingreso_mensual"], 0.0),
    ):
        ingreso_restante = (p["ingreso_mensual"] + pj["ingreso_mensual"]) - ingreso
        # necesidad: sostener el hogar 5 años + fondo de transición
        deficit_mensual = max(gastos_hogar - ingreso_restante, 0)
        necesidad = deficit_mensual * 12 * 5 + gastos_hogar * 6
        recursos = ahorro + con_seguro
        brecha = max(necesidad - recursos, 0)
        resultados.append({
            "quien": quien,
            "aporta": ingreso,
            "necesidad": necesidad,
            "recursos": recursos,
            "brecha": brecha,
            "cobertura_pct": min(recursos / necesidad, 1.0) * 100 if necesidad > 0 else 100.0,
            "suma_sugerida": max(round(brecha, -4), 0),
        })
    return resultados
