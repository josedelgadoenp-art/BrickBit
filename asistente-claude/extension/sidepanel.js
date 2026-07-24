'use strict';

/* ============================================================
   Asistente Claude — Pantalla y Voz (panel lateral)
   - Captura de pantalla (getDisplayMedia) → fotograma por pregunta
   - Voz del usuario: Web Speech API (SpeechRecognition)
   - Voz del asistente: navegador (speechSynthesis) o ElevenLabs
   - Conexión: API de Anthropic (streaming) o puente a Claude Code
   ============================================================ */

const $ = (id) => document.getElementById(id);
const icon = (name) => `<svg class="ic"><use href="#i-${name}"/></svg>`;

/* ---------------- marca (white-label) ---------------- */
function applyBrand() {
  const b = window.BRAND;
  if (!b) return;
  const root = document.documentElement;
  if (b.brand) root.style.setProperty('--brand', b.brand);
  if (b.brand2) root.style.setProperty('--brand-2', b.brand2);
  if (b.name) { $('brandName').textContent = b.name; document.title = b.name; }
  if (b.subtitle) $('brandSub').textContent = b.subtitle;
  if (b.logo) {
    const img = new Image();
    img.src = b.logo;
    img.alt = b.name || '';
    img.style.cssText = 'width:100%;height:100%;object-fit:contain;border-radius:inherit';
    img.onload = () => { const m = $('brandMark'); m.innerHTML = ''; m.style.background = 'transparent'; m.style.boxShadow = 'none'; m.appendChild(img); };
  }
  if (b.welcomeTitle && $('emptyState')) { const h = $('emptyState').querySelector('h2'); if (h) h.textContent = b.welcomeTitle; }
  if (b.welcomeText && $('emptyState')) { const p = $('emptyState').querySelector('p'); if (p) p.textContent = b.welcomeText; }
}

const SYSTEM_PROMPT = `Eres un asistente de voz que ayuda al usuario mientras usa su ordenador.
Recibes sus preguntas transcritas por voz y, normalmente, una captura de su pantalla.
Normas:
- Responde en el idioma en el que hable el usuario (por defecto, español de México).
- Tus respuestas se leen en voz alta: usa frases cortas y naturales, sin markdown, sin asteriscos, sin listas con símbolos ni encabezados.
- Si te preguntan por algo visible en la captura, básate en ella. Si no se distingue bien, dilo y pide que amplíen esa zona.
- Cuando guíes al usuario, da los pasos de uno en uno y espera a que pregunte por el siguiente si la tarea es larga.
- No leas en voz alta fragmentos largos de código; descríbelos y di dónde están.
- La transcripción de voz puede traer erratas: interpreta la intención con sentido común.`;

const DEFAULTS = {
  theme: 'auto',
  mode: 'api',
  apiKey: '',
  model: 'claude-opus-4-8',
  effort: 'low',
  language: 'es-MX',
  ttsProvider: 'browser',
  voiceName: '',
  elevenKey: '',
  elevenModel: 'eleven_flash_v2_5',
  elevenVoiceId: '',
  elevenVoiceName: '',
  autoSend: true,
  speakReplies: true,
  attachScreenshot: true,
  maxTokens: 1024,
  bridgeUrl: 'ws://127.0.0.1:8787',
};

const state = {
  settings: { ...DEFAULTS },
  history: [],
  stream: null,
  micOn: false,
  recognition: null,
  recognizing: false,
  resumeMicAfterTTS: false,
  sending: false,
  abort: null,
  ws: null,
  wsOpenPromise: null,
  pendingAsk: null,
  autoSendTimer: null,
  hasMessages: false,
};

// cola de voz
const tts = {
  textQueue: [],
  running: false,
  currentAudio: null,
  nextAudioPromise: null,
  buffer: '',
};

const video = $('preview');

/* ---------------- interfaz base ---------------- */

function setStatus(text, dotClass) {
  $('statusText').textContent = text;
  $('statusDot').className = 'dot' + (dotClass ? ' ' + dotClass : '');
}

function ensureChatReady() {
  if (!state.hasMessages) { $('emptyState').remove(); state.hasMessages = true; }
}

