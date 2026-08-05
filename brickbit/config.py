"""Configuración central: ICPs, catálogo de señales de intención y zonas geográficas."""

# ---------------------------------------------------------------------------
# Verticales y productos
# ---------------------------------------------------------------------------

VERTICALES = {
    "seguros": "Seguros GNP",
    "inmobiliario": "Mercado inmobiliario",
}

PRODUCTOS_SEGUROS = {
    "vida": "Seguro de Vida",
    "gmm": "Gastos Médicos Mayores",
    "gmm_colectivo": "GMM Colectivo / Beneficios PyME",
    "autos": "Seguro de Autos",
    "hogar": "Seguro de Hogar",
    "empresarial": "Seguro Empresarial",
}

PRODUCTOS_INMO = {
    "comprador": "Comprador de vivienda",
    "inversionista": "Inversionista patrimonial",
    "desarrollador": "Desarrollador / suelo",
    "oficinas": "Empresa en expansión (oficinas)",
}

ETAPAS_PIPELINE = [
    "nuevo",
    "contactado",
    "respondio",
    "cita_agendada",
    "cita_realizada",
    "cerrado_ganado",
    "cerrado_perdido",
    "seguimiento_futuro",
]

ETAPAS_LABELS = {
    "nuevo": "🆕 Nuevo",
    "contactado": "📤 Contactado",
    "respondio": "💬 Respondió",
    "cita_agendada": "📅 Cita agendada",
    "cita_realizada": "🤝 Cita realizada",
    "cerrado_ganado": "✅ Cerrado ganado",
    "cerrado_perdido": "❌ Cerrado perdido",
    "seguimiento_futuro": "⏰ Seguimiento futuro",
}

# ---------------------------------------------------------------------------
# Catálogo de señales de intención ("El Oráculo")
# Cada señal: peso base (0-100), vertical, productos que dispara,
# y si genera oportunidad de venta cruzada en la otra vertical.
# ---------------------------------------------------------------------------

SENALES = {
    # --- Momentos de vida -> Seguros GNP ---
    "nuevo_bebe": {
        "label": "👶 Nacimiento de hijo",
        "vertical": "seguros",
        "productos": ["vida", "gmm"],
        "peso": 85,
        "cross_sell": None,
        "descripcion": "Momento de máxima receptividad para vida y GMM familiar.",
    },
    "matrimonio": {
        "label": "💍 Matrimonio reciente",
        "vertical": "seguros",
        "productos": ["vida", "gmm"],
        "peso": 70,
        "cross_sell": "inmobiliario",
        "descripcion": "Parejas recién casadas: seguros conjuntos y primera vivienda.",
    },
    "compra_auto": {
        "label": "🚗 Compra de auto reciente",
        "vertical": "seguros",
        "productos": ["autos"],
        "peso": 90,
        "cross_sell": None,
        "descripcion": "Auto nuevo sin asegurar o con póliza de agencia por vencer.",
    },
    "compra_casa": {
        "label": "🏠 Compra de vivienda",
        "vertical": "seguros",
        "productos": ["hogar", "vida"],
        "peso": 88,
        "cross_sell": None,
        "descripcion": "Crédito hipotecario implica seguro de vida y daños: momento perfecto.",
    },
    "nuevo_empleo_ejecutivo": {
        "label": "💼 Nuevo puesto ejecutivo",
        "vertical": "seguros",
        "productos": ["gmm", "vida"],
        "peso": 65,
        "cross_sell": "inmobiliario",
        "descripcion": "Aumento de ingreso: GMM individual, vida con ahorro, y capacidad de compra inmobiliaria.",
    },
    "renovacion_proxima": {
        "label": "📆 Renovación de póliza próxima (competencia)",
        "vertical": "seguros",
        "productos": ["autos", "gmm", "vida"],
        "peso": 75,
        "cross_sell": None,
        "descripcion": "Ventana de 30-45 días antes de renovar con otra aseguradora.",
    },
    "cotizo_en_linea": {
        "label": "🖱️ Cotizó seguro en línea",
        "vertical": "seguros",
        "productos": ["autos", "gmm", "vida"],
        "peso": 80,
        "cross_sell": None,
        "descripcion": "Intención explícita: cotizó en el radar o en comparadores.",
    },
    "pyme_contratando": {
        "label": "📈 PyME contratando personal",
        "vertical": "seguros",
        "productos": ["gmm_colectivo", "empresarial"],
        "peso": 78,
        "cross_sell": "inmobiliario",
        "descripcion": "Vacantes abiertas = crecimiento = beneficios colectivos y más espacio.",
    },
    # --- Señales inmobiliarias ---
    "preaprobacion_credito": {
        "label": "🏦 Preaprobación de crédito hipotecario",
        "vertical": "inmobiliario",
        "productos": ["comprador"],
        "peso": 92,
        "cross_sell": "seguros",
        "descripcion": "Comprador listo para ejecutar; cross-sell natural a vida y hogar.",
    },
    "visita_repetida_radar": {
        "label": "🔁 Uso repetido del Radar BrickBit",
        "vertical": "inmobiliario",
        "productos": ["comprador", "inversionista"],
        "peso": 70,
        "cross_sell": None,
        "descripcion": "3+ sesiones analizando la misma zona en la herramienta gratuita.",
    },
    "busqueda_activa_zona": {
        "label": "🔎 Búsqueda activa en zona específica",
        "vertical": "inmobiliario",
        "productos": ["comprador"],
        "peso": 60,
        "cross_sell": "seguros",
        "descripcion": "Alertas y búsquedas guardadas en portales para una colonia.",
    },
    "empresa_expansion": {
        "label": "🏢 Empresa en expansión (contratación técnica)",
        "vertical": "inmobiliario",
        "productos": ["oficinas"],
        "peso": 82,
        "cross_sell": "seguros",
        "descripcion": "Contratación acelerada de ingenieros/datos: necesitará oficinas y beneficios.",
    },
    "permiso_construccion": {
        "label": "🏗️ Solicitud de permiso de construcción",
        "vertical": "inmobiliario",
        "productos": ["desarrollador"],
        "peso": 85,
        "cross_sell": "seguros",
        "descripcion": "Manifestación de construcción registrada: desarrollador activo en la zona.",
    },
    "inversionista_activo": {
        "label": "💰 Inversionista con operaciones recientes",
        "vertical": "inmobiliario",
        "productos": ["inversionista"],
        "peso": 72,
        "cross_sell": "seguros",
        "descripcion": "2+ operaciones de compra en 18 meses; busca rendimiento patrimonial.",
    },
    "evento_liquidez": {
        "label": "💵 Evento de liquidez (venta de empresa/bono)",
        "vertical": "inmobiliario",
        "productos": ["inversionista"],
        "peso": 88,
        "cross_sell": "seguros",
        "descripcion": "Capital fresco buscando destino: inmuebles + vida con inversión.",
    },
}

