"""API de Momentos de Vida: el gemelo se re-simula cuando tu vida cambia.

En producción, disparadores externos (con consentimiento: buró, nómina,
CURP, ubicación) detectan momentos de vida y re-simulan proactivamente.
Aquí el usuario los declara y ve el impacto inmediato en su vulnerabilidad.
"""

from __future__ import annotations

import datetime

import streamlit as st

MOMENTOS = {
    "bebe": {
        "nombre": "Llegó un bebé",
        "icono": "👶",
        "desc": "Un nuevo dependiente: +gastos, +necesidad de protección y una meta educativa nueva.",
        "delta": {"dependientes": +1, "gastos_mensuales": +4_500},
        "alerta": "Tu necesidad de suma asegurada de vida subió ~35%. Considera abrir un Proyecta educativo hoy: cada año de espera encarece la meta 8.2%.",
    },
    "matrimonio": {
        "nombre": "Me caso / vivo en pareja",
        "icono": "💍",
        "desc": "Dos vidas, un hogar: es momento de fusionar gemelos digitales.",
        "delta": {"gastos_mensuales": +3_000},
        "alerta": "Activa el 👨‍👩‍👧 Gemelo Familiar para simular el hogar completo y el análisis de supervivencia cruzado.",
    },
    "ascenso": {
        "nombre": "Nuevo trabajo / ascenso",
        "icono": "📈",
        "desc": "Tu ingreso sube: tu capacidad de blindaje y de sueños también.",
        "delta_pct": {"ingreso_mensual": 1.22},
        "alerta": "Regla de oro: destina la mitad del aumento a tus metas antes de que el gasto se lo coma (lifestyle creep).",
    },
    "recorte": {
        "nombre": "Recorte / ingresos a la baja",
        "icono": "📉",
        "desc": "Ingreso golpeado: prioriza liquidez y protege lo esencial.",
        "delta_pct": {"ingreso_mensual": 0.70},
        "alerta": "Tu fondo de emergencia es ahora tu primera línea. No canceles tu protección: rescatar un seguro y recontratarlo después cuesta más (edad + salud).",
    },
    "mudanza": {
        "nombre": "Me mudo de ciudad",
        "icono": "📦",
        "desc": "Nueva zona = nueva siniestralidad, nuevos costos médicos.",
        "delta": {},
        "alerta": "Recalibré la siniestralidad de tu nueva zona. Revisa tu radar de Patrimonio.",
        "especial": "zona",
    },
    "universidad": {
        "nombre": "Mi hijo entra a la universidad",
        "icono": "🎓",
        "desc": "La meta educativa se vuelve gasto presente.",
        "delta": {"gastos_mensuales": +8_000},
        "alerta": "Si esta meta estaba financiada con Proyecta, el plan la absorbe sin tocar tu flujo. Si no… ahora ves por qué existía.",
    },
}


def aplicar_momento(key: str, perfil: dict, zona_nueva: str | None = None) -> dict:
    """Muta el perfil según el momento y registra el evento. Devuelve el momento."""
    m = MOMENTOS[key]
    for campo, delta in m.get("delta", {}).items():
        perfil[campo] = max(perfil[campo] + delta, 0)
    for campo, factor in m.get("delta_pct", {}).items():
        perfil[campo] = max(perfil[campo] * factor, 0)
    if m.get("especial") == "zona" and zona_nueva:
        perfil["zona"] = zona_nueva
    feed = st.session_state.setdefault("momentos_feed", [])
    feed.insert(0, {
        "ts": datetime.datetime.now().strftime("%d %b %Y · %H:%M"),
        "icono": m["icono"],
        "nombre": m["nombre"],
        "alerta": m["alerta"],
    })
    return m
