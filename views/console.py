"""Consola de Comando de Vida: seguro proactivo, Prima Viva y Momentos de Vida."""

import plotly.graph_objects as go
import streamlit as st

from core import moments, pulse, simulator, ui
from core.gamification import MISIONES, completar_mision, descuento_deducible_simulado, nivel_actual
from core.products import recomendar_por_pilar
from core.risk import brechas_criticas, pilar_de, radar_vulnerabilidad, score_blindaje
from core.state import ZONAS, cobertura, perfil

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


def _tab_radar(p: dict, radar: dict, ss) -> None:
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
        _, _, pts, sig = nivel_actual()
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


def _tab_prima_viva(p: dict, c: dict) -> None:
    st.markdown(
        "#### 💓 Prima Viva: tu seguro tiene pulso\n"
        "Tu prima deja de ser un precio fijo: **baja mes a mes con hábitos verificados** "
        "(wearables, telemática de manejo, prevención). Aquí simulas tus datos; en producción "
        "se conectan Apple Health / Google Fit y la telemática de tu auto."
    )
    h = pulse.habitos()
    col1, col2 = st.columns([1, 1.4], gap="large")

    with col1:
        st.markdown("##### 📲 Tus señales verificadas")
        h["pasos"] = st.slider("Pasos diarios promedio", 0, 20_000, int(h["pasos"]), step=500)
        h["sueno"] = st.slider("Horas de sueño promedio", 4.0, 10.0, float(h["sueno"]), step=0.5)
        h["manejo_brusco"] = st.slider("Manejo brusco (telemática, % de eventos)", 0, 100, int(h["manejo_brusco"]))
        h["chequeo_anual"] = st.toggle("Chequeo médico anual verificado", h["chequeo_anual"])
        h["sin_tabaco"] = st.toggle("Racha sin tabaco verificada", h["sin_tabaco"])
        h["racha_semanas"] = st.slider("Semanas cumpliendo tus metas de hábitos", 0, 52, int(h["racha_semanas"]))

    score = pulse.score_habitos(h)
    prima_base = pulse.prima_base_paquete(p, c)
    desc = pulse.descuento_actual(score, h["racha_semanas"])
    prima_hoy = prima_base * (1 - desc)

    if desc > 0.02:
        completar_mision("prima_viva")

    with col2:
        k1, k2, k3 = st.columns(3)
        k1.metric("Score de Vitalidad verificada", f"{score:.0f}/100")
        k2.metric("Descuento vivo", f"-{desc*100:.1f}%", delta=f"tope -{pulse.DESCUENTO_MAX*100:.0f}%", delta_color="off")
        k3.metric("Prima este mes", f"${prima_hoy:,.0f}", delta=f"-${prima_base - prima_hoy:,.0f} vs. prima fija",
                  delta_color="inverse" if prima_hoy < prima_base else "off")

        meses, primas = pulse.proyeccion_12_meses(prima_base, score, h["racha_semanas"])
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=meses, y=[prima_base] * len(meses), name="Seguro tradicional (fijo)",
                                 line=dict(color="#8B93A7", dash="dash")))
        fig.add_trace(go.Scatter(x=meses, y=primas, name="Tu Prima Viva", fill="tonexty",
                                 fillcolor="rgba(255,105,0,.15)", line=dict(color=ui.NARANJA, width=3)))
        fig.update_layout(template="plotly_dark", paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                          height=300, margin=dict(l=10, r=10, t=40, b=10),
                          title="Si mantienes tus hábitos 12 meses…",
                          xaxis_title="Meses", yaxis_title="Prima mensual (MXN)",
                          legend=dict(orientation="h", y=1.15, x=0))
        st.plotly_chart(fig, width="stretch", key="prima_viva_chart")
        ahorro_anual = sum(prima_base - x for x in primas[1:])
        st.success(
            f"💰 Manteniendo estos hábitos, en 12 meses habrás dejado de pagar **${ahorro_anual:,.0f}** "
            f"y tu cuerpo lo agradece gratis. El seguro que te premia por vivir bien.",
            icon="💓",
        )


