"""Landing: la promesa de la plataforma y las 3 puertas de entrada."""

import streamlit as st

from core import ui
from core.gamification import nivel_actual


def render() -> None:
    ui.hero(
        "GNP LifeOS · El Sistema Operativo de tu Vida",
        "No vendemos pólizas. Construimos tu Gemelo Digital, simulamos 10,000 versiones de tu futuro "
        "y diseñamos el blindaje exacto para que tus metas se cumplan — pase lo que pase.",
    )

    st.markdown(
        '<span class="via-chip">🧬 Gemelo Digital</span>'
        '<span class="via-chip">🤖 IA Conversacional</span>'
        '<span class="via-chip">🎯 Metas de Vida</span>'
        '<span class="via-chip">⚡ Seguro Proactivo</span>'
        '<span class="via-chip">🎮 Gamificado</span>',
        unsafe_allow_html=True,
    )
    st.write("")

    c1, c2, c3 = st.columns(3)
    with c1:
        ui.tarjeta(
            "Auditoría de Vulnerabilidad",
            "Conversa 3 minutos con VIA, nuestra estratega de IA. Detecta tus puntos ciegos "
            "financieros cruzando siniestralidad regional, inflación médica y curvas de longevidad.",
            "🔍",
        )
        st.write("")
        if st.button("Iniciar auditoría con VIA →", width="stretch", type="primary"):
            st.session_state["_nav"] = "audit"
            st.rerun()
    with c2:
        ui.tarjeta(
            "Tu Gemelo Digital",
            "Un simulador Monte Carlo corre 10,000 escenarios de tu vida: patrimonio, salud y "
            "longevidad. Activa escudos GNP y mira tu futuro estabilizarse en tiempo real.",
            "🧬",
        )
        st.write("")
        if st.button("Construir mi gemelo →", width="stretch"):
            st.session_state["_nav"] = "twin"
            st.rerun()
    with c3:
        ui.tarjeta(
            "Marketplace de Metas",
            "Arrastra tus sueños a tu línea de vida: universidad, retiro a los 55, casa propia. "
            "La IA calcula el costo real indexado a inflación y arma la arquitectura financiera.",
            "🎯",
        )
        st.write("")
        if st.button("Diseñar mis metas →", width="stretch"):
            st.session_state["_nav"] = "goals"
            st.rerun()

    st.write("")
    nombre, icono, pts, _ = nivel_actual()
    st.info(
        f"{icono} Tu progreso: **{pts} Puntos Vitalidad** · Nivel **{nombre}**. "
        "Cada acción de planeación suma puntos que, como cliente GNP, se convertirían en "
        "reducción de deducibles y beneficios de renovación.",
        icon="🎮",
    )
    st.caption(
        "Demo conceptual. Cifras, primas y productos son ilustrativos y no constituyen una cotización "
        "oficial de GNP Seguros."
    )
