"""Pruebas del conector de permisos de construcción CDMX.

Se ejecutan sin red: el conector corre en modo fixture.

    python -m pytest tests/ -q      (o)      python tests/test_conector_permisos.py
"""

import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from brickbit import db, scoring                                    # noqa: E402
from brickbit.connectors import base, permisos_cdmx                 # noqa: E402


def conexion_temporal():
    """Base limpia en disco temporal, aislada de data/brickbit.db."""
    tmp = Path(tempfile.mkdtemp()) / "prueba.db"
    original = db.DB_PATH
    db.DB_PATH = tmp
    conn = db.get_conn()
    db.DB_PATH = original
    return conn


# ---------------------------------------------------------------------------
# Normalización
# ---------------------------------------------------------------------------

def test_clave_normalizada_colapsa_razon_social():
    """El mismo desarrollador escrito de tres formas debe dar una sola clave."""
    variantes = [
        "Constructora Bosque Real, S.A. de C.V.",
        "CONSTRUCTORA BOSQUE REAL SA DE CV",
        "  constructora   bosque  real S.A.  ",
    ]
    claves = {base.clave_normalizada(v) for v in variantes}
    assert len(claves) == 1, f"esperaba 1 clave, obtuve {claves}"
    assert claves.pop() == "constructora bosque real"


def test_normalizar_registro_soporta_encabezados_alternos():
    """Los datasets republican con otros nombres de columna; el mapa de alias lo absorbe."""
    variante_a = {"folio": "X-1", "fecha_registro": "2026-01-05", "propietario": "Obras SA",
                  "latitud": 19.41, "longitud": -99.16, "superficie_construccion": 500}
    variante_b = {"num_folio": "X-1", "fecha_ingreso": "05/01/2026", "razon_social": "Obras SA",
                  "lat": 19.41, "lng": -99.16, "m2_construccion": 500}

    a = permisos_cdmx.normalizar_registro(variante_a)
    b = permisos_cdmx.normalizar_registro(variante_b)

    for campo in ("folio", "propietario", "lat", "lon", "superficie"):
        assert a[campo] == b[campo], f"campo {campo}: {a[campo]} != {b[campo]}"


def test_parse_fecha_acepta_formatos_mixtos():
    for texto in ["2026-07-14", "14/07/2026", "2026-07-14T10:30:00", "2026-07-14 10:30:00"]:
        f = base.parse_fecha(texto)
        assert f is not None and f.year == 2026 and f.month == 7 and f.day == 14, texto
    assert base.parse_fecha("") is None
    assert base.parse_fecha("no es fecha") is None


# ---------------------------------------------------------------------------
# Geolocalización
# ---------------------------------------------------------------------------

def test_zona_mas_cercana_asigna_y_rechaza():
    zona, _ = base.zona_mas_cercana(19.4171, -99.1633)      # Roma Norte
    assert zona == "Roma Norte", zona

    # Milpa Alta: dentro del Valle de México pero lejos de toda zona cubierta.
    zona_lejos, dist = base.zona_mas_cercana(19.1934, -99.0142)
    assert zona_lejos is None and dist > 4, (zona_lejos, dist)

    assert base.zona_mas_cercana(None, None) == (None, None)
    assert base.zona_mas_cercana(40.7, -74.0)[0] is None      # fuera del país


# ---------------------------------------------------------------------------
# Scoring de fit
# ---------------------------------------------------------------------------

def test_fit_escala_con_la_magnitud_de_la_obra():
    torre = {"superficie": 52000, "niveles": 24, "viviendas": 210, "tipo": "C"}
    edificio = {"superficie": 4100, "niveles": 7, "viviendas": 26, "tipo": "B"}
    casa = {"superficie": 180, "niveles": 2, "viviendas": 1, "tipo": "A"}

    f_torre, f_edif, f_casa = map(permisos_cdmx.calcular_fit, (torre, edificio, casa))
    assert f_torre > f_edif > f_casa, (f_torre, f_edif, f_casa)
    assert f_casa >= 30 and f_torre <= 98


def test_fit_tolera_campos_faltantes():
    assert permisos_cdmx.calcular_fit({}) == 30.0


# ---------------------------------------------------------------------------
# Ingesta end-to-end
# ---------------------------------------------------------------------------

