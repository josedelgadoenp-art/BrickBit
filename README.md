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

## Ejecutar

```bash
pip install -r requirements.txt
streamlit run streamlit_app.py
```

Opcional — modo IA aumentada: define `ANTHROPIC_API_KEY` en el entorno o en
`.streamlit/secrets.toml` para que VIA responda consultas libres con Claude.

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
  ui.py               # identidad visual + gráficos Plotly de alto impacto
views/                # las 6 pantallas de la experiencia
```

> ⚠️ **Demo conceptual.** Parámetros actuariales, primas y productos son ilustrativos y no
> constituyen cotización ni oferta de GNP Seguros. Para producción se conectaría vía API a los
> sistemas de tarificación de GNP (arquitectura de microservicios) y al CRM para el handoff.
