# Asistente Claude — Pantalla y Voz 🖥️🎤

Extensión de Chrome que convierte a Claude en tu asistente mientras usas el ordenador:

- **Ve tu pantalla**: compartes pantalla una vez y, con cada pregunta, envía una captura actual a Claude.
- **Te escucha**: hablas con tu voz (reconocimiento de voz del navegador, en español u otros idiomas).
- **Te responde con voz**: lee las respuestas en voz alta mientras van llegando, con la voz del navegador o con **ElevenLabs** (voz natural y multilingüe).
- **Se conecta con Claude Code**: mediante un pequeño puente local, tus preguntas por voz **continúan la misma conversación de Claude Code** que tienes en tu proyecto (con su memoria, sus herramientas y tus permisos).

## ¿Qué es posible y qué no? (respuesta honesta)

| Lo que pediste | Estado |
|---|---|
| Ver tu pantalla "en tiempo real" | ✅ Casi: Claude no puede recibir vídeo continuo, pero la extensión captura tu pantalla **en el momento de cada pregunta** (y puedes preguntar tantas veces como quieras). En la práctica funciona como asistencia en tiempo real. |
| Hablarle con tu voz y que te responda con voz | ✅ Sí, con la Web Speech API de Chrome (no requiere nada extra). |
| Conectarse a la sesión de Claude Code que ya tienes abierta | ⚠️ Parcial: no existe API pública para "engancharse" a la ventana viva del CLI, pero el puente **continúa exactamente la misma conversación** (equivale a `claude --continue` / `--resume`): mismo historial, mismo proyecto, mismas herramientas. |
| Conectarse a Cowork | ❌ Cowork no tiene API pública hoy. La vía soportada es Claude Code / Agent SDK, que es lo que usa el puente. |

## Estructura

```
asistente-claude/
├── extension/    ← extensión de Chrome (panel lateral)
└── bridge/       ← puente local opcional para el modo Claude Code
```

## 1. Instalar la extensión

1. Descarga o clona este repositorio.
2. Abre Chrome y ve a `chrome://extensions`.
3. Activa **Modo de desarrollador** (arriba a la derecha).
4. Pulsa **Cargar descomprimida** y elige la carpeta `asistente-claude/extension`.
5. Fija el icono de la extensión y púlsalo: se abre el panel lateral.

## 2. Elegir modo de conexión (⚙️ Ajustes)

### Modo A — API de Claude (el más sencillo)

1. Crea una clave en <https://console.anthropic.com> → *API keys*.
2. Pégala en Ajustes ⚙️ del panel.
3. Listo. Modelo recomendado: **Claude Opus 4.8**.

> 💰 Coste orientativo: cada pregunta con captura son ~1.500–2.500 tokens de entrada. La "profundidad de razonamiento" en *Rápida* da respuestas más ágiles y baratas.

### Voz natural con ElevenLabs (opcional)

Por defecto habla con la voz del navegador (gratis). Para una voz mucho más natural:

1. En Ajustes ⚙️ → **Motor de voz** elige **ElevenLabs**.
2. Pega tu clave de ElevenLabs (elevenlabs.io → perfil → *API Keys*).
3. Pulsa **Cargar mis voces**, elige una de tu cuenta y **Probar voz**.
4. Modelo recomendado para asistente en vivo: **Flash v2.5** (baja latencia). Para máxima calidad, *Multilingual v2*.

> El audio se genera frase a frase durante la respuesta (con precarga de la siguiente para reducir pausas). Si ElevenLabs falla, cae automáticamente a la voz del navegador.

### Apariencia

La interfaz tiene **tema claro y oscuro** (botón de la cabecera; sigue el del sistema por defecto).

### Marca (white-label)

