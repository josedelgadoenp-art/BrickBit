'use strict';

/* ============================================================
   Base de conocimiento (RAG) — sin dependencias externas.
   · Lee documentos .txt / .md de una carpeta.
   · Los parte en fragmentos y construye un índice BM25.
   · Ante una pregunta, devuelve los fragmentos más relevantes
     para inyectarlos en el prompt (respuestas fundamentadas).

   Para un piloto y demos, BM25 (búsqueda por relevancia de
   términos) funciona muy bien y no necesita otro proveedor ni
   otra clave. Para corpus enormes en producción se puede migrar
   a embeddings vectoriales (Voyage/OpenAI) — ver README.
   ============================================================ */

import fs from 'node:fs';
import path from 'node:path';

const K1 = 1.5, B = 0.75;

// palabras vacías del español (mejoran la relevancia)
const STOP = new Set(('de la que el en y a los las un una para con no por su al lo como mas o este esta pero sus le ya se me si sin sobre entre cuando todo esta ser son dos tiene tienen del es' ).split(' '));

function norm(s) {
  return s.toLowerCase().normalize('NFD').replace(/[̀-ͯ]/g, '').replace(/[^a-z0-9 ]/g, ' ');
}
function tokenize(s) {
  return norm(s).split(/\s+/).filter((w) => w.length > 1 && !STOP.has(w));
}

function walk(dir) {
  const out = [];
  let entries;
  try { entries = fs.readdirSync(dir, { withFileTypes: true }); } catch (_) { return out; }
  for (const e of entries) {
    const full = path.join(dir, e.name);
    if (e.isDirectory()) out.push(...walk(full));
    else if (/\.(txt|md|markdown)$/i.test(e.name) && !/^LEEME/i.test(e.name)) out.push(full);
  }
  return out;
}

function chunkText(text, source) {
  const paras = text.split(/\n\s*\n/).map((p) => p.trim()).filter(Boolean);
  const chunks = [];
  let cur = '';
  for (const p of paras) {
    if (cur && (cur.length + p.length + 2) > 900) { chunks.push(cur); cur = p; }
    else cur = cur ? cur + '\n\n' + p : p;
  }
  if (cur) chunks.push(cur);
  return chunks.map((c) => ({ source, text: c }));
}

export function buildIndex(dir) {
  const files = walk(dir);
  const chunks = [];
  for (const f of files) {
    let text; try { text = fs.readFileSync(f, 'utf8'); } catch (_) { continue; }
    for (const c of chunkText(text, path.basename(f))) chunks.push(c);
  }
  // estadísticas BM25
  const df = new Map();
  let totalLen = 0;
  for (const c of chunks) {
    c.tf = new Map();
    const toks = tokenize(c.text);
    c.len = toks.length;
    totalLen += toks.length;
    for (const t of toks) c.tf.set(t, (c.tf.get(t) || 0) + 1);
    for (const t of new Set(toks)) df.set(t, (df.get(t) || 0) + 1);
  }
  const N = chunks.length || 1;
  const avgdl = totalLen / N || 1;
  const idf = new Map();
  for (const [t, d] of df) idf.set(t, Math.log(1 + (N - d + 0.5) / (d + 0.5)));
  return { chunks, idf, avgdl, files: files.length };
}

export function retrieve(index, query, topK = 4) {
  if (!index || !index.chunks.length) return [];
  const qterms = tokenize(query);
  if (!qterms.length) return [];
  const scored = [];
  for (const c of index.chunks) {
    let score = 0;
    for (const t of qterms) {
      const f = c.tf.get(t); if (!f) continue;
      const idf = index.idf.get(t) || 0;
      score += idf * (f * (K1 + 1)) / (f + K1 * (1 - B + B * (c.len / index.avgdl)));
    }
    if (score > 0) scored.push({ source: c.source, text: c.text, score });
  }
  scored.sort((a, b) => b.score - a.score);
  return scored.slice(0, topK);
}

export function contextBlock(hits) {
  return hits.map((h, i) => `(${i + 1}) [${h.source}]\n${h.text}`).join('\n\n');
}
