# 🧬 GNP LifeOS — El Sistema Operativo de tu Vida

Plataforma disruptiva de venta consultiva de seguros para **GNP** que abandona el cotizador
tradicional y lo reemplaza por una **experiencia de simulación hiperpersonalizada, predictiva
y gamificada**. Unifica en un solo producto tres conceptos:

| Módulo | Concepto original | Qué hace |
|---|---|---|
| 🔍 **Auditoría con VIA** | Asistente de riesgo en tiempo real | Agente conversacional de IA que detecta puntos ciegos financieros en 3 minutos de charla natural (sin formularios). Con `ANTHROPIC_API_KEY` opcional, responde consultas libres con un LLM. |
| 🧬 **Gemelo Digital** | Digital Twin financiero y de longevidad | Motor **Monte Carlo de 10,000 simulaciones** (mortalidad Gompertz, inflación médica 11.5%, siniestralidad por zona, invalidez, desempleo). Activa "escudos GNP" y mira el cono de incertidumbre estabilizarse en tiempo real. |
| 🎯 **Metas de Vida** | Marketplace de proyectos de vida | Sueños en una línea de tiempo interactiva con costo **indexado a inflación futura** (educativa 8.2%, médica 11.5%, FX) y la mezcla protección + ahorro GNP para garantizarlos. |
| ⚡ **Consola de Vida** | Seguro proactivo 24/7 | Radar de Vulnerabilidad en vivo, alertas preventivas por zona y **gamificación** (Puntos Vitalidad → reducción de deducibles). |
| 🤝 **Copiloto Humano** | Asesoría automatizada + cierre humano | Handoff del expediente completo (mapa de sueños, radar, guion sugerido) al asesor GNP para una llamada 100% estratégica. |
| 🪞 **Modo Espejo** | Economía del comportamiento | Sube tu foto y conoce a tus dos «yo» del futuro: el blindado y el expuesto (estilización local simbólica; producción: modelo generativo con consentimiento). Dentro del Gemelo Digital. |
| 💓 **Prima Viva** | Suscripción dinámica | La prima baja mes a mes con hábitos verificados (wearables/telemática simulados) hasta -25%, con proyección a 12 meses vs. seguro fijo. Dentro de la Consola. |
| 👨‍👩‍👧 **Gemelo Familiar** | Hogar completo | Fusiona dos gemelos digitales, simula el hogar y ejecuta el **análisis de supervivencia cruzado** con suma asegurada sugerida por miembro. |
| 🌊 **Momentos de Vida** | Re-simulación proactiva | Declara eventos (bebé, ascenso, mudanza, recorte…) y el gemelo se re-simula mostrando el antes/después del radar. Dentro de la Consola. |
| 🔗 **Certificados de Destino** | Logros verificables | Cada meta 100% financiada acuña un certificado encadenado por SHA-256 (mini-blockchain de sesión, verificable y descargable). Dentro de Metas. |
| 🧑‍💼 **Modo Asesor** | Copiloto del vendedor | Pipeline con scoring de propensión, señales de compra, argumentos rankeados por peso emocional, manejo de objeciones con los números del prospecto y guion de llamada (LLM opcional). |

## Ejecutar

```bash
pip install -r requirements.txt
streamlit run streamlit_app.py
```

Opcional — modo IA aumentada: define `ANTHROPIC_API_KEY` en el entorno o en
`.streamlit/secrets.toml` para que VIA responda consultas libres con Claude.

## 🎙️ Extensión de Chrome: Copiloto de Videollamada

En [`extension/`](extension/README.md) vive el **Copiloto GNP para videollamadas**: una
extensión de Chrome (panel lateral) que guía la llamada de venta con 10 preguntas de
descubrimiento, transcribe en vivo (es-MX), y al terminar genera con Claude una asesoría
personalizada —análisis financiero, producto GNP ideal o combinación, y presupuesto
sugerido presentado **por quincena**— exportable a **PDF**. Ver instrucciones de
instalación y uso en su [README](extension/README.md).

## Arquitectura

```
streamlit_app.py      # entrada, navegación, tema
core/
  state.py            # estado de sesión (perfil, cobertura, metas, puntos)
  simulator.py        # motor Monte Carlo del Gemelo Digital
  risk.py             # Radar de Vulnerabilidad y Score de Blindaje (0-1000)
  goals.py            # metas indexadas a inflación + PMT requerido
  products.py         # catálogo GNP referencial + recomendador
  advisor.py          # VIA: NLU en español + LLM opcional (Anthropic)
  gamification.py     # Puntos Vitalidad, niveles, misiones, insignias
  mirror.py           # Modo Espejo: estilización de tus dos «yo» futuros
  pulse.py            # Prima Viva: prima dinámica por hábitos verificados
  family.py           # Gemelo Familiar: hogar fusionado + supervivencia cruzada
  moments.py          # Momentos de Vida: eventos que re-simulan el gemelo
  ledger.py           # Certificados de Destino: hash-chain SHA-256 de metas
  copilot.py          # Copiloto del Asesor: propensión, argumentos, objeciones
  ui.py               # identidad visual + gráficos Plotly de alto impacto
views/                # las 8 pantallas de la experiencia
```

> ⚠️ **Demo conceptual.** Parámetros actuariales, primas y productos son ilustrativos y no
> constituyen cotización ni oferta de GNP Seguros. Para producción se conectaría vía API a los
> sistemas de tarificación de GNP (arquitectura de microservicios) y al CRM para el handoff.
