"""Modelo de negocio: pago por cita calificada + revenue share, con calculadora."""

import pandas as pd
import streamlit as st

st.title("💰 Modelo de negocio · Cero fricción")
st.caption(
    "Cobramos cuando el cliente recibe valor: por cita calificada realizada, "
    "y revenue share solo en high-ticket. Setup pequeño para filtrar curiosos."
)

st.markdown("""
| Componente | Cuándo aplica | Por qué |
|---|---|---|
| **Setup único (bajo)** | Al arrancar con un cliente | Filtra no-serios y cubre configuración del ICP; reembolsable contra las primeras citas |
| **Pago por cita calificada** | Cita **realizada** que cumple criterios pactados | Riesgo cero percibido; alinea incentivos con calidad, no volumen |
| **Revenue share** | Solo high-ticket (desarrollos, inversión) | En tickets de millones, un % pequeño supera cualquier tarifa fija |
| ~~Suscripción mensual fija~~ | ❌ Recortado al inicio | Genera desconfianza sin historial; se introduce después como plan 'siempre encendido' |

**Definición de cita calificada (se pacta por escrito):** el prospecto (1) cumple el ICP,
(2) confirmó asistencia y asistió, (3) tiene la necesidad activa detectada por señal.
Sin esa definición, 'pago por cita' se vuelve una discusión eterna.
""")

st.divider()
st.subheader("🧮 Calculadora de unit economics")

c1, c2, c3 = st.columns(3)
with c1:
    st.markdown("**Embudo mensual**")
    senales_mes = st.number_input("Señales detectadas / mes", 50, 20000, 800, 50)
    tasa_contacto = st.slider("% señales → contacto efectivo", 5, 80, 35)
    tasa_cita = st.slider("% contactos → cita calificada", 2, 40, 12)
with c2:
    st.markdown("**Precios**")
    precio_cita = st.number_input("Precio por cita calificada (MXN)", 200, 20000, 1500, 100)
    pct_rev_share = st.slider("Revenue share high-ticket (%)", 0.0, 5.0, 1.0, 0.25)
    pct_leads_ht = st.slider("% de citas que son high-ticket", 0, 50, 10)
    ticket_ht = st.number_input("Ticket promedio high-ticket (MXN)", 100_000, 50_000_000, 3_000_000, 100_000)
    tasa_cierre_ht = st.slider("% cierre high-ticket", 1, 50, 15)
with c3:
    st.markdown("**Costos**")
    costo_infra = st.number_input("Infraestructura + APIs / mes (MXN)", 0, 200_000, 8_000, 1_000)
    costo_datos = st.number_input("Datos y herramientas / mes (MXN)", 0, 200_000, 5_000, 1_000)
    horas_humanas = st.number_input("Horas humanas / mes", 0, 700, 120, 10)
    costo_hora = st.number_input("Costo por hora (MXN)", 50, 2000, 250, 50)

contactos = senales_mes * tasa_contacto / 100
citas = contactos * tasa_cita / 100
citas_ht = citas * pct_leads_ht / 100
cierres_ht = citas_ht * tasa_cierre_ht / 100

ingreso_citas = citas * precio_cita
ingreso_rs = cierres_ht * ticket_ht * pct_rev_share / 100
ingreso_total = ingreso_citas + ingreso_rs
costo_total = costo_infra + costo_datos + horas_humanas * costo_hora
margen = ingreso_total - costo_total

st.divider()
m1, m2, m3, m4, m5 = st.columns(5)
m1.metric("Citas calificadas / mes", f"{citas:,.0f}")
m2.metric("Ingreso por citas", f"${ingreso_citas:,.0f}")
m3.metric("Ingreso revenue share", f"${ingreso_rs:,.0f}")
m4.metric("Costo total", f"${costo_total:,.0f}")
m5.metric("Margen mensual", f"${margen:,.0f}",
          delta=f"{(margen / ingreso_total * 100) if ingreso_total else 0:.0f}% margen")

if margen < 0:
    st.error("Con estos números el modelo pierde dinero: sube el precio por cita, "
             "mejora la tasa señal→contacto (speed-to-lead) o reduce horas humanas con más automatización.")
elif ingreso_rs > ingreso_citas:
    st.success("El revenue share domina: el negocio real está en high-ticket. "
               "Prioriza señales de desarrolladores e inversionistas.")

st.divider()
st.subheader("📆 Plan de ejecución 90 días")
plan = pd.DataFrame([
    ["Semana 1-2", "Publicar el Radar (Caballo de Troya) y compartirlo en comunidades locales", "Primeras 100 capturas"],
    ["Semana 2-4", "Activar 2 conectores de señales (empleos + permisos) y el scoring", "Primeros 20 leads prioridad A"],
    ["Semana 3-6", "Muestreo Inverso manual-asistido: 10 mensajes/día hiper-personalizados", "3-5 citas calificadas"],
    ["Semana 6-8", "Cerrar 2-3 clientes ancla (agente GNP con cartera + inmobiliaria boutique) en pago por cita", "Ingreso recurrente inicial"],
    ["Semana 8-12", "Automatizar clasificación de respuestas y seguimientos; medir costo por cita", "Máquina repetible + caso de estudio"],
], columns=["Cuándo", "Qué", "Meta"])
st.dataframe(plan, width="stretch", hide_index=True)
