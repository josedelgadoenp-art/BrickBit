#!/usr/bin/env node
/**
 * Backend del Asistente (Asistente GNP)
 * ------------------------------------------------------------
 * Proxy seguro entre la extensión y los proveedores (Anthropic + ElevenLabs).
 * Las CLAVES viven aquí, en el servidor — nunca en el navegador del empleado.
 *
 * Qué aporta:
 *   · Una sola clave central de Anthropic (y otra de ElevenLabs), no una por persona.
 *   · Autenticación por usuario con tokens de acceso (comparación en tiempo constante).
 *   · Límite de peticiones por minuto por usuario.
 *   · Registro de USO (solo metadatos: usuario, tokens, ok/error) — NUNCA el contenido
 *     de la pantalla ni de los mensajes (privacidad / datos personales).
 *   · Streaming de la respuesta al estilo de Anthropic (la extensión no cambia su parser).
 *
 * Cero dependencias npm: solo módulos nativos de Node (fácil de auditar).
 *
 * Arranque:   node server.mjs        (lee configuración de variables de entorno o .env)
 * Requisitos: Node 18+
 * ------------------------------------------------------------
 */

import http from 'node:http';
import https from 'node:https';
import fs from 'node:fs';
import crypto from 'node:crypto';

/* ---------------- configuración ---------------- */

loadDotEnv('.env');

const CFG = {
  port: Number(process.env.PORT || 8080),
  anthropicKey: process.env.ANTHROPIC_API_KEY || '',
  anthropicBase: (process.env.ANTHROPIC_BASE_URL || 'https://api.anthropic.com').replace(/\/$/, ''),
  anthropicVersion: process.env.ANTHROPIC_VERSION || '2023-06-01',
  model: process.env.MODEL || 'claude-opus-4-8',
  maxTokens: Number(process.env.MAX_TOKENS || 1024),
  elevenKey: process.env.ELEVENLABS_API_KEY || '',
  elevenBase: (process.env.ELEVENLABS_BASE_URL || 'https://api.elevenlabs.io').replace(/\/$/, ''),
  elevenModel: process.env.ELEVENLABS_MODEL || 'eleven_flash_v2_5',
  elevenVoice: process.env.ELEVENLABS_VOICE_ID || '',
  ratePerMin: Number(process.env.RATE_PER_MIN || 20),
  maxBodyBytes: Number(process.env.MAX_BODY_BYTES || 12 * 1024 * 1024),
  logFile: process.env.LOG_FILE || '',
  extraOrigins: (process.env.ALLOWED_ORIGINS || '').split(',').map((s) => s.trim()).filter(Boolean),
  system: process.env.SYSTEM_PROMPT || `Eres un asistente de voz que ayuda a un asesor mientras usa su ordenador.
Recibes sus preguntas transcritas por voz y, normalmente, una captura de su pantalla.
Responde en español de México, con frases cortas y naturales (tus respuestas se leen en voz alta): sin markdown, sin listas con símbolos, sin encabezados.
Si te preguntan por algo visible en la captura, básate en ella; si no se distingue, pídelo ampliado. Guía paso a paso, uno a uno.`,
};

const USERS = loadUsers(); // Map<sha256(token) -> {name}>
if (!USERS.size) console.warn('[backend] AVISO: no hay usuarios configurados (USERS o USERS_FILE). Nadie podrá autenticarse.');
if (!CFG.anthropicKey) console.warn('[backend] AVISO: falta ANTHROPIC_API_KEY. /v1/chat devolverá error hasta configurarla.');

const rate = new Map(); // name -> number[] (timestamps ms)

/* ---------------- servidor ---------------- */

