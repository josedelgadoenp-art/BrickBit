# 🧱 BrickBit — Motor de Prospección Predictiva

**Objetivo único: la mayor cantidad de prospectos calificados en el menor tiempo posible.**
Dos verticales: **Seguros GNP** (vida, GMM, autos, hogar, empresarial) y **Mercado inmobiliario** (compradores, inversionistas, desarrolladores, oficinas).

Este repo contiene (1) el **playbook estratégico** — tus 5 ideas ordenadas, mejoradas y con recortes deliberados — y (2) la **plataforma funcionando** en Streamlit con datos demo.

```bash
pip install -r requirements.txt
streamlit run streamlit_app.py
```

> Opcional: exporta `ANTHROPIC_API_KEY` para activar el refinado de mensajes con IA (Claude) en la página de Muestreo Inverso. Sin la clave, todo lo demás funciona igual.

---

## El playbook (ordenado y mejorado)

Las 5 ideas originales eran buenas pero estaban al mismo nivel. La mejora principal es **ordenarlas como un sistema donde cada pieza alimenta a la siguiente**:

```
1. CABALLO DE TROYA        →  atrae tráfico y captura leads con consentimiento
       ↓ (cada registro es una señal)
2. EL ORÁCULO              →  cruza señales y decide QUIÉN necesita comprar HOY
       ↓ (solo prioridad A/B pasan)
3. MUESTREO INVERSO        →  primer contacto que regala el resultado final
       ↓ (las respuestas se clasifican solas)
4. SDR INVISIBLE           →  automatiza seguimiento; el humano solo va a la cita
       ↓ (la cita es la unidad de valor)
5. MODELO CERO FRICCIÓN    →  se cobra por cita calificada + revenue share
       ↺ (cada cierre genera referidos y datos que mejoran el Oráculo)
```

### 1. El Caballo de Troya — *Radar Inmobiliario* ✅ (implementado: página "Radar de mercado")

Tu idea, con dos ajustes:

- **La herramienta es 100% usable sin registro.** Si el mapa entero está tras un muro, nadie lo comparte y muere. Lo que se bloquea es lo **accionable**: contactos de tomadores de decisión, anomalías de precio concretas, desarrolladores activos. El análisis gratis viraliza; el candado convierte.
- **Doble propósito que no estaba en tu plan:** el Radar no solo captura leads inmobiliarios — el formulario pregunta el interés, y "seguro de auto / vida / GMM" son opciones. La misma herramienta alimenta las dos verticales.

### 2. El Oráculo — señales de intención ✅ (implementado: motor de scoring + catálogo de 15 señales)

Tu idea era correcta; lo que le faltaba era **aritmética explícita**:

- `score = 40% fit + 60% intención`, donde la intención **decae con el tiempo** (vida media 45 días). Una preaprobación de crédito de ayer vale el doble que una de hace mes y medio. Esto es lo que convierte "una lista" en "los 10 que necesitan comprar hoy".
- Catálogo de señales por vertical con pesos: nacimiento de hijo (85), compra de auto (90), preaprobación hipotecaria (92), PyME contratando (78), permiso de construcción (85)…
- **Idea añadida — motor de venta cruzada:** es tu ventaja injusta por tener dos verticales. Compró casa → necesita vida + hogar (GNP). Preaprobación de crédito → cliente inmobiliario Y de seguros. Evento de liquidez → inmueble + vida con inversión. Cada lead se monetiza dos veces; ningún competidor de una sola vertical puede copiarlo.
- **Idea añadida — speed-to-lead:** el KPI operativo #1. Lead prioridad A se contacta en < 5 minutos; la probabilidad de conectar cae ~8x tras la primera hora. De nada sirve detectar la señal antes que nadie si contactas al día siguiente.

### 3. Muestreo Inverso ✅ (implementado: generador con plantillas + refinado con Claude)

Tu mejor idea; se implementa casi tal cual. Anatomía del mensaje que convierte: gancho de datos → regalo completo sin condición → "tengo 15 más como este" → CTA de 10 minutos. Ajustes:

