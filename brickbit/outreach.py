"""Generador de Muestreo Inverso: el mensaje que regala el resultado final.

Dos modos:
  1. Plantillas deterministas en español (siempre disponibles, cero costo).
  2. Refinado con Claude (opcional): si hay credenciales de la API de Anthropic,
     el borrador se reescribe hiper-personalizado. Incluye fallback del lado
     del servidor por defecto para que una negativa del clasificador se
     re-enrute automáticamente a otro modelo.
"""

from . import config

# ---------------------------------------------------------------------------
# Plantillas (modo sin IA)
# ---------------------------------------------------------------------------

_PLANTILLA_SEGUROS = """Asunto: {nombre}, detecté el momento exacto — {producto_label}

Hola {nombre},

No te escribo para venderte nada todavía. Mi sistema de señales detectó esto:

{senales_bullets}

Por eso preparé un análisis gratuito de tu situación: la cobertura de {producto_label} \
que personas en tu mismo momento suelen necesitar, cuánto cuesta realmente con GNP y \
qué pasa si esperas 6 meses más.

Te lo mando sin compromiso. Tengo además {n_similares} casos con este mismo perfil \
de urgencia en mi sistema, así que sé exactamente qué comparar.

¿Te parecen 10 minutos esta semana para revisarlo?

Saludos,
{firma}"""

_PLANTILLA_INMO = """Asunto: {nombre}, {zona} se está moviendo — y tú apareces en mis datos

Hola {nombre},

Mi plataforma monitorea el mercado inmobiliario de CDMX en tiempo real y tu perfil \
apareció por estas señales:

{senales_bullets}

Preparé un reporte gratuito de {zona}: precio por m², crecimiento de los últimos \
12 meses, inventario disponible y las 3 mejores oportunidades activas para un perfil \
como el tuyo ({producto_label}).

Es tuyo sin costo — el análisis ya está hecho. Tengo {n_similares} oportunidades más \
con esta misma ventana de tiempo en el sistema.

¿10 minutos esta semana para mostrártelo?

Saludos,
{firma}"""


def _bullets(senales_tipos: list[str]) -> str:
    lineas = []
    for t in senales_tipos:
        info = config.SENALES.get(t)
        if info:
            lineas.append(f"  • {info['label']}: {info['descripcion']}")
    return "\n".join(lineas) or "  • Señal de intención detectada en el mercado."


def generar_borrador(lead: dict, senales_tipos: list[str], firma: str = "El equipo BrickBit",
                     n_similares: int = 15) -> str:
    productos = {**config.PRODUCTOS_SEGUROS, **config.PRODUCTOS_INMO}
    plantilla = _PLANTILLA_SEGUROS if lead["vertical"] == "seguros" else _PLANTILLA_INMO
    return plantilla.format(
        nombre=lead["nombre"].split()[0],
        zona=lead.get("zona") or "tu zona",
        producto_label=productos.get(lead["producto"], lead["producto"]),
        senales_bullets=_bullets(senales_tipos),
        n_similares=n_similares,
        firma=firma,
    )


# ---------------------------------------------------------------------------
# Refinado con Claude (opcional)
# ---------------------------------------------------------------------------

def credenciales_disponibles() -> bool:
    import os
    return bool(os.environ.get("ANTHROPIC_API_KEY") or os.environ.get("ANTHROPIC_AUTH_TOKEN"))


_SYSTEM_REDACTOR = (
    "Eres el mejor redactor de outreach B2C/B2B en español de México. Reescribes "
    "borradores de primer contacto para que suenen humanos, específicos y breves "
    "(máximo 130 palabras de cuerpo). Reglas: nunca inventes datos que no estén en "
    "el borrador; conserva el asunto en una línea que empiece con 'Asunto:'; tono "
    "cálido y directo, sin clichés de venta ('oferta única', 'no te lo pierdas'); "
    "cierra siempre con una sola pregunta de bajo compromiso. Devuelve únicamente "
    "el correo final, sin explicaciones."
)


def refinar_con_claude(borrador: str, contexto_extra: str = "") -> tuple[bool, str]:
    """Reescribe el borrador con Claude. Devuelve (exito, texto_o_error)."""
    try:
        import anthropic
    except ImportError:
        return False, "El paquete 'anthropic' no está instalado (pip install anthropic)."

    prompt = f"Reescribe este borrador de primer contacto:\n\n{borrador}"
    if contexto_extra.strip():
        prompt += f"\n\nContexto adicional del vendedor (úsalo solo si aporta):\n{contexto_extra.strip()}"

    client = anthropic.Anthropic()
    try:
        response = client.beta.messages.create(
            model="claude-opus-5",
            max_tokens=2048,
            betas=["server-side-fallback-2026-07-01"],
            fallbacks="default",
            system=_SYSTEM_REDACTOR,
            messages=[{"role": "user", "content": prompt}],
        )
    except anthropic.AuthenticationError:
        return False, "Credenciales de la API de Anthropic inválidas."
    except anthropic.RateLimitError:
        return False, "Límite de peticiones alcanzado; intenta en un minuto."
    except anthropic.APIStatusError as e:
        return False, f"Error de la API ({e.status_code}): {e.message}"
    except anthropic.APIConnectionError:
        return False, "Sin conexión con la API de Anthropic."

    if response.stop_reason == "refusal":
        return False, "El modelo declinó la petición; usa el borrador de plantilla."

    texto = "".join(b.text for b in response.content if b.type == "text").strip()
    if not texto:
        return False, "La API no devolvió texto; usa el borrador de plantilla."
    return True, texto
