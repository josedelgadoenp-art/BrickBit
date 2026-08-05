"""Persistencia SQLite: leads, señales, capturas de la herramienta gratuita y reuniones.

Las columnas `origen`/`origen_ref` (leads) y `origen`/`origen_id` (señales) son la
base de la idempotencia de los conectores: sus índices únicos hacen que reingerir
la misma fuente no duplique nada.
"""

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
    origen TEXT,
    origen_ref TEXT,
    creado TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS senales (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    lead_id INTEGER NOT NULL REFERENCES leads(id) ON DELETE CASCADE,
    tipo TEXT NOT NULL,
    detalle TEXT,
    origen TEXT,
    origen_id TEXT,
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

-- Idempotencia de conectores. SQLite trata los NULL como distintos entre sí, así
-- que los índices solo restringen filas que sí traen procedencia; los leads y
-- señales capturados a mano no se ven afectados.
CREATE UNIQUE INDEX IF NOT EXISTS idx_leads_origen
    ON leads(origen, origen_ref) WHERE origen IS NOT NULL AND origen_ref IS NOT NULL;
CREATE UNIQUE INDEX IF NOT EXISTS idx_senales_origen
    ON senales(origen, origen_id) WHERE origen IS NOT NULL AND origen_id IS NOT NULL;
"""

# Columnas añadidas después de la v0.1: las bases ya creadas se migran al vuelo.
_MIGRACIONES = {
    "leads": {"origen": "TEXT", "origen_ref": "TEXT"},
    "senales": {"origen": "TEXT", "origen_id": "TEXT"},
}


def _migrar(conn: sqlite3.Connection):
    for tabla, columnas in _MIGRACIONES.items():
        existentes = {f["name"] for f in conn.execute(f"PRAGMA table_info({tabla})")}
        for columna, tipo in columnas.items():
            if columna not in existentes:
                conn.execute(f"ALTER TABLE {tabla} ADD COLUMN {columna} {tipo}")
    conn.commit()


def get_conn() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    # Las tablas primero, luego las columnas nuevas, y al final los índices que
    # dependen de ellas: en una base preexistente el índice fallaría sin la migración.
    conn.executescript(_SCHEMA.split("-- Idempotencia")[0])
    _migrar(conn)
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


def upsert_lead_por_origen(conn, origen: str, origen_ref: str, campos: dict) -> tuple[int, bool]:
    """Crea o actualiza un lead identificado por (origen, origen_ref).

    Devuelve (lead_id, fue_creado). Al actualizar se preserva deliberadamente el
    trabajo humano: la `etapa` no se toca (un lead ya en 'cita_agendada' no puede
    volver a 'nuevo' porque el conector lo vuelva a ver) y el `fit_score` solo
    sube — si el mismo desarrollador registra una obra más grande, gana la mayor.
    """
    fila = conn.execute(
        "SELECT id, fit_score FROM leads WHERE origen = ? AND origen_ref = ?",
        (origen, origen_ref),
    ).fetchone()

    if fila is None:
        lead_id = insertar_lead(conn, origen=origen, origen_ref=origen_ref, **campos)
        return lead_id, True

    conn.execute(
        "UPDATE leads SET fit_score = MAX(fit_score, ?), zona = COALESCE(?, zona), "
        "notas = COALESCE(?, notas) WHERE id = ?",
        (campos.get("fit_score", 0), campos.get("zona"), campos.get("notas"), fila["id"]),
    )
    conn.commit()
    return fila["id"], False


def insertar_senal_unica(conn, lead_id: int, tipo: str, detalle: str = "",
                         fecha: str | None = None, origen: str | None = None,
                         origen_id: str | None = None) -> bool:
    """Inserta una señal deduplicada por (origen, origen_id). True si era nueva.

    El índice único hace el trabajo: reingerir el mismo folio no crea una segunda
    señal, que si no inflaría el score de intención en cada corrida del conector.
    """
    cur = conn.execute(
        "INSERT OR IGNORE INTO senales (lead_id, tipo, detalle, origen, origen_id, fecha) "
        "VALUES (?, ?, ?, ?, ?, COALESCE(?, datetime('now')))",
        (lead_id, tipo, detalle, origen, origen_id, fecha),
    )
    conn.commit()
    return cur.rowcount > 0


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
