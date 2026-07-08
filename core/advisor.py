"""VIA — Vida Inteligente Asistida.

Agente conversacional que realiza la Auditoría de Vulnerabilidad en ~3 minutos.
Funciona 100% offline con NLU ligero (regex + heurísticas en español) y, si
existe ANTHROPIC_API_KEY en secrets/entorno, eleva las respuestas con un LLM
de Anthropic para un tono de estratega financiero humano.
"""

from __future__ import annotations

import os
import re

from core.state import ZONAS

# ---------------------------------------------------------------------------
# Flujo de la entrevista
# ---------------------------------------------------------------------------
PASOS = [
    "nombre", "edad", "zona", "dependientes", "ingreso",
    "gastos", "ahorro", "fumador", "ejercicio", "salud", "prioridad",
]

PREGUNTAS = {
    "nombre": "Hola 👋 Soy **VIA**, tu estratega de vida de GNP. En 3 minutos voy a detectar tus puntos ciegos financieros y de protección. Empecemos por lo importante: ¿cómo te llamas?",
    "edad": "Un gusto, **{nombre}**. ¿Cuántos años tienes? La edad define cuánto tiempo trabaja el interés compuesto a tu favor.",
    "zona": "¿En qué zona del país vives? (por ejemplo: CDMX, Guadalajara, Monterrey, Bajío, Sureste, Norte…) Cruzo datos de siniestralidad por región.",
    "dependientes": "¿Cuántas personas dependen económicamente de ti? (hijos, pareja, padres…) Escribe un número.",
    "ingreso": "Hablemos de flujo. ¿Cuál es tu ingreso mensual aproximado? Puedes escribir «35 mil», «35k» o «35,000» — todo queda entre nosotros.",
    "gastos": "¿Y cuánto gastas al mes, más o menos? Esto define tu capacidad real de blindaje.",
    "ahorro": "¿Cuánto tienes ahorrado o invertido hoy en total? (aproximado, en pesos)",
    "fumador": "Ahora tu biología, que es tu primer activo: ¿fumas? (sí / no)",
    "ejercicio": "¿Con qué frecuencia haces ejercicio? (nunca / ocasional / regular / intenso)",
    "salud": "En general, ¿cómo describirías tu salud hoy? (excelente / buena / regular / delicada)",
    "prioridad": "Última y la más importante: si solo pudieras blindar UNA cosa, ¿cuál sería? (familia / patrimonio / retiro / salud / equilibrio)",
}

ACKS = {
    "edad": "Perfecto. A los {valor} años, cada peso que proteges hoy vale varias veces más en tu futuro.",
    "zona": "Anotado: **{valor}**. Ya estoy cruzando la siniestralidad y costos médicos de tu región. 📡",
    "dependientes": "Entendido — {valor} persona(s) cuentan contigo. Eso convierte tu protección en algo no negociable.",
    "ingreso": "Bien. Con ${valor:,.0f} al mes, tu ingreso futuro proyectado supera los ${proyeccion:,.0f}: ese es el activo que hay que asegurar.",
    "gastos": "Registrado: ${valor:,.0f} mensuales. Tu margen de maniobra ya está en mi modelo.",
    "ahorro": "${valor:,.0f} de patrimonio inicial. Veamos qué tan resistente es ante 10,000 futuros posibles.",
    "fumador_si": "Gracias por la honestidad. Lo integro al modelo de riesgo — y te adelanto: dejarlo es la póliza más barata que existe. 🚭",
    "fumador_no": "Excelente. Tu perfil biológico suma puntos a tu favor. ✅",
    "ejercicio": "Registrado: ejercicio **{valor}**. Tu cuerpo es la primera línea de defensa de tu patrimonio.",
    "salud": "Anotado: salud **{valor}**. Con esto calibro tu curva de riesgo médico.",
    "prioridad": "**{valor}** será el eje de tu estrategia. Dame un segundo… ⚙️ Ejecutando diagnóstico multicapa…",
}