const server = http.createServer(async (req, res) => {
  setCors(req, res);
  if (req.method === 'OPTIONS') { res.writeHead(204); return res.end(); }

  const url = new URL(req.url, 'http://localhost');
  try {
    if (req.method === 'GET' && url.pathname === '/health') return health(res);
    if (req.method === 'POST' && url.pathname === '/v1/chat') return await handleChat(req, res);
    if (req.method === 'POST' && url.pathname === '/v1/tts') return await handleTts(req, res);
    if (req.method === 'GET' && url.pathname === '/v1/voices') return await handleVoices(req, res);
    json(res, 404, { error: 'ruta no encontrada' });
  } catch (e) {
    if (!res.headersSent) json(res, 500, { error: 'error interno', detail: String(e.message || e) });
    else try { res.end(); } catch (_) {}
  }
});

server.listen(CFG.port, () => {
  console.log('╭───────────────────────────────────────────────╮');
  console.log('│  Backend Asistente — proxy seguro             │');
  console.log('╰───────────────────────────────────────────────╯');
  console.log(`[backend] escuchando en http://0.0.0.0:${CFG.port}`);
  console.log(`[backend] modelo: ${CFG.model} · proveedor: ${CFG.anthropicBase}`);
  console.log(`[backend] usuarios: ${USERS.size} · límite: ${CFG.ratePerMin}/min · voz: ${CFG.elevenKey ? 'ElevenLabs' : 'no configurada'}`);
  console.log('[backend] recuerda: en producción debe ir tras HTTPS (proxy TLS).');
});

/* ---------------- rutas ---------------- */

function health(res) {
  json(res, 200, { ok: true, model: CFG.model, tts: !!CFG.elevenKey, users: USERS.size });
}

async function handleChat(req, res) {
  const user = auth(req, res); if (!user) return;
  if (limited(res, user)) return;
  if (!CFG.anthropicKey) return json(res, 503, { error: 'proveedor no configurado (falta ANTHROPIC_API_KEY)' });

  const body = await readJson(req, res); if (body === undefined) return;
  if (!Array.isArray(body.messages) || !body.messages.length) return json(res, 400, { error: 'faltan mensajes' });
  const effort = ['low', 'medium', 'high'].includes(body.effort) ? body.effort : 'low';

  const upstreamBody = JSON.stringify({
    model: CFG.model,
    max_tokens: CFG.maxTokens,
    system: CFG.system,
    thinking: { type: 'adaptive' },
    output_config: { effort },
    stream: true,
    messages: body.messages, // incluye bloques de imagen si los hay
  });

  const upstream = requestUpstream(`${CFG.anthropicBase}/v1/messages`, {
    method: 'POST',
    headers: {
      'content-type': 'application/json',
      'x-api-key': CFG.anthropicKey,
      'anthropic-version': CFG.anthropicVersion,
      'content-length': Buffer.byteLength(upstreamBody),
    },
  }, (ures) => {
    if (ures.statusCode !== 200) {
      let b = ''; ures.on('data', (d) => (b += d)); ures.on('end', () => {
        logUse({ user: user.name, route: 'chat', ok: false, status: ures.statusCode });
        json(res, ures.statusCode, safeJson(b) || { error: 'error del proveedor', status: ures.statusCode });
      });
      return;
    }
    res.writeHead(200, { 'content-type': 'text/event-stream', 'cache-control': 'no-cache', connection: 'keep-alive' });
    let buf = '', usage = {};
    ures.on('data', (chunk) => {
      res.write(chunk);
      buf += chunk.toString('utf8');
      let i;
      while ((i = buf.indexOf('\n\n')) >= 0) { parseUsage(buf.slice(0, i), usage); buf = buf.slice(i + 2); }
    });
    ures.on('end', () => {
      res.end();
      logUse({ user: user.name, route: 'chat', model: CFG.model, ok: true, input_tokens: usage.in, output_tokens: usage.out });
    });
  });

  req.on('close', () => upstream.destroy());
  upstream.on('error', (e) => { if (!res.headersSent) json(res, 502, { error: 'no se pudo contactar al proveedor', detail: e.message }); else try { res.end(); } catch (_) {} });
  upstream.write(upstreamBody);
  upstream.end();
}