- **Recorte:** el "video cinematográfico generado por IA" sale del MVP. Hoy, un video IA en un primer contacto en frío grita "automatizado" y quema el lead. El reporte escrito hiper-específico convierte mejor y cuesta 100x menos. Se revalúa cuando haya volumen.
- La IA (Claude) refina el borrador con el contexto del vendedor ("lo vi en el podcast X…"), con regla dura: **no inventar datos** que no estén en las señales.

### 4. SDR Invisible ✅ (implementado: pipeline con clasificación de respuestas y citas)

Tu idea, con un recorte importante:

- **Recorte: la "clonación de identidad" (conectar bandejas de clientes y enviar en su nombre) sale de la fase 1.** Es la parte con mayor riesgo de entregabilidad (dominios quemados), de confianza y legal. El SDR invisible del MVP opera **nuestro** embudo: clasifica respuestas (interesa / búscame en 3 meses / duda / no), agenda seguimientos automáticos y solo escala al humano cuando hay interés real.
- **Ajuste México:** para B2C (seguros, vivienda), WhatsApp convierte mucho mejor que el email. Email queda para B2B. Ambos con consentimiento y baja disponible.

### 5. Modelo de negocio cero fricción ✅ (implementado: calculadora de unit economics)

Tus dos mecanismos (pago por cita + revenue share) están bien; tres ajustes de supervivencia:

- **Setup único pequeño** (reembolsable contra las primeras citas). "Gratis hasta la cita" atrae clientes no-serios que no se presentan a las citas que tú pagaste por generar.
- **Definición escrita de "cita calificada"** (cumple ICP + asistió + necesidad activa por señal). Sin esto, cada factura es una negociación.
- Revenue share **solo** high-ticket (desarrollos, inversión): en tickets de millones el 1% supera cualquier tarifa; en una póliza de autos no tiene sentido.

### Lo que se recortó (y por qué)

| Idea original | Veredicto | Razón |
|---|---|---|
| Video IA "cinematográfico" en outreach | ⏸️ Fase 2+ | En frío se percibe automatizado; el reporte escrito específico convierte mejor y cuesta 100x menos |
| Clonación de identidad (bandejas de clientes) | ⏸️ Fase 2, opt-in | Riesgo de entregabilidad, confianza y legal; primero operar nuestro propio embudo |
| Matrices insumo-producto / índices de confianza | ❌ Recortado | Señales macro: no dicen QUIÉN compra HOY. Mejor 6 fuentes micro (empleos, permisos, portales) |
| Solo suscripción mensual | ❌ Recortado al inicio | Tu instinto era correcto: genera desconfianza sin historial |

### Lo que se añadió

1. **Venta cruzada seguros ⇄ inmobiliario** — la ventaja estructural de tener ambas verticales.
2. **Speed-to-lead < 5 min** como KPI operativo central.
3. **WhatsApp como canal primario B2C** en México.
4. **Cumplimiento desde el día 1 (LFPDPPP):** solo fuentes públicas o con consentimiento, opción de baja siempre, nada de comprar bases. No es solo ética: los leads con consentimiento convierten mejor y no queman dominios.
5. **Clientes ancla definidos:** agentes GNP con cartera existente e inmobiliarias boutique — ciclos de venta cortos y dolor agudo de prospección.
6. **Plan 90 días** (página "Modelo de negocio"): Radar público → 2 conectores → 10 mensajes/día → 2-3 clientes ancla → automatizar y medir.

---

## Arquitectura del código

