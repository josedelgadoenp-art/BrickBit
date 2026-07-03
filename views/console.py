"""Consola de Comando de Vida: seguro proactivo 24/7 + gamificación."""

import streamlit as st

from core import simulator, ui
from core.gamification import MISIONES, descuento_deducible_simulado, nivel_actual
from core.risk import brechas_criticas, pilar_de, radar_vulnerabilidad, score_blindaje
from core.products import recomendar_por_pilar
from core.state import cobertura, perfil

# Alertas proactivas de demostración (en producción: feeds en tiempo real)
_ALERTAS = {
    "CDMX / Zona Metropolitana": [
        ("🌧️", "Temporada de lluvias: +32% de percances viales en tu zona este mes. Revisa neumáticos y frenos — suma 15 Puntos Vitalidad al confirmarlo."),
        ("🏥", "La inflación médica acumulada este año va en 11.9%. Tu deducible congelado con GNP vale más cada mes."),
    ],
    "default": [
        ("🩺", "Recordatorio preventivo: tu chequeo anual bonifica 25 Puntos Vitalidad y detecta a tiempo el 80% de padecimientos costosos."),
        ("📈", "El costo de educación superior subió 8.2% este año. Tus metas educativas fueron re-indexadas automáticamente."),
    ],
}


def render() -> None:
    p, c = perfil(), cobertura()
    ss = st.session_state

    ui.hero("⚡ Consola de Comando de Vida",
            "El seguro que evita el siniestro, no solo el que lo paga. Tu asesor 24/7 vigila "
            "variables externas, te alerta antes del riesgo y premia tu prevención.")

    radar = radar_vulnerabilidad(p, c, ss["metas"])
    score = score_blindaje(radar)
    res = simulator.correr(p, c)

    k1, k2, k3, k4 = st.columns(4)
    nombre_nivel, icono_nivel, pts, sig = nivel_actual()
    k1.metric("Score de Blindaje", f"{score}/1000")
    k2.metric("Índice de Estabilidad Vital", f"{res['estabilidad']:.0f}/100")
    k3.metric("Puntos Vitalidad", f"{pts} pts", delta=f"Nivel {nombre_nivel} {icono_nivel}", delta_color="off")
    k4.metric("Reducción de deducible ganada", f"-{descuento_deducible_simulado()}%",
              delta="por tus hábitos preventivos", delta_color="off")

    col1, col2 = st.columns([1.3, 1], gap="large")

    with col1:
        st.markdown("#### 🛰️ Radar de Vulnerabilidad en vivo")
        st.plotly_chart(ui.radar_chart(radar), width="stretch", key="radar_console")

        st.markdown("#### 📡 Alertas proactivas de tu zona")
        for icono, texto in _ALERTAS.get(p["zona"], _ALERTAS["default"]):
            st.warning(f"{icono} {texto}")

    with col2:
        st.markdown("#### 🎮 Misiones de blindaje")
        for clave, (titulo, puntos, insignia) in MISIONES.items():
            hecha = clave in ss["misiones_completadas"]
            st.markdown(
                f"{'✅' if hecha else '⬜'} {insignia} {titulo} "
                f"<span style='color:#FFB27A'>+{puntos} pts</span>",
                unsafe_allow_html=True,
            )
        st.progress(min(pts / max(sig, 1), 1.0), text=f"Progreso al siguiente nivel ({pts}/{sig} pts)")

        st.markdown("#### 🎯 Acciones recomendadas por la IA")
        for dim, val in brechas_criticas(radar, 3):
            productos = recomendar_por_pilar(pilar_de(dim))
            if productos:
                pr = productos[0]
                st.markdown(
                    f"<div class='via-card'><h4>{pr['icono']} Refuerza «{dim}» ({val:.0f}%)</h4>"
                    f"<p><b>{pr['nombre']}</b> · {pr['tipo']}<br>{pr['desc']}</p></div>",
                    unsafe_allow_html=True,
                )
                st.write("")

    st.divider()
    st.markdown(
        "💡 **Así funciona el seguro proactivo:** en producción, esta consola se conecta a fuentes en "
        "tiempo real (clima, siniestralidad vial por zona, inflación médica, wearables opcionales) y "
        "convierte cada hábito preventivo en beneficios tangibles: deducibles menores, puntos y "
        "prioridad de servicio. GNP deja de ser un pagador de siniestros y se vuelve tu suscripción "
        "de bienestar integral."
    )
