"""Gemelo Digital: simulación Monte Carlo con escudos GNP + Modo Espejo."""

import streamlit as st

from core import simulator, ui
from core.gamification import completar_mision
from core.risk import nivel_avatar
from core.state import ZONAS, cobertura, perfil


def _formulario_perfil(p: dict) -> None:
    with st.expander("🧬 Calibrar mi Gemelo Digital", expanded=not p["perfil_completo"]):
        c1, c2, c3 = st.columns(3)
        with c1:
            p["nombre"] = st.text_input("Tu nombre", p["nombre"] or "")
            p["edad"] = st.slider("Edad", 18, 80, int(p["edad"]))
            p["dependientes"] = st.slider("Dependientes económicos", 0, 8, int(p["dependientes"]))
            p["zona"] = st.selectbox("Zona donde vives", ZONAS, index=ZONAS.index(p["zona"]))
        with c2:
            p["ingreso_mensual"] = st.number_input("Ingreso mensual (MXN)", 0.0, 1_000_000.0,
                                                   float(p["ingreso_mensual"]), step=1_000.0)
            p["gastos_mensuales"] = st.number_input("Gastos mensuales (MXN)", 0.0, 1_000_000.0,
                                                    float(p["gastos_mensuales"]), step=1_000.0)
            p["ahorro_actual"] = st.number_input("Ahorro/inversión actual (MXN)", 0.0, 100_000_000.0,
                                                 float(p["ahorro_actual"]), step=10_000.0)
            p["edad_retiro"] = st.slider("Edad de retiro deseada", max(p["edad"] + 1, 40), 75,
                                         int(max(p["edad_retiro"], p["edad"] + 1)))
        with c3:
            p["fumador"] = st.toggle("Fumador", p["fumador"])
            p["ejercicio"] = st.select_slider("Ejercicio", ["Nunca", "Ocasional", "Regular", "Intenso"],
                                              p["ejercicio"])
            p["salud_general"] = st.select_slider("Salud general",
                                                  ["Delicada", "Regular", "Buena", "Excelente"],
                                                  p["salud_general"])
            p["ahorro_mensual"] = st.number_input("Ahorro mensual propio (MXN)", 0.0, 500_000.0,
                                                  float(p["ahorro_mensual"]), step=500.0)
        p["perfil_completo"] = True


def _panel_escudos(c: dict) -> None:
    st.markdown("#### ⚡ Escudos GNP")
    st.caption("Actívalos y observa cómo se estabiliza tu futuro.")
    c["gmm"] = st.toggle("🏥 Gastos Médicos (Línea Azul)", c["gmm"])
    c["vida"] = st.toggle("🛡️ Vida (Privilegio / Magnolia)", c["vida"])
    if c["vida"]:
        c["suma_vida"] = st.slider("Suma asegurada de vida (MXN)", 500_000, 10_000_000,
                                   int(c["suma_vida"]), step=250_000, format="$%d")
    c["retiro"] = st.toggle("🌅 Plan de Retiro (Trasciende)", c["retiro"])
    if c["retiro"]:
        c["aporte_retiro"] = st.slider("Aporte mensual al plan (MXN)", 500, 50_000,
                                       int(c["aporte_retiro"]), step=500, format="$%d")
    c["patrimonio"] = st.toggle("🚗🏠 Patrimonio (Autos + Hogar)", c["patrimonio"])


def _tab_simulacion(p: dict, c: dict) -> tuple[dict, dict | None]:
    col_izq, col_der = st.columns([1, 2.6], gap="large")

    with col_izq:
        _panel_escudos(c)
        hay_escudo = any(c[k] for k in ("gmm", "vida", "retiro", "patrimonio"))
        if hay_escudo:
            completar_mision("blindaje")

    base = dict(c, gmm=False, vida=False, retiro=False, patrimonio=False)
    with st.spinner("Simulando 10,000 versiones de tu futuro…"):
        res_sin = simulator.correr(p, base)
        res_con = simulator.correr(p, c) if hay_escudo else None
    completar_mision("simulacion")
    res_activo = res_con or res_sin

    with col_der:
        emoji, etiqueta, color = nivel_avatar(res_activo["estabilidad"])
        a1, a2 = st.columns([1, 3])
        with a1:
            st.markdown(f'<div class="via-avatar">{emoji}</div>', unsafe_allow_html=True)
            st.markdown(
                f"<div style='text-align:center;color:{color};font-weight:700'>{etiqueta}</div>",
                unsafe_allow_html=True,
            )
        with a2:
            st.plotly_chart(ui.gauge_estabilidad(res_activo["estabilidad"]),
                            width="stretch", key="gauge_twin")

        st.plotly_chart(ui.grafico_abanico(res_sin, res_con, p["edad_retiro"]),
                        width="stretch", key="fan_twin")

    st.markdown("### 📊 Lectura de tu futuro")
    m1, m2, m3, m4 = st.columns(4)

    with m1:
        st.metric("Probabilidad de quiebra antes del retiro",
                  f"{res_activo['prob_ruina']*100:.1f}%",
                  delta=(f"{(res_activo['prob_ruina']-res_sin['prob_ruina'])*100:+.1f} pts" if res_con else None),
                  delta_color="inverse")
    with m2:
        st.metric("Patrimonio mediano al retiro",
                  ui.dinero(res_activo["patrimonio_retiro_mediano"]),
                  delta=(ui.dinero(res_con["patrimonio_retiro_mediano"] - res_sin["patrimonio_retiro_mediano"])
                         if res_con else None))
    with m3:
        st.metric("Protección familiar si tú faltas",
                  f"{res_activo['proteccion_familiar']*100:.0f}%",
                  delta=(f"{(res_con['proteccion_familiar']-res_sin['proteccion_familiar'])*100:+.0f} pts"
                         if res_con else None))
    with m4:
        st.metric("Gasto médico de bolsillo (vida entera, promedio)",
                  ui.dinero(res_activo["gasto_medico_promedio"]),
                  delta=(ui.dinero(res_con["gasto_medico_promedio"] - res_sin["gasto_medico_promedio"])
                         if res_con else None),
                  delta_color="inverse")

    if res_con:
        total = sum(res_con["primas_mensuales"].values())
        st.success(
            f"⚡ Blindaje activo por **~${total:,.0f}/mes** (estimado demo). "
            f"Tu Índice de Estabilidad pasó de **{res_sin['estabilidad']:.0f}** a "
            f"**{res_con['estabilidad']:.0f}** — eso es lo que compra un seguro: futuro predecible.",
            icon="🛡️",
        )
    else:
        st.warning(
            "Tu gemelo está corriendo **sin protección**. Activa un escudo GNP a la izquierda "
            "y mira el cono de incertidumbre encogerse en tiempo real.",
            icon="⚠️",
        )
    return res_sin, res_con