```
streamlit_app.py          # entrada multi-página (st.navigation)
app_pages/
  inicio.py               # panel de control: KPIs, embudo, "los 10 de hoy"
  radar.py                # Caballo de Troya: mapa pydeck + captura de leads
  oraculo.py              # señales, scoring A/B/C, catálogo, conectores
  muestreo.py             # generador de Muestreo Inverso (+ Claude opcional)
  pipeline.py             # SDR: tablero por etapa, clasificación, citas
  modelo.py               # calculadora de unit economics + plan 90 días
brickbit/
  config.py               # ICPs, catálogo de señales con pesos, zonas CDMX
  db.py                   # SQLite: leads, señales, capturas, reuniones
  scoring.py              # fit x intención con decaimiento de recencia
  outreach.py             # plantillas + refinado con la API de Claude
  demo_data.py            # dataset sintético determinista (semilla fija)
  connectors/
    base.py               # normalización, geolocalización, HTTP con reintentos
    permisos_cdmx.py      # conector de manifestaciones de construcción
    __main__.py           # CLI para cron
tests/                    # pruebas del conector (12, corren sin red)
data/fixtures/            # muestras sintéticas para desarrollo offline
data/brickbit.db          # se crea sola al arrancar (gitignored)
```

---

## Conector de permisos de construcción (CDMX)

**Por qué esta fuente primero:** un folio de manifestación de construcción es la señal de intención más limpia que existe en inmobiliario. Quien registra una obra ya pasó por notario, ya tiene el terreno y ya tiene presupuesto. No es un "interesado": es un desarrollador con proyecto activo que además necesita seguro de obra — o sea, entra por las dos verticales. Y es dato público y gratuito, así que el costo de adquisición es cero.

```bash
python -m brickbit.connectors --listar             # conectores disponibles
python -m brickbit.connectors permisos_cdmx        # ejecutar ingesta
python -m brickbit.connectors --buscar "manifestacion construccion"   # descubrir resource_id
```

También se ejecuta desde el botón "▶️ Ejecutar ingesta" en la página del Oráculo.

### Conectarlo al portal real

El portal de datos abiertos de CDMX corre CKAN, cuya API es estándar. El `resource_id` cambia cada vez que la dependencia republica el dataset, así que no se hardcodea:

```bash
export BRICKBIT_CKAN_BASE="https://datos.cdmx.gob.mx/api/3/action"
export BRICKBIT_PERMISOS_RESOURCE_ID="<id del recurso vigente>"
```

Sin esa variable, el conector corre en **modo muestra local** con el fixture incluido, así que la app funciona y las pruebas pasan sin depender de que el portal esté arriba. `--buscar` consulta el catálogo para encontrar el id vigente.

En cron, para que los leads estén listos antes de que abra la fuerza de ventas:

```
0 7 * * *  cd /ruta/BrickBit && python -m brickbit.connectors permisos_cdmx >> logs/ingesta.log 2>&1
```

### Qué resuelve por dentro

| Problema real | Cómo se resuelve |
|---|---|
| El dataset republica con otros encabezados (`folio` / `num_folio` / `FOLIO`) | Mapa de alias por campo en vez de acoplarse a una versión del CSV |
| El mismo desarrollador escrito de tres formas distintas | Clave normalizada que colapsa acentos, puntuación y sufijos de razón social (`S.A. de C.V.`) |
| Correr el conector dos veces inflaría el score de intención | Índices únicos `(origen, origen_id)`: reingerir el mismo folio no crea otra señal |
| El vendedor ya avanzó un lead y la reingesta lo pisaría | El upsert nunca toca la `etapa`, y el `fit_score` solo sube |
| Un permiso en Milpa Alta caería en Polanco por ser "el menos lejano" | Radio máximo de 4 km; fuera de cobertura se descarta en vez de inventar la zona |
| Fechas en cuatro formatos distintos | Parser tolerante que prueba los formatos comunes |
| El portal se cae a media ingesta | Reintentos con backoff, y degradación al fixture con aviso en vez de excepción |

El **fit se calcula desde la magnitud de la obra** (superficie, viviendas, niveles y tipo de manifestación: A unifamiliar < B plurifamiliar < C gran magnitud). Una torre de 210 viviendas y un particular que amplía su casa no valen lo mismo, y el ranking lo refleja: sobre la muestra incluida, el desarrollador con dos obras grandes sale prioridad A y el particular cae a C.

```bash
python tests/test_conector_permisos.py     # 12 pruebas, sin red
```

**Todos los datos de la demo son sintéticos** (nombres, empresas y contactos ficticios, semilla fija). En producción, `demo_data.py` se sustituye por los conectores de ingesta listados en la página del Oráculo.
