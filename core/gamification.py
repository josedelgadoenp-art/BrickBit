"""Capa de gamificación: Puntos Vitalidad, niveles, misiones e insignias.

Los puntos simulan el programa de bienestar: completar acciones de prevención
y planeación bonifica puntos que (en producción) reducirían deducibles o
darían beneficios en la renovación.
"""

import streamlit as st

NIVELES = [
    (0, "Explorador", "🧭"),
    (150, "Estratega", "♟️"),
    (400, "Guardián", "🛡️"),
    (800, "Arquitecto de Destino", "🏛️"),
]

MISIONES = {
    "perfil": ("Construye tu Gemelo Digital", 100, "🧬"),
    "simulacion": ("Corre tu primera simulación de 10,000 vidas", 80, "🎲"),
    "auditoria": ("Completa tu Auditoría de Vulnerabilidad con VIA", 120, "🔍"),
    "meta_1": ("Define tu primera Meta de Vida", 60, "🎯"),
    "meta_3": ("Arquitectura completa: 3 metas en tu línea de vida", 90, "🗺️"),
    "blindaje": ("Activa tu primer escudo GNP en el simulador", 70, "⚡"),
    "asesor": ("Conecta con tu copiloto humano GNP", 100, "🤝"),
}


def completar_mision(clave: str) -> bool:
    """Marca una misión como completada. True si es la primera vez."""
    ss = st.session_state
    if clave in ss["misiones_completadas"] or clave not in MISIONES:
        return False
    ss["misiones_completadas"].add(clave)
    ss["puntos"] += MISIONES[clave][1]
    ss["insignias"].add(MISIONES[clave][2])
    return True


def nivel_actual() -> tuple[str, str, int, int]:
    """(nombre, icono, puntos_actuales, puntos_siguiente_nivel)."""
    pts = st.session_state["puntos"]
    nombre, icono = NIVELES[0][1], NIVELES[0][2]
    siguiente = NIVELES[-1][0]
    for i, (umbral, n, ic) in enumerate(NIVELES):
        if pts >= umbral:
            nombre, icono = n, ic
            siguiente = NIVELES[i + 1][0] if i + 1 < len(NIVELES) else umbral
    return nombre, icono, pts, siguiente


def descuento_deducible_simulado() -> int:
    """% de reducción de deducible que los puntos otorgarían (demo)."""
    return min(st.session_state["puntos"] // 100 * 2, 20)
