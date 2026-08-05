"""Conector: manifestaciones de construcción de CDMX (datos abiertos).

Por qué esta fuente primero: un folio de manifestación es la señal de intención
más limpia que existe en inmobiliario. Cuando alguien registra una obra ya pasó
por notario, ya tiene el terreno y ya tiene presupuesto. No es un "interesado":
es un desarrollador con proyecto activo, y necesita seguro de obra (GNP) además
de todo lo inmobiliario. Es dato público y gratuito, lo que lo hace ideal para
arrancar sin costo de adquisición.

## Cómo se conecta a la fuente real

El portal de datos abiertos de CDMX corre **CKAN**, cuya API es estándar:

    GET {base}/datastore_search?resource_id={id}&limit=100&offset=0

El `resource_id` cambia cada vez que la dependencia republica el dataset, así que
**no se hardcodea**: se toma de variables de entorno.

    export BRICKBIT_CKAN_BASE="https://datos.cdmx.gob.mx/api/3/action"
    export BRICKBIT_PERMISOS_RESOURCE_ID="<id del recurso>"

Para descubrir el id vigente, `buscar_recursos()` consulta el catálogo con
`package_search`. Sin `RESOURCE_ID` configurado, el conector corre en **modo
fixture** con la muestra en `data/fixtures/` — así la app funciona y es testeable
sin depender de que el portal esté arriba.
"""

import os
from pathlib import Path

from .. import config
from .base import (
    ErrorFuente, ResultadoIngesta, a_float, clave_normalizada, get_json,
    parse_fecha, titulo, zona_mas_cercana,
)

FUENTE = "permisos_cdmx"
SENAL = "permiso_construccion"

CKAN_BASE = os.environ.get("BRICKBIT_CKAN_BASE", "https://datos.cdmx.gob.mx/api/3/action")
RESOURCE_ID = os.environ.get("BRICKBIT_PERMISOS_RESOURCE_ID", "")

FIXTURE = Path(__file__).resolve().parent.parent.parent / "data" / "fixtures" / "permisos_cdmx_muestra.json"

PAGINA = 100
MAX_REGISTROS = 1000

# ---------------------------------------------------------------------------
# Normalización de columnas
#
# Los datasets oficiales republican con encabezados distintos entre ejercicios
# ('folio' / 'num_folio' / 'FOLIO'), así que mapeamos alias a un esquema propio
# en lugar de acoplarnos a una versión del CSV.
# ---------------------------------------------------------------------------

ALIAS = {
    "folio": ["folio", "num_folio", "no_folio", "numero_folio", "folio_manifestacion", "id_folio", "id"],
    "fecha": ["fecha_registro", "fecha_ingreso", "fecha_expedicion", "fecha_manifestacion", "fecha"],
    "tipo": ["tipo_manifestacion", "tipo_de_manifestacion", "modalidad", "tipo_obra", "tipo"],
    "propietario": ["propietario", "nombre_propietario", "razon_social", "solicitante",
                    "nombre_solicitante", "representante_legal", "nombre"],
    "alcaldia": ["alcaldia", "delegacion", "demarcacion", "alcaldia_o_municipio", "municipio"],
    "colonia": ["colonia", "nombre_colonia", "col"],
    "calle": ["calle", "via", "nombre_via", "domicilio", "ubicacion", "direccion"],
    "lat": ["latitud", "lat", "coord_y", "y"],
    "lon": ["longitud", "lon", "lng", "coord_x", "x"],
    "superficie": ["superficie_construccion", "superficie_total_construccion", "sup_construccion",
                   "m2_construccion", "superficie_total", "superficie"],
    "niveles": ["niveles", "num_niveles", "no_niveles", "numero_niveles"],
    "viviendas": ["viviendas", "num_viviendas", "no_viviendas", "numero_viviendas", "unidades"],
    "uso": ["uso", "uso_suelo", "uso_de_suelo", "destino", "uso_actual"],
}


