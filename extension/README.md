# 🎙️ GNP Copiloto de Videollamada — Extensión de Chrome

Extensión que acompaña al asesor GNP durante una **videollamada de venta consultiva**
(Google Meet, Zoom Web, Teams Web…): guía la conversación con **10 preguntas de
descubrimiento**, **transcribe en vivo** lo que se dice, permite tomar **notas por
pregunta** y, al terminar, genera con IA una **asesoría completa y personalizada**:

- 📊 **Análisis financiero** del prospecto (score de protección, brechas, fortalezas)
- 🎯 **Producto GNP ideal** — o la **combinación** de productos que mejor cubre sus brechas
- 💰 **Monto sugerido** basado en lo que el cliente declaró que le resulta cómodo,
  presentado **por quincena** (mensual ÷ 2) para que se perciba más accesible
- 🗣️ **Argumentos de venta** rankeados (emocional → numérico) y **manejo de objeciones**
  con los números del propio prospecto
- 📄 **PDF descargable** con todo el análisis, listo para enviar al cliente

Forma parte del ecosistema [GNP LifeOS](../README.md) y reutiliza su catálogo de
productos y su metodología de auditoría (VIA).

## Instalación (modo desarrollador)

1. Abre Chrome y ve a `chrome://extensions`
2. Activa **«Modo de desarrollador»** (esquina superior derecha)
3. Clic en **«Cargar descomprimida»** y selecciona la carpeta `extension/` de este repo
4. Se abrirá la página de opciones: pega tu **API key de Anthropic**
   (consíguela en [platform.claude.com](https://platform.claude.com/)) y guarda
5. Fija la extensión en la barra y haz clic en su icono para abrir el **panel lateral**

## Flujo de uso en la videollamada

1. **Antes de empezar**: informa al cliente que la llamada se transcribe para preparar
   su análisis personalizado y obtén su consentimiento ⚖️
2. Escribe el **nombre del prospecto** y el tuyo en el panel
3. Pulsa **🎙️ Escuchar** (la primera vez Chrome pedirá permiso de micrófono; si el
   diálogo no aparece en el panel, se abre una pestaña para concederlo)
4. Sigue la **guía de 10 preguntas**: cada tarjeta trae el guion sugerido y qué capturar.
   La transcripción se asocia automáticamente a la pregunta activa. Marca cada una como
   **✓ Respondida** para pasar a la siguiente
5. Anota lo importante en las **notas rápidas** (refuerzan a la IA, sobre todo cifras)
6. Al terminar, pulsa **✨ Generar asesoría con IA** → revisa el resultado en el panel
7. Pulsa **⬇️ Descargar PDF** y compártelo con el cliente

## 💜 Iris — la asistente de voz en la llamada

Iris participa en la conversación: cuando cualquiera dice **«Iris»** seguido de
una duda («Iris, ¿qué es un deducible?», «Iris, ¿cuánto vale la UDI hoy?»),
ella recopila la pregunta, la resuelve con Claude —**puede buscar activamente en la web**
(herramienta de búsqueda del API) y consulta el **catálogo GNP**— y **responde con voz**
en español mediante el sintetizador del navegador.

- «Iris» es un nombre corto y claro que el reconocedor de voz transcribe de forma confiable
- Mientras habla, el micrófono se ignora para no transcribir su propia voz
- También puedes escribirle la duda en su campo de texto del panel
- El interruptor «activa» la enciende/apaga; el botón 🔇 la calla al instante
- Las dudas que respondió se incluyen en el análisis final como contexto
- Nunca inventa primas ni condiciones: si le preguntan precios, remite a la cotización oficial

### Tres modos de ayuda

Iris distingue automáticamente qué le pides:

1. **🤫 Modo privado (apuntadora).** Con el selector «Responde: Privada (solo tú)»,
   Iris **no habla**: muestra la respuesta como texto en el panel para que solo tú
   la leas y la digas con tus palabras. «En voz alta» la deja sonar para el cliente.
2. **🧮 Calculadora y proyecciones en vivo.** «Iris, ¿cuánto es el 10% de 45 mil?»,
   «45 mil al mes en quincenal», «proyecta 500 al mes a 20 años al 8%». Hace la cuenta
   **localmente** (exacta e instantánea, sin usar el API) y te da el resultado, incluyendo
   la conversión a quincenal para enmarcar la prima.
3. **🛡️ Manejo de objeciones.** «Iris, el cliente dice que está caro», «lo va a
   pensar», «ya tiene el del trabajo»… Te da un **guion de rebate** usando los números
   del propio prospecto. Estas respuestas **siempre son privadas** (nunca se dicen en voz
   alta) para que el cliente no escuche cómo lo estás rebatiendo.

**Para que el cliente la escuche**: reproduce su voz por tus **bocinas** — el micrófono
de la llamada la captura y el cliente la oye como un participante más. (Con audífonos
solo tú la escuchas, útil como apuntador privado.)

### 🧑‍🎨 Avatar animado
Iris tiene un **rostro animado** que reacciona en tiempo real: parpadea y respira en reposo,
muestra un anillo verde cuando **te escucha**, uno violeta girando cuando **piensa**, y mueve
los labios con un ecualizador cuando **habla**. (Es una ilustración animada del lado del
navegador; un avatar de video foto-realista requeriría un servicio externo de pago.)

### 🎙️ Comandos de voz (manos libres)
Además de dudas, Iris entiende **órdenes** para controlar el copiloto sin tocar el teclado:

| Di… | Hace |
|---|---|
| «Iris, marca la 3» | Marca la pregunta 3 como respondida y avanza |
| «Iris, siguiente pregunta» / «pregunta anterior» | Navega la guía |
| «Iris, anota que gana 40 mil» | Agrega eso a las notas generales |
| «Iris, genera la asesoría» | Lanza el análisis con IA |
| «Iris, modo privado» / «en voz alta» | Cambia cómo responde |
| «Iris, cállate» | La detiene al instante |

### 🧠 Iris proactiva
Sin que la llames, Iris **escucha la conversación** y te sopla una **pista discreta** (solo
para ti, nunca en voz alta) cuando detecta una **objeción** o una **señal de compra** —por
ejemplo si el cliente pregunta el precio, menciona a su familia o expresa una preocupación.

### 📄 Iris en el PDF
Las dudas que Iris resolvió durante la llamada se agregan como **anexo** al PDF de la asesoría.

### 💡 Consejo sobre el audio

El reconocimiento de voz usa tu micrófono. Si escuchas la llamada por **bocinas**, el
micrófono también captura la voz del cliente. Si usas **audífonos**, parafrasea sus
respuestas clave («perfecto, entonces son dos hijos de 5 y 8 años…») — además de
alimentar la transcripción, es una excelente técnica de venta consultiva.

## Las 10 preguntas (Mapa de Ruta Financiera)

Guion consultivo de BrickBit; captura la mentalidad y el perfil de riesgo, no solo cifras.

| # | Tema | Qué captura |
|---|------|-------------|
| 1 | Visión a 10–15 años | Sueños y metas; el «con quién» revela familia/dependientes |
| 2 | Foco y motivación | Ocupación/negocio, proyecto principal, motor emocional |
| 3 | Perfil de inversión | Apetito de riesgo (conservador/moderado/agresivo) |
| 4 | Crédito y deuda | Deudas actuales y postura ante el crédito |
| 5 | Reacción ante imprevistos | Metáfora de la cumbre: prudencia vs. riesgo |
| 6 | Ante una crisis | Tolerancia real a la volatilidad |
| 7 | Colchón / independencia | Meses de fondo de emergencia |
| 8 | Salud y GMM | Gastos médicos mayores vigentes y salud |
| 9 | Capacidad de ahorro | % de ingreso que ahorra/invierte |
| 10 | Legado y protección | Dependientes, vida vigente, testamento/fideicomiso |

El perfil de riesgo se deduce de las preguntas 3, 5 y 6, y afina la recomendación de producto.

## Arquitectura

```
extension/
  manifest.json        # Manifest V3: side panel + storage + api.anthropic.com
  background.js        # abre el panel al hacer clic en el icono
  sidepanel.html/.css  # interfaz principal
  js/
    questions.js       # guía de 10 preguntas (guion + qué capturar)
    products.js        # catálogo GNP (portado de core/products.py)
    speech.js          # transcripción Web Speech API es-MX con auto-reinicio
    calculadora.js     # cálculos financieros locales (%, quincenal, proyecciones)
    hadassah.js        # asistente de voz: wake word, modo privado, objeciones, TTS
    claude.js          # API de Claude: asesoría (streaming + JSON) y Iris (web search)
    pdf.js             # generación del PDF de asesoría (jsPDF)
    sidepanel.js       # controlador: estado, persistencia, render
  vendor/jspdf.umd.min.js
  options.html         # API key + modelo
  permission.html      # concesión de permiso de micrófono
```

- **Modelo**: Claude Opus 4.8 por defecto (configurable a Sonnet 5 en opciones).
  La respuesta usa *structured outputs* (`output_config.format` con JSON Schema),
  por lo que el análisis siempre llega en el formato esperado.
- **Privacidad**: la API key y la sesión viven solo en `chrome.storage.local`.
  Mientras el micrófono está activo, el reconocimiento de voz de Chrome procesa el audio
  en los servidores de Google (así funciona la Web Speech API); la transcripción resultante
  se envía al API de Anthropic al generar la asesoría. Inclúyelo en tu aviso de consentimiento.
- **Sin build**: JavaScript plano, sin dependencias externas más allá de jsPDF empaquetado.

## Avisos importantes

- ⚖️ **Consentimiento**: grabar/transcribir una llamada requiere informar al cliente y
  obtener su consentimiento (LFPDPPP en México). La extensión te lo recuerda al abrirla.
- 💵 **No es cotización**: los montos que produce la IA son *presupuestos sugeridos de
  protección* con base en la capacidad y comodidad del cliente. La prima real depende
  de la tarificación y suscripción oficiales de GNP.
- 🧪 **Catálogo GNP**: los **8 productos** (Línea Azul/GMM Platino, Trasciende, Proyecta,
  Capitaliza, Vida Vive, Básico Estandarizado de Vida, Auto Accesible y Hogar Versátil) se
  tomaron de las **páginas oficiales de gnp.com.mx** (coberturas, sumas aseguradas, plazos y
  notas fiscales reales). Las primas y condiciones exactas dependen de la cotización oficial
  de GNP; la herramienta nunca las presenta como oferta.
