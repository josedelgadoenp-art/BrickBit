"""BrickBit — Plataforma de prospección predictiva (Seguros GNP + Inmobiliario)."""

import streamlit as st

st.set_page_config(
    page_title="BrickBit · Prospección Predictiva",
    page_icon="🧱",
    layout="wide",
)

paginas = [
    st.Page("app_pages/inicio.py", title="Panel de control", icon="📊", default=True),
    st.Page("app_pages/radar.py", title="Radar de mercado (gratis)", icon="🗺️"),
    st.Page("app_pages/oraculo.py", title="El Oráculo · Señales", icon="🔮"),
    st.Page("app_pages/muestreo.py", title="Muestreo Inverso · Outreach", icon="✉️"),
    st.Page("app_pages/pipeline.py", title="Pipeline SDR", icon="🤖"),
    st.Page("app_pages/modelo.py", title="Modelo de negocio", icon="💰"),
]

nav = st.navigation(paginas)

with st.sidebar:
    st.markdown("### 🧱 BrickBit")
    st.caption(
        "Motor de prospección: la mayor cantidad de prospectos calificados "
        "en el menor tiempo posible.\n\n"
        "**Verticales:** Seguros GNP · Inmobiliario"
    )
    st.divider()
    st.caption("⚠️ Datos demo sintéticos. Conecta tus fuentes reales en producción.")

nav.run()
