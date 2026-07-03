"""Copiloto humano: handoff del diagnóstico completo al asesor GNP."""

import datetime

import streamlit as st

from core import simulator, ui
from core.gamification import completar_mision
from core.risk import brechas_criticas, radar_vulnerabilidad, score_blindaje
from core.state import cobertura, perfil


def _reporte_md(p: dict, radar: dict, score: int, res: dict, metas: list) -> str:
    lineas = [
        "# Mapa de Vida GNP — Expediente para el asesor",
        f"*Generado por GNP LifeOS el {datetime.date.today().isoformat()}*",
        "",
        "## Perfil",
        f"- **Nombre:** {p['nombre'] or 'Prospecto'}",
        f"- **Edad:** {p['edad']} · **Zona:** {p['zona']} · **Dependientes:** {p['dependientes']}",
        f"- **Ingreso mensual:** ${p['ingreso_mensual']:,.0f} · **Gastos:** ${p['gastos_mensuales']:,.0f}",
        f"- **Ahorro actual:** ${p['ahorro_actual']:,.0f} · **Retiro deseado:** {p['edad_retiro']} años",
        f"- **Hábitos:** fumador={'sí' if p['fumador'] else 'no'}, ejercicio={p['ejercicio']}, salud={p['salud_general']}",
        f"- **Prioridad declarada:** {p['prioridad']}",
        "",
        "## Diagnóstico automatizado",
        f"- **Score de Blindaje:** {score}/1000",
        f"- **Índice de Estabilidad Vital:** {res['estabilidad']:.0f}/100",
        f"- **Probabilidad de quiebra pre-retiro (simulada):** {res['prob_ruina']*100:.1f}%",
        f"- **Protección familiar en caso de fallecimiento:** {res['proteccion_familiar']*100:.0f}%",
        "",
        "### Radar de protección por dimensión",
    ]
    lineas += [f"- {dim}: {val:.0f}%" for dim, val in radar.items()]
    lineas += ["", "### Brechas críticas (orden de ataque sugerido)"]
    lineas += [f"1. {dim} ({val:.0f}%)" for dim, val in brechas_criticas(radar, 3)]
    if metas:
        lineas += ["", "## Mapa de sueños"]
        for m in metas:
            lineas.append(
                f"- {m['icono']} **{m['nombre']}** ({m['anio_objetivo']}): costo futuro "
                f"${m['costo_futuro']:,.0f} · aporte ${m['aporte_mensual']:,.0f}/mes · "
                f"vehículo sugerido: {m['producto']['nombre']}"
            )
    lineas += [
        "",
        "## Guion sugerido para la llamada",
        "1. Validar prioridad declarada y brecha #1 del radar.",
        "2. Mostrar la simulación con/sin escudos (la plataforma ya se la enseñó).",
        "3. Cerrar con la meta de mayor carga emocional del mapa de sueños.",
        "",
        "*Cifras de demostración generadas por simulación Monte Carlo; validar con cotizador oficial GNP.*",
    ]
    return "\n".join(lineas)


def render() -> None:
    p, c = perfil(), cobertura()
    ss = st.session_state

    ui.hero("🤝 Tu Copiloto Humano",
            "La IA hizo el diagnóstico; un estratega humano de GNP hace el cierre. Tu asesor recibe "
            "tu mapa completo para que la llamada sea 100% estratégica y cero invasiva.")

    radar = radar_vulnerabilidad(p, c, ss["metas"])
    score = score_blindaje(radar)
    res = simulator.correr(p, c)
    reporte = _reporte_md(p, radar, score, res, ss["metas"])

    col1, col2 = st.columns([1.2, 1], gap="large")

    with col1:
        st.markdown("#### 📋 Esto es lo que recibirá tu asesor")
        with st.container(border=True, height=430):
            st.markdown(reporte)
        st.download_button("⬇️ Descargar mi Mapa de Vida (Markdown)", reporte,
                           file_name="mapa_de_vida_gnp.md", width="stretch")

    with col2:
        st.markdown("#### 📞 Agenda tu sesión estratégica")
        if ss["lead_enviado"]:
            st.success("✅ ¡Listo! Un estratega GNP te contactará en el horario elegido con tu mapa ya estudiado.", icon="🤝")
        with st.form("lead"):
            nombre = st.text_input("Nombre completo", p["nombre"])
            contacto = st.text_input("Teléfono o correo")
            horario = st.selectbox("Horario preferido", ["Mañana (9–12h)", "Tarde (12–17h)", "Noche (17–20h)"])
            medio = st.radio("¿Cómo prefieres la sesión?", ["Videollamada", "Llamada", "WhatsApp"], horizontal=True)
            enviar = st.form_submit_button("Conectar con mi estratega →", type="primary", width="stretch")
            if enviar:
                if not contacto.strip():
                    st.error("Necesito un teléfono o correo para conectarte.")
                else:
                    ss["lead_enviado"] = True
                    ss["lead"] = {"nombre": nombre, "contacto": contacto, "horario": horario, "medio": medio}
                    completar_mision("asesor")
                    st.rerun()
        st.caption(
            "En producción este lead viaja por API al CRM de GNP con el expediente completo, "
            "scoring de propensión y el producto de mayor afinidad ya priorizado."
        )
