#!/usr/bin/env node
/**
 * Puente local: extensión "Asistente Claude" ⇄ Claude Code (Agent SDK).
 *
 * Uso:
 *   node server.mjs [/ruta/de/tu/proyecto]
 *
 * - La primera pregunta CONTINÚA la conversación más reciente de Claude Code
 *   en ese directorio (la misma que ves con `claude --continue`).
 * - Variables opcionales:
 *     PUENTE_PORT=8787            puerto de escucha (solo 127.0.0.1)
 *     CLAUDE_SESSION_ID=<uuid>    reanudar una sesión concreta en vez de la última
 *     NUEVA=1                     empezar una conversación nueva
 *
 * Autenticación: usa las credenciales que ya tenga Claude Code en este
 * ordenador (tu login de `claude` o ANTHROPIC_API_KEY).
 */

import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import { WebSocketServer } from 'ws';
import { query } from '@anthropic-ai/claude-agent-sdk';

const PORT = Number(process.env.PUENTE_PORT || 8787);
const projectDir = path.resolve(process.argv[2] || process.cwd());
const resumeId = process.env.CLAUDE_SESSION_ID || null;
const forceNew = process.env.NUEVA === '1';
const PERMISSION_TIMEOUT_MS = 120_000;

// Herramientas de solo lectura que aprobamos sin preguntar.
const AUTO_ALLOW = new Set(['Read', 'Glob', 'Grep', 'WebSearch', 'WebFetch', 'TodoWrite', 'NotebookRead']);

/* ---------- ¿existe una conversación previa en este proyecto? ---------- */

function hasPreviousConversation(dir) {
  // Claude Code guarda transcripciones en ~/.claude/projects/<cwd-codificado>/*.jsonl
  const encoded = dir.replace(/[^a-zA-Z0-9]/g, '-');
  const base = process.env.CLAUDE_CONFIG_DIR || path.join(os.homedir(), '.claude');
  const projDir = path.join(base, 'projects', encoded);
  try {
    return fs.readdirSync(projDir).some((f) => f.endsWith('.jsonl'));
  } catch {
    return false;
  }
}

/* ---------- estado global ---------- */

let currentWs = null;          // panel conectado (el último gana)
let session = null;            // { push, interrupt, sessionId }
const pendingPerms = new Map();

function sendToPanel(obj) {
  if (currentWs && currentWs.readyState === 1) {
    try { currentWs.send(JSON.stringify(obj)); } catch {}
  }
}

/* ---------- sesión de Claude Code (una por proceso, arranque perezoso) ---------- */

function createSession({ tryContinue, resume }) {
  const queue = [];
  let wake = null;
  let lastContent = null;

  const push = (content) => {
    lastContent = content;
    queue.push(content);
    if (wake) { const w = wake; wake = null; w(); }
  };

  async function* input() {
    for (;;) {
      while (queue.length === 0) await new Promise((r) => { wake = r; });
      const content = queue.shift();
      yield {
        type: 'user',
        message: { role: 'user', content },
        parent_tool_use_id: null,
        session_id: '',
      };
    }
  }

  const q = query({
    prompt: input(),
    options: {
      cwd: projectDir,
      ...(resume ? { resume } : tryContinue ? { continue: true } : {}),
      permissionMode: 'default',
      // Las herramientas que no estén ya permitidas por tu configuración de
      // Claude Code se aprueban o deniegan desde el panel de la extensión.
      canUseTool: async (toolName, input) => {
        if (AUTO_ALLOW.has(toolName)) return { behavior: 'allow', updatedInput: input };
        const id = Math.random().toString(36).slice(2);
        sendToPanel({
          type: 'permission',
          id,
          tool: toolName,
          input: JSON.stringify(input).slice(0, 400),
        });
        const allowed = await new Promise((resolve) => {
          pendingPerms.set(id, resolve);
          setTimeout(() => { if (pendingPerms.delete(id)) resolve(false); }, PERMISSION_TIMEOUT_MS);
        });
        return allowed
          ? { behavior: 'allow', updatedInput: input }
          : { behavior: 'deny', message: 'Denegado por el usuario desde el asistente de voz.' };
      },
    },
  });

  const s = {
    push,
    interrupt: () => q.interrupt().catch(() => {}),
    sessionId: resume || null,
    lastContent: () => lastContent,
  };

  (async () => {
    try {
      for await (const m of q) {
        if (m.type === 'system' && m.subtype === 'init') {
          s.sessionId = m.session_id;
          console.log(`[puente] sesión activa: ${s.sessionId}`);
        } else if (m.type === 'assistant') {
          for (const block of m.message.content || []) {
            if (block.type === 'text' && block.text.trim()) {
              sendToPanel({ type: 'text', text: block.text });
            } else if (block.type === 'tool_use') {
              sendToPanel({ type: 'status', text: `usando ${block.name}…` });
            }
          }
        } else if (m.type === 'result') {
          if (m.subtype !== 'success') {
            sendToPanel({ type: 'error', text: 'Claude Code terminó con error: ' + m.subtype });
          }
          sendToPanel({ type: 'done' });
        }
      }
    } catch (e) {
      console.error('[puente] la sesión falló:', e.message);
      const noPrev = /no conversation|not found/i.test(String(e.message));
      session = null;
      // Si "--continue" falló porque no había conversación previa,
      // reintenta una vez con una conversación nueva.
      if (tryContinue && noPrev && s.lastContent()) {
        console.log('[puente] no había conversación previa; empiezo una nueva.');
        session = createSession({ tryContinue: false, resume: null });
        session.push(s.lastContent());
      } else {
        sendToPanel({ type: 'error', text: 'La sesión de Claude Code falló: ' + e.message });
        sendToPanel({ type: 'done' });
      }
    }
  })();

  return s;
}

