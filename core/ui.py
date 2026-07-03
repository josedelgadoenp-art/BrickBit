"""Identidad visual y componentes gráficos de alto impacto (Plotly)."""

from __future__ import annotations

import plotly.graph_objects as go
import streamlit as st

NARANJA = "#FF6900"      # naranja GNP
NARANJA_SUAVE = "#FFA45C"
AZUL_FONDO = "#0B0F1A"
PANEL = "rgba(255,255,255,0.045)"
VERDE = "#22c55e"
ROJO = "#ef4444"
TEXTO_SUAVE = "#9AA4B8"

_CSS = """
<style>
  .stApp { background: radial-gradient(1200px 600px at 15% -10%, rgba(255,105,0,.14), transparent 60%),
                       radial-gradient(1000px 500px at 110% 10%, rgba(56,120,255,.10), transparent 55%),
                       #0B0F1A; }
  h1, h2, h3 { letter-spacing: -0.5px; }
  .via-hero {
    background: linear-gradient(135deg, rgba(255,105,0,.16), rgba(255,105,0,.03) 55%);
    border: 1px solid rgba(255,105,0,.35);
    border-radius: 20px; padding: 26px 30px; margin-bottom: 8px;
  }
  .via-hero h1 { margin: 0 0 6px 0; font-size: 2.1rem;
    background: linear-gradient(90deg, #fff, #FFA45C); -webkit-background-clip: text;
    -webkit-text-fill-color: transparent; }
  .via-hero p { color: #C9D2E3; margin: 0; font-size: 1.02rem; }
  .via-card {
    background: rgba(255,255,255,0.045); border: 1px solid rgba(255,255,255,0.09);
    border-radius: 16px; padding: 18px 20px; height: 100%;
  }
  .via-card h4 { margin: 0 0 6px 0; }
  .via-card p { color: #9AA4B8; font-size: .9rem; margin: 0; }
  .via-chip {
    display: inline-block; padding: 3px 12px; border-radius: 999px; font-size: .78rem;
    background: rgba(255,105,0,.15); border: 1px solid rgba(255,105,0,.4); color: #FFB27A;
    margin-right: 6px; margin-bottom: 6px;
  }
  .via-kpi { font-size: 1.9rem; font-weight: 800; }
  .via-kpi-label { color: #9AA4B8; font-size: .82rem; text-transform: uppercase; letter-spacing: 1px; }
  .via-avatar {
    font-size: 4.2rem; text-align: center; filter: drop-shadow(0 0 18px rgba(255,105,0,.45));
    animation: pulso 2.6s ease-in-out infinite;
  }
  @keyframes pulso { 0%,100% { transform: scale(1); } 50% { transform: scale(1.07); } }
  div[data-testid="stMetric"] {
    background: rgba(255,255,255,0.045); border: 1px solid rgba(255,255,255,0.09);
    border-radius: 14px; padding: 12px 16px;
  }
</style>
"""


def aplicar_estilo() -> None:
    st.markdown(_CSS, unsafe_allow_html=True)


def hero(titulo: str, subtitulo: str) -> None:
    st.markdown(
        f'<div class="via-hero"><h1>{titulo}</h1><p>{subtitulo}</p></div>',
        unsafe_allow_html=True,
    )


def tarjeta(titulo: str, cuerpo: str, icono: str = "") -> None:
    st.markdown(
        f'<div class="via-card"><h4>{icono} {titulo}</h4><p>{cuerpo}</p></div>',
        unsafe_allow_html=True,
    )


def _base_layout(fig: go.Figure, altura: int = 380) -> go.Figure:
    fig.update_layout(
        template="plotly_dark",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        height=altura,
        margin=dict(l=10, r=10, t=40, b=10),
        font=dict(family="sans-serif", color="#E8EDF6"),
        legend=dict(orientation="h", y=1.08, x=0),
    )
    return fig


