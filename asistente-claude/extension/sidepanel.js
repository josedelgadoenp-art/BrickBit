'use strict';

/* ============================================================
   Asistente Claude — Pantalla y Voz (panel lateral)
   - Captura de pantalla con getDisplayMedia (fotogramas bajo demanda)
   - Voz del usuario con Web Speech API (SpeechRecognition)
   - Respuestas habladas con speechSynthesis
   - Modo "api": llama directamente a la API de Anthropic (streaming)
   - Modo "bridge": WebSocket a un puente local que continúa tu
     conversación de Claude Code (Agent SDK)
   ============================================================ */

const $ = (id) => document.getElementById(id);

const SYSTEM_PROMPT = `Eres un asistente de voz que ayuda al usuario mientras usa su ordenador.
Recibes sus preguntas transcritas por voz y, normalmente, una captura de su pantalla.
Normas:
- Responde en el idioma en el que hable el usuario (por defecto, español).
- Tus respuestas se leen en voz alta: usa frases cortas y naturales, sin markdown, sin asteriscos, sin listas con símbolos ni encabezados.
- Si te preguntan por algo visible en la captura, básate en ella. Si no se distingue bien, dilo y pide que amplíen o acerquen esa zona.
- Cuando guíes al usuario, da los pasos de uno en uno y espera a que pregunte por el siguiente si la tarea es larga.
- No leas en voz alta fragmentos largos de código; descríbelos y di dónde están.
- La transcripción de voz puede traer erratas: interpreta la intención con sentido común.`;

const DEFAULTS = {
  mode: 'api',
  apiKey: '',
  model: 'claude-opus-4-8',
  effort: 'low',
  language: 'es-ES',
  voiceName: '',
  autoSend: true,
  speakReplies: true,
  attachScreenshot: true,
  maxTokens: 1024,
  bridgeUrl: 'ws://127.0.0.1:8787',
};

const state = {
  settings: { ...DEFAULTS },
  history: [],              // [{role:'user'|'assistant', text}]
  stream: null,             // MediaStream de la pantalla
  micOn: false,
  recognition: null,
  recognizing: false,
  resumeMicAfterTTS: false,
  speakQueue: [],
  speakingNow: false,
  ttsBuffer: '',
  sending: false,
  abort: null,              // AbortController de la petición en curso (modo api)
  ws: null,
  wsOpenPromise: null,
  pendingAsk: null,         // {resolve, reject, onDelta} del ask en curso (modo bridge)
  autoSendTimer: null,
};

const video = $('preview');

/* ---------------- utilidades de interfaz ---------------- */

function setStatus(text, dotClass) {
  $('statusBar').textContent = text;
  $('statusDot').className = 'dot' + (dotClass ? ' ' + dotClass : '');
}

function addMsg(role, text) {
  const el = document.createElement('div');
  el.className = 'msg ' + role;
  el.textContent = text;
  $('chat').appendChild(el);
  el.scrollIntoView({ block: 'end' });
  return el;
}

function scrollChat() {
  const c = $('chat');
  c.scrollTop = c.scrollHeight;
}

/* ---------------- ajustes ---------------- */

async function loadSettings() {
  const stored = await chrome.storage.local.get('settings');
  state.settings = { ...DEFAULTS, ...(stored.settings || {}) };
  $('setMode').value = state.settings.mode;
  $('setApiKey').value = state.settings.apiKey;
  $('setModel').value = state.settings.model;
  $('setEffort').value = state.settings.effort;
  $('setLanguage').value = state.settings.language;
  $('setAutoSend').checked = state.settings.autoSend;
  $('setSpeak').checked = state.settings.speakReplies;
  $('setAttach').checked = state.settings.attachScreenshot;
  $('setBridgeUrl').value = state.settings.bridgeUrl;
  toggleModeSections();
  populateVoices();
}

function saveSettings() {
  state.settings = {
    ...state.settings,
    mode: $('setMode').value,
    apiKey: $('setApiKey').value.trim(),
    model: $('setModel').value,
    effort: $('setEffort').value,
    language: $('setLanguage').value,
    voiceName: $('setVoice').value,
    autoSend: $('setAutoSend').checked,
    speakReplies: $('setSpeak').checked,
    attachScreenshot: $('setAttach').checked,
    bridgeUrl: $('setBridgeUrl').value.trim() || DEFAULTS.bridgeUrl,
  };
  chrome.storage.local.set({ settings: state.settings });
  if (state.recognition) state.recognition.lang = state.settings.language;
}