_ZONA_KEYWORDS = {
    "cdmx": ZONAS[0], "ciudad de mexico": ZONAS[0], "df": ZONAS[0], "metropolitana": ZONAS[0],
    "edomex": ZONAS[0], "guadalajara": ZONAS[1], "gdl": ZONAS[1], "jalisco": ZONAS[1],
    "monterrey": ZONAS[2], "mty": ZONAS[2], "nuevo leon": ZONAS[2],
    "queretaro": ZONAS[3], "leon": ZONAS[3], "bajio": ZONAS[3], "san luis": ZONAS[3], "slp": ZONAS[3],
    "aguascalientes": ZONAS[3], "merida": ZONAS[4], "cancun": ZONAS[4], "sureste": ZONAS[4],
    "yucatan": ZONAS[4], "quintana roo": ZONAS[4], "veracruz": ZONAS[4], "oaxaca": ZONAS[4],
    "chihuahua": ZONAS[5], "hermosillo": ZONAS[5], "norte": ZONAS[5], "tijuana": ZONAS[5],
    "sonora": ZONAS[5], "rural": ZONAS[7], "pueblo": ZONAS[7], "rancho": ZONAS[7],
}

_PRIORIDADES = {
    "familia": "Familia", "hijos": "Familia", "esposa": "Familia", "esposo": "Familia",
    "patrimonio": "Patrimonio", "casa": "Patrimonio", "dinero": "Patrimonio",
    "retiro": "Retiro", "pension": "Retiro", "jubil": "Retiro",
    "salud": "Salud", "medic": "Salud",
    "equilibrio": "Equilibrio", "todo": "Equilibrio", "balance": "Equilibrio",
}


def _parse_numero(texto: str) -> float | None:
    """Interpreta «35 mil», «1.2 millones», «35k», «35,000», «$35000»."""
    t = texto.lower().replace("$", "").replace(",", "").strip()
    m = re.search(r"(\d+(?:\.\d+)?)", t)
    if not m:
        return None
    val = float(m.group(1))
    if re.search(r"millon|mdp|\bm\b", t):
        val *= 1_000_000
    elif re.search(r"mil\b|k\b", t):
        val *= 1_000
    return val


def _parse_zona(texto: str) -> str:
    t = texto.lower()
    t = t.translate(str.maketrans("áéíóúü", "aeiouu"))
    for kw, zona in _ZONA_KEYWORDS.items():
        if kw in t:
            return zona
    return "Otra ciudad media"


