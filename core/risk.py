"""Radar de Vulnerabilidad: diagnóstico por capas de datos del perfil.

Convierte el perfil en un nivel de protección 0–100 por dimensión de vida.
100 = blindado, 0 = totalmente expuesto.
"""

from core.simulator import RIESGO_ZONA

DIMENSIONES = ["Salud", "Vida / Familia", "Retiro", "Educación", "Patrimonio", "Liquidez"]

_PILAR_POR_DIM = {
    "Salud": "salud",
    "Vida / Familia": "vida",
    "Retiro": "retiro",
    "Educación": "educacion",
    "Patrimonio": "patrimonio",
    "Liquidez": "liquidez",
}


def radar_vulnerabilidad(perfil: dict, cobertura: dict, metas: list) -> dict:
    """Devuelve {dimension: score 0-100}."""
    edad = perfil["edad"]
    dep = perfil["dependientes"]
    ingreso = max(perfil["ingreso_mensual"], 1)
    gastos = perfil["gastos_mensuales"]
    ahorro = perfil["ahorro_actual"]
    zona_mult = RIESGO_ZONA.get(perfil["zona"], 1.0)

    scores = {}

    # Salud: exposición a gasto médico catastrófico
    s = 25.0
    if perfil["salud_general"] in ("Regular", "Delicada"):
        s -= 10
    if perfil["fumador"]:
        s -= 8
    if perfil["ejercicio"] in ("Regular", "Intenso"):
        s += 8
    if cobertura["gmm"]:
        s += 62
    scores["Salud"] = s

    # Vida / Familia: qué pasa con los dependientes si el titular falta
    if dep == 0:
        base = 60.0
    else:
        necesidad = gastos * 12 * 5 * (1 + 0.6 * dep)
        respaldo = ahorro + (cobertura["suma_vida"] if cobertura["vida"] else 0)
        base = min(respaldo / necesidad, 1.0) * 100
    scores["Vida / Familia"] = base

    # Retiro: brecha entre ahorro proyectado y necesidad
    anios_restantes = max(perfil["edad_retiro"] - edad, 1)
    necesidad_retiro = gastos * 12 * 20 * 0.85
    proyectado = ahorro * (1.05 ** anios_restantes) + perfil["ahorro_mensual"] * 12 * anios_restantes * 1.4
    if cobertura["retiro"]:
        proyectado += cobertura["aporte_retiro"] * 12 * anios_restantes * 1.8
    scores["Retiro"] = min(proyectado / max(necesidad_retiro, 1), 1.0) * 100

    # Educación: cobertura de metas educativas (si hay hijos)
    metas_edu = [m for m in metas if m.get("categoria") == "educacion"]
    if dep == 0 and not metas_edu:
        scores["Educación"] = 70.0
    elif metas_edu:
        fund = sum(1 for m in metas_edu if m.get("financiada"))
        scores["Educación"] = 25 + 65 * (fund / len(metas_edu))
    else:
        scores["Educación"] = 18.0

    # Patrimonio: exposición de bienes según zona
    s = 40.0 / zona_mult
    if cobertura["patrimonio"]:
        s += 55
    scores["Patrimonio"] = s

    # Liquidez: meses de gastos cubiertos por ahorro líquido
    meses = ahorro / max(gastos, 1)
    scores["Liquidez"] = min(meses / 6.0, 1.0) * 100

    return {k: round(min(max(v, 2), 99), 1) for k, v in scores.items()}


def score_blindaje(radar: dict) -> int:
    """Score global 0–1000 estilo 'score crediticio' de protección."""
    if not radar:
        return 0
    prom = sum(radar.values()) / len(radar)
    peor = min(radar.values())
    return int(round((0.7 * prom + 0.3 * peor) * 10))


def brechas_criticas(radar: dict, n: int = 3) -> list[tuple[str, float]]:
    return sorted(radar.items(), key=lambda kv: kv[1])[:n]


def pilar_de(dimension: str) -> str:
    return _PILAR_POR_DIM.get(dimension, "patrimonio")


def nivel_avatar(estabilidad: float) -> tuple[str, str, str]:
    """(emoji, etiqueta, color) del estado del gemelo digital."""
    if estabilidad >= 80:
        return "🛡️", "Blindado", "#22c55e"
    if estabilidad >= 60:
        return "😎", "Sólido", "#84cc16"
    if estabilidad >= 40:
        return "🙂", "En construcción", "#f59e0b"
    if estabilidad >= 25:
        return "😬", "Vulnerable", "#f97316"
    return "😰", "En riesgo", "#ef4444"
