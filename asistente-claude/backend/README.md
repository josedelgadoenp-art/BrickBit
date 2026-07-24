# Backend del Asistente — proxy seguro

Convierte el prototipo en algo **desplegable a un equipo**: en vez de que cada persona meta su propia clave, la clave vive **una sola vez en el servidor**, con autenticación por usuario, límite de peticiones y registro de uso.

- **Cero dependencias npm** (solo módulos nativos de Node) → fácil de auditar por seguridad.
- La extensión, en modo **"Servidor de la empresa"**, habla con este backend; ya no toca a Anthropic ni a ElevenLabs directamente.

## Qué hace

| Ruta | Método | Para qué |
|---|---|---|
| `/health` | GET | Comprobación de estado (no requiere código). |
| `/v1/chat` | POST | Pregunta a Claude; responde en streaming (mismo formato que Anthropic). |
| `/v1/tts` | POST | Genera voz con ElevenLabs (opcional). Devuelve audio. |
| `/v1/voices` | GET | Lista las voces de la cuenta de ElevenLabs (opcional). |

Todas menos `/health` exigen `Authorization: Bearer <código-de-usuario>`.

## Arranque rápido (para la demo)

```bash
cd asistente-claude/backend
cp .env.example .env      # y edita los valores
node server.mjs           # Node 18+, sin npm install
```

Mínimo en `.env`:

```
ANTHROPIC_API_KEY=sk-ant-...
USERS=CODIGO-DE-ANA:Ana,CODIGO-DE-LUIS:Luis
```

Luego, en la extensión → Ajustes → **Modo: Servidor de la empresa**, pon la dirección (`http://TU-IP:8080` en pruebas, `https://...` en producción) y el código de acceso de esa persona.

## Configuración (variables de entorno o `.env`)

| Variable | Por defecto | Descripción |
|---|---|---|
| `ANTHROPIC_API_KEY` | — | **Obligatoria.** Clave central de Anthropic. |
| `MODEL` | `claude-opus-4-8` | Modelo. El servidor decide el modelo (control central). |
| `MAX_TOKENS` | `1024` | Tope de respuesta. |
| `USERS` | — | Lista `token:nombre` separada por comas (rápido para demo). |
| `USERS_FILE` | — | Alternativa: ruta a un JSON `[{token,name}]`. |
| `RATE_PER_MIN` | `20` | Límite de peticiones por minuto y usuario. |
| `ELEVENLABS_API_KEY` | — | Opcional: voz natural centralizada. |
| `ELEVENLABS_VOICE_ID` | — | Voz por defecto si el cliente no envía una. |
| `PORT` | `8080` | Puerto. |
| `ALLOWED_ORIGINS` | — | Orígenes web extra (las extensiones de Chrome se permiten solas). |
| `LOG_FILE` | (consola) | Ruta del registro de uso (JSONL). |
| `SYSTEM_PROMPT` | (incluido) | Instrucciones del asistente. |

## Privacidad (importante para GNP)

- El registro de uso guarda **solo metadatos**: usuario, ruta, tokens, ok/error y hora. **Nunca** el texto de los mensajes ni las capturas de pantalla.
- Las claves de proveedor no salen del servidor. La extensión solo conoce la dirección y el código del usuario.
- Aun así, las capturas viajan **a través** del backend hacia Anthropic para poder responder. Para datos personales/sensibles conviene: acuerdo empresarial con Anthropic con **retención cero**, y desplegar el backend dentro de la infraestructura de GNP.

## Producción — lista de comprobación

1. **HTTPS obligatorio.** Coloca el backend detrás de un proxy TLS (nginx, balanceador, o el gateway de GNP). Nunca expongas HTTP con datos reales.
2. **Autenticación real (SSO).** Los tokens por usuario del `.env`/`USERS_FILE` sirven para la demo y un piloto pequeño. Para producción, sustituye la función `auth()` de `server.mjs` por validación de **OIDC/SSO corporativo** (p. ej. Microsoft Entra ID, habitual en aseguradoras): validas el token JWT del proveedor de identidad y sacas el usuario de ahí. Es un cambio localizado en una sola función.
3. **Límites y cuotas.** `RATE_PER_MIN` es por proceso y en memoria. Con varias réplicas, mueve el contador a Redis y añade cuota diaria/mensual por usuario o por área.
4. **Registro y coste.** Envía el JSONL de uso a tu sistema de logs; con los tokens por usuario puedes repartir el coste por área.
5. **Secretos.** No pongas las claves en el código ni en la imagen; usa el gestor de secretos de GNP.

## Cómo se probó

Se validó de punta a punta con un proveedor simulado (eventos al estilo de Anthropic):
salud, CORS/preflight, rechazo sin código y con código inválido (401), respuesta en streaming con captura, presencia de CORS en la respuesta y límite por minuto (429). Además, una prueba en **Chromium real** confirma que el navegador hace el preflight y recibe el streaming sin errores de CORS.