def _tab_momentos(p: dict, c: dict, ss) -> None:
    st.markdown(
        "#### 🌊 Momentos de Vida: tu gemelo nunca se queda viejo\n"
        "La vida cambia y tu protección debe cambiar sola. Declara un momento (en producción se "
        "detectan con disparadores externos y tu consentimiento) y mira tu vulnerabilidad re-simularse."
    )

    radar_actual = radar_vulnerabilidad(p, c, ss["metas"])
    res_actual = simulator.correr(p, c)

    col1, col2 = st.columns([1, 1.5], gap="large")
    with col1:
        key = st.selectbox("¿Qué pasó en tu vida?", list(moments.MOMENTOS.keys()),
                           format_func=lambda k: f"{moments.MOMENTOS[k]['icono']} {moments.MOMENTOS[k]['nombre']}")
        m = moments.MOMENTOS[key]
        st.caption(m["desc"])
        zona_nueva = None
        if m.get("especial") == "zona":
            zona_nueva = st.selectbox("¿A dónde te mudas?", ZONAS, index=ZONAS.index(p["zona"]))
        if st.button("🌊 Registrar momento y re-simular", type="primary", width="stretch"):
            # instantánea del "antes", previa a mutar el perfil
            ss["_impacto_antes"] = {
                "radar": radar_actual,
                "estabilidad": res_actual["estabilidad"],
                "score": score_blindaje(radar_actual),
            }
            moments.aplicar_momento(key, p, zona_nueva)
            completar_mision("momento")
            st.rerun()

        if ss.get("momentos_feed"):
            st.markdown("##### 📜 Tu historia reciente")
            for ev in ss["momentos_feed"][:5]:
                st.markdown(f"**{ev['icono']} {ev['nombre']}** · <span style='color:#9AA4B8'>{ev['ts']}</span><br>"
                            f"<span style='color:#C9D2E3;font-size:.9rem'>{ev['alerta']}</span>",
                            unsafe_allow_html=True)
                st.write("")

    with col2:
        antes = ss.get("_impacto_antes")
        if antes:
            st.markdown("##### ⚡ Impacto del momento en tu blindaje")
            st.plotly_chart(ui.radar_chart(radar_actual, antes["radar"]), width="stretch", key="radar_momento")
            k1, k2 = st.columns(2)
            k1.metric("Índice de Estabilidad", f"{res_actual['estabilidad']:.0f}/100",
                      delta=f"{res_actual['estabilidad'] - antes['estabilidad']:+.0f} pts")
            k2.metric("Score de Blindaje", f"{score_blindaje(radar_actual)}/1000",
                      delta=f"{score_blindaje(radar_actual) - antes['score']:+d} pts")
        else:
            st.plotly_chart(ui.radar_chart(radar_actual), width="stretch", key="radar_momentos_base")
            st.caption("Registra un momento a la izquierda para ver el antes/después de tu radar.")


def render() -> None:
    p, c = perfil(), cobertura()
    ss = st.session_state

    ui.hero("⚡ Consola de Comando de Vida",
            "El seguro que evita el siniestro, no solo el que lo paga. Tu asesor 24/7 vigila "
            "variables externas, premia tu prevención y re-simula tu vida cuando cambia.")

    radar = radar_vulnerabilidad(p, c, ss["metas"])
    score = score_blindaje(radar)
    res = simulator.correr(p, c)

    k1, k2, k3, k4 = st.columns(4)
    nombre_nivel, icono_nivel, pts, _ = nivel_actual()
    k1.metric("Score de Blindaje", f"{score}/1000")
    k2.metric("Índice de Estabilidad Vital", f"{res['estabilidad']:.0f}/100")
    k3.metric("Puntos Vitalidad", f"{pts} pts", delta=f"Nivel {nombre_nivel} {icono_nivel}", delta_color="off")
    k4.metric("Reducción de deducible ganada", f"-{descuento_deducible_simulado()}%",
              delta="por tus hábitos preventivos", delta_color="off")

    tab1, tab2, tab3 = st.tabs(["🛰️ Radar y misiones", "💓 Prima Viva", "🌊 Momentos de Vida"])
    with tab1:
        _tab_radar(p, radar, ss)
    with tab2:
        _tab_prima_viva(p, c)
    with tab3:
        _tab_momentos(p, c, ss)

    st.divider()
    st.markdown(
        "💡 **Así funciona el seguro proactivo:** esta consola se conecta (en producción) a fuentes en "
        "tiempo real — clima, siniestralidad vial, inflación médica, wearables y telemática con tu "
        "consentimiento — y convierte cada hábito preventivo en dinero: primas y deducibles que bajan. "
        "GNP deja de ser un pagador de siniestros y se vuelve tu suscripción de bienestar integral."
    )