def test_ingesta_crea_leads_y_senales():
    conn = conexion_temporal()
    res = permisos_cdmx.ingestar(conn, forzar_fixture=True)

    assert res.ok, res.error
    assert res.modo == "fixture"
    assert res.registros_leidos == 14

    # 2 descartes esperados: el de Milpa Alta (fuera de zona) y el que no trae propietario.
    assert res.descartados == 2, res.resumen()

    # 12 folios válidos, pero dos son del mismo desarrollador -> 11 leads.
    assert res.senales_nuevas == 12, res.resumen()
    assert res.leads_nuevos == 11, res.resumen()
    assert res.leads_actualizados == 1, res.resumen()

    leads = db.leads_df(conn)
    assert len(leads) == 11
    assert (leads["producto"] == "desarrollador").all()
    assert leads["zona"].notna().all()


def test_ingesta_es_idempotente():
    """Correr el conector dos veces no debe duplicar nada: es la garantía del contrato."""
    conn = conexion_temporal()
    primera = permisos_cdmx.ingestar(conn, forzar_fixture=True)
    leads_tras_primera = len(db.leads_df(conn))
    senales_tras_primera = len(db.senales_df(conn))

    segunda = permisos_cdmx.ingestar(conn, forzar_fixture=True)

    assert segunda.leads_nuevos == 0, segunda.resumen()
    assert segunda.senales_nuevas == 0, segunda.resumen()
    assert segunda.duplicados_omitidos == primera.senales_nuevas, segunda.resumen()
    assert len(db.leads_df(conn)) == leads_tras_primera
    assert len(db.senales_df(conn)) == senales_tras_primera


def test_reingesta_preserva_el_trabajo_humano():
    """Si un vendedor ya avanzó el lead, el conector no lo regresa a 'nuevo'."""
    conn = conexion_temporal()
    permisos_cdmx.ingestar(conn, forzar_fixture=True)

    lead_id = db.leads_df(conn)["id"].iloc[0]
    db.actualizar_etapa(conn, int(lead_id), "cita_agendada")

    permisos_cdmx.ingestar(conn, forzar_fixture=True)

    etapa = db.lead_por_id(conn, int(lead_id))["etapa"]
    assert etapa == "cita_agendada", f"la reingesta pisó la etapa: {etapa}"


def test_dos_folios_del_mismo_desarrollador_se_agregan_en_un_lead():
    """Tezontle aparece con dos folios: un solo lead con dos señales acumuladas."""
    conn = conexion_temporal()
    permisos_cdmx.ingestar(conn, forzar_fixture=True)

    leads = db.leads_df(conn)
    tezontle = leads[leads["nombre"].str.contains("Tezontle", case=False)]
    assert len(tezontle) == 1, f"esperaba 1 lead, obtuve {len(tezontle)}"

    senales = db.senales_de_lead(conn, int(tezontle["id"].iloc[0]))
    assert len(senales) == 2, f"esperaba 2 señales, obtuve {len(senales)}"

    # El fit se queda con la obra mayor (24,500 m² sobre 9,200 m²).
    otros = leads[~leads["nombre"].str.contains("Tezontle", case=False)]
    assert tezontle["fit_score"].iloc[0] >= otros["fit_score"].median()


def test_leads_ingeridos_entran_al_scoring_con_prioridad_util():
    """La ingesta debe producir prospectos accionables, no filas inertes."""
    conn = conexion_temporal()
    permisos_cdmx.ingestar(conn, forzar_fixture=True)

    scored = scoring.calcular_scores(db.leads_df(conn), db.senales_df(conn))
    assert not scored.empty
    assert (scored["prioridad"] == "A").any(), scored[["nombre", "score", "prioridad"]].to_string()
    assert scored["cross_sell"].all(), "permiso_construccion debe abrir venta cruzada a seguros"


def test_error_de_fuente_no_lanza_excepcion():
    """Contrato de degradación limpia: sin fixture y sin API, error poblado y app viva."""
    conn = conexion_temporal()
    original = permisos_cdmx.FIXTURE
    permisos_cdmx.FIXTURE = Path("/ruta/que/no/existe.json")
    try:
        res = permisos_cdmx.ingestar(conn, forzar_fixture=True)
        assert not res.ok
        assert "fixture" in res.error.lower()
    finally:
        permisos_cdmx.FIXTURE = original


if __name__ == "__main__":
    pruebas = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    fallos = 0
    for prueba in pruebas:
        try:
            prueba()
            print(f"✅ {prueba.__name__}")
        except AssertionError as e:
            fallos += 1
            print(f"❌ {prueba.__name__}: {e}")
        except Exception as e:
            fallos += 1
            print(f"💥 {prueba.__name__}: {type(e).__name__}: {e}")
    print(f"\n{len(pruebas) - fallos}/{len(pruebas)} pruebas pasaron")
    sys.exit(1 if fallos else 0)