async function handleTts(req, res) {
  const user = auth(req, res); if (!user) return;
  if (limited(res, user)) return;
  if (!CFG.elevenKey) return json(res, 503, { error: 'voz no configurada (falta ELEVENLABS_API_KEY)' });

  const body = await readJson(req, res); if (body === undefined) return;
  const text = String(body.text || '').slice(0, 5000);
  if (!text.trim()) return json(res, 400, { error: 'falta texto' });
  const voiceId = String(body.voiceId || CFG.elevenVoice || '').trim();
  if (!voiceId) return json(res, 400, { error: 'no hay voz configurada' });

  const upstreamBody = JSON.stringify({
    text,
    model_id: CFG.elevenModel,
    voice_settings: { stability: 0.45, similarity_boost: 0.8, use_speaker_boost: true },
  });

  const upstream = requestUpstream(`${CFG.elevenBase}/v1/text-to-speech/${encodeURIComponent(voiceId)}/stream?output_format=mp3_44100_128`, {
    method: 'POST',
    headers: { 'content-type': 'application/json', 'xi-api-key': CFG.elevenKey, 'content-length': Buffer.byteLength(upstreamBody) },
  }, (ures) => {
    if (ures.statusCode !== 200) {
      let b = ''; ures.on('data', (d) => (b += d)); ures.on('end', () => { logUse({ user: user.name, route: 'tts', ok: false, status: ures.statusCode }); json(res, ures.statusCode, safeJson(b) || { error: 'error de voz' }); });
      return;
    }
    res.writeHead(200, { 'content-type': 'audio/mpeg', 'cache-control': 'no-cache' });
    ures.pipe(res);
    ures.on('end', () => logUse({ user: user.name, route: 'tts', ok: true, chars: text.length }));
  });
  req.on('close', () => upstream.destroy());
  upstream.on('error', (e) => { if (!res.headersSent) json(res, 502, { error: 'no se pudo generar la voz', detail: e.message }); });
  upstream.write(upstreamBody);
  upstream.end();
}

async function handleVoices(req, res) {
  const user = auth(req, res); if (!user) return;
  if (!CFG.elevenKey) return json(res, 503, { error: 'voz no configurada' });
  const upstream = requestUpstream(`${CFG.elevenBase}/v1/voices`, { method: 'GET', headers: { 'xi-api-key': CFG.elevenKey } }, (ures) => {
    let b = ''; ures.on('data', (d) => (b += d)); ures.on('end', () => json(res, ures.statusCode || 200, safeJson(b) || { error: 'respuesta no válida' }));
  });
  upstream.on('error', (e) => json(res, 502, { error: 'no se pudieron listar las voces', detail: e.message }));
  upstream.end();
}

/* ---------------- autenticación y límites ---------------- */

function auth(req, res) {
  const h = req.headers['authorization'] || '';
  const token = h.startsWith('Bearer ') ? h.slice(7).trim() : '';
  if (!token) { json(res, 401, { error: 'falta el código de acceso' }); return null; }
  const digest = sha256(token);
  for (const [known, user] of USERS) {
    if (known.length === digest.length && crypto.timingSafeEqual(Buffer.from(known), Buffer.from(digest))) return user;
  }
  json(res, 401, { error: 'código de acceso no válido' });
  return null;
}

function limited(res, user) {
  const now = Date.now();
  const arr = (rate.get(user.name) || []).filter((t) => now - t < 60000);
  if (arr.length >= CFG.ratePerMin) {
    res.setHeader('retry-after', '60');
    json(res, 429, { error: 'demasiadas peticiones, espera un momento' });
    return true;
  }
  arr.push(now);
  rate.set(user.name, arr);
  return false;
}

/* ---------------- utilidades ---------------- */

function setCors(req, res) {
  const origin = req.headers.origin || '';
  const ok = origin.startsWith('chrome-extension://') || CFG.extraOrigins.includes(origin);
  res.setHeader('Access-Control-Allow-Origin', ok ? origin : (CFG.extraOrigins[0] || '*'));
  res.setHeader('Vary', 'Origin');
  res.setHeader('Access-Control-Allow-Headers', 'authorization, content-type');
  res.setHeader('Access-Control-Allow-Methods', 'POST, GET, OPTIONS');
}