Para adaptar la extensión a una organización, edita **solo** `extension/brand.js`: nombre, subtítulo, colores (`brand` / `brand2`) y, opcionalmente, un logotipo en `extension/brand/`. No hace falta tocar el CSS ni el HTML. El repositorio incluye el perfil de **GNP** ya cargado como ejemplo (naranja de marca; confirma el tono exacto y coloca el logotipo oficial siguiendo `extension/brand/LEEME.txt`).

### Modo B — Claude Code (continúa tu sesión)

Requisitos: Node.js 18+ y Claude Code ya instalado y con sesión iniciada en tu ordenador.

```bash
cd asistente-claude/bridge
npm install
node server.mjs /ruta/de/tu/proyecto
```

- La primera pregunta **continúa la conversación más reciente** de Claude Code en ese proyecto.
- ¿Quieres una sesión concreta? `CLAUDE_SESSION_ID=<uuid> node server.mjs /ruta` (el uuid aparece con `claude --resume`).
- ¿Empezar de cero? `NUEVA=1 node server.mjs /ruta`.
- En el panel, cambia el modo a **Claude Code (puente local)**.

Cuando Claude Code quiera usar una herramienta con efectos (Bash, editar archivos…), el panel te mostrará **Permitir / Denegar**. Las herramientas de solo lectura (Read, Grep, Glob…) pasan sin preguntar. Las capturas de pantalla se guardan como archivo temporal y Claude Code las abre con su herramienta `Read`.

## 3. Uso

1. **🖥️ Compartir** → elige pantalla completa, ventana o pestaña.
2. **🎤 Micrófono** → concede el permiso la primera vez.
3. Habla con normalidad: al terminar la frase, la pregunta se envía sola (desactivable en ajustes) junto con la captura, y la respuesta se lee en voz alta.
4. **🔇 Callar** detiene la voz; **⏹️ Detener** corta la respuesta en curso. Si empiezas a hablar mientras Claude habla, se calla solo.
5. También puedes escribir en el cuadro de texto.

## Privacidad y seguridad

- Las capturas se envían a la API de Anthropic (modo A) o se guardan como archivo temporal local que lee Claude Code (modo B). **No compartas la pantalla con datos sensibles a la vista** (contraseñas, datos bancarios…).
- La clave de API se guarda solo en `chrome.storage.local` de tu navegador.
- El puente escucha únicamente en `127.0.0.1` y rechaza conexiones que no vengan de una extensión de Chrome.
- El reconocimiento de voz de Chrome procesa el audio en servidores de Google (así funciona la Web Speech API).

## Solución de problemas

| Problema | Solución |
|---|---|
| No aparece el permiso del micrófono | Pulsa 🎤; si Chrome lo bloqueó: `chrome://settings/content/microphone`. |
| Claude "se transcribe a sí mismo" (eco) | El micrófono se pausa solo mientras habla; con altavoces muy altos, usa auriculares. |
| `No se pudo conectar con el puente local` | ¿Está corriendo `node server.mjs`? ¿Coincide el puerto (8787) con los ajustes? |
| El puente dice que no hay conversación previa | Abre antes `claude` en ese proyecto, o deja que empiece una nueva (lo hace solo). |
| Respuestas cortadas | Sube la profundidad de razonamiento o pregunta "continúa". |
| La voz suena robótica | Elige otra voz en Ajustes → *Voz de respuesta* (las de Google suelen sonar mejor). |

## Cómo funciona por dentro

```
┌───────────────────────── Chrome ─────────────────────────┐
│  Panel lateral (extensión)                               │
│  · getDisplayMedia → captura JPEG por pregunta           │
│  · SpeechRecognition (tu voz) / speechSynthesis (Claude) │
└──────────────┬───────────────────────────┬───────────────┘
               │ modo A                    │ modo B
               ▼                           ▼
   API de Anthropic (streaming)   ws://127.0.0.1:8787 (puente)
   modelo: claude-opus-4-8        Agent SDK → continúa tu sesión
                                  de Claude Code (--continue/--resume)
```