def normalizar_registro(bruto: dict) -> dict:
    """Aplana un registro heterogéneo al esquema interno usando el mapa de alias."""
    indice = {clave_normalizada(k).replace(" ", "_"): v for k, v in bruto.items()}
    salida = {}
    for campo, alias in ALIAS.items():
        valor = next((indice[a] for a in alias if indice.get(a) not in (None, "", "NULL")), None)
        salida[campo] = valor
    return salida


# ---------------------------------------------------------------------------
# Scoring de fit: qué tan buen prospecto es este desarrollador
# ---------------------------------------------------------------------------

# Clasificación oficial CDMX: A = vivienda unifamiliar pequeña, B = plurifamiliar,
# C = obra de gran magnitud o alto impacto urbano. A mayor tipo, mayor ticket.
PESO_TIPO = {"a": 0, "b": 12, "c": 22}


def calcular_fit(reg: dict) -> float:
    """Fit 30-98 según magnitud de la obra.

    Un desarrollador de torre de 120 departamentos vale mucho más que quien
    amplía una casa: el ticket de seguro de obra y el volumen inmobiliario
    escalan con la magnitud del proyecto.
    """
    fit = 30.0

    superficie = a_float(reg.get("superficie")) or 0
    if superficie >= 20000:
        fit += 35
    elif superficie >= 5000:
        fit += 28
    elif superficie >= 1000:
        fit += 18
    elif superficie >= 200:
        fit += 8

    viviendas = a_float(reg.get("viviendas")) or 0
    if viviendas >= 100:
        fit += 22
    elif viviendas >= 30:
        fit += 16
    elif viviendas >= 10:
        fit += 10
    elif viviendas >= 2:
        fit += 4

    niveles = a_float(reg.get("niveles")) or 0
    if niveles >= 15:
        fit += 12
    elif niveles >= 6:
        fit += 7
    elif niveles >= 3:
        fit += 3

    tipo = clave_normalizada(reg.get("tipo") or "")
    fit += next((p for clave, p in PESO_TIPO.items() if clave in tipo), 0)

    return round(min(fit, 98.0), 1)


def describir(reg: dict, zona: str | None) -> str:
    """Detalle legible que verá el vendedor en el mensaje de outreach."""
    partes = []
    if reg.get("tipo"):
        partes.append(f"Manifestación tipo {str(reg['tipo']).strip().upper()[:1]}")
    superficie = a_float(reg.get("superficie"))
    if superficie:
        partes.append(f"{superficie:,.0f} m² de construcción")
    viviendas = a_float(reg.get("viviendas"))
    if viviendas:
        partes.append(f"{viviendas:,.0f} viviendas")
    niveles = a_float(reg.get("niveles"))
    if niveles:
        partes.append(f"{niveles:,.0f} niveles")
    ubicacion = titulo(reg.get("colonia") or "") or titulo(reg.get("alcaldia") or "")
    if ubicacion:
        partes.append(f"en {ubicacion}")
    if zona:
        partes.append(f"(zona {zona})")
    return " · ".join(partes) or "Manifestación de construcción registrada"


# ---------------------------------------------------------------------------
# Lectura de la fuente
# ---------------------------------------------------------------------------

def buscar_recursos(consulta: str = "manifestacion construccion", filas: int = 5) -> list[dict]:
    """Descubre datasets candidatos en el catálogo CKAN.

    Utilidad de operación: se corre a mano para obtener el `resource_id` vigente
    y ponerlo en BRICKBIT_PERMISOS_RESOURCE_ID.
    """
    url = f"{CKAN_BASE}/package_search?q={urllib_quote(consulta)}&rows={filas}"
    datos = get_json(url)
    encontrados = []
    for paquete in datos.get("result", {}).get("results", []):
        for recurso in paquete.get("resources", []):
            if recurso.get("datastore_active"):
                encontrados.append({
                    "dataset": paquete.get("title"),
                    "recurso": recurso.get("name"),
                    "resource_id": recurso.get("id"),
                    "formato": recurso.get("format"),
                })
    return encontrados


def urllib_quote(texto: str) -> str:
    from urllib.parse import quote
    return quote(texto)