def procesar_respuesta(paso_key: str, texto: str, perfil: dict) -> tuple[bool, str]:
    """Aplica la respuesta al perfil. Devuelve (ok, mensaje_de_VIA)."""
    t = texto.strip()
    tl = t.lower()

    if paso_key == "nombre":
        nombre = re.sub(r"(?i)^(hola,?\s*)?(me llamo|soy|mi nombre es)\s*", "", t).strip().split(",")[0]
        perfil["nombre"] = (nombre.title() or "Explorador")[:40]
        return True, ""

    if paso_key == "edad":
        n = _parse_numero(t)
        if n is None or not (16 <= n <= 85):
            return False, "Necesito una edad entre 16 y 85 años para calibrar el modelo. ¿Cuántos años tienes?"
        perfil["edad"] = int(n)
        perfil["edad_retiro"] = max(perfil["edad"] + 5, 65) if perfil["edad"] > 60 else 65
        return True, ACKS["edad"].format(valor=int(n))

    if paso_key == "zona":
        perfil["zona"] = _parse_zona(t)
        return True, ACKS["zona"].format(valor=perfil["zona"])

    if paso_key == "dependientes":
        n = _parse_numero(t)
        if any(w in tl for w in ("ningun", "nadie", "cero", "no ")) or tl == "no":
            n = 0
        if n is None or n < 0 or n > 15:
            return False, "¿Cuántas personas dependen de ti? Un número del 0 al 15 me basta."
        perfil["dependientes"] = int(n)
        if n == 0:
            return True, "Sin dependientes por ahora — tu estrategia puede ser más agresiva en crecimiento. 🚀"
        return True, ACKS["dependientes"].format(valor=int(n))

    if paso_key in ("ingreso", "gastos", "ahorro"):
        n = _parse_numero(t)
        if paso_key == "ahorro" and (n is None) and any(w in tl for w in ("nada", "cero", "no tengo")):
            n = 0.0
        if n is None or n < 0:
            return False, "No logré leer la cifra 😅. Escríbela como «35 mil», «35k» o «35,000»."
        if paso_key == "ingreso":
            if n < 1000:
                return False, "Esa cifra parece muy baja para un ingreso mensual. ¿Puedes confirmarla en pesos?"
            perfil["ingreso_mensual"] = n
            anios = max(perfil["edad_retiro"] - perfil["edad"], 1)
            return True, ACKS["ingreso"].format(valor=n, proyeccion=n * 12 * anios)
        if paso_key == "gastos":
            perfil["gastos_mensuales"] = n
            perfil["ahorro_mensual"] = max((perfil["ingreso_mensual"] - n) * 0.4, 0)
            return True, ACKS["gastos"].format(valor=n)
        perfil["ahorro_actual"] = n
        return True, ACKS["ahorro"].format(valor=n)

    if paso_key == "fumador":
        if any(w in tl for w in ("no", "nunca", "jamas", "jamás", "dejé", "deje")):
            perfil["fumador"] = False
            return True, ACKS["fumador_no"]
        if any(w in tl for w in ("si", "sí", "socialmente", "a veces", "poco", "ocasional")):
            perfil["fumador"] = True
            return True, ACKS["fumador_si"]
        return False, "¿Fumas actualmente? Con un «sí» o «no» me basta."

    if paso_key == "ejercicio":
        opciones = {"nunca": "Nunca", "sedentari": "Nunca", "ocasional": "Ocasional", "a veces": "Ocasional",
                    "poco": "Ocasional", "regular": "Regular", "3 veces": "Regular", "diario": "Intenso",
                    "intens": "Intenso", "gym": "Regular", "corro": "Regular", "mucho": "Intenso"}
        for kw, v in opciones.items():
            if kw in tl:
                perfil["ejercicio"] = v
                return True, ACKS["ejercicio"].format(valor=v.lower())
        return False, "¿Dirías que haces ejercicio nunca, ocasional, regular o intenso?"

    if paso_key == "salud":
        opciones = {"excelente": "Excelente", "muy buena": "Excelente", "buena": "Buena", "bien": "Buena",
                    "normal": "Buena", "regular": "Regular", "mas o menos": "Regular", "más o menos": "Regular",
                    "delicada": "Delicada", "mala": "Delicada", "enferm": "Delicada"}
        for kw, v in opciones.items():
            if kw in tl:
                perfil["salud_general"] = v
                return True, ACKS["salud"].format(valor=v.lower())
        return False, "¿Cómo describirías tu salud: excelente, buena, regular o delicada?"

    if paso_key == "prioridad":
        for kw, v in _PRIORIDADES.items():
            if kw in tl:
                perfil["prioridad"] = v
                perfil["perfil_completo"] = True
                return True, ACKS["prioridad"].format(valor=v)
        return False, "¿Qué blindarías primero: familia, patrimonio, retiro, salud… o buscas equilibrio?"

    return False, "No entendí, ¿puedes reformular?"


def pregunta_de(paso_idx: int, perfil: dict) -> str | None:
    if paso_idx >= len(PASOS):
        return None
    return PREGUNTAS[PASOS[paso_idx]].format(**{"nombre": perfil.get("nombre") or "amig@"})