def grafico_abanico(res_sin: dict, res_con: dict | None, edad_retiro: int) -> go.Figure:
    """Fan chart del patrimonio: cono de incertidumbre sin/con protección GNP."""
    fig = go.Figure()
    edades = res_sin["edades"]

    def _cono(res, color_linea, color_relleno, nombre):
        p = res["percentiles"]
        fig.add_trace(go.Scatter(x=edades, y=p[90], line=dict(width=0), showlegend=False, hoverinfo="skip"))
        fig.add_trace(go.Scatter(
            x=edades, y=p[10], fill="tonexty", fillcolor=color_relleno,
            line=dict(width=0), name=f"{nombre} (p10–p90)", hoverinfo="skip",
        ))
        fig.add_trace(go.Scatter(
            x=edades, y=p[50], line=dict(color=color_linea, width=3.2), name=f"{nombre} (mediana)",
            hovertemplate="Edad %{x} · $%{y:,.0f}<extra></extra>",
        ))

    _cono(res_sin, "#8B93A7", "rgba(139,147,167,0.16)", "Sin protección")
    if res_con is not None:
        _cono(res_con, NARANJA, "rgba(255,105,0,0.18)", "Con GNP")

    fig.add_vline(x=edad_retiro, line_dash="dot", line_color="#5B6B8C")
    fig.add_annotation(x=edad_retiro, y=1, yref="paper", text="Retiro", showarrow=False,
                       font=dict(color="#8B93A7", size=11), yshift=8)
    fig.add_hline(y=0, line_color="rgba(239,68,68,.5)", line_width=1)
    fig.update_layout(title="10,000 futuros posibles de tu patrimonio",
                      xaxis_title="Edad", yaxis_title="Patrimonio (MXN)")
    return _base_layout(fig, 430)


def gauge_estabilidad(valor: float, titulo: str = "Índice de Estabilidad Vital") -> go.Figure:
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=round(valor),
        title={"text": titulo, "font": {"size": 15, "color": TEXTO_SUAVE}},
        number={"suffix": " /100", "font": {"size": 42}},
        gauge=dict(
            axis=dict(range=[0, 100], tickcolor="#5B6B8C"),
            bar=dict(color=NARANJA, thickness=0.28),
            bgcolor="rgba(255,255,255,0.05)",
            borderwidth=0,
            steps=[
                dict(range=[0, 35], color="rgba(239,68,68,.25)"),
                dict(range=[35, 65], color="rgba(245,158,11,.22)"),
                dict(range=[65, 100], color="rgba(34,197,94,.22)"),
            ],
        ),
    ))
    return _base_layout(fig, 260)


def radar_chart(radar: dict, radar_previo: dict | None = None) -> go.Figure:
    dims = list(radar.keys())
    fig = go.Figure()
    if radar_previo:
        fig.add_trace(go.Scatterpolar(
            r=[radar_previo[d] for d in dims] + [radar_previo[dims[0]]],
            theta=dims + [dims[0]], fill="toself", name="Antes",
            line=dict(color="#8B93A7"), fillcolor="rgba(139,147,167,.15)",
        ))
    fig.add_trace(go.Scatterpolar(
        r=[radar[d] for d in dims] + [radar[dims[0]]],
        theta=dims + [dims[0]], fill="toself", name="Tu protección hoy",
        line=dict(color=NARANJA, width=2.5), fillcolor="rgba(255,105,0,.22)",
    ))
    fig.update_layout(polar=dict(
        bgcolor="rgba(0,0,0,0)",
        radialaxis=dict(range=[0, 100], showticklabels=False, gridcolor="rgba(255,255,255,.12)"),
        angularaxis=dict(gridcolor="rgba(255,255,255,.12)"),
    ))
    return _base_layout(fig, 380)


def timeline_metas(metas: list, edad: int) -> go.Figure:
    """Línea de vida interactiva con las metas como hitos."""
    import datetime
    anio_hoy = datetime.date.today().year
    fig = go.Figure()
    if metas:
        xs = [m["anio_objetivo"] for m in metas]
        ys = [m["costo_futuro"] for m in metas]
        textos = [f"{m['icono']} {m['nombre']}" for m in metas]
        colores = [VERDE if m.get("financiada") else NARANJA for m in metas]
        fig.add_trace(go.Scatter(
            x=xs, y=ys, mode="markers+text", text=textos, textposition="top center",
            marker=dict(size=[max(18, min(46, v / 200_000)) for v in ys],
                        color=colores, opacity=.9, line=dict(color="white", width=1)),
            hovertemplate="%{text}<br>Año %{x} · Costo futuro $%{y:,.0f}<extra></extra>",
            name="Metas",
        ))
    fig.add_vline(x=anio_hoy, line_dash="dot", line_color="#5B6B8C")
    fig.add_annotation(x=anio_hoy, y=1, yref="paper", text=f"Hoy ({edad} años)",
                       showarrow=False, font=dict(color="#8B93A7", size=11), yshift=10)
    fig.update_layout(title="Tu línea de vida", xaxis_title="Año",
                      yaxis_title="Costo futuro indexado (MXN)")
    return _base_layout(fig, 400)


def dinero(v: float) -> str:
    if abs(v) >= 1_000_000:
        return f"${v/1_000_000:,.1f} M"
    return f"${v:,.0f}"
