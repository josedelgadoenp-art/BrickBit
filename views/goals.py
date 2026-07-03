"""Marketplace de Metas de Vida: sueños en la línea de tiempo + arquitectura GNP."""

import datetime

import streamlit as st

from core import goals as g
from core import ui
from core.gamification import completar_mision
from core.state import perfil


def render() -> None:
    ui.hero("🎯 Marketplace de Metas de Vida",
            "Nadie quiere «comprar un seguro». Todos queremos que nuestros sueños sucedan. "
            "Ponlos en tu línea de vida y la IA calcula su costo real con inflación futura — "
            "y el vehículo GNP exacto para garantizarlos.")

    p = perfil()
    ss = st.session_state
    anio_hoy = datetime.date.today().year

    # --- catálogo de sueños ----------------------------------------------------
    st.markdown("#### 🛒 Elige un sueño y colócalo en tu línea de vida")
    cols = st.columns(4)
    claves = list(g.PLANTILLAS.keys())
    for i, key in enumerate(claves):
        pl = g.PLANTILLAS[key]
        with cols[i % 4]:
            ui.tarjeta(pl["nombre"], pl["desc"], pl["icono"])
            st.write("")

    c1, c2, c3 = st.columns([2, 1.4, 1])
    with c1:
        sel = st.selectbox("Sueño", claves, format_func=lambda k: f"{g.PLANTILLAS[k]['icono']} {g.PLANTILLAS[k]['nombre']}")
    with c2:
        anio = st.slider("¿En qué año quieres lograrlo?", anio_hoy + 1, anio_hoy + 40, anio_hoy + 10)
    with c3:
        st.write("")
        st.write("")
        if st.button("➕ Agregar a mi vida", type="primary", width="stretch"):
            ss["metas"].append(g.crear_meta(sel, anio, p))
            completar_mision("meta_1")
            if len(ss["metas"]) >= 3:
                completar_mision("meta_3")
            st.rerun()

    metas = ss["metas"]
    if not metas:
        st.info("Agrega tu primer sueño para ver la magia: costo indexado a inflación, aporte mensual y arquitectura GNP.", icon="✨")
        return

    # --- línea de vida ----------------------------------------------------------
    st.plotly_chart(ui.timeline_metas(metas, p["edad"]), width="stretch", key="timeline_goals")

    # --- arquitectura financiera --------------------------------------------------
    st.markdown("#### 🏗️ Arquitectura financiera de tus sueños")
    for i, m in enumerate(metas):
        with st.container(border=True):
            a, b, c, d, e = st.columns([2.2, 1.2, 1.2, 1.6, 0.6])
            anios = max(m["anio_objetivo"] - anio_hoy, 1)
            with a:
                st.markdown(f"**{m['icono']} {m['nombre']}** · {m['anio_objetivo']}")
                st.caption(m["desc"])
            with b:
                st.metric("Costo hoy", ui.dinero(m["costo_base"] or m["costo_futuro"] / (1 + m["inflacion"]) ** anios))
            with c:
                st.metric("Costo real en tu año", ui.dinero(m["costo_futuro"]),
                          delta=f"inflación {m['inflacion']*100:.1f}%/año", delta_color="off")
            with d:
                st.metric("Aporte mensual GNP", ui.dinero(m["aporte_mensual"]))
                st.caption(f"vía **{m['producto']['icono']} {m['producto']['nombre']}** ({m['producto']['tipo']})")
            with e:
                if st.button("🗑️", key=f"del_{i}", help="Quitar meta"):
                    metas.pop(i)
                    st.rerun()

    # --- viabilidad -----------------------------------------------------------------
    res = g.resumen_plan(metas, p)
    st.markdown("#### 🧠 Veredicto del arquitecto financiero")
    k1, k2, k3 = st.columns(3)
    k1.metric("Costo futuro total de tus sueños", ui.dinero(res["total_futuro"]))
    k2.metric("Aporte mensual total requerido", ui.dinero(res["total_mensual"]))
    k3.metric("Tu capacidad mensual actual", ui.dinero(res["capacidad"]))

    if res["viable"]:
        st.success(
            f"✅ Tu plan es **viable hoy**: usarías el {res['pct_capacidad']:.0f}% de tu excedente mensual. "
            "El paso crítico: blindar el plan con protección de vida e invalidez para que se cumpla "
            "**aunque tú no puedas seguir aportando**. Eso es exactamente lo que hace la combinación "
            "protección + ahorro de GNP.",
            icon="🏛️",
        )
    else:
        st.error(
            f"⚠️ Tus sueños requieren {ui.dinero(res['total_mensual'])}/mes y tu excedente es "
            f"{ui.dinero(res['capacidad'])}/mes. Opciones del arquitecto: mover años objetivo, "
            "priorizar metas, o usar vehículos GNP con rendimiento superior para reducir el aporte. "
            "Un asesor humano puede reestructurarlo contigo en una llamada.",
            icon="🧮",
        )

    if st.button("🤝 Enviar mi mapa de sueños a un asesor GNP", type="primary"):
        ss["_nav"] = "handoff"
        st.rerun()