function addMsg(role, text) {
  ensureChatReady();
  const el = document.createElement('div');
  el.className = 'msg ' + role;
  el.textContent = text;
  $('chat').appendChild(el);
  el.scrollIntoView({ block: 'end' });
  return el;
}

function scrollChat() { const c = $('chat'); c.scrollTop = c.scrollHeight; }

/* ---------------- tema ---------------- */

function applyTheme() {
  const t = state.settings.theme;
  const root = document.documentElement;
  if (t === 'auto') root.removeAttribute('data-theme');
  else root.setAttribute('data-theme', t);
  const dark = t === 'dark' || (t === 'auto' && matchMedia('(prefers-color-scheme: dark)').matches);
  $('btnTheme').innerHTML = icon(dark ? 'sun' : 'moon');
}

function toggleTheme() {
  const order = { auto: 'light', light: 'dark', dark: 'auto' };
  state.settings.theme = order[state.settings.theme] || 'dark';
  applyTheme();
  chrome.storage.local.set({ settings: state.settings });
}

/* ---------------- ajustes ---------------- */

async function loadSettings() {
  const stored = await chrome.storage.local.get('settings');
  state.settings = { ...DEFAULTS, ...(stored.settings || {}) };
  const s = state.settings;
  $('setMode').value = s.mode;
  $('setApiKey').value = s.apiKey;
  $('setModel').value = s.model;
  $('setEffort').value = s.effort;
  $('setLanguage').value = s.language;
  $('setTtsProvider').value = s.ttsProvider;
  $('setElevenKey').value = s.elevenKey;
  $('setElevenModel').value = s.elevenModel;
  $('setAutoSend').checked = s.autoSend;
  $('setSpeak').checked = s.speakReplies;
  $('setAttach').checked = s.attachScreenshot;
  $('setBridgeUrl').value = s.bridgeUrl;
  if (s.elevenVoiceId) {
    const o = document.createElement('option');
    o.value = s.elevenVoiceId; o.textContent = s.elevenVoiceName || s.elevenVoiceId; o.selected = true;
    $('setElevenVoice').appendChild(o);
  }
  applyTheme();
  toggleModeSections();
  toggleVoiceSections();
  populateBrowserVoices();
}

function saveSettings() {
  const s = state.settings;
  s.mode = $('setMode').value;
  s.apiKey = $('setApiKey').value.trim();
  s.model = $('setModel').value;
  s.effort = $('setEffort').value;
  s.language = $('setLanguage').value;
  s.ttsProvider = $('setTtsProvider').value;
  s.voiceName = $('setVoice').value;
  s.elevenKey = $('setElevenKey').value.trim();
  s.elevenModel = $('setElevenModel').value;
  s.elevenVoiceId = $('setElevenVoice').value;
  s.elevenVoiceName = $('setElevenVoice').selectedOptions[0]?.textContent || '';
  s.autoSend = $('setAutoSend').checked;
  s.speakReplies = $('setSpeak').checked;
  s.attachScreenshot = $('setAttach').checked;
  s.bridgeUrl = $('setBridgeUrl').value.trim() || DEFAULTS.bridgeUrl;
  chrome.storage.local.set({ settings: s });
  if (state.recognition) state.recognition.lang = s.language;
}

function toggleModeSections() {
  const api = $('setMode').value === 'api';
  $('apiSettings').classList.toggle('hidden', !api);
  $('bridgeSettings').classList.toggle('hidden', api);
}

function toggleVoiceSections() {
  const eleven = $('setTtsProvider').value === 'elevenlabs';
  $('elevenVoice').classList.toggle('hidden', !eleven);
  $('browserVoice').classList.toggle('hidden', eleven);
}

function populateBrowserVoices() {
  const sel = $('setVoice');
  const current = state.settings.voiceName;
  const voices = speechSynthesis.getVoices();
  sel.innerHTML = '<option value="">(voz por defecto)</option>';
  const prefix = (state.settings.language || 'es').slice(0, 2);
  for (const v of voices) {
    if (!v.lang.toLowerCase().startsWith(prefix)) continue;
    const o = document.createElement('option');
    o.value = v.name; o.textContent = `${v.name} (${v.lang})`;
    if (v.name === current) o.selected = true;
    sel.appendChild(o);
  }
}
speechSynthesis.onvoiceschanged = populateBrowserVoices;

