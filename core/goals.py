"""Marketplace de Metas de Vida: costos reales indexados a inflación futura
y arquitectura financiera automática (protección + ahorro GNP)."""

from __future__ import annotations

from core.products import recomendar_para_meta

INFLACION = {
    "educacion": 0.082,     # inflación educativa histórica MX
    "educacion_ext": 0.085, # + efecto cambiario se agrega aparte
    "retiro": 0.045,
    "vivienda": 0.065,
    "general": 0.045,
    "salud": 0.115,
}

# Plantillas de sueños: costo base a valor presente (MXN, demo)
PLANTILLAS = {
    "uni_mx": {
        "nombre": "Universidad privada en México",
        "icono": "🎓",
        "categoria": "educacion",
        "costo_base": 1_400_000,
        "inflacion": INFLACION["educacion"],
        "desc": "Carrera completa en universidad privada top (colegiaturas + materiales).",
    },
    "uni_ext": {
        "nombre": "Universidad en el extranjero",
        "icono": "✈️🎓",
        "categoria": "educacion",
        "costo_base": 4_800_000,
        "inflacion": INFLACION["educacion_ext"] + 0.03,  # + depreciación FX estimada
        "desc": "4 años de universidad en el extranjero (colegiatura + manutención).",
    },
    "retiro_55": {
        "nombre": "Retiro anticipado a los 55",
        "icono": "🌅",
        "categoria": "retiro",
        "costo_base": 0,  # se calcula del perfil
        "inflacion": INFLACION["retiro"],
        "desc": "Libertad financiera 10 años antes: viajar sin depender de nadie.",
    },
    "casa": {
        "nombre": "Casa propia",
        "icono": "🏡",
        "categoria": "vivienda",
        "costo_base": 3_200_000,
        "inflacion": INFLACION["vivienda"],
        "desc": "Enganche fuerte + escrituras de una vivienda media-alta.",
    },
    "negocio": {
        "nombre": "Emprender un negocio",
        "icono": "🚀",
        "categoria": "general",
        "costo_base": 900_000,
        "inflacion": INFLACION["general"],
        "desc": "Capital semilla para arrancar tu propio negocio sin deuda.",
    },
    "sabatico": {
        "nombre": "Año sabático viajando",
        "icono": "🌍",
        "categoria": "general",
        "costo_base": 550_000,
        "inflacion": INFLACION["general"] + 0.02,
        "desc": "12 meses recorriendo el mundo sin tocar tu patrimonio.",
    },
    "legado": {
        "nombre": "Legado para mi familia",
        "icono": "💞",
        "categoria": "vida",
        "costo_base": 2_000_000,
        "inflacion": INFLACION["general"],
        "desc": "Un patrimonio garantizado para los tuyos, pase lo que pase.",
    },
}


def costo_futuro(meta: dict, perfil: dict) -> float:
    """Costo de la meta indexado a inflación al año objetivo."""
    anios = max(meta["anio_objetivo"] - _anio_actual(), 0)
    base = meta["costo_base"]
    if meta["categoria"] == "retiro" and base == 0:
        # necesidad: 85% del gasto actual x 25 años a partir de esa edad
        base = perfil["gastos_mensuales"] * 12 * 25 * 0.85
    return base * (1 + meta["inflacion"]) ** anios


def aporte_mensual_requerido(costo_fut: float, anios: int, retorno_anual: float = 0.085) -> float:
    """PMT para acumular costo_fut en `anios` con retorno del plan GNP."""
    n = max(anios, 1) * 12
    r = retorno_anual / 12
    if r <= 0:
        return costo_fut / n
    return costo_fut * r / ((1 + r) ** n - 1)


def crear_meta(plantilla_key: str, anio_objetivo: int, perfil: dict) -> dict:
    p = PLANTILLAS[plantilla_key]
    meta = {
        "key": plantilla_key,
        "nombre": p["nombre"],
        "icono": p["icono"],
        "categoria": p["categoria"],
        "costo_base": p["costo_base"],
        "inflacion": p["inflacion"],
        "desc": p["desc"],
        "anio_objetivo": anio_objetivo,
        "financiada": False,
    }
    anios = max(anio_objetivo - _anio_actual(), 1)
    cf = costo_futuro(meta, perfil)
    meta["costo_futuro"] = cf
    meta["aporte_mensual"] = aporte_mensual_requerido(cf, anios)
    meta["producto"] = recomendar_para_meta(p["categoria"], anios)
    return meta


def _anio_actual() -> int:
    import datetime
    return datetime.date.today().year


def resumen_plan(metas: list, perfil: dict) -> dict:
    total_futuro = sum(m["costo_futuro"] for m in metas)
    total_mensual = sum(m["aporte_mensual"] for m in metas)
    capacidad = max(perfil["ingreso_mensual"] - perfil["gastos_mensuales"], 0)
    return {
        "total_futuro": total_futuro,
        "total_mensual": total_mensual,
        "capacidad": capacidad,
        "viable": total_mensual <= capacidad,
        "pct_capacidad": (total_mensual / capacidad * 100) if capacidad > 0 else float("inf"),
    }
