"""Panel de control: el embudo completo de un vistazo."""

import pandas as pd
import streamlit as st

from app_pages._common import datos_scoreados, conexion
from brickbit import config, db

st.title("📊 Panel de control")
st.caption("Objetivo: la mayor cantidad de prospectos calificados en el menor tiempo posible.")

leads, conn = datos_scoreados()
capturas = db.capturas_df(conn)
reuniones = db.reuniones_df(conn)

# --- KPIs principales ---
c1, c2, c3, c4, c5 = st.columns(5)
prioridad_a = leads[leads["prioridad"] == "A"]
c1.metric("Leads totales", len(leads))
c2.metric("🔴 Prioridad A (contactar HOY)", len(prioridad_a))
c3.metric("Capturas herramienta gratuita", len(capturas))
c4.metric("Citas agendadas", len(reuniones[reuniones["estado"] == "agendada"]))
ganados = leads[leads["etapa"] == "cerrado_ganado"]
c5.metric("Cerrados ganados", len(ganados))

st.divider()

col_izq, col_der = st.columns([3, 2])

with col_izq:
    st.subheader("Embudo por etapa")
    orden = config.ETAPAS_PIPELINE
    conteo = leads["etapa"].value_counts().reindex(orden).fillna(0).astype(int)
    embudo = pd.DataFrame({
        "Etapa": [config.ETAPAS_LABELS[e] for e in orden],
        "Leads": conteo.values,
    })
    st.bar_chart(embudo.set_index("Etapa"), horizontal=True, color="#E4572E")

with col_der:
    st.subheader("Mix por vertical y prioridad")
    mix = (
        leads.groupby(["vertical", "prioridad"]).size().unstack(fill_value=0)
        .rename(index=config.VERTICALES)
    )
    st.dataframe(mix, width="stretch")

    st.subheader("Velocidad (speed-to-lead)")
    st.caption(
        "Regla de oro: un lead A se contacta en **menos de 5 minutos** desde que "
        "aparece la señal. La probabilidad de conectar cae ~8x después de la primera hora."
    )
    valor_pipeline = reuniones["valor_estimado"].sum() if not reuniones.empty else 0
    st.metric("Valor estimado en pipeline", f"${valor_pipeline:,.0f} MXN")

st.divider()

st.subheader("🔥 Los 10 de hoy — leads que necesitan comprar ahora")
st.caption("No vendemos listas de 1,000 nombres: entregamos los 10 que tienen la señal encendida.")

top = leads.head(10)[
    ["nombre", "empresa", "vertical", "producto", "zona", "score", "prioridad", "senales_labels", "etapa"]
].copy()
top["vertical"] = top["vertical"].map(config.VERTICALES)
top["etapa"] = top["etapa"].map(config.ETAPAS_LABELS)
top.columns = ["Nombre", "Empresa", "Vertical", "Producto", "Zona", "Score", "Prioridad", "Señales", "Etapa"]
st.dataframe(top, width="stretch", hide_index=True)

cross = leads[leads["cross_sell"] & (leads["prioridad"] != "C")]
if not cross.empty:
    st.info(
        f"🔁 **Motor de venta cruzada:** {len(cross)} leads activos tienen señales que conectan "
        "las dos verticales (ej. compró casa → necesita seguro de vida y hogar; "
        "preaprobación de crédito → cliente inmobiliario y de GNP a la vez). "
        "Cada lead puede monetizarse dos veces."
    )