def _tab_espejo(p: dict, res_sin: dict, res_con: dict | None) -> None:
    from core import mirror

    st.markdown(
        "#### 🪞 Conoce a tus dos «yo» del futuro\n"
        "Sube una foto (o tómala aquí) y mira simbólicamente a la persona que serás a los "
        f"**{max(p['edad_retiro'], 70)} años** en tus dos futuros posibles: el blindado y el expuesto. "
        "Ver tu propio rostro en el futuro cambia decisiones — está documentado en economía del comportamiento."
    )
    st.caption("La imagen se procesa localmente en tu sesión y no se almacena. Estilización simbólica de demostración "
               "(en producción: modelo generativo de envejecimiento con consentimiento explícito).")

    fuente = st.radio("Fuente de tu foto", ["📁 Subir archivo", "📷 Cámara"], horizontal=True,
                      label_visibility="collapsed")
    img_bytes = None
    if fuente == "📷 Cámara":
        cam = st.camera_input("Tómate una foto")
        if cam:
            img_bytes = cam.getvalue()
    else:
        up = st.file_uploader("Sube tu foto", type=["jpg", "jpeg", "png", "webp"])
        if up:
            img_bytes = up.getvalue()

    if not img_bytes:
        st.info("Tu espejo está esperando. Sube una foto para conocer a tus dos futuros.", icon="🪞")
        return

    try:
        protegido, desprotegido = mirror.espejo(img_bytes)
    except Exception:
        st.error("No pude procesar esa imagen. Intenta con otra foto (JPG o PNG).")
        return

    completar_mision("espejo")
    res_ok = res_con or res_sin
    c1, c2 = st.columns(2, gap="large")
    with c1:
        st.markdown("##### 🛡️ Tu «yo» blindado")
        st.image(protegido, width="stretch")
        st.success(
            f"Patrimonio mediano al retiro: **{ui.dinero(max(res_ok['patrimonio_retiro_mediano'], res_sin['patrimonio_retiro_mediano']))}** · "
            f"Estabilidad **{max(res_ok['estabilidad'], res_sin['estabilidad']):.0f}/100**. "
            "Duerme tranquilo: sus riesgos catastróficos los absorbe GNP.",
            icon="🌅",
        )
    with c2:
        st.markdown("##### ⚠️ Tu «yo» expuesto")
        st.image(desprotegido, width="stretch")
        st.error(
            f"Probabilidad de quiebra pre-retiro: **{res_sin['prob_ruina']*100:.1f}%** · "
            f"gasto médico de bolsillo esperado **{ui.dinero(res_sin['gasto_medico_promedio'])}**. "
            "Cada imprevisto lo paga solo, con su patrimonio.",
            icon="🌫️",
        )
    st.markdown("👉 ¿Con cuál de los dos quieres desayunar a los 70? Activa tus escudos en la pestaña "
                "**📈 Simulación** o diseña tu plan en **🎯 Metas de Vida**.")


def render() -> None:
    p, c = perfil(), cobertura()
    ui.hero("🧬 Tu Gemelo Digital",
            "10,000 simulaciones de tu vida financiera y biológica. Esto no es una cotización: "
            "es el tablero de control de tu propio destino.")

    _formulario_perfil(p)
    if p["perfil_completo"]:
        completar_mision("perfil")

    tab_sim, tab_espejo = st.tabs(["📈 Simulación de destino", "🪞 Modo Espejo"])
    with tab_sim:
        res_sin, res_con = _tab_simulacion(p, c)
    with tab_espejo:
        _tab_espejo(p, res_sin, res_con)
