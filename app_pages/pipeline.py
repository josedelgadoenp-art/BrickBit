"""Pipeline SDR: seguimiento de leads, clasificación de respuestas y citas."""

from datetime import date, timedelta

import streamlit as st

from app_pages._common import datos_scoreados, invalidar_datos
from brickbit import config, db

st.title("🤖 Pipeline SDR")
st.caption(
    "El 'SDR invisible' opera el embudo: clasifica respuestas, agenda seguimientos y "
    "solo escala al humano cuando el lead dice 'me interesa'. Aquí gestionas ese flujo."
)

leads, conn = datos_scoreados()

# --- Tablero por etapa ---
etapas_activas = ["nuevo", "contactado", "respondio", "cita_agendada", "seguimiento_futuro"]
cols = st.columns(len(etapas_activas))
for col, etapa in zip(cols, etapas_activas):
    grupo = leads[leads["etapa"] == etapa].head(8)
    with col:
        st.markdown(f"**{config.ETAPAS_LABELS[etapa]}** ({len(leads[leads['etapa'] == etapa])})")
        for _, l in grupo.iterrows():
            st.markdown(
                f"<div style='border:1px solid #444;border-radius:6px;padding:6px;margin-bottom:6px;font-size:0.8em'>"
                f"<b>#{l['id']} {l['nombre']}</b><br/>{config.VERTICALES[l['vertical']]} · "
                f"score {l['score']} ({l['prioridad']})</div>",
                unsafe_allow_html=True,
            )

st.divider()

col_izq, col_der = st.columns(2)

with col_izq:
    st.subheader("📨 Clasificar respuesta de un lead")
    st.caption("En producción, la IA clasifica la respuesta del correo automáticamente; "
               "aquí simulas el resultado de esa clasificación.")
    with st.form("clasificar"):
        lead_sel = st.selectbox(
            "Lead", leads["id"],
            format_func=lambda i: f"#{i} · {leads.set_index('id').loc[i, 'nombre']} "
                                  f"({config.ETAPAS_LABELS[leads.set_index('id').loc[i, 'etapa']]})",
        )
        resultado = st.radio("La respuesta indica…", [
            "✅ Me interesa → agendar cita",
            "⏰ 'Búscame en unos meses' → seguimiento futuro",
            "💬 Respondió con dudas → sigue la conversación",
            "❌ No le interesa → cerrar perdido",
        ])
        valor = st.number_input("Valor estimado de la oportunidad (MXN)", 0, 5_000_000, 25_000, 5_000)
        if st.form_submit_button("Aplicar", type="primary"):
            lid = int(lead_sel)
            if resultado.startswith("✅"):
                db.agendar_reunion(conn, lid, (date.today() + timedelta(days=3)).isoformat(),
                                   valor, "Cita generada desde clasificación de respuesta")
            elif resultado.startswith("⏰"):
                db.actualizar_etapa(conn, lid, "seguimiento_futuro")
            elif resultado.startswith("💬"):
                db.actualizar_etapa(conn, lid, "respondio")
            else:
                db.actualizar_etapa(conn, lid, "cerrado_perdido")
            invalidar_datos()
            st.rerun()

with col_der:
    st.subheader("📅 Citas (la unidad que cobramos)")
    reuniones = db.reuniones_df(conn)
    if reuniones.empty:
        st.info("Sin citas todavía.")
    else:
        vista = reuniones[["fecha", "nombre", "empresa", "vertical", "estado", "valor_estimado"]].copy()
        vista["vertical"] = vista["vertical"].map(config.VERTICALES)
        vista.columns = ["Fecha", "Lead", "Empresa", "Vertical", "Estado", "Valor est. (MXN)"]
        st.dataframe(vista, width="stretch", hide_index=True)
        st.metric("Citas totales", len(reuniones))

st.divider()
st.subheader("⚙️ Automatización del SDR invisible (diseño de producción)")
st.markdown("""
| Paso | Automatización | Humano entra cuando… |
|---|---|---|
| 1. Señal detectada | Score recalculado; si es A, entra a cola de contacto inmediato (< 5 min) | Nunca |
| 2. Primer contacto | Mensaje de Muestreo Inverso generado y enviado (email/WhatsApp*) | Nunca |
| 3. Respuesta | IA clasifica: interés / futuro / duda / rechazo | Clasificación ambigua |
| 4. Seguimiento | 'Búscame en marzo' → tarea agendada automática | Nunca |
| 5. Cita | Lead interesado recibe liga de calendario; cita confirmada | **Aquí entra el humano: a la cita** |

\\* En México, WhatsApp convierte mejor que el email para B2C (seguros e inmobiliario
persona física); el email queda para B2B. Ambos con consentimiento y opción de baja.

🚫 **Qué NO automatizamos (recorte deliberado):** conectar bandejas de entrada de clientes
para enviar en su nombre desde el día 1 ("clonación de identidad"). Riesgo alto de
entregabilidad y confianza. Fase 2, solo con clientes que lo pidan y con dominios propios calentados.
""")