function toggleModeSections() {
  const api = $('setMode').value === 'api';
  $('apiSettings').classList.toggle('hidden', !api);
  $('bridgeSettings').classList.toggle('hidden', api);
}

function populateVoices() {
  const sel = $('setVoice');
  const current = state.settings.voiceName;
  const voices = speechSynthesis.getVoices();
  sel.innerHTML = '<option value="">(voz por defecto)</option>';
  const prefix = (state.settings.language || 'es').slice(0, 2);
  for (const v of voices) {
    if (!v.lang.toLowerCase().startsWith(prefix)) continue;
    const o = document.createElement('option');
    o.value = v.name;
    o.textContent = `${v.name} (${v.lang})`;
    if (v.name === current) o.selected = true;
    sel.appendChild(o);
  }
}
speechSynthesis.onvoiceschanged = populateVoices;

/* ---------------- captura de pantalla ---------------- */

async function startShare() {
  try {
    const stream = await navigator.mediaDevices.getDisplayMedia({
      video: { frameRate: 5 },
      audio: false,
    });
    state.stream = stream;
    video.srcObject = stream;
    await video.play();
    stream.getVideoTracks()[0].addEventListener('ended', stopShare);
    $('btnShare').classList.add('active');
    addMsg('system', 'Pantalla compartida. Enviaré una captura con cada pregunta.');
    setStatus('Pantalla compartida. Te escucho cuando quieras.', state.micOn ? 'listening' : '');
  } catch (e) {
    addMsg('error', 'No se pudo compartir la pantalla: ' + e.message);
  }
}

function stopShare() {
  if (state.stream) {
    for (const t of state.stream.getTracks()) t.stop();
  }
  state.stream = null;
  video.srcObject = null;
  $('btnShare').classList.remove('active');
  addMsg('system', 'Captura de pantalla detenida.');
}

// Devuelve el fotograma actual como JPEG base64 (sin prefijo data:)
function captureFrame() {
  if (!state.stream) return null;
  const track = state.stream.getVideoTracks()[0];
  if (!track || track.readyState !== 'live') return null;
  const vw = video.videoWidth, vh = video.videoHeight;
  if (!vw || !vh) return null;
  const MAX = 1568; // lado largo máximo: buen equilibrio calidad/coste
  const scale = Math.min(1, MAX / Math.max(vw, vh));
  const canvas = document.createElement('canvas');
  canvas.width = Math.round(vw * scale);
  canvas.height = Math.round(vh * scale);
  canvas.getContext('2d').drawImage(video, 0, 0, canvas.width, canvas.height);
  return canvas.toDataURL('image/jpeg', 0.85).split(',')[1];
}

/* ---------------- voz del usuario (STT) ---------------- */

function initRecognition() {
  const SR = self.SpeechRecognition || self.webkitSpeechRecognition;
  if (!SR) {
    addMsg('error', 'Este navegador no soporta reconocimiento de voz (usa Chrome).');
    return null;
  }
  const r = new SR();
  r.lang = state.settings.language;
  r.continuous = true;
  r.interimResults = true;

  r.onresult = (e) => {
    let interim = '';
    let finals = '';
    for (let i = e.resultIndex; i < e.results.length; i++) {
      const res = e.results[i];
      if (res.isFinal) finals += res[0].transcript;
      else interim += res[0].transcript;
    }
    if (interim) {
      // si el usuario empieza a hablar mientras Claude habla, lo callamos
      if (state.speakingNow) cancelSpeech();
      $('interim').textContent = '… ' + interim;
    }
    if (finals.trim()) {
      $('interim').textContent = '';
      const input = $('input');
      input.value = (input.value ? input.value + ' ' : '') + finals.trim();
      autoGrowInput();
      if (state.settings.autoSend) scheduleAutoSend();
    }
  };

  r.onend = () => {
    state.recognizing = false;
    // Chrome corta el reconocimiento tras silencios: lo relanzamos si el mic sigue activo
    if (state.micOn && !state.speakingNow) {
      setTimeout(() => { if (state.micOn && !state.recognizing) startRecognition(); }, 250);
    }
  };

  r.onerror = (e) => {
    if (e.error === 'not-allowed' || e.error === 'service-not-allowed') {
      state.micOn = false;
      updateMicUI();
      addMsg('error', 'Permiso de micrófono denegado. Actívalo en el candado de la barra de direcciones o en la configuración del sitio.');
    }
  };
  return r;
}

function startRecognition() {
  if (!state.recognition) state.recognition = initRecognition();
  if (!state.recognition || state.recognizing) return;
  try {
    state.recognition.lang = state.settings.language;
    state.recognition.start();
    state.recognizing = true;
  } catch (_) { /* ya arrancado */ }
  updateMicUI();
}