function requestUpstream(urlStr, opts, cb) {
  const u = new URL(urlStr);
  const mod = u.protocol === 'http:' ? http : https;
  return mod.request(u, opts, cb);
}

function readBody(req, res, max) {
  return new Promise((resolve) => {
    let size = 0; const chunks = [];
    req.on('data', (c) => {
      size += c.length;
      if (size > max) { json(res, 413, { error: 'petición demasiado grande' }); req.destroy(); resolve(undefined); }
      else chunks.push(c);
    });
    req.on('end', () => resolve(chunks.length ? Buffer.concat(chunks) : Buffer.alloc(0)));
    req.on('error', () => resolve(undefined));
  });
}

async function readJson(req, res) {
  const raw = await readBody(req, res, CFG.maxBodyBytes);
  if (raw === undefined) return undefined; // ya respondido
  try { return JSON.parse(raw.toString('utf8') || '{}'); }
  catch (_) { json(res, 400, { error: 'JSON no válido' }); return undefined; }
}

function parseUsage(eventText, usage) {
  for (const line of eventText.split('\n')) {
    if (!line.startsWith('data:')) continue;
    const obj = safeJson(line.slice(5).trim());
    if (!obj) continue;
    if (obj.type === 'message_start' && obj.message?.usage) {
      usage.in = obj.message.usage.input_tokens;
      if (obj.message.usage.cache_read_input_tokens) usage.cache_read = obj.message.usage.cache_read_input_tokens;
    } else if (obj.type === 'message_delta' && obj.usage) {
      usage.out = obj.usage.output_tokens;
    }
  }
}

function logUse(rec) {
  // Solo metadatos. NUNCA el contenido de mensajes ni capturas.
  const line = JSON.stringify({ ts: new Date().toISOString(), ...rec });
  if (CFG.logFile) { try { fs.appendFileSync(CFG.logFile, line + '\n'); } catch (_) {} }
  else console.log('[uso]', line);
}

function json(res, code, obj) {
  const body = JSON.stringify(obj);
  res.writeHead(code, { 'content-type': 'application/json', 'content-length': Buffer.byteLength(body) });
  res.end(body);
}

function sha256(s) { return crypto.createHash('sha256').update(s).digest('hex'); }
function safeJson(s) { try { return JSON.parse(s); } catch (_) { return null; } }

function loadUsers() {
  const map = new Map();
  const add = (token, name) => { if (token) map.set(sha256(token.trim()), { name: name || 'usuario' }); };
  if (process.env.USERS_FILE) {
    try {
      const arr = JSON.parse(fs.readFileSync(process.env.USERS_FILE, 'utf8'));
      for (const u of arr) add(u.token, u.name);
    } catch (e) { console.error('[backend] no pude leer USERS_FILE:', e.message); }
  }
  if (process.env.USERS) {
    for (const pair of process.env.USERS.split(',')) {
      const [token, name] = pair.split(':');
      add(token, name);
    }
  }
  return map;
}

function loadDotEnv(path) {
  try {
    for (const raw of fs.readFileSync(path, 'utf8').split('\n')) {
      const line = raw.trim();
      if (!line || line.startsWith('#')) continue;
      const eq = line.indexOf('=');
      if (eq < 0) continue;
      const key = line.slice(0, eq).trim();
      let val = line.slice(eq + 1).trim();
      if ((val.startsWith('"') && val.endsWith('"')) || (val.startsWith("'") && val.endsWith("'"))) val = val.slice(1, -1);
      if (!(key in process.env)) process.env[key] = val;
    }
  } catch (_) { /* .env es opcional */ }
}

process.on('SIGINT', () => { console.log('\n[backend] cerrando…'); process.exit(0); });
