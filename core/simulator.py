"""Motor de simulación Monte Carlo del Gemelo Digital.

Simula miles de trayectorias de vida (patrimonio, salud, longevidad) a partir
del perfil del usuario, con y sin protección GNP, para visualizar el impacto
real de asegurarse. Los parámetros actuariales son aproximaciones de
demostración, no tarifas reales de GNP.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import streamlit as st

# ---------------------------------------------------------------------------
# Parámetros macro (aproximados para México, fines demostrativos)
# ---------------------------------------------------------------------------
INFLACION_GENERAL = 0.045
INFLACION_MEDICA = 0.115          # la inflación médica en México duplica+ la general
CRECIMIENTO_SALARIAL = 0.055
RETORNO_MEDIO = 0.075             # retorno nominal de inversión propia
RETORNO_VOL = 0.12
RETORNO_PLAN_RETIRO = 0.085       # plan con gestión institucional
EDAD_MAX = 90

RIESGO_ZONA = {                    # multiplicador de siniestros patrimoniales
    "CDMX / Zona Metropolitana": 1.35,
    "Guadalajara": 1.15,
    "Monterrey": 1.10,
    "Bajío (Querétaro, León, SLP)": 1.00,
    "Sureste (Mérida, Cancún)": 0.85,
    "Norte (Chihuahua, Hermosillo)": 1.05,
    "Otra ciudad media": 0.90,
    "Zona rural": 0.80,
}

_EJERCICIO_MULT = {"Nunca": 1.30, "Ocasional": 1.10, "Regular": 0.90, "Intenso": 0.85}
_SALUD_MULT = {"Excelente": 0.80, "Buena": 1.00, "Regular": 1.30, "Delicada": 1.75}


def _mult_salud(perfil: dict) -> float:
    m = _EJERCICIO_MULT.get(perfil["ejercicio"], 1.0) * _SALUD_MULT.get(perfil["salud_general"], 1.0)
    if perfil["fumador"]:
        m *= 1.55
    return m


def prima_mensual_estimada(perfil: dict, cobertura: dict) -> dict:
    """Primas mensuales aproximadas (demo) según edad y riesgo."""
    edad = perfil["edad"]
    ms = _mult_salud(perfil)
    primas = {}
    if cobertura["gmm"]:
        primas["gmm"] = round((650 + edad * 28) * ms * (1 + 0.25 * perfil["dependientes"]), 0)
    if cobertura["vida"]:
        tasa = 0.00009 * np.exp(0.055 * max(edad - 25, 0)) * ms
        primas["vida"] = round(cobertura["suma_vida"] * tasa, 0)
    if cobertura["retiro"]:
        primas["retiro"] = round(cobertura["aporte_retiro"], 0)
    if cobertura["patrimonio"]:
        primas["patrimonio"] = round(1_100 * RIESGO_ZONA.get(perfil["zona"], 1.0), 0)
    return primas


@st.cache_data(show_spinner=False)
def simular(perfil_t: tuple, cobertura_t: tuple, n_sims: int = 10_000, seed: int = 7) -> dict:
    """Corre la simulación. Recibe tuplas hashables (ver empaquetar())."""
    perfil = dict(perfil_t)
    cobertura = dict(cobertura_t)

    rng = np.random.default_rng(seed)
    edad0 = int(perfil["edad"])
    anios = max(EDAD_MAX - edad0, 5)
    edades = np.arange(edad0, edad0 + anios)

    ms = _mult_salud(perfil)
    zona_mult = RIESGO_ZONA.get(perfil["zona"], 1.0)

    ingreso_anual = perfil["ingreso_mensual"] * 12.0
    gastos_anual = perfil["gastos_mensuales"] * 12.0
    ahorro_extra = perfil["ahorro_mensual"] * 12.0
    edad_retiro = int(perfil["edad_retiro"])

    primas = prima_mensual_estimada(perfil, cobertura)
    prima_anual = sum(primas.values()) * 12.0

    # --- estado por simulación -------------------------------------------------
    wealth = np.full(n_sims, float(perfil["ahorro_actual"]))
    fondo_retiro = np.zeros(n_sims)
    vivo = np.ones(n_sims, dtype=bool)
    incapacitado = np.zeros(n_sims, dtype=bool)
    edad_muerte = np.full(n_sims, edad0 + anios, dtype=float)
    wealth_muerte = np.zeros(n_sims)
    ruina = np.zeros(n_sims, dtype=bool)
    gasto_medico_bolsillo = np.zeros(n_sims)

    trayectoria = np.zeros((anios, n_sims))

    for t, edad in enumerate(edades):
        activos = vivo.copy()

        # Mortalidad (Gompertz–Makeham ajustada por hábitos)
        hazard = (0.0004 + 3.2e-5 * np.exp(0.093 * edad)) * ms
        muere = activos & (rng.random(n_sims) < np.clip(hazard, 0, 0.5))
        edad_muerte[muere] = edad
        wealth_muerte[muere] = wealth[muere] + fondo_retiro[muere]
        vivo &= ~muere

        # Flujo laboral
        trabajando = vivo & (edad < edad_retiro) & ~incapacitado
        ingreso_t = ingreso_anual * (1 + CRECIMIENTO_SALARIAL) ** t
        gastos_t = gastos_anual * (1 + INFLACION_GENERAL) ** t

        # Pérdida de empleo: ~6 meses sin ingreso
        desempleo = trabajando & (rng.random(n_sims) < 0.045)
        factor_ingreso = np.where(desempleo, 0.5, 1.0)

        # Invalidez permanente (reduce ingreso a 40%)
        nueva_inc = vivo & ~incapacitado & (rng.random(n_sims) < 0.0022 * ms)
        incapacitado |= nueva_inc
        factor_ingreso = np.where(incapacitado & (edad < edad_retiro), 0.40, factor_ingreso)

        flujo = np.where(vivo & (edad < edad_retiro), ingreso_t * factor_ingreso - gastos_t, 0.0)
        flujo = np.where(vivo & (edad >= edad_retiro), -gastos_t * 0.85, flujo)
        flujo = np.where(vivo, flujo + np.where(edad < edad_retiro, ahorro_extra, 0.0) - prima_anual, 0.0)

        # Evento médico mayor (probabilidad crece con la edad)
        p_med = np.clip((0.020 + 0.0011 * max(edad - 30, 0)) * ms, 0, 0.6)
        evento_med = vivo & (rng.random(n_sims) < p_med)
        # cola pesada: mediana ~$160k pero p99 supera $2M (evento catastrófico)
        costo_med = rng.lognormal(mean=12.0, sigma=1.1, size=n_sims) * (1 + INFLACION_MEDICA) ** t
        if cobertura["gmm"]:
            # deducible + 10% coaseguro con tope
            bolsillo = np.minimum(costo_med, 28_000 + 0.10 * np.maximum(costo_med - 28_000, 0))
            bolsillo = np.minimum(bolsillo, 75_000 * (1 + INFLACION_GENERAL) ** t)
        else:
            bolsillo = costo_med
        golpe_med = np.where(evento_med, bolsillo, 0.0)
        gasto_medico_bolsillo += golpe_med

        # Siniestro patrimonial (auto / hogar) según zona
        evento_pat = vivo & (rng.random(n_sims) < 0.06 * zona_mult)
        costo_pat = rng.lognormal(mean=10.6, sigma=0.7, size=n_sims) * (1 + INFLACION_GENERAL) ** t
        if cobertura["patrimonio"]:
            costo_pat = np.minimum(costo_pat, 9_000 * (1 + INFLACION_GENERAL) ** t)
        golpe_pat = np.where(evento_pat, costo_pat, 0.0)

        # Rendimiento del patrimonio líquido
        r = rng.normal(RETORNO_MEDIO, RETORNO_VOL, n_sims)
        wealth = np.where(vivo, wealth * (1 + np.where(wealth > 0, r, 0.02)) + flujo - golpe_med - golpe_pat, wealth)

        # Plan de retiro GNP: aporte disciplinado, retorno institucional con piso
        if cobertura["retiro"]:
            aporta = vivo & (edad < edad_retiro)
            r_plan = np.maximum(rng.normal(RETORNO_PLAN_RETIRO, 0.06, n_sims), 0.0)
            fondo_retiro = fondo_retiro * (1 + r_plan) + np.where(aporta, cobertura["aporte_retiro"] * 12, 0.0)
            # el aporte ya se descontó vía prima_anual

        # Al llegar al retiro, el fondo se libera al patrimonio
        if edad == edad_retiro:
            wealth = np.where(vivo, wealth + fondo_retiro, wealth)
            fondo_retiro = np.zeros(n_sims)

        ruina |= vivo & (wealth < 0) & (edad < edad_retiro)
        trayectoria[t] = np.where(vivo, wealth + fondo_retiro, np.nan)

    # --- métricas ---------------------------------------------------------------
    idx_ret = min(max(edad_retiro - edad0, 0), anios - 1)
    pat_retiro = trayectoria[idx_ret]
    pat_retiro = pat_retiro[~np.isnan(pat_retiro)]

    # Protección familiar: recursos disponibles si el titular fallece antes del retiro
    fallece_antes = edad_muerte < edad_retiro
    necesidad_familia = gastos_anual * 5 * (1 + 0.6 * perfil["dependientes"])
    recursos = np.maximum(wealth_muerte, 0.0)
    if cobertura["vida"]:
        recursos = recursos + cobertura["suma_vida"]
    if fallece_antes.any() and perfil["dependientes"] > 0:
        prot_familiar = float(np.mean(np.clip(recursos[fallece_antes] / necesidad_familia, 0, 1)))
    else:
        prot_familiar = 1.0

    percentiles = {p: np.nanpercentile(trayectoria, p, axis=1) for p in (10, 25, 50, 75, 90)}

    prob_ruina = float(ruina.mean())
    esperanza_vida = float(np.median(edad_muerte))
    mediana_retiro = float(np.median(pat_retiro)) if len(pat_retiro) else 0.0

    # Índice de Estabilidad Vital (0–100)
    disp = percentiles[90][idx_ret] - percentiles[10][idx_ret]
    rel_disp = disp / max(abs(percentiles[50][idx_ret]), 1.0)
    estabilidad = 100.0
    estabilidad -= 55 * prob_ruina * 2.2
    estabilidad -= 20 * min(rel_disp / 6.0, 1.0)
    estabilidad -= 25 * (1 - prot_familiar)
    estabilidad = float(np.clip(estabilidad, 3, 99))

    return {
        "edades": edades,
        "percentiles": {k: v for k, v in percentiles.items()},
        "prob_ruina": prob_ruina,
        "esperanza_vida": esperanza_vida,
        "patrimonio_retiro_mediano": mediana_retiro,
        "proteccion_familiar": prot_familiar,
        "estabilidad": estabilidad,
        "gasto_medico_promedio": float(gasto_medico_bolsillo.mean()),
        "primas_mensuales": primas,
        "n_sims": n_sims,
    }


def empaquetar(perfil: dict, cobertura: dict):
    """Convierte los dicts en tuplas hashables para st.cache_data."""
    p = tuple(sorted((k, v) for k, v in perfil.items()))
    c = tuple(sorted((k, v) for k, v in cobertura.items()))
    return p, c


def correr(perfil: dict, cobertura: dict, n_sims: int = 10_000) -> dict:
    p, c = empaquetar(perfil, cobertura)
    return simular(p, c, n_sims=n_sims)


def a_dataframe(res: dict) -> pd.DataFrame:
    df = pd.DataFrame({"edad": res["edades"]})
    for p, serie in res["percentiles"].items():
        df[f"p{p}"] = serie
    return df