def diagnostico_final(perfil: dict, radar: dict, score: int) -> str:
    """Mensaje de cierre de la auditoría con hallazgos accionables."""
    peores = sorted(radar.items(), key=lambda kv: kv[1])[:2]
    lineas = [
        f"### 🔬 Diagnóstico listo, {perfil['nombre']}",
        f"Analicé tu perfil contra datos de siniestralidad regional, inflación médica (~11.5% anual) y curvas de longevidad. Tu **Score de Blindaje es {score}/1000**.",
        "",
        "**Tus 2 puntos ciegos más críticos:**",
    ]
    for dim, val in peores:
        lineas.append(f"- **{dim}** — protección al {val:.0f}%. " + _insight(dim, perfil))
    lineas += [
        "",
        "👉 Ve al **🧬 Gemelo Digital** para ver estas vulnerabilidades en 10,000 simulaciones de tu vida, o al **🎯 Metas de Vida** para diseñar tu plan.",
    ]
    return "\n".join(lineas)


def _insight(dim: str, perfil: dict) -> str:
    dep = perfil["dependientes"]
    insights = {
        "Salud": "Un solo evento médico mayor sin seguro promedia cifras de 6 dígitos, y la inflación médica lo duplica cada ~6 años.",
        "Vida / Familia": f"Si tú faltas, {dep or 'tu familia'} necesitaría ~5 años de gastos cubiertos; hoy hay una brecha importante." if dep else "Aún sin dependientes, una cobertura temprana congela un costo bajísimo de por vida.",
        "Retiro": "Cada año que pospones tu plan de retiro encarece ~12% el aporte mensual necesario para la misma pensión.",
        "Educación": "La inflación educativa (~8.2%) hace que una carrera duplique su costo cada ~9 años.",
        "Patrimonio": "Tu zona presenta siniestralidad por encima de la media nacional; tus bienes están expuestos.",
        "Liquidez": "Tu fondo de emergencia cubre menos de lo recomendado (6 meses de gastos): cualquier imprevisto te obligaría a malbaratar activos o endeudarte.",
    }
    return insights.get(dim, "")


# ---------------------------------------------------------------------------
# Elevación opcional con LLM (Anthropic) — la app funciona sin esto
# ---------------------------------------------------------------------------
def _api_key() -> str | None:
    try:
        import streamlit as st
        if "ANTHROPIC_API_KEY" in st.secrets:
            return st.secrets["ANTHROPIC_API_KEY"]
    except Exception:
        pass
    return os.environ.get("ANTHROPIC_API_KEY")


def llm_disponible() -> bool:
    return _api_key() is not None


def responder_libre(pregunta_usuario: str, perfil: dict, radar: dict | None) -> str:
    """Modo consulta libre post-auditoría. Usa LLM si hay API key."""
    key = _api_key()
    if key:
        try:
            import anthropic
            client = anthropic.Anthropic(api_key=key)
            contexto = f"Perfil: {perfil}. Radar de protección: {radar}."
            msg = client.messages.create(
                model="claude-sonnet-5",
                max_tokens=400,
                system=(
                    "Eres VIA, estratega financiera de GNP Seguros en México. Responde en español, "
                    "cálida, directa y experta, en máximo 120 palabras. Usa el contexto del cliente. "
                    "Orienta hacia protección y ahorro GNP sin inventar precios ni condiciones."
                ),
                messages=[{"role": "user", "content": f"{contexto}\n\nPregunta del cliente: {pregunta_usuario}"}],
            )
            return msg.content[0].text
        except Exception:
            pass
    return (
        "Buena pregunta. Con tu perfil actual, mi recomendación es revisar primero tus brechas en el "
        "**Radar de Vulnerabilidad** y simular el impacto en tu **Gemelo Digital**. Si quieres una "
        "respuesta a fondo, conecta con tu copiloto humano en la sección **🤝 Asesor**."
    )
