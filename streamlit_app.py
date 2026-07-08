"""GNP LifeOS — El Sistema Operativo de tu Vida.

Plataforma disruptiva de venta consultiva de seguros GNP que unifica:
  1. Gemelo Digital financiero y de longevidad (simulador Monte Carlo de vida)
  2. VIA: agente conversacional de IA para la Auditoría de Vulnerabilidad
  3. Marketplace de Metas de Vida (protección + ahorro orientados a sueños)
  4. Consola de Comando de Vida: seguro proactivo y gamificado
  5. Handoff inteligente al copiloto humano (asesor GNP)
"""

import streamlit as st

st.set_page_config(
    page_title="GNP LifeOS · Simulador de Destino",
    page_icon="🧬",
    layout="wide",
    initial_sidebar_state="expanded",
)

from core.state import init_state          # noqa: E402
from core.ui import aplicar_estilo         # noqa: E402
from core.gamification import nivel_actual  # noqa: E402
from views import audit, console, copilot, family, goals, handoff, home, twin  # noqa: E402

init_state()
aplicar_estilo()

_PAGES = {
    "home": st.Page(home.render, title="Inicio", icon="🏠", url_path="inicio", default=True),
    "audit": st.Page(audit.render, title="Auditoría con VIA", icon="🔍", url_path="auditoria"),
    "twin": st.Page(twin.render, title="Gemelo Digital", icon="🧬", url_path="gemelo"),
    "family": st.Page(family.render, title="Gemelo Familiar", icon="👨‍👩‍👧", url_path="familia"),
    "goals": st.Page(goals.render, title="Metas de Vida", icon="🎯", url_path="metas"),
    "console": st.Page(console.render, title="Consola de Vida", icon="⚡", url_path="consola"),
    "handoff": st.Page(handoff.render, title="Asesor Humano", icon="🤝", url_path="asesor"),
    "copilot": st.Page(copilot.render, title="Modo Asesor (interno)", icon="🧑‍💼", url_path="copiloto"),
}

nav = st.navigation(
    {
        "Tu experiencia": [_PAGES["home"], _PAGES["audit"], _PAGES["twin"], _PAGES["family"], _PAGES["goals"]],
        "Ecosistema vivo": [_PAGES["console"]],
        "Cierre": [_PAGES["handoff"], _PAGES["copilot"]],
    },
    position="sidebar",
)

# Navegación programática desde botones internos
destino = st.session_state.pop("_nav", None)
if destino and destino in _PAGES:
    st.switch_page(_PAGES[destino])

with st.sidebar:
    st.markdown("### 🧬 GNP LifeOS")
    nombre, icono, pts, _ = nivel_actual()
    st.markdown(f"**{icono} {nombre}** · {pts} Puntos Vitalidad")
    p = st.session_state["perfil"]
    if p["nombre"]:
        st.caption(f"Gemelo activo: **{p['nombre']}**, {p['edad']} años · {p['zona']}")
    else:
        st.caption("Aún no construyes tu Gemelo Digital.")
    st.divider()
    st.caption(
        "Demo conceptual — simulaciones actuariales ilustrativas. "
        "No constituye cotización ni oferta de GNP Seguros."
    )

nav.run()
