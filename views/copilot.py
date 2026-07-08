"""Modo Asesor: el copiloto de IA del estratega humano de GNP."""

import pandas as pd
import streamlit as st

from core import copilot, simulator, ui
from core.pulse import prima_base_paquete
from core.risk import radar_vulnerabilidad, score_blindaje
from core.state import cobertura, perfil


def render() -> None:
    p, c = perfil(), cobertura()
    ss = st.session_state

    ui.hero("🧑‍💼 Copiloto del Asesor",
            "La misma IA que diagnosticó al prospecto, ahora del lado del estratega humano: scoring de "
            "propensión, argumentos rankeados por peso emocional y manejo de objeciones con los números "
            "del propio cliente. En producción vive dentro del CRM y sugiere en vivo durante la llamada.")

    prop, senales = copilot.propension(ss)
    nombre = p["nombre"] or "Prospecto de esta sesión"

    # --- pipeline ---------------------------------------------------------------
    st.markdown("#### 📊 Pipeline de prospectos")
    filas = [{"Prospecto": f"⭐ {nombre} (sesión actual)", "Edad": p["edad"],
              "Propensión": prop, "Etapa": "Explorando la plataforma", "Prioridad": p["prioridad"]}]
    filas += [{"Prospecto": l["nombre"], "Edad": l["edad"], "Propensión": l["propension"],
               "Etapa": l["etapa"], "Prioridad": l["prioridad"]} for l in copilot.DEMO_LEADS]
    df = pd.DataFrame(filas).sort_values("Propensión", ascending=False).reset_index(drop=True)
    st.dataframe(
        df, width="stretch", hide_index=True,
        column_config={"Propensión": st.column_config.ProgressColumn(
            "Propensión a cierre", min_value=0, max_value=100, format="%d%%")},
    )
    st.caption("Los demás prospectos son datos demo del CRM; el primero es la sesión en vivo.")

    st.divider()
    st.markdown(f"### 🎧 Sala de estrategia: **{nombre}** · propensión {prop}%")

    radar = radar_vulnerabilidad(p, c, ss["metas"])
    res = simulator.correr(p, c)
    prima_total = prima_base_paquete(p, c)

    col1, col2 = st.columns([1.2, 1], gap="large")

    with col1:
        st.markdown("#### 🧠 Señales de compra detectadas")
        if senales:
            for s in senales:
                st.markdown(f"- {s}")
        else:
            st.caption("El prospecto aún no interactúa lo suficiente — invítalo a la Auditoría con VIA.")

        st.markdown("#### 💬 Argumentos rankeados (primero lo emocional)")
        for punto in copilot.puntos_de_charla(p, radar, ss["metas"], res):
            st.markdown(f"- {punto}")

    with col2:
        st.markdown("#### 🥊 Manejo de objeciones con SUS números")
        for objecion, respuesta in copilot.objeciones(res, prima_total):
            with st.expander(objecion):
                st.markdown(respuesta)

        st.markdown("#### 📈 Resumen técnico")
        st.markdown(
            f"- Score de Blindaje: **{score_blindaje(radar)}/1000**\n"
            f"- Estabilidad Vital: **{res['estabilidad']:.0f}/100**\n"
            f"- Prob. de quiebra simulada: **{res['prob_ruina']*100:.1f}%**\n"
            f"- Paquete Vital estimado: **${prima_total:,.0f}/mes**\n"
            f"- Metas activas: **{len(ss['metas'])}** · Certificados: **{len(ss.get('ledger', []))}**"
        )

    st.divider()
    st.markdown("#### 🤖 Guion de llamada generado por IA")
    if st.button("✨ Generar guion personalizado", type="primary"):
        with st.spinner("Redactando guion con los datos del prospecto…"):
            guion = copilot.guion_llamada_llm(p, radar, ss["metas"], res)
        if guion:
            st.markdown(guion)
        else:
            st.markdown(_guion_offline(p, radar, ss["metas"], res))
            st.caption("Guion generado con plantillas locales. Configura ANTHROPIC_API_KEY para guiones "
                       "redactados por Claude con el contexto completo del prospecto.")


def _guion_offline(p: dict, radar: dict, metas: list, res: dict) -> str:
    from core.risk import brechas_criticas
    peor = brechas_criticas(radar, 1)[0]
    meta_txt = (f"su sueño «{metas[0]['nombre']}» para {metas[0]['anio_objetivo']}"
                if metas else "las metas que aún no ha puesto en su línea de vida")
    return f"""
**1. Apertura (30s) — su mundo, no el tuyo.** «{p['nombre'] or 'Hola'}, vi tu Mapa de Vida: me detuve en {meta_txt}. ¿Me cuentas qué significa para ti?»

**2. Espejo (1 min).** Reproduce su simulación en pantalla compartida. No expliques: pregunta. «¿Qué sentiste al ver tu cono sin protección?»

**3. La brecha (2 min).** Su radar marca **{peor[0]} al {peor[1]:.0f}%**. Usa SU dato: «esto no lo digo yo, lo dice tu propia simulación de 10,000 vidas».

**4. La arquitectura (3 min).** Presenta la mezcla protección + ahorro que su plataforma ya sugirió. Ancla al aporte mensual de su meta, nunca al costo anual.

**5. Cierre suave (1 min).** «No tienes que decidir hoy. Decide qué versión de los dos futuros que viste quieres alimentar este mes.» Silencio. El que habla primero, pierde.
"""