/* ---------------- ElevenLabs: cargar voces / probar ---------------- */

async function loadElevenVoices() {
  const key = $('setElevenKey').value.trim();
  if (!key) { addMsg('error', 'Escribe primero tu clave de ElevenLabs.'); return; }
  const btn = $('btnLoadVoices'); btn.disabled = true; btn.textContent = 'Cargando…';
  try {
    const res = await fetch('https://api.elevenlabs.io/v1/voices', { headers: { 'xi-api-key': key } });
    if (!res.ok) throw new Error('HTTP ' + res.status);
    const data = await res.json();
    const sel = $('setElevenVoice');
    const prev = state.settings.elevenVoiceId;
    sel.innerHTML = '';
    for (const v of data.voices || []) {
      const o = document.createElement('option');
      o.value = v.voice_id; o.textContent = v.name;
      if (v.voice_id === prev) o.selected = true;
      sel.appendChild(o);
    }
    if (!sel.options.length) sel.innerHTML = '<option value="">(sin voces en tu cuenta)</option>';
    addMsg('system', `Cargadas ${data.voices?.length || 0} voces de ElevenLabs.`);
  } catch (e) {
    addMsg('error', 'No pude cargar las voces: ' + e.message + ' (¿clave correcta?)');
  } finally {
    btn.disabled = false; btn.textContent = 'Cargar mis voces';
  }
}

async function testVoice() {
  saveSettings();
  cancelSpeech();
  enqueueSpeak('Hola, soy tu asistente. Así sonará mi voz.');
}

/* ---------------- captura de pantalla ---------------- */

async function startShare() {
  try {
    const stream = await navigator.mediaDevices.getDisplayMedia({ video: { frameRate: 5 }, audio: false });
    state.stream = stream;
    video.srcObject = stream;
    await video.play();
    stream.getVideoTracks()[0].addEventListener('ended', stopShare);
    $('btnShare').classList.add('active');
    addMsg('system', 'Pantalla compartida. Enviaré una captura con cada pregunta.');
    setStatus(state.micOn ? 'Escuchando' : 'Listo', state.micOn ? 'listening' : '');
  } catch (e) {
    addMsg('error', 'No se pudo compartir la pantalla: ' + e.message);
  }
}

function stopShare() {
  if (state.stream) for (const t of state.stream.getTracks()) t.stop();
  state.stream = null;
  video.srcObject = null;
  $('btnShare').classList.remove('active');
  addMsg('system', 'Captura de pantalla detenida.');
}

function captureFrame() {
  if (!state.stream) return null;
  const track = state.stream.getVideoTracks()[0];
  if (!track || track.readyState !== 'live') return null;
  const vw = video.videoWidth, vh = video.videoHeight;
  if (!vw || !vh) return null;
  const MAX = 1568;
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
  if (!SR) { addMsg('error', 'Este navegador no soporta reconocimiento de voz (usa Chrome).'); return null; }
  const r = new SR();
  r.lang = state.settings.language;
  r.continuous = true;
  r.interimResults = true;

  r.onresult = (e) => {
    let interim = '', finals = '';
    for (let i = e.resultIndex; i < e.results.length; i++) {
      const res = e.results[i];
      if (res.isFinal) finals += res[0].transcript; else interim += res[0].transcript;
    }
    if (interim) {
      if (tts.running) cancelSpeech(); // barge-in: el usuario habla → callamos a Claude
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
    if (state.micOn && !tts.running) setTimeout(() => { if (state.micOn && !state.recognizing) startRecognition(); }, 250);
  };
  r.onerror = (e) => {
    if (e.error === 'not-allowed' || e.error === 'service-not-allowed') {
      state.micOn = false; updateMicUI();
      addMsg('error', 'Permiso de micrófono denegado. Actívalo en el candado de la barra de direcciones.');
    }
  };
  return r;
}

function startRecognition() {
  if (!state.recognition) state.recognition = initRecognition();
  if (!state.recognition || state.recognizing) return;
  try { state.recognition.lang = state.settings.language; state.recognition.start(); state.recognizing = true; }
  catch (_) {}
  updateMicUI();
}

function stopRecognition() {
  if (state.recognition && state.recognizing) { try { state.recognition.abort(); } catch (_) {} }
  state.recognizing = false;
  updateMicUI();
}

function toggleMic() {
  state.micOn = !state.micOn;
  if (state.micOn) { startRecognition(); setStatus('Escuchando', 'listening'); }
  else { stopRecognition(); $('interim').textContent = ''; setStatus('Micrófono apagado'); }
  updateMicUI();
}

function updateMicUI() {
  $('btnMic').classList.toggle('active', state.micOn);
  if (state.micOn && !state.sending && !tts.running) $('statusDot').className = 'dot listening';
}

function scheduleAutoSend() {
  clearTimeout(state.autoSendTimer);
  state.autoSendTimer = setTimeout(() => {
    const q = $('input').value.trim();
    if (q && !state.sending) { $('input').value = ''; autoGrowInput(); sendQuestion(q); }
  }, 900);
}

/* ---------------- voz del asistente (TTS) ---------------- */

function useEleven() {
  return state.settings.ttsProvider === 'elevenlabs' && state.settings.elevenKey && state.settings.elevenVoiceId;
}

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
  tts.buffer += text;
  let m;
  while ((m = tts.buffer.match(/^[\s\S]*?[.!?…\n]+(?=\s|$)/))) {
    const sentence = m[0];
    tts.buffer = tts.buffer.slice(sentence.length);
    enqueueSpeak(sentence);
  }
}
function flushTTS() {
  if (state.settings.speakReplies && tts.buffer.trim()) enqueueSpeak(tts.buffer);
  tts.buffer = '';
}