# Vida media de una señal en días (decaimiento de recencia).
SENAL_VIDA_MEDIA_DIAS = 45

# Umbrales de prioridad sobre el score final (0-100).
UMBRAL_A = 70
UMBRAL_B = 40

# ---------------------------------------------------------------------------
# Zonas geográficas (CDMX) para el Radar — lat, lon y métricas de mercado demo.
# En producción estas métricas vienen de scrapers de portales + datos abiertos.
# ---------------------------------------------------------------------------

ZONAS_CDMX = {
    "Polanco":      {"lat": 19.4326, "lon": -99.1998, "precio_m2": 95000, "crecimiento": 4.2,  "inventario": 310},
    "Roma Norte":   {"lat": 19.4177, "lon": -99.1620, "precio_m2": 62000, "crecimiento": 8.1,  "inventario": 420},
    "Condesa":      {"lat": 19.4113, "lon": -99.1735, "precio_m2": 68000, "crecimiento": 6.5,  "inventario": 280},
    "Del Valle":    {"lat": 19.3867, "lon": -99.1660, "precio_m2": 52000, "crecimiento": 7.4,  "inventario": 510},
    "Nápoles":      {"lat": 19.3947, "lon": -99.1743, "precio_m2": 48000, "crecimiento": 9.2,  "inventario": 350},
    "Santa Fe":     {"lat": 19.3590, "lon": -99.2600, "precio_m2": 45000, "crecimiento": 3.1,  "inventario": 620},
    "Coyoacán":     {"lat": 19.3467, "lon": -99.1617, "precio_m2": 41000, "crecimiento": 5.8,  "inventario": 390},
    "Narvarte":     {"lat": 19.3985, "lon": -99.1520, "precio_m2": 43000, "crecimiento": 10.4, "inventario": 460},
    "Juárez":       {"lat": 19.4265, "lon": -99.1580, "precio_m2": 55000, "crecimiento": 8.8,  "inventario": 240},
    "Lindavista":   {"lat": 19.4880, "lon": -99.1300, "precio_m2": 32000, "crecimiento": 6.1,  "inventario": 300},
    "Portales":     {"lat": 19.3720, "lon": -99.1450, "precio_m2": 38000, "crecimiento": 11.2, "inventario": 330},
    "Anzures":      {"lat": 19.4300, "lon": -99.1830, "precio_m2": 58000, "crecimiento": 5.2,  "inventario": 190},
}
