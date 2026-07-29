"""Persistencia SQLite: leads, señales, capturas de la herramienta gratuita y reuniones."""

import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent.parent / "data" / "brickbit.db"

_SCHEMA = """
CREATE TABLE IF NOT EXISTS leads (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre TEXT NOT NULL,
    empresa TEXT,
    cargo TEXT,
    vertical TEXT NOT NULL,
    producto TEXT NOT NULL,
    zona TEXT,
    email TEXT,
    telefono TEXT,
    fit_score REAL NOT NULL DEFAULT 50,
    etapa TEXT NOT NULL DEFAULT 'nuevo',
    fuente TEXT,
    notas TEXT,
    creado TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS senales (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    lead_id INTEGER NOT NULL REFERENCES leads(id) ON DELETE CASCADE,
    tipo TEXT NOT NULL,
    detalle TEXT,
    fecha TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS capturas (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre TEXT NOT NULL,
    email TEXT NOT NULL,
    interes TEXT,
    zona TEXT,
    fecha TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS reuniones (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    lead_id INTEGER NOT NULL REFERENCES leads(id) ON DELETE CASCADE,
    fecha TEXT NOT NULL,
    estado TEXT NOT NULL DEFAULT 'agendada',
    valor_estimado REAL DEFAULT 0,
    notas TEXT
);

CREATE INDEX IF NOT EXISTS idx_senales_lead ON senales(lead_id);
CREATE INDEX IF NOT EXISTS idx_leads_etapa ON leads(etapa);
"""


def get_conn() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    conn.executescript(_SCHEMA)
    return conn


def esta_vacia(conn: sqlite3.Connection) -> bool:
    return conn.execute("SELECT COUNT(*) FROM leads").fetchone()[0] == 0


# ---------------------------------------------------------------------------
# Escrituras
# ---------------------------------------------------------------------------

def insertar_lead(conn, **campos) -> int:
    cols = ", ".join(campos)
    marks = ", ".join("?" for _ in campos)
    cur = conn.execute(f"INSERT INTO leads ({cols}) VALUES ({marks})", list(campos.values()))
    conn.commit()
    return cur.lastrowid


def insertar_senal(conn, lead_id: int, tipo: str, detalle: str = "", fecha: str | None = None):
    if fecha:
        conn.execute(
            "INSERT INTO senales (lead_id, tipo, detalle, fecha) VALUES (?, ?, ?, ?)",
            (lead_id, tipo, detalle, fecha),
        )
    else:
        conn.execute(
            "INSERT INTO senales (lead_id, tipo, detalle) VALUES (?, ?, ?)",
            (lead_id, tipo, detalle),
        )
    conn.commit()


def registrar_captura(conn, nombre: str, email: str, interes: str, zona: str):
    conn.execute(
        "INSERT INTO capturas (nombre, email, interes, zona) VALUES (?, ?, ?, ?)",
        (nombre, email, interes, zona),
    )
    conn.commit()


def actualizar_etapa(conn, lead_id: int, etapa: str):
    conn.execute("UPDATE leads SET etapa = ? WHERE id = ?", (etapa, lead_id))
    conn.commit()


def agendar_reunion(conn, lead_id: int, fecha: str, valor_estimado: float, notas: str = ""):
    conn.execute(
        "INSERT INTO reuniones (lead_id, fecha, valor_estimado, notas) VALUES (?, ?, ?, ?)",
        (lead_id, fecha, valor_estimado, notas),
    )
    conn.execute("UPDATE leads SET etapa = 'cita_agendada' WHERE id = ?", (lead_id,))
    conn.commit()


# ---------------------------------------------------------------------------
# Lecturas
# ---------------------------------------------------------------------------

def leads_df(conn):
    import pandas as pd
    return pd.read_sql_query("SELECT * FROM leads", conn)


def senales_df(conn):
    import pandas as pd
    return pd.read_sql_query("SELECT * FROM senales", conn)


def capturas_df(conn):
    import pandas as pd
    return pd.read_sql_query("SELECT * FROM capturas ORDER BY fecha DESC", conn)


def reuniones_df(conn):
    import pandas as pd
    return pd.read_sql_query(
        """SELECT r.*, l.nombre, l.empresa, l.vertical, l.producto
           FROM reuniones r JOIN leads l ON l.id = r.lead_id
           ORDER BY r.fecha""",
        conn,
    )


def lead_por_id(conn, lead_id: int):
    return conn.execute("SELECT * FROM leads WHERE id = ?", (lead_id,)).fetchone()


def senales_de_lead(conn, lead_id: int):
    return conn.execute(
        "SELECT * FROM senales WHERE lead_id = ? ORDER BY fecha DESC", (lead_id,)
    ).fetchall()