function enqueueSpeak(text) {
  const clean = cleanForSpeech(text);
  if (!clean) return;
  tts.textQueue.push(clean);
  ttsPump();
}

function pauseMicForTTS() {
  if (state.recognizing) { state.resumeMicAfterTTS = true; stopRecognition(); }
}
function maybeResumeMic() {
  if (!state.sending) $('statusDot').className = state.micOn ? 'dot listening' : 'dot';
  if (state.resumeMicAfterTTS && state.micOn) startRecognition();
  state.resumeMicAfterTTS = false;
}

async function ttsPump() {
  if (tts.running) return;
  tts.running = true;
  pauseMicForTTS();
  $('statusDot').className = 'dot speaking';
  while (tts.textQueue.length) {
    const text = tts.textQueue.shift();
    if (useEleven()) {
      const promise = tts.nextAudioPromise || elevenFetch(text);
      tts.nextAudioPromise = null;
      if (tts.textQueue.length) tts.nextAudioPromise = elevenFetch(tts.textQueue[0]).catch(() => null);
      let url = null;
      try { url = await promise; } catch (_) {}
      if (url) { try { await playUrl(url); } catch (_) {} }
      else { await browserSpeak(text); } // si ElevenLabs falla, usa el navegador
    } else {
      await browserSpeak(text);
    }
    if (!tts.running) break; // cancelado
  }
  tts.running = false;
  maybeResumeMic();
}

async function elevenFetch(text) {
  const s = state.settings;
  const url = `https://api.elevenlabs.io/v1/text-to-speech/${s.elevenVoiceId}/stream?output_format=mp3_44100_128`;
  const res = await fetch(url, {
    method: 'POST',
    headers: { 'xi-api-key': s.elevenKey, 'content-type': 'application/json' },
    body: JSON.stringify({
      text,
      model_id: s.elevenModel,
      voice_settings: { stability: 0.45, similarity_boost: 0.8, style: 0.0, use_speaker_boost: true },
    }),
  });
  if (!res.ok) throw new Error('ElevenLabs HTTP ' + res.status);
  const buf = await res.arrayBuffer();
  return URL.createObjectURL(new Blob([buf], { type: 'audio/mpeg' }));
}

function playUrl(url) {
  return new Promise((resolve) => {
    const a = new Audio(url);
    tts.currentAudio = a;
    const done = () => { URL.revokeObjectURL(url); if (tts.currentAudio === a) tts.currentAudio = null; resolve(); };
    a.onended = done;
    a.onerror = done;
    a.play().catch(done);
  });
}

