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

### 💡 Consejo sobre el audio

El reconocimiento de voz usa tu micrófono. Si escuchas la llamada por **bocinas**, el
micrófono también captura la voz del cliente. Si usas **audífonos**, parafrasea sus
respuestas clave («perfecto, entonces son dos hijos de 5 y 8 años…») — además de
alimentar la transcripción, es una excelente técnica de venta consultiva.

## Las 10 preguntas

| # | Tema | Qué captura |
|---|------|-------------|
| 1 | Datos básicos | Nombre, edad, ocupación, zona |
| 2 | Familia | Dependientes económicos y edades |
| 3 | Ingresos | Ingreso mensual del hogar |
| 4 | Gastos | Gasto mensual, deudas y compromisos |
| 5 | Patrimonio | Ahorro, inversiones, bienes propios |
| 6 | Salud | Estado general, hábitos, antecedentes |
| 7 | Protección actual | Seguros vigentes y sumas aseguradas |
| 8 | Metas | Sueños con horizonte de tiempo |
| 9 | Prioridad | Qué blindaría primero / qué le quita el sueño |
| 10 | Presupuesto | Monto mensual/quincenal cómodo |

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
    claude.js          # llamada al API de Claude con salida JSON estructurada
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
- 🧪 **Demo conceptual**: el catálogo de productos es referencial; valídalo contra el
  portafolio vigente de GNP antes de usarlo en producción.
