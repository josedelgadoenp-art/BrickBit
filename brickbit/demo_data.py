"""Generador de datos demo sintéticos y deterministas.

Todos los nombres, empresas y contactos son ficticios. En producción, este
módulo se sustituye por los conectores de ingesta (scrapers, datos abiertos,
capturas del Radar). La semilla fija hace la demo reproducible.
"""

import random
from datetime import datetime, timedelta

from . import config, db

SEED = 42

NOMBRES = [
    "Ana", "Luis", "María", "Carlos", "Fernanda", "Jorge", "Sofía", "Ricardo",
    "Valeria", "Andrés", "Paola", "Miguel", "Daniela", "Roberto", "Gabriela",
    "Eduardo", "Lucía", "Héctor", "Mariana", "Diego", "Ximena", "Raúl",
]
APELLIDOS = [
    "García", "Hernández", "López", "Martínez", "Rodríguez", "Pérez", "Sánchez",
    "Ramírez", "Torres", "Flores", "Vargas", "Castillo", "Mendoza", "Rojas",
    "Navarro", "Salazar", "Ibarra", "Cervantes", "Del Río", "Quintero",
]
EMPRESAS = [
    "Grupo Altiplano", "TecnoVía MX", "Constructora Bosque Real", "DataNorte",
    "Logística Anáhuac", "Clínicas Vitalia", "Fintech Cobre", "Alimentos Sierra",
    "Estudio Jurídico Palma", "Inmobiliaria Cardal", "Software Colibrí",
    "Manufactura Orizaba", "Consultora Ferro", "Transportes Bajío",
    "Energía Solaris", "Agencia Creativa Nopal", "Distribuidora Ceiba",
    "Laboratorios Ámbar", "Hotelera Mar Abierto", "Educativa Quetzal",
]
CARGOS_EMPRESA = [
    "Director General", "Directora de Finanzas", "Director de RRHH",
    "Directora de Operaciones", "Fundador", "Fundadora", "Director Comercial",
]
FUENTES = [
    "radar_brickbit", "scraper_empleos", "datos_abiertos_permisos",
    "comparador_seguros", "referido", "registro_herramienta",
]


def _fecha_reciente(rng: random.Random, max_dias: int = 90) -> str:
    dt = datetime.now() - timedelta(days=rng.uniform(0, max_dias))
    return dt.strftime("%Y-%m-%d %H:%M:%S")


def generar(conn, n_leads: int = 150):
    """Puebla la base con leads sintéticos, señales y algunas reuniones."""
    rng = random.Random(SEED)
    zonas = list(config.ZONAS_CDMX)

    senales_por_vertical = {
        "seguros": [k for k, s in config.SENALES.items() if s["vertical"] == "seguros"],
        "inmobiliario": [k for k, s in config.SENALES.items() if s["vertical"] == "inmobiliario"],
    }

    for i in range(n_leads):
        vertical = "seguros" if rng.random() < 0.55 else "inmobiliario"
        nombre = f"{rng.choice(NOMBRES)} {rng.choice(APELLIDOS)}"
        zona = rng.choice(zonas)

        # 1 a 3 señales por lead; la primera define el producto principal.
        tipos = rng.sample(senales_por_vertical[vertical], k=rng.randint(1, 3))
        producto = rng.choice(config.SENALES[tipos[0]]["productos"])

        es_empresa = producto in ("gmm_colectivo", "empresarial", "oficinas", "desarrollador")
        empresa = rng.choice(EMPRESAS) if es_empresa else None
        cargo = rng.choice(CARGOS_EMPRESA) if es_empresa else None

        slug = nombre.lower().replace(" ", ".").replace("í", "i").replace("é", "e") \
            .replace("á", "a").replace("ó", "o").replace("ú", "u").replace("ñ", "n")
        email = f"{slug}@ejemplo-demo.mx"
        telefono = f"55{rng.randint(10000000, 99999999)}"

        fit = round(rng.uniform(35, 98), 1)
        etapa = rng.choices(
            ["nuevo", "contactado", "respondio", "cita_agendada", "cita_realizada",
             "cerrado_ganado", "cerrado_perdido", "seguimiento_futuro"],
            weights=[38, 20, 12, 8, 6, 5, 6, 5],
        )[0]

        lead_id = db.insertar_lead(
            conn,
            nombre=nombre, empresa=empresa, cargo=cargo,
            vertical=vertical, producto=producto, zona=zona,
            email=email, telefono=telefono,
            fit_score=fit, etapa=etapa,
            fuente=rng.choice(FUENTES),
            creado=_fecha_reciente(rng, 120),
        )

        for tipo in tipos:
            db.insertar_senal(
                conn, lead_id, tipo,
                detalle=config.SENALES[tipo]["descripcion"],
                fecha=_fecha_reciente(rng, 75),
            )

        if etapa in ("cita_agendada", "cita_realizada", "cerrado_ganado"):
            valor = rng.choice([8000, 15000, 25000, 45000, 120000, 350000])
            db.agendar_reunion(
                conn, lead_id,
                fecha=_fecha_reciente(rng, 30),
                valor_estimado=valor,
                notas="Reunión generada por el sistema (demo)",
            )
            db.actualizar_etapa(conn, lead_id, etapa)

    # Capturas de la herramienta gratuita (embudo del Caballo de Troya).
    for _ in range(40):
        nombre = f"{rng.choice(NOMBRES)} {rng.choice(APELLIDOS)}"
        db.registrar_captura(
            conn, nombre,
            f"{nombre.split()[0].lower()}@correo-demo.mx",
            rng.choice(["Comprar vivienda", "Invertir", "Seguro de auto",
                        "Seguro de vida", "GMM", "Oficinas"]),
            rng.choice(zonas),
        )


def asegurar_datos(conn):
    if db.esta_vacia(conn):
        generar(conn)