function browserSpeak(text) {
  return new Promise((resolve) => {
    if (!('speechSynthesis' in window)) return resolve();
    const u = new SpeechSynthesisUtterance(text);
    u.lang = state.settings.language;
    const v = pickBrowserVoice();
    if (v) u.voice = v;
    u.rate = 1.05;
    u.onend = u.onerror = () => resolve();
    tts.currentAudio = { _utter: u };
    speechSynthesis.speak(u);
  });
}

function pickBrowserVoice() {
  const voices = speechSynthesis.getVoices();
  if (state.settings.voiceName) { const v = voices.find((v) => v.name === state.settings.voiceName); if (v) return v; }
  return voices.find((v) => v.lang === state.settings.language)
      || voices.find((v) => v.lang.startsWith(state.settings.language.slice(0, 2))) || null;
}

function cancelSpeech() {
  tts.textQueue.length = 0;
  tts.buffer = '';
  tts.nextAudioPromise = null;
  tts.running = false;
  if (tts.currentAudio && tts.currentAudio.pause) { try { tts.currentAudio.pause(); tts.currentAudio.src = ''; } catch (_) {} }
  tts.currentAudio = null;
  try { speechSynthesis.cancel(); } catch (_) {}
  maybeResumeMic();
}

/* ---------------- envío de preguntas ---------------- */

async function sendQuestion(text) {
  if (!text.trim() || state.sending) return;
  state.sending = true;
  $('btnStop').classList.remove('hidden');
  cancelSpeech();

  const shot = state.settings.attachScreenshot ? captureFrame() : null;
  const userEl = addMsg('user', text);
  if (shot) { const t = document.createElement('span'); t.className = 'tag'; t.textContent = '📸'; userEl.appendChild(t); }
  const assistantEl = addMsg('assistant', '…');
  let full = '';
  const onDelta = (t) => {
    if (assistantEl.textContent === '…') assistantEl.textContent = '';
    full += t; assistantEl.textContent += t; feedTTS(t); scrollChat();
  };

  setStatus('Pensando', 'thinking');
  try {
    if (state.settings.mode === 'api') await askViaApi(text, shot, onDelta);
    else await askViaBridge(text, shot, onDelta);
    if (!full.trim()) assistantEl.textContent = '(sin respuesta)';
    state.history.push({ role: 'user', text });
    state.history.push({ role: 'assistant', text: full });
    if (state.history.length > 16) state.history.splice(0, state.history.length - 16);
  } catch (e) {
    if (e.name === 'AbortError') addMsg('system', 'Respuesta detenida.');
    else addMsg('error', e.message || String(e));
    if (!full.trim()) assistantEl.remove();
  } finally {
    flushTTS();
    state.sending = false;
    state.abort = null;
    $('btnStop').classList.add('hidden');
    setStatus(state.micOn ? 'Escuchando' : 'Listo', state.micOn ? 'listening' : '');
  }
}

/* ---------------- modo API directa ---------------- */

async function askViaApi(text, shot, onDelta) {
  const s = state.settings;
  if (!s.apiKey) throw new Error('Falta la clave de API. Ábrela en Ajustes (console.anthropic.com → API keys).');

  const content = [];
  if (shot) content.push({ type: 'image', source: { type: 'base64', media_type: 'image/jpeg', data: shot } });
  content.push({ type: 'text', text });

  const messages = state.history.map((m) => ({ role: m.role, content: [{ type: 'text', text: m.text }] }));
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
    try { const j = await res.json(); detail = j.error?.message || detail; } catch (_) {}
    throw new Error('Error de la API: ' + detail);
  }

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
        let ev; try { ev = JSON.parse(data); } catch (_) { continue; }
        if (ev.type === 'content_block_delta' && ev.delta?.type === 'text_delta') onDelta(ev.delta.text);
        else if (ev.type === 'message_delta' && ev.delta?.stop_reason === 'refusal') onDelta(' No puedo ayudar con esa petición.');
        else if (ev.type === 'error') throw new Error('Error de la API: ' + (ev.error?.message || 'desconocido'));
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
    ws.onerror = () => { if (!settled) { settled = true; reject(new Error('No se pudo conectar con el puente local (' + state.settings.bridgeUrl + '). ¿Arrancaste "node server.mjs"?')); } };
    ws.onclose = () => {
      state.ws = null; state.wsOpenPromise = null;
      if (state.pendingAsk) { state.pendingAsk.reject(new Error('Se cerró la conexión con el puente local.')); state.pendingAsk = null; }
    };
    ws.onmessage = (e) => handleBridgeMessage(e.data);
  }).finally(() => { state.wsOpenPromise = null; });
  return state.wsOpenPromise;
}