def _leer_api(resource_id: str, limite: int) -> list[dict]:
    """Pagina datastore_search hasta `limite` registros."""
    registros, offset = [], 0
    while len(registros) < limite:
        url = (f"{CKAN_BASE}/datastore_search?resource_id={resource_id}"
               f"&limit={min(PAGINA, limite - len(registros))}&offset={offset}")
        datos = get_json(url)
        if not datos.get("success", False):
            raise ErrorFuente("la API respondió success=false")
        pagina = datos.get("result", {}).get("records", [])
        if not pagina:
            break
        registros.extend(pagina)
        offset += len(pagina)
        if offset >= datos.get("result", {}).get("total", 0):
            break
    return registros


def _leer_fixture() -> list[dict]:
    import json
    if not FIXTURE.exists():
        raise ErrorFuente(f"no se encontró el fixture en {FIXTURE}")
    with open(FIXTURE, encoding="utf-8") as f:
        return json.load(f).get("result", {}).get("records", [])


# ---------------------------------------------------------------------------
# Ingesta
# ---------------------------------------------------------------------------

def ingestar(conn, limite: int = MAX_REGISTROS, forzar_fixture: bool = False) -> ResultadoIngesta:
    """Lee la fuente, crea/actualiza leads y registra señales. Idempotente."""
    from .. import db

    res = ResultadoIngesta(fuente=FUENTE)

    # 1. Obtener registros crudos, con degradación a fixture.
    if forzar_fixture or not RESOURCE_ID:
        res.modo = "fixture"
        if not forzar_fixture:
            res.avisos.append(
                "BRICKBIT_PERMISOS_RESOURCE_ID no está configurado: corriendo con la "
                "muestra local. Usa buscar_recursos() para obtener el id vigente."
            )
        try:
            crudos = _leer_fixture()
        except ErrorFuente as e:
            res.error = str(e)
            return res
    else:
        res.modo = "api"
        try:
            crudos = _leer_api(RESOURCE_ID, limite)
        except ErrorFuente as e:
            res.avisos.append(f"La API falló ({e}); se usó la muestra local.")
            res.modo = "fixture"
            try:
                crudos = _leer_fixture()
            except ErrorFuente as e2:
                res.error = f"{e} · y tampoco hay fixture: {e2}"
                return res

    res.registros_leidos = len(crudos)
    peso_senal = config.SENALES[SENAL]

    for bruto in crudos:
        reg = normalizar_registro(bruto)

        folio = str(reg.get("folio") or "").strip()
        propietario = titulo(reg.get("propietario") or "")
        if not folio or not propietario:
            res.descartados += 1   # sin folio no hay dedup; sin nombre no hay lead
            continue

        zona, _ = zona_mas_cercana(a_float(reg.get("lat")), a_float(reg.get("lon")))
        if zona is None:
            # Fuera de las zonas que cubrimos: se descarta en vez de forzarlo a
            # la zona menos lejana, que produciría outreach con datos falsos.
            res.descartados += 1
            continue

        fecha = parse_fecha(reg.get("fecha"))
        fecha_txt = fecha.strftime("%Y-%m-%d %H:%M:%S") if fecha else None
        ref_lead = clave_normalizada(propietario)

        lead_id, creado = db.upsert_lead_por_origen(
            conn, origen=FUENTE, origen_ref=ref_lead,
            campos={
                "nombre": propietario,
                "empresa": propietario if len(propietario.split()) > 2 else None,
                "cargo": "Desarrollador / propietario de obra",
                "vertical": peso_senal["vertical"],
                "producto": "desarrollador",
                "zona": zona,
                "fit_score": calcular_fit(reg),
                "fuente": FUENTE,
                "notas": f"Alta automática desde manifestaciones de construcción CDMX (folio {folio}).",
            },
        )
        if creado:
            res.leads_nuevos += 1
        else:
            res.leads_actualizados += 1

        inserted = db.insertar_senal_unica(
            conn, lead_id=lead_id, tipo=SENAL,
            detalle=describir(reg, zona), fecha=fecha_txt,
            origen=FUENTE, origen_id=folio,
        )
        if inserted:
            res.senales_nuevas += 1
        else:
            res.duplicados_omitidos += 1

    return res
