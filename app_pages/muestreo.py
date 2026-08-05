"""Muestreo Inverso: regalar el resultado final como primer contacto."""

import streamlit as st

from app_pages._common import datos_scoreados
from brickbit import config, db, outreach

st.title("✉️ Muestreo Inverso · Generador de outreach")
st.caption(
    "El mejor primer contacto no dice 'somos una agencia': **entrega valor ya hecho**. "
    "Selecciona un lead y el sistema arma el mensaje con sus señales reales, "
    "regalando el análisis y dejando la puerta abierta a los 15 casos similares."
)

leads, conn = datos_scoreados()
candidatos = leads[leads["prioridad"].isin(["A", "B"])]

if candidatos.empty:
    st.warning("No hay leads prioridad A/B. Registra señales en El Oráculo.")
    st.stop()

c1, c2 = st.columns([2, 1])
lead_id = c1.selectbox(
    "Lead objetivo (solo prioridad A/B)",
    candidatos["id"],
    format_func=lambda i: (
        f"#{i} · {candidatos.set_index('id').loc[i, 'nombre']} · "
        f"score {candidatos.set_index('id').loc[i, 'score']} "
        f"({candidatos.set_index('id').loc[i, 'prioridad']})"
    ),
)
firma = c2.text_input("Firma", value="José · BrickBit")

lead = dict(db.lead_por_id(conn, int(lead_id)))
senales_tipos = [s["tipo"] for s in db.senales_de_lead(conn, int(lead_id))]
similares = len(leads[
    (leads["producto"] == lead["producto"]) & (leads["prioridad"].isin(["A", "B"]))
])

st.markdown("#### Perfil del lead")
p1, p2, p3, p4 = st.columns(4)
p1.metric("Vertical", config.VERTICALES[lead["vertical"]])
p2.metric("Producto", lead["producto"])
p3.metric("Zona", lead["zona"] or "—")
p4.metric("Casos similares en sistema", similares)

borrador = outreach.generar_borrador(lead, senales_tipos, firma=firma,
                                     n_similares=max(similares - 1, 3))

st.markdown("#### 1️⃣ Borrador (plantilla con señales reales)")
st.code(borrador, language=None)

st.markdown("#### 2️⃣ Refinado hiper-personalizado con IA (opcional)")
if outreach.credenciales_disponibles():
    contexto = st.text_area(
        "Contexto extra para la IA (opcional)",
        placeholder="Ej. 'lo vi en el podcast X hablando de expansión', 'su empresa acaba de abrir sucursal en Monterrey'…",
    )
    if st.button("✨ Refinar con Claude", type="primary"):
        with st.spinner("Reescribiendo con Claude…"):
            ok, resultado = outreach.refinar_con_claude(borrador, contexto)
        if ok:
            st.success("Versión refinada (con fallback automático de modelo activado):")
            st.code(resultado, language=None)
        else:
            st.error(resultado)
else:
    st.info(
        "Configura la variable de entorno `ANTHROPIC_API_KEY` para activar el refinado con IA. "
        "Mientras tanto, el borrador de plantilla es completamente funcional."
    )

st.divider()
st.markdown("""
##### 📐 Anatomía del mensaje (por qué convierte)
1. **Gancho de datos** — "mi sistema detectó X sobre ti/tu empresa": demuestra el producto sin describirlo.
2. **Regalo completo** — el análisis/reporte va gratis y sin condición: reciprocidad real, no clickbait.
3. **Prueba de profundidad** — "tengo N casos más con este perfil": el regalo es la muestra, no el inventario.
4. **CTA mínimo** — 10 minutos, una sola pregunta. Nunca pedir "una llamada para conocernos".

⚖️ **Reglas anti-spam:** primer contacto solo con base legítima (registro en el Radar,
dato comercial público, referido). Siempre con opción de baja. Volumen bajo y
personalización alta ganan a volumen alto con plantilla genérica — también en entregabilidad.
""")
