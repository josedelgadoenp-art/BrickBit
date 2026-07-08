"""Auditoría de Vulnerabilidad: chat con VIA (agente conversacional de IA)."""

import streamlit as st

from core import advisor, ui
from core.gamification import completar_mision
from core.risk import radar_vulnerabilidad, score_blindaje
from core.state import cobertura, perfil


def _push(rol: str, texto: str) -> None:
    st.session_state["chat_historial"].append({"rol": rol, "texto": texto})


def render() -> None:
    ui.hero("🔍 Auditoría de Vulnerabilidad",
            "3 minutos de conversación con VIA. Sin formularios, sin letra pequeña: "
            "un diagnóstico multicapa de tus puntos ciegos financieros.")

    p = perfil()
    ss = st.session_state
    historial = ss["chat_historial"]

    if advisor.llm_disponible():
        st.caption("🧠 Modo IA aumentada activo (Anthropic conectado para consultas libres).")

    # Primera pregunta
    if not historial:
        _push("via", advisor.pregunta_de(0, p))

    for msg in historial:
        avatar = "🟠" if msg["rol"] == "via" else "🧑"
        with st.chat_message("assistant" if msg["rol"] == "via" else "user", avatar=avatar):
            st.markdown(msg["texto"])

    terminado = ss["chat_paso"] >= len(advisor.PASOS)

    placeholder = "Pregúntale lo que quieras a VIA…" if terminado else "Escribe tu respuesta…"
    texto = st.chat_input(placeholder)

    if texto:
        _push("usuario", texto)

        if not terminado:
            paso_key = advisor.PASOS[ss["chat_paso"]]
            ok, ack = advisor.procesar_respuesta(paso_key, texto, p)
            if ok:
                ss["chat_paso"] += 1
                if ack:
                    _push("via", ack)
                siguiente = advisor.pregunta_de(ss["chat_paso"], p)
                if siguiente:
                    _push("via", siguiente)
                else:
                    # Auditoría completa → diagnóstico
                    radar = radar_vulnerabilidad(p, cobertura(), ss["metas"])
                    score = score_blindaje(radar)
                    ss["auditoria_completa"] = True
                    completar_mision("auditoria")
                    completar_mision("perfil")
                    _push("via", advisor.diagnostico_final(p, radar, score))
            else:
                _push("via", ack)
        else:
            radar = radar_vulnerabilidad(p, cobertura(), ss["metas"])
            _push("via", advisor.responder_libre(texto, p, radar))
        st.rerun()

    # Panel de resultados post-auditoría
    if ss["auditoria_completa"]:
        st.divider()
        radar = radar_vulnerabilidad(p, cobertura(), ss["metas"])
        score = score_blindaje(radar)
        c1, c2 = st.columns([1.4, 1])
        with c1:
            st.plotly_chart(ui.radar_chart(radar), width="stretch", key="radar_audit")
        with c2:
            st.markdown(
                f'<div class="via-kpi-label">Score de Blindaje</div>'
                f'<div class="via-kpi" style="font-size:3.4rem">{score}<span style="font-size:1.2rem;color:#9AA4B8"> /1000</span></div>',
                unsafe_allow_html=True,
            )
            st.progress(min(score / 1000, 1.0))
            st.write("")
            b1, b2 = st.columns(2)
            with b1:
                if st.button("🧬 Ver en mi Gemelo", width="stretch", type="primary"):
                    ss["_nav"] = "twin"
                    st.rerun()
            with b2:
                if st.button("🎯 Diseñar metas", width="stretch"):
                    ss["_nav"] = "goals"
                    st.rerun()

        if st.button("🔄 Reiniciar auditoría"):
            ss["chat_historial"] = []
            ss["chat_paso"] = 0
            ss["auditoria_completa"] = False
            st.rerun()