function handleBridgeMessage(raw) {
  let msg; try { msg = JSON.parse(raw); } catch (_) { return; }
  const ask = state.pendingAsk;
  switch (msg.type) {
    case 'text': if (ask) { ask.onDelta((ask.gotText ? '\n' : '') + msg.text); ask.gotText = true; } break;
    case 'status': setStatus('Claude Code: ' + msg.text, 'thinking'); break;
    case 'permission': renderPermissionRequest(msg); break;
    case 'done': if (ask) { ask.resolve(); state.pendingAsk = null; } break;
    case 'error': if (ask) { ask.reject(new Error(msg.text)); state.pendingAsk = null; } else addMsg('error', msg.text); break;
  }
}

function renderPermissionRequest(msg) {
  ensureChatReady();
  const el = document.createElement('div');
  el.className = 'msg system';
  el.textContent = `Claude Code quiere usar "${msg.tool}":\n${msg.input}`;
  const actions = document.createElement('div');
  actions.className = 'perm-actions';
  const allow = document.createElement('button'); allow.className = 'allow'; allow.textContent = 'Permitir';
  const deny = document.createElement('button'); deny.className = 'deny'; deny.textContent = 'Denegar';
  const answer = (ok) => {
    if (state.ws && state.ws.readyState === WebSocket.OPEN) state.ws.send(JSON.stringify({ type: 'permission_response', id: msg.id, allow: ok }));
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
  if (state.settings.mode === 'api' && state.abort) state.abort.abort();
  else if (state.ws && state.ws.readyState === WebSocket.OPEN) state.ws.send(JSON.stringify({ type: 'interrupt' }));
  cancelSpeech();
}

/* ---------------- arranque e interfaz ---------------- */

function autoGrowInput() {
  const t = $('input');
  t.style.height = 'auto';
  t.style.height = Math.min(t.scrollHeight, 120) + 'px';
}

function bindUI() {
  $('btnShare').onclick = () => (state.stream ? stopShare() : startShare());
  $('btnMic').onclick = toggleMic;
  $('btnMute').onclick = cancelSpeech;
  $('btnStop').onclick = stopCurrent;
  $('btnTheme').onclick = toggleTheme;

  $('btnSend').onclick = () => {
    const q = $('input').value.trim();
    if (q) { $('input').value = ''; autoGrowInput(); sendQuestion(q); }
  };
  $('input').addEventListener('keydown', (e) => {
    if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); $('btnSend').click(); }
  });
  $('input').addEventListener('input', autoGrowInput);

  // chips del estado vacío
  document.querySelectorAll('.chip').forEach((c) => {
    c.onclick = () => sendQuestion(c.dataset.q);
  });

  $('btnSettings').onclick = () => $('settings').classList.remove('hidden');
  $('btnCloseX').onclick = () => $('settings').classList.add('hidden');
  $('btnCloseSettings').onclick = () => {
    saveSettings();
    $('settings').classList.add('hidden');
    addMsg('system', 'Ajustes guardados.');
  };
  $('setMode').onchange = toggleModeSections;
  $('setTtsProvider').onchange = toggleVoiceSections;
  $('setLanguage').onchange = populateBrowserVoices;
  $('btnLoadVoices').onclick = loadElevenVoices;
  $('btnTestVoice').onclick = testVoice;

  for (const id of ['setApiKey','setModel','setEffort','setLanguage','setVoice','setAutoSend','setSpeak','setAttach','setBridgeUrl','setMode','setTtsProvider','setElevenKey','setElevenModel','setElevenVoice']) {
    $(id).addEventListener('change', saveSettings);
  }
  matchMedia('(prefers-color-scheme: dark)').addEventListener('change', () => { if (state.settings.theme === 'auto') applyTheme(); });
}

(async function init() {
  applyBrand();
  bindUI();
  await loadSettings();
})();
