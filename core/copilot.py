"""Copiloto del Asesor: la misma IA, ahora del lado del estratega humano.

Scoring de propensión, puntos de charla rankeados por peso emocional,
manejo de objeciones con los números del propio prospecto, y guion de
llamada generado por LLM (si hay API key). En producción vive dentro del
CRM de GNP y escucha la llamada en vivo para sugerir en tiempo real.
"""

from __future__ import annotations

import streamlit as st

from core.advisor import _api_key
from core.risk import brechas_criticas


def propension(ss) -> tuple[int, list[str]]:
    """Score 0–100 de propensión a cierre + señales que lo explican."""
    score, senales = 5, []
    if ss.get("auditoria_completa"):
        score += 25
        senales.append("✅ Completó la auditoría con VIA (invirtió tiempo en su diagnóstico)")
    n_metas = len(ss.get("metas", []))
    if n_metas:
        score += min(n_metas * 10, 25)
        senales.append(f"🎯 Definió {n_metas} meta(s) de vida (compra emocional activada)")
    c = ss.get("cobertura", {})
    escudos = sum(1 for k in ("gmm", "vida", "retiro", "patrimonio") if c.get(k))
    if escudos:
        score += escudos * 6
        senales.append(f"⚡ Activó {escudos} escudo(s) en el simulador (ya se visualizó protegido)")
    pts = ss.get("puntos", 0)
    if pts >= 300:
        score += 10
        senales.append(f"🎮 {pts} Puntos Vitalidad (alta interacción con la plataforma)")
    if ss.get("lead_enviado"):
        score += 15
        senales.append("🤝 Pidió contacto humano (lead caliente)")
    if ss.get("pareja", {}).get("activo"):
        score += 8
        senales.append("👨‍👩‍👧 Fusionó gemelo familiar (decisión en pareja avanzada)")
    if ss.get("ledger"):
        senales.append("🔗 Acuñó certificados de destino (compromiso simbólico)")
    return min(score, 99), senales


def puntos_de_charla(perfil: dict, radar: dict, metas: list, res: dict) -> list[str]:
    """Argumentos rankeados: primero lo emocional, luego lo numérico."""
    puntos = []
    if metas:
        m = max(metas, key=lambda x: x["costo_futuro"])
        puntos.append(
            f"💛 **Abrir con su sueño mayor:** {m['icono']} «{m['nombre']}» ({m['anio_objetivo']}). "
            f"Costará ${m['costo_futuro']:,.0f}; su plan lo logra con ${m['aporte_mensual']:,.0f}/mes vía {m['producto']['nombre']}."
        )
    for dim, val in brechas_criticas(radar, 2):
        puntos.append(f"🔴 **Brecha crítica en {dim}** (protección al {val:.0f}%): usar el radar que él/ella misma generó.")
    if perfil["dependientes"]:
        puntos.append(
            f"👨‍👩‍👧 **{perfil['dependientes']} dependiente(s):** su protección familiar simulada es del "
            f"{res['proteccion_familiar']*100:.0f}%. Preguntar: «¿qué pasa con ellos el día 31 del mes uno?»"
        )
    puntos.append(
        f"📉 **Su probabilidad de quiebra pre-retiro simulada es {res['prob_ruina']*100:.1f}%** — "
        "mostrar cómo cambia el cono del Gemelo Digital al activar escudos (ya lo vio, repetirlo en vivo)."
    )
    puntos.append(
        f"⏳ **Urgencia honesta:** cada año de espera sube la prima por edad y la inflación médica (11.5%) "
        "encarece el riesgo. El mejor momento fue ayer; el segundo mejor es esta llamada."
    )
    return puntos


def objeciones(res: dict, prima_total: float) -> list[tuple[str, str]]:
    return [
        ("«Está caro»",
         f"Su propio simulador mostró un gasto médico de bolsillo esperado de ${res['gasto_medico_promedio']:,.0f} "
         f"sin seguro. La prima (~${prima_total:,.0f}/mes) es el {prima_total/max(res['gasto_medico_promedio'],1)*100*12:.1f}% "
         "anualizado de ese riesgo — y congela el costo a su edad actual."),
        ("«Lo veo después»",
         "Reproducir su simulación con edad +5: la prima sube y la meta educativa se encarece 48%. "
         "El costo de 'después' está calculado en su propio expediente."),
        ("«Ya tengo el del trabajo»",
         "El seguro colectivo muere con el empleo y promedia sumas de 1-2 años de sueldo. Su brecha familiar "
         "simulada necesita más — y su plan personal lo acompaña aunque cambie de trabajo."),
        ("«No creo en los seguros»",
         "Válido — por eso la plataforma no le vendió: le mostró 10,000 versiones de su futuro con datos. "
         "La pregunta no es creer en seguros, es en cuál de sus 10,000 futuros quiere vivir."),
    ]


def guion_llamada_llm(perfil: dict, radar: dict, metas: list, res: dict) -> str | None:
    """Guion personalizado vía Claude (si hay API key); None si no disponible."""
    key = _api_key()
    if not key:
        return None
    try:
        import anthropic
        client = anthropic.Anthropic(api_key=key)
        contexto = {
            "perfil": {k: v for k, v in perfil.items() if k != "perfil_completo"},
            "radar": radar,
            "metas": [{"nombre": m["nombre"], "anio": m["anio_objetivo"], "costo": m["costo_futuro"]} for m in metas],
            "prob_ruina": res["prob_ruina"],
            "proteccion_familiar": res["proteccion_familiar"],
        }
        msg = client.messages.create(
            model="claude-sonnet-5",
            max_tokens=700,
            system=(
                "Eres coach de ventas consultivas de seguros GNP. Genera un guion de llamada de cierre "
                "de 5 pasos, empático y cero invasivo, usando los datos del prospecto. Español mexicano, "
                "formato markdown con los 5 pasos numerados. No inventes precios."
            ),
            messages=[{"role": "user", "content": f"Datos del prospecto: {contexto}"}],
        )
        return msg.content[0].text
    except Exception:
        return None


DEMO_LEADS = [
    {"nombre": "Mariana T.", "edad": 29, "propension": 84, "etapa": "Mapa de sueños completo", "prioridad": "Educación"},
    {"nombre": "Ricardo V.", "edad": 41, "propension": 67, "etapa": "Simulación con 2 escudos", "prioridad": "Familia"},
    {"nombre": "Paola G.", "edad": 35, "propension": 52, "etapa": "Auditoría completa", "prioridad": "Retiro"},
]
