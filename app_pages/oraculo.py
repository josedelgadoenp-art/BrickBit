"""El Oráculo: señales de intención predictiva y priorización A/B/C."""

import streamlit as st

from app_pages._common import datos_scoreados, invalidar_datos, COLORES_PRIORIDAD
from brickbit import config, db

st.title("🔮 El Oráculo · Señales de intención")
st.caption(
    "No vendemos una lista de 1,000 nombres: detectamos **quién necesita comprar hoy**. "
    "Score = 40% fit (parecido al cliente ideal) + 60% intención (señales con decaimiento: "
    f"una señal pierde la mitad de su valor cada {config.SENAL_VIDA_MEDIA_DIAS} días)."
)

leads, conn = datos_scoreados()

# --- Filtros ---
f1, f2, f3, f4 = st.columns(4)
vertical = f1.selectbox("Vertical", ["todas"] + list(config.VERTICALES),
                        format_func=lambda v: config.VERTICALES.get(v, "Todas"))
prioridades = f2.multiselect("Prioridad", ["A", "B", "C"], default=["A", "B"])
zona = f3.selectbox("Zona", ["todas"] + list(config.ZONAS_CDMX))
solo_cross = f4.checkbox("Solo venta cruzada 🔁")

vista = leads.copy()
if vertical != "todas":
    vista = vista[vista["vertical"] == vertical]
if prioridades:
    vista = vista[vista["prioridad"].isin(prioridades)]
if zona != "todas":
    vista = vista[vista["zona"] == zona]
if solo_cross:
    vista = vista[vista["cross_sell"]]

st.markdown(
    f"**{len(vista)} leads** · "
    f"🔴 A: {len(vista[vista['prioridad'] == 'A'])} · "
    f"🟡 B: {len(vista[vista['prioridad'] == 'B'])} · "
    f"⚪ C: {len(vista[vista['prioridad'] == 'C'])}"
)

tabla = vista[["id", "nombre", "empresa", "vertical", "producto", "zona",
               "fit_score", "intencion", "score", "prioridad", "senales_labels"]].copy()
tabla["prioridad"] = tabla["prioridad"].map(lambda p: f"{COLORES_PRIORIDAD[p]} {p}")
tabla["vertical"] = tabla["vertical"].map(config.VERTICALES)
tabla.columns = ["ID", "Nombre", "Empresa", "Vertical", "Producto", "Zona",
                 "Fit", "Intención", "Score", "Prioridad", "Señales"]
st.dataframe(tabla, width="stretch", hide_index=True, height=420)

st.divider()

col_a, col_b = st.columns(2)

with col_a:
    st.subheader("➕ Registrar señal detectada")
    st.caption("En producción, los scrapers y conectores insertan señales automáticamente. "
               "Aquí puedes simular la llegada de una señal y ver el score reaccionar.")
    with st.form("nueva_senal"):
        opciones = {f"{v['label']} ({config.VERTICALES[v['vertical']]})": k
                    for k, v in config.SENALES.items()}
        lead_sel = st.selectbox(
            "Lead", leads["id"],
            format_func=lambda i: f"#{i} · {leads.set_index('id').loc[i, 'nombre']}",
        )
        senal_sel = st.selectbox("Señal", list(opciones))
        detalle = st.text_input("Detalle (opcional)")
        if st.form_submit_button("Registrar señal", type="primary"):
            tipo = opciones[senal_sel]
            db.insertar_senal(conn, int(lead_sel), tipo,
                              detalle or config.SENALES[tipo]["descripcion"])
            invalidar_datos()
            st.success(f"Señal registrada. El score del lead #{lead_sel} se recalculó.")
            st.rerun()

with col_b:
    st.subheader("📚 Catálogo de señales")
    st.caption("Cada señal tiene un peso base 0-100 según qué tan cerca está de la decisión de compra.")
    for tipo, info in sorted(config.SENALES.items(), key=lambda kv: -kv[1]["peso"]):
        cruz = " · 🔁 cross-sell" if info["cross_sell"] else ""
        st.markdown(
            f"**{info['label']}** — peso {info['peso']} · "
            f"{config.VERTICALES[info['vertical']]}{cruz}  \n"
            f"<small>{info['descripcion']}</small>",
            unsafe_allow_html=True,
        )

st.divider()
st.subheader("🔌 Conectores de ingesta (roadmap de producción)")
st.markdown("""
| Conector | Fuente | Señales que alimenta | Estado |
|---|---|---|---|
| Radar BrickBit | Registros y uso de la herramienta gratuita | `visita_repetida_radar`, `cotizo_en_linea` | ✅ Activo (esta app) |
| Bolsas de empleo | Vacantes públicas por empresa | `pyme_contratando`, `empresa_expansion` | 🔧 Conector stub |
| Datos abiertos CDMX | Manifestaciones de construcción | `permiso_construccion` | 🔧 Conector stub |
| Portales inmobiliarios | Listados, precios, tiempo en mercado | anomalías de precio, `busqueda_activa_zona` | 🔧 Conector stub |
| Registro público / notarías | Operaciones de compraventa | `compra_casa`, `inversionista_activo` | 🔜 Evaluar acceso |
| LinkedIn / prensa | Cambios de puesto, rondas de inversión | `nuevo_empleo_ejecutivo`, `evento_liquidez` | 🔜 Evaluar acceso |

⚖️ **Regla de cumplimiento:** solo fuentes públicas o con consentimiento (LFPDPPP).
El dato de contacto se usa cuando la persona se registró en nuestra herramienta o
el dato es de carácter comercial público (empresas). Nada de comprar bases de datos.
""")