function ensureSession() {
  if (session) return session;
  const tryContinue = !forceNew && !resumeId && hasPreviousConversation(projectDir);
  session = createSession({ tryContinue, resume: resumeId });
  return session;
}

/* ---------- servidor WebSocket (solo local) ---------- */

const wss = new WebSocketServer({ host: '127.0.0.1', port: PORT });

wss.on('listening', () => {
  console.log('╭──────────────────────────────────────────────────────╮');
  console.log('│  Puente Asistente Claude ⇄ Claude Code               │');
  console.log('╰──────────────────────────────────────────────────────╯');
  console.log(`[puente] escuchando en ws://127.0.0.1:${PORT}`);
  console.log(`[puente] proyecto: ${projectDir}`);
  if (resumeId) console.log(`[puente] reanudaré la sesión ${resumeId}`);
  else if (forceNew) console.log('[puente] empezaré una conversación nueva');
  else if (hasPreviousConversation(projectDir)) console.log('[puente] continuaré tu conversación más reciente de Claude Code en ese proyecto');
  else console.log('[puente] no hay conversación previa: empezaré una nueva');
  console.log('[puente] deja esta terminal abierta y usa la extensión en Chrome.');
});

wss.on('connection', (ws, req) => {
  const origin = req.headers.origin || '';
  // Solo aceptamos conexiones desde extensiones de Chrome (las webs normales
  // tendrían un origin http/https y quedan rechazadas).
  if (origin && !origin.startsWith('chrome-extension://')) {
    ws.close(1008, 'origen no permitido');
    return;
  }
  console.log('[puente] panel conectado');
  currentWs = ws;

  ws.on('close', () => { if (currentWs === ws) currentWs = null; });

  ws.on('message', (raw) => {
    let msg;
    try { msg = JSON.parse(raw.toString()); } catch { return; }

    if (msg.type === 'permission_response') {
      const resolver = pendingPerms.get(msg.id);
      if (resolver) { pendingPerms.delete(msg.id); resolver(msg.allow === true); }
      return;
    }

    if (msg.type === 'interrupt') {
      session?.interrupt();
      return;
    }

    if (msg.type !== 'ask') return;

    let prompt = String(msg.text || '').trim();
    if (!prompt) return;

    if (msg.image) {
      try {
        const file = path.join(os.tmpdir(), `captura-pantalla-${Date.now()}.jpg`);
        fs.writeFileSync(file, Buffer.from(msg.image, 'base64'));
        prompt += `\n\n(Te adjunto una captura actual de mi pantalla en ${file} — ábrela con la herramienta Read si ayuda a responder. Estoy hablando por voz: respóndeme breve y sin markdown.)`;
      } catch (e) {
        console.error('[puente] no pude guardar la captura:', e.message);
      }
    } else {
      prompt += '\n\n(Estoy hablando por voz: respóndeme breve y sin markdown.)';
    }

    console.log('[puente] pregunta:', prompt.split('\n')[0].slice(0, 80));
    ensureSession().push(prompt);
  });
});

process.on('SIGINT', () => {
  console.log('\n[puente] cerrando…');
  process.exit(0);
});
