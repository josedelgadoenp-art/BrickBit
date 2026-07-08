"""Estado global de la sesión: perfil del usuario, cobertura, metas y progreso."""

import streamlit as st

DEFAULT_PROFILE = {
    "nombre": "",
    "edad": 32,
    "genero": "No especificado",
    "zona": "CDMX / Zona Metropolitana",
    "dependientes": 0,
    "ingreso_mensual": 35_000.0,
    "gastos_mensuales": 24_000.0,
    "ahorro_actual": 120_000.0,
    "ahorro_mensual": 3_000.0,
    "fumador": False,
    "ejercicio": "Ocasional",       # Nunca / Ocasional / Regular / Intenso
    "salud_general": "Buena",       # Excelente / Buena / Regular / Delicada
    "edad_retiro": 65,
    "prioridad": "Equilibrio",      # Familia / Patrimonio / Retiro / Salud / Equilibrio
    "perfil_completo": False,
}

# Cobertura activable en el Gemelo Digital (portafolio GNP simulado).
DEFAULT_COVERAGE = {
    "gmm": False,          # Gastos Médicos Mayores
    "vida": False,         # Seguro de Vida
    "retiro": False,       # Plan de retiro / ahorro
    "patrimonio": False,   # Auto + Hogar / daños
    "suma_vida": 2_000_000.0,
    "aporte_retiro": 3_000.0,
}

ZONAS = [
    "CDMX / Zona Metropolitana",
    "Guadalajara",
    "Monterrey",
    "Bajío (Querétaro, León, SLP)",
    "Sureste (Mérida, Cancún)",
    "Norte (Chihuahua, Hermosillo)",
    "Otra ciudad media",
    "Zona rural",
]


def init_state() -> None:
    ss = st.session_state
    ss.setdefault("perfil", dict(DEFAULT_PROFILE))
    ss.setdefault("cobertura", dict(DEFAULT_COVERAGE))
    ss.setdefault("metas", [])                 # lista de dicts (ver core/goals.py)
    ss.setdefault("chat_historial", [])        # historial del chat de auditoría
    ss.setdefault("chat_paso", 0)              # paso del flujo conversacional
    ss.setdefault("auditoria_completa", False)
    ss.setdefault("puntos", 0)
    ss.setdefault("misiones_completadas", set())
    ss.setdefault("insignias", set())
    ss.setdefault("lead_enviado", False)


def perfil() -> dict:
    return st.session_state["perfil"]


def cobertura() -> dict:
    return st.session_state["cobertura"]