function stopRecognition() {
  if (state.recognition && state.recognizing) {
    try { state.recognition.abort(); } catch (_) {}
  }
  state.recognizing = false;
  updateMicUI();
}

function toggleMic() {
  state.micOn = !state.micOn;
  if (state.micOn) {
    startRecognition();
    setStatus('Escuchando… habla cuando quieras.', 'listening');
  } else {
    stopRecognition();
    $('interim').textContent = '';
    setStatus('Micrófono apagado.');
  }
  updateMicUI();
}

function updateMicUI() {
  $('btnMic').classList.toggle('active', state.micOn);
  if (state.micOn && !state.sending && !state.speakingNow) $('statusDot').className = 'dot listening';
}

function scheduleAutoSend() {
  clearTimeout(state.autoSendTimer);
  state.autoSendTimer = setTimeout(() => {
    const q = $('input').value.trim();
    if (q && !state.sending) {
      $('input').value = '';
      autoGrowInput();
      sendQuestion(q);
    }
  }, 900);
}

/* ---------------- voz del asistente (TTS) ---------------- */

function cleanForSpeech(text) {
  return text
    .replace(/```[\s\S]*?```/g, ' (hay un bloque de código en el panel) ')
    .replace(/`([^`]+)`/g, '$1')
    .replace(/[*_#>|]+/g, ' ')
    .replace(/\[(.*?)\]\(.*?\)/g, '$1')
    .replace(/\s{2,}/g, ' ')
    .trim();
}

function feedTTS(text) {
  if (!state.settings.speakReplies) return;
  state.ttsBuffer += text;
  // extrae frases completas para ir hablando durante el streaming
  let m;
  while ((m = state.ttsBuffer.match(/^[\s\S]*?[.!?…\n]+(?=\s|$)/))) {
    const sentence = m[0];
    state.ttsBuffer = state.ttsBuffer.slice(sentence.length);
    enqueueSpeak(sentence);
  }
}

function flushTTS() {
  if (state.settings.speakReplies && state.ttsBuffer.trim()) enqueueSpeak(state.ttsBuffer);
  state.ttsBuffer = '';
}

function enqueueSpeak(text) {
  const clean = cleanForSpeech(text);
  if (!clean) return;
  state.speakQueue.push(clean);
  pumpSpeak();
}

function pickVoice() {
  const voices = speechSynthesis.getVoices();
  if (state.settings.voiceName) {
    const v = voices.find((v) => v.name === state.settings.voiceName);
    if (v) return v;
  }
  return voices.find((v) => v.lang === state.settings.language)
      || voices.find((v) => v.lang.startsWith(state.settings.language.slice(0, 2)))
      || null;
}

function pumpSpeak() {
  if (state.speakingNow || state.speakQueue.length === 0) return;
  // pausamos el micrófono mientras habla para no transcribirse a sí mismo
  if (state.recognizing) {
    state.resumeMicAfterTTS = true;
    stopRecognition();
  }
  const u = new SpeechSynthesisUtterance(state.speakQueue.shift());
  u.lang = state.settings.language;
  const v = pickVoice();
  if (v) u.voice = v;
  u.rate = 1.05;
  state.speakingNow = true;
  $('statusDot').className = 'dot speaking';
  u.onend = u.onerror = () => {
    state.speakingNow = false;
    if (state.speakQueue.length) pumpSpeak();
    else maybeResumeMic();
  };
  speechSynthesis.speak(u);
}

function maybeResumeMic() {
  if (!state.sending) $('statusDot').className = state.micOn ? 'dot listening' : 'dot';
  if (state.resumeMicAfterTTS && state.micOn) startRecognition();
  state.resumeMicAfterTTS = false;
}

function cancelSpeech() {
  state.speakQueue.length = 0;
  state.ttsBuffer = '';
  speechSynthesis.cancel();
  state.speakingNow = false;
  maybeResumeMic();
}

/* ---------------- envío de preguntas ---------------- */

async function sendQuestion(text) {
  if (!text.trim() || state.sending) return;
  state.sending = true;
  $('btnStop').classList.remove('hidden');
  cancelSpeech();

  const shot = state.settings.attachScreenshot ? captureFrame() : null;
  addMsg('user', text + (shot ? '  📸' : ''));
  const assistantEl = addMsg('assistant', '…');
  let full = '';
  const onDelta = (t) => {
    if (assistantEl.textContent === '…') assistantEl.textContent = '';
    full += t;
    assistantEl.textContent += t;
    feedTTS(t);
    scrollChat();
  };

  setStatus('Pensando…', 'thinking');
  try {
    if (state.settings.mode === 'api') {
      await askViaApi(text, shot, onDelta);
    } else {
      await askViaBridge(text, shot, onDelta);
    }
    if (!full.trim()) assistantEl.textContent = '(sin respuesta)';
    state.history.push({ role: 'user', text });
    state.history.push({ role: 'assistant', text: full });
    if (state.history.length > 16) state.history.splice(0, state.history.length - 16);
  } catch (e) {
    if (e.name === 'AbortError') {
      addMsg('system', 'Respuesta detenida.');
    } else {
      addMsg('error', e.message || String(e));
    }
    if (!full.trim()) assistantEl.remove();
  } finally {
    flushTTS();
    state.sending = false;
    state.abort = null;
    $('btnStop').classList.add('hidden');
    setStatus(state.micOn ? 'Escuchando…' : 'Listo.', state.micOn ? 'listening' : '');
  }
}

/* ---------------- modo API directa ---------------- */

async function askViaApi(text, shot, onDelta) {
  const s = state.settings;
  if (!s.apiKey) throw new Error('Falta la clave de API. Ábrela en Ajustes ⚙️ (console.anthropic.com → API keys).');

  const content = [];
  if (shot) {
    content.push({
      type: 'image',
      source: { type: 'base64', media_type: 'image/jpeg', data: shot },
    });
  }
  content.push({ type: 'text', text });

  const messages = state.history.map((m) => ({
    role: m.role,
    content: [{ type: 'text', text: m.text }],
  }));
  messages.push({ role: 'user', content });

  state.abort = new AbortController();
  const res = await fetch('https://api.anthropic.com/v1/messages', {
    method: 'POST',
    signal: state.abort.signal,
    headers: {
      'content-type': 'application/json',
      'x-api-key': s.apiKey,
      'anthropic-version': '2023-06-01',
      'anthropic-dangerous-direct-browser-access': 'true',
    },
    body: JSON.stringify({
      model: s.model,
      max_tokens: s.maxTokens,
      system: SYSTEM_PROMPT,
      thinking: { type: 'adaptive' },
      output_config: { effort: s.effort },
      stream: true,
      messages,
    }),
  });

  if (!res.ok) {
    let detail = 'HTTP ' + res.status;
    try {
      const j = await res.json();
      detail = j.error?.message || detail;
    } catch (_) {}
    throw new Error('Error de la API: ' + detail);
  }

  // lector de eventos SSE
  const reader = res.body.getReader();
  const decoder = new TextDecoder();
  let buf = '';
  while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    buf += decoder.decode(value, { stream: true });
    let idx;
    while ((idx = buf.indexOf('\n\n')) >= 0) {
      const rawEvent = buf.slice(0, idx);
      buf = buf.slice(idx + 2);
      for (const line of rawEvent.split('\n')) {
        if (!line.startsWith('data:')) continue;
        const data = line.slice(5).trim();
        if (!data) continue;
        let ev;
        try { ev = JSON.parse(data); } catch (_) { continue; }
        if (ev.type === 'content_block_delta' && ev.delta?.type === 'text_delta') {
          onDelta(ev.delta.text);
        } else if (ev.type === 'message_delta' && ev.delta?.stop_reason === 'refusal') {
          onDelta(' No puedo ayudar con esa petición.');
        } else if (ev.type === 'error') {
          throw new Error('Error de la API: ' + (ev.error?.message || 'desconocido'));
        }
      }
    }
  }
}

/* ---------------- modo puente Claude Code ---------------- */

function connectBridge() {
  if (state.ws && state.ws.readyState === WebSocket.OPEN) return Promise.resolve();
  if (state.wsOpenPromise) return state.wsOpenPromise;

  state.wsOpenPromise = new Promise((resolve, reject) => {
    let settled = false;
    const ws = new WebSocket(state.settings.bridgeUrl);
    state.ws = ws;

    ws.onopen = () => { settled = true; resolve(); };
    ws.onerror = () => {
      if (!settled) {
        settled = true;
        reject(new Error('No se pudo conectar con el puente local (' + state.settings.bridgeUrl + '). ¿Has arrancado "node server.mjs" en tu ordenador?'));
      }
    };
    ws.onclose = () => {
      state.ws = null;
      state.wsOpenPromise = null;
      if (state.pendingAsk) {
        state.pendingAsk.reject(new Error('Se cerró la conexión con el puente local.'));
        state.pendingAsk = null;
      }
    };
    ws.onmessage = (e) => handleBridgeMessage(e.data);
  }).finally(() => { state.wsOpenPromise = null; });

  return state.wsOpenPromise;
}

function handleBridgeMessage(raw) {
  let msg;
  try { msg = JSON.parse(raw); } catch (_) { return; }
  const ask = state.pendingAsk;
  switch (msg.type) {
    case 'text':
      if (ask) ask.onDelta((ask.gotText ? '\n' : '') + msg.text), (ask.gotText = true);
      break;
    case 'status':
      setStatus('Claude Code: ' + msg.text, 'thinking');
      break;
    case 'permission':
      renderPermissionRequest(msg);
      break;
    case 'done':
      if (ask) { ask.resolve(); state.pendingAsk = null; }
      break;
    case 'error':
      if (ask) { ask.reject(new Error(msg.text)); state.pendingAsk = null; }
      else addMsg('error', msg.text);
      break;
  }
}

function renderPermissionRequest(msg) {
  const el = document.createElement('div');
  el.className = 'msg system';
  el.textContent = `Claude Code quiere usar la herramienta "${msg.tool}":\n${msg.input}`;
  const actions = document.createElement('div');
  actions.className = 'perm-actions';
  const allow = document.createElement('button');
  allow.className = 'allow';
  allow.textContent = 'Permitir';
  const deny = document.createElement('button');
  deny.className = 'deny';
  deny.textContent = 'Denegar';
  const answer = (ok) => {
    if (state.ws && state.ws.readyState === WebSocket.OPEN) {
      state.ws.send(JSON.stringify({ type: 'permission_response', id: msg.id, allow: ok }));
    }
    actions.remove();
    el.textContent += ok ? '\n✅ Permitido' : '\n⛔ Denegado';
  };
  allow.onclick = () => answer(true);
  deny.onclick = () => answer(false);
  actions.append(allow, deny);
  el.appendChild(actions);
  $('chat').appendChild(el);
  scrollChat();
  enqueueSpeak(`Claude Code pide permiso para usar ${msg.tool}. Pulsa permitir o denegar.`);
}

async function askViaBridge(text, shot, onDelta) {
  await connectBridge();
  return new Promise((resolve, reject) => {
    state.pendingAsk = { resolve, reject, onDelta, gotText: false };
    state.ws.send(JSON.stringify({ type: 'ask', text, image: shot || undefined }));
  });
}

function stopCurrent() {
  if (state.settings.mode === 'api' && state.abort) {
    state.abort.abort();
  } else if (state.ws && state.ws.readyState === WebSocket.OPEN) {
    state.ws.send(JSON.stringify({ type: 'interrupt' }));
  }
  cancelSpeech();
}

/* ---------------- arranque e interfaz ---------------- */

function autoGrowInput() {
  const t = $('input');
  t.style.height = 'auto';
  t.style.height = Math.min(t.scrollHeight, 110) + 'px';
}

function bindUI() {
  $('btnShare').onclick = () => (state.stream ? stopShare() : startShare());
  $('btnMic').onclick = toggleMic;
  $('btnStopVoice').onclick = cancelSpeech;
  $('btnStop').onclick = stopCurrent;

  $('btnSend').onclick = () => {
    const q = $('input').value.trim();
    if (q) {
      $('input').value = '';
      autoGrowInput();
      sendQuestion(q);
    }
  };
  $('input').addEventListener('keydown', (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      $('btnSend').click();
    }
  });
  $('input').addEventListener('input', autoGrowInput);

  $('btnSettings').onclick = () => $('settings').classList.toggle('hidden');
  $('btnCloseSettings').onclick = () => {
    saveSettings();
    $('settings').classList.add('hidden');
    addMsg('system', 'Ajustes guardados (modo: ' + (state.settings.mode === 'api' ? 'API directa' : 'puente Claude Code') + ').');
  };
  $('setMode').onchange = toggleModeSections;
  $('setLanguage').onchange = populateVoices;
  for (const id of ['setApiKey', 'setModel', 'setEffort', 'setLanguage', 'setVoice', 'setAutoSend', 'setSpeak', 'setAttach', 'setBridgeUrl', 'setMode']) {
    $(id).addEventListener('change', saveSettings);
  }
}

(async function init() {
  bindUI();
  await loadSettings();
  addMsg('system', 'Hola 👋 Comparte tu pantalla, activa el micrófono y pregúntame lo que quieras. Configura el modo de conexión en ⚙️.');
})();
