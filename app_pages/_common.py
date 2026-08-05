"""Utilidades compartidas por las páginas: conexión, datos y scores cacheados."""

import streamlit as st

from brickbit import db, demo_data, scoring


@st.cache_resource
def conexion():
    conn = db.get_conn()
    demo_data.asegurar_datos(conn)
    return conn


def datos_scoreados():
    """Leads con score calculado. Se recalcula cuando cambia la versión de datos."""
    conn = conexion()
    version = st.session_state.get("version_datos", 0)
    return _scores_cacheados(version), conn


@st.cache_data
def _scores_cacheados(version: int):
    conn = conexion()
    leads = db.leads_df(conn)
    senales = db.senales_df(conn)
    return scoring.calcular_scores(leads, senales)


def invalidar_datos():
    st.session_state["version_datos"] = st.session_state.get("version_datos", 0) + 1


COLORES_PRIORIDAD = {"A": "🔴", "B": "🟡", "C": "⚪"}
