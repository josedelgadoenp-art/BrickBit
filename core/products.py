"""Catálogo de soluciones GNP y motor de recomendación.

Nota: catálogo referencial para demostración. Nombres, coberturas y retornos
deben validarse contra el portafolio vigente de GNP antes de producción.
"""

CATALOGO = {
    "linea_azul": {
        "nombre": "GNP Línea Azul",
        "tipo": "Gastos Médicos Mayores",
        "pilar": "salud",
        "desc": "Cobertura médica amplia con red hospitalaria premium, deducible flexible y cobertura internacional opcional.",
        "icono": "🏥",
    },
    "vida_privilegio": {
        "nombre": "Privilegio Universal",
        "tipo": "Vida + Ahorro",
        "pilar": "vida",
        "desc": "Protección por fallecimiento con componente de ahorro flexible y liquidez parcial.",
        "icono": "🛡️",
    },
    "magnolia": {
        "nombre": "GNP Magnolia",
        "tipo": "Protección integral",
        "pilar": "vida",
        "desc": "Solución de protección pensada para el bienestar integral de la familia.",
        "icono": "🌸",
    },
    "proyecta": {
        "nombre": "Proyecta",
        "tipo": "Ahorro / Educación",
        "pilar": "educacion",
        "desc": "Plan de ahorro a mediano-largo plazo ideal para metas educativas, indexable a UDIs o dólares.",
        "icono": "🎓",
    },
    "consolida": {
        "nombre": "Consolida",
        "tipo": "Ahorro garantizado",
        "pilar": "patrimonio",
        "desc": "Ahorro con capital garantizado para metas a corto y mediano plazo.",
        "icono": "🏦",
    },
    "trasciende": {
        "nombre": "Trasciende",
        "tipo": "Retiro",
        "pilar": "retiro",
        "desc": "Plan personal de retiro (PPR) con beneficios fiscales (Art. 151 LISR) y gestión institucional.",
        "icono": "🌅",
    },
    "autos": {
        "nombre": "GNP Autos Amplia",
        "tipo": "Patrimonio",
        "pilar": "patrimonio",
        "desc": "Cobertura amplia de auto con asistencia total y app de siniestros en tiempo real.",
        "icono": "🚗",
    },
    "hogar": {
        "nombre": "Hogar Versátil",
        "tipo": "Patrimonio",
        "pilar": "patrimonio",
        "desc": "Protección del hogar y contenidos ante sismo, robo e imprevistos.",
        "icono": "🏠",
    },
}

# Mapeo pilar → producto principal recomendado
_POR_PILAR = {
    "salud": ["linea_azul"],
    "vida": ["vida_privilegio", "magnolia"],
    "educacion": ["proyecta"],
    "retiro": ["trasciende"],
    "patrimonio": ["consolida", "autos", "hogar"],
    "liquidez": ["consolida"],
}


def recomendar_por_pilar(pilar: str) -> list[dict]:
    return [CATALOGO[k] for k in _POR_PILAR.get(pilar, []) if k in CATALOGO]


def recomendar_para_meta(categoria: str, horizonte_anios: int) -> dict:
    """Elige el vehículo GNP adecuado según tipo de meta y horizonte."""
    if categoria == "retiro":
        return CATALOGO["trasciende"]
    if categoria == "educacion":
        return CATALOGO["proyecta"]
    if horizonte_anios <= 5:
        return CATALOGO["consolida"]
    return CATALOGO["proyecta"]
