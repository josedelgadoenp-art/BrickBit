"""El Caballo de Troya: Radar de mercado gratuito con captura de leads.

La herramienta es 100% usable sin registrarse (esa es la gracia: se comparte
sola). El 'paywall' está en los datos accionables: contactos de tomadores de
decisión y oportunidades concretas requieren dejar tus datos -> cada registro
es un lead capturado para BrickBit.
"""

import pandas as pd
import pydeck as pdk
import streamlit as st

from app_pages._common import conexion, invalidar_datos
from brickbit import config, db

st.title("🗺️ Radar Inmobiliario CDMX")
st.caption(
    "Herramienta **gratuita** de análisis de mercado. Precio por m², crecimiento anual "
    "e inventario por zona. (Datos demo — en producción: scrapers de portales + datos abiertos.)"
)

zonas = pd.DataFrame([
    {"zona": nombre, **datos} for nombre, datos in config.ZONAS_CDMX.items()
])

# --- Controles ---
c1, c2 = st.columns([1, 1])
metrica = c1.selectbox(
    "Colorear mapa por",
    ["crecimiento", "precio_m2", "inventario"],
    format_func={"crecimiento": "📈 Crecimiento anual (%)",
                 "precio_m2": "💲 Precio por m² (MXN)",
                 "inventario": "🏘️ Inventario disponible"}.get,
)
crecimiento_min = c2.slider("Crecimiento mínimo (%)", 0.0, 12.0, 0.0, 0.5)

filtradas = zonas[zonas["crecimiento"] >= crecimiento_min].copy()

# Normalizar la métrica elegida para altura y color.
vmax = filtradas[metrica].max() or 1
filtradas["intensidad"] = filtradas[metrica] / vmax
filtradas["altura"] = filtradas["intensidad"] * 3000
filtradas["color_r"] = (228 * filtradas["intensidad"] + 27).astype(int)
filtradas["color_g"] = (87 * (1 - filtradas["intensidad"]) + 60).astype(int)

capa = pdk.Layer(
    "ColumnLayer",
    data=filtradas,
    get_position=["lon", "lat"],
    get_elevation="altura",
    elevation_scale=1,
    radius=600,
    get_fill_color=["color_r", "color_g", 46, 200],
    pickable=True,
    auto_highlight=True,
)

st.pydeck_chart(pdk.Deck(
    layers=[capa],
    initial_view_state=pdk.ViewState(latitude=19.40, longitude=-99.17, zoom=10.8, pitch=45),
    tooltip={"html": "<b>{zona}</b><br/>Precio m²: ${precio_m2}<br/>"
                     "Crecimiento: {crecimiento}%<br/>Inventario: {inventario}"},
    map_style=None,
))

st.subheader("Tabla comparativa de zonas")
tabla = filtradas[["zona", "precio_m2", "crecimiento", "inventario"]].sort_values(
    "crecimiento", ascending=False
)
tabla.columns = ["Zona", "Precio m² (MXN)", "Crecimiento anual (%)", "Inventario"]
st.dataframe(tabla, width="stretch", hide_index=True)

st.divider()

# --- La captura: el candado sobre lo accionable ---
st.subheader("🔓 Desbloquear oportunidades y contactos clave")
st.markdown(
    "El análisis de mercado es gratis y siempre lo será. Las **oportunidades concretas** "
    "(propiedades con anomalía de precio, desarrolladores activos en la zona y sus "
    "contactos directos) se desbloquean registrándote — sin costo."
)

if st.session_state.get("radar_desbloqueado"):
    st.success("Acceso desbloqueado. Estas son las oportunidades activas en tu zona de interés:")
    zona_sel = st.session_state.get("radar_zona", "Roma Norte")
    info = config.ZONAS_CDMX.get(zona_sel, {})
    st.markdown(f"""
| Oportunidad ({zona_sel}) | Detalle | Contacto |
|---|---|---|
| 🏗️ Desarrollador con permiso activo | Manifestación tipo B registrada hace 21 días | Director de proyecto — *desbloqueado* |
| 💲 Anomalía de precio (-18% vs zona) | Depto 92 m², {info.get('precio_m2', 50000):,} → oportunidad | Propietario directo — *desbloqueado* |
| 🏢 Empresa buscando oficinas | Contratando 12 posiciones técnicas | Directora de Operaciones — *desbloqueado* |

*(Demo: en producción estos datos provienen del motor de señales en tiempo real.)*
""")
else:
    with st.form("captura_radar"):
        st.markdown("**Regístrate gratis para desbloquear:**")
        f1, f2 = st.columns(2)
        nombre = f1.text_input("Nombre")
        email = f2.text_input("Email")
        f3, f4 = st.columns(2)
        interes = f3.selectbox("Me interesa", [
            "Comprar vivienda", "Invertir", "Encontrar oficinas",
            "Desarrollar", "Seguro de auto", "Seguro de vida / GMM",
        ])
        zona_interes = f4.selectbox("Zona de interés", list(config.ZONAS_CDMX))
        enviado = st.form_submit_button("🔓 Desbloquear gratis", type="primary")

    if enviado:
        if not nombre.strip() or "@" not in email:
            st.error("Necesitamos tu nombre y un email válido.")
        else:
            db.registrar_captura(conexion(), nombre.strip(), email.strip(), interes, zona_interes)
            st.session_state["radar_desbloqueado"] = True
            st.session_state["radar_zona"] = zona_interes
            invalidar_datos()
            st.rerun()

st.divider()
capturas = db.capturas_df(conexion())
st.caption(
    f"📥 **Vista interna (solo equipo BrickBit):** la herramienta ha capturado "
    f"**{len(capturas)}** registros. Cada registro entra al Oráculo como señal de intención "
    "('usó el Radar') y arranca la secuencia de contacto."
)
with st.expander("Ver capturas recientes"):
    st.dataframe(capturas.head(15), width="stretch", hide_index=True)
