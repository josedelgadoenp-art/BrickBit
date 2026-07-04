# 📥 Receptor de leads BrickBit — guía de instalación (15 min)

Cadena completa: **tus páginas → función Netlify (`/api/lead`) → Google Apps Script → tu hoja de cálculo + correo de aviso**.

Los leads de `/financial` y los eventos del loop viral de `/destino` (llegadas por referido, resultados, clics a tu WhatsApp) quedan guardados en un Google Sheet que funciona como tu mini-CRM, y cada lead con teléfono/correo te dispara un email al instante.

---

## Paso 1 · La hoja de cálculo + Apps Script (tu CRM, gratis)

1. Crea una hoja nueva en [sheets.google.com](https://sheets.google.com) — nómbrala p. ej. **"CRM BrickBit"**.
2. Menú **Extensiones → Apps Script**.
3. Borra el contenido y pega todo `google-apps-script/Code.gs`.
4. Edita las 2 líneas de arriba:
   - `SECRET` → inventa una contraseña larga (ej. `bb-7kQ9-xR2m-2026`). La usarás también en el Paso 2.
   - `NOTIFY_EMAIL` → ya trae tu correo; cámbialo si quieres los avisos en otro.
5. **Implementar → Nueva implementación → ⚙️ Aplicación web**:
   - *Ejecutar como:* **Yo**
   - *Quién tiene acceso:* **Cualquier persona**
6. Autoriza los permisos y **copia la URL** que termina en `/exec`. Esa es tu `SHEETS_WEBHOOK_URL`.
7. Prueba: abre esa URL en el navegador → debes ver `{"ok":true,"servicio":"BrickBit leads",...}`.

> Las pestañas "Leads" y "Eventos" se crean solas con la primera entrada.

## Paso 2 · La función en Netlify

1. En el proyecto de tu sitio (donde están `financial.html` y `destino.html`), copia:
   - `netlify.toml` → a la **raíz** del sitio
   - `netlify/functions/lead.mjs` → respetando esa ruta de carpetas
2. En Netlify: **Site configuration → Environment variables**, agrega:
   | Variable | Valor |
   |---|---|
   | `SHEETS_WEBHOOK_URL` | la URL `/exec` del Paso 1 |
   | `LEAD_SECRET` | el mismo `SECRET` del Paso 1 |
   | `ALLOWED_ORIGIN` | `https://brickbit.co` (opcional, recomendado) |
3. Vuelve a desplegar el sitio. Tu endpoint queda en `https://brickbit.co/api/lead`.

## Paso 3 · Conectar tus páginas

- **`destino.html`**: ya viene con `leadEndpoint: "/api/lead"` — no hay que tocar nada.
- **`financial.html`**: en su bloque `CONFIG`, cambia una línea:
  ```js
  leadEndpoint: "/api/lead",
  ```

## Paso 4 · Probar la cadena completa

Desde tu sitio ya publicado, en la consola del navegador (F12):
```js
fetch("/api/lead",{method:"POST",headers:{"Content-Type":"application/json"},
  body:JSON.stringify({nombre:"Prueba",telefono:"5500000000",producto:"GMM Versátil",origen:"prueba"})})
  .then(r=>r.json()).then(console.log)
```
Debes ver `{ok: true}`, una fila nueva en la pestaña **Leads**, y el correo de aviso en tu bandeja.

---

### Qué guarda cada pestaña

- **Leads** — fecha, nombre, contacto, producto de interés, hueco de protección, score, origen (`buscador-seguro` / `destino`), código de referido y respuestas del cuestionario.
- **Eventos** — el pulso del loop viral: `llegada_referido` (alguien entró con enlace de un invitador), `resultado` (número calculado, arquetipo, percentil) y `click_whatsapp_agente` (lead caliente aunque no dejara datos).

### Seguridad incluida

- La URL del Apps Script y el secreto **nunca** están en el HTML público: viven como variables de entorno en Netlify.
- Campo *honeypot* anti-bots, límites de tamaño y lista blanca de campos en la función.
- Los eventos de `/destino` son anónimos (no llevan datos personales).
