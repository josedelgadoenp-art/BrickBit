"""Gemelo Familiar: fusiona dos gemelos digitales y simula el hogar completo."""

import plotly.graph_objects as go
import streamlit as st

from core import family, simulator, ui
from core.gamification import completar_mision
from core.state import cobertura, perfil


def render() -> None:
    p, c = perfil(), cobertura()
    pj = family.pareja()

    ui.hero("👨‍👩‍👧 Gemelo Familiar",
            "Dos vidas, un destino compartido. Fusiona tu gemelo con el de tu pareja y simula el hogar "
            "completo: qué pasa si falta cualquiera de los dos, y cuánto blindaje cierra cada brecha.")

    with st.expander("💞 Invitar a mi pareja (crear su gemelo)", expanded=not pj["activo"]):
        c1, c2, c3 = st.columns(3)
        with c1:
            pj["nombre"] = st.text_input("Nombre de tu pareja", pj["nombre"])
            pj["edad"] = st.slider("Edad de tu pareja", 18, 80, int(pj["edad"]))
        with c2:
            pj["ingreso_mensual"] = st.number_input("Su ingreso mensual (MXN)", 0.0, 1_000_000.0,
                                                    float(pj["ingreso_mensual"]), step=1_000.0)
            pj["gastos_aportados"] = st.number_input("Gasto adicional que agrega al hogar (MXN)", 0.0, 500_000.0,
                                                     float(pj["gastos_aportados"]), step=500.0)
        with c3:
            pj["fumador"] = st.toggle("¿Fuma?", pj["fumador"])
            pj["salud_general"] = st.select_slider("Su salud general",
                                                   ["Delicada", "Regular", "Buena", "Excelente"],
                                                   pj["salud_general"])
        if st.button("💞 Fusionar gemelos", type="primary"):
            pj["activo"] = True
            completar_mision("familiar")
            st.rerun()

    if not pj["activo"]:
        st.info("En producción, tu pareja recibe una invitación y construye su gemelo desde su teléfono; "
                "aquí puedes capturarlo directamente. Al fusionar, la decisión de protección se toma en "
                "pareja — donde realmente se toma.", icon="💡")
        return

    hogar = family.perfil_hogar(p, pj)
    with st.spinner("Simulando 10,000 futuros de tu hogar…"):
        res_hogar = simulator.correr(hogar, c)
        base = dict(c, gmm=False, vida=False, retiro=False, patrimonio=False)
        res_hogar_sin = simulator.correr(hogar, base)

    st.markdown(f"### 🏠 Hogar fusionado: **{hogar['nombre']}**")
    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Ingreso del hogar", ui.dinero(hogar["ingreso_mensual"]) + "/mes")
    k2.metric("Gasto del hogar", ui.dinero(hogar["gastos_mensuales"]) + "/mes")
    k3.metric("Estabilidad del hogar", f"{res_hogar['estabilidad']:.0f}/100",
              delta=f"{res_hogar['estabilidad'] - res_hogar_sin['estabilidad']:+.0f} vs. sin escudos")
    k4.metric("Prob. de quiebra del hogar", f"{res_hogar['prob_ruina']*100:.1f}%")

    st.plotly_chart(ui.grafico_abanico(res_hogar_sin,
                                       res_hogar if res_hogar["estabilidad"] != res_hogar_sin["estabilidad"] else None,
                                       hogar["edad_retiro"]),
                    width="stretch", key="fan_hogar")

    # --- análisis de supervivencia cruzado ---------------------------------------
    st.markdown("### 🕊️ Análisis de supervivencia cruzado")
    st.caption("La pregunta que nadie quiere hacerse, respondida con datos: ¿la economía del hogar sobrevive si falta uno de los dos?")

    analisis = family.analisis_supervivencia(p, pj, c)
    fig = go.Figure()
    nombres = [f"Si falta {a['quien']}" for a in analisis]
    fig.add_trace(go.Bar(name="Necesidad del hogar", x=nombres, y=[a["necesidad"] for a in analisis],
                         marker_color="rgba(239,68,68,.75)"))
    fig.add_trace(go.Bar(name="Recursos disponibles (ahorro + seguro)", x=nombres, y=[a["recursos"] for a in analisis],
                         marker_color=ui.NARANJA))
    fig.update_layout(template="plotly_dark", paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                      barmode="group", height=340, margin=dict(l=10, r=10, t=30, b=10),
                      yaxis_title="MXN", legend=dict(orientation="h", y=1.12, x=0))
    st.plotly_chart(fig, width="stretch", key="supervivencia")

    c1, c2 = st.columns(2)
    for col, a in zip((c1, c2), analisis):
        with col:
            if a["brecha"] > 0:
                st.error(
                    f"**Si falta {a['quien']}** (aporta {ui.dinero(a['aporta'])}/mes): el hogar queda cubierto al "
                    f"**{a['cobertura_pct']:.0f}%**. Brecha: **{ui.dinero(a['brecha'])}**. "
                    f"Suma asegurada sugerida: **{ui.dinero(a['suma_sugerida'])}** en un seguro de vida GNP a su nombre.",
                    icon="🔴",
                )
            else:
                st.success(
                    f"**Si falta {a['quien']}**: el hogar resiste — cobertura del {a['cobertura_pct']:.0f}%. "
                    "La estrategia actual protege este escenario.",
                    icon="🟢",
                )

    st.info(
        "💡 **Por qué esto es disruptivo:** el seguro de vida siempre se vendió individual, pero el riesgo "
        "es del hogar. Fusionar gemelos duplica los leads orgánicamente (tu pareja ya está dentro) y "
        "convierte la conversación incómoda en un tablero que los dos miran juntos.",
        icon="👨‍👩‍👧",
    )
