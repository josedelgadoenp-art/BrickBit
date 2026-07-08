// Espejo del Futuro — gráfico en vivo de dos trayectorias de vida a 20 años:
// "con tu plan GNP" (estable) vs. "sin protección" (con caídas por imprevistos).
// Las líneas se separan conforme se avanza la llamada y se detecta más riesgo,
// haciendo visible y emotivo el valor de protegerse.

function _blindajeYriesgo(sesion) {
  // Si ya hay asesoría, usar su score como fuente autoritativa.
  const score = sesion.asesoria?.analisis?.score_proteccion;
  if (typeof score === "number") {
    const b = Math.min(Math.max(score / 100, 0.05), 0.95);
    return { blindaje: b, riesgo: 1 - b, progreso: 1 };
  }
  // Proxy en vivo antes de la asesoría.
  const progreso = (sesion.preguntasHechas?.length || 0) / (PREGUNTAS.length || 10);
  const texto = [
    sesion.notasGenerales || "",
    ...Object.values(sesion.notasPregunta || {}),
    ...(sesion.transcript || []).map((s) => s.texto),
  ].join(" ");
  const t = typeof _sinAcentos === "function" ? _sinAcentos(texto).toLowerCase() : texto.toLowerCase();
  let riesgo = 0.5;
  if (/\bhij|\bfamilia\b|\bdependi|\besposa\b|\besposo\b|\bpareja\b/.test(t)) riesgo += 0.2;
  if (/\bno tengo seguro\b|\bsin seguro\b|\bdel trabajo\b|\bno cuento con\b/.test(t)) riesgo += 0.15;
  if (/\bdeuda|\bcredito|\bhipoteca\b/.test(t)) riesgo += 0.08;
  if (/\bahorr|\binvier|\bproyecta\b|\btrasciende\b/.test(t)) riesgo -= 0.1;
  riesgo = Math.min(Math.max(riesgo, 0.28), 0.9);
  return { blindaje: 1 - riesgo, riesgo, progreso };
}

function _trayectorias(riesgo, progreso) {
  const N = 20;
  const prot = [];
  const exp = [];
  const shocks = [0.28, 0.58, 0.82];
  for (let i = 0; i <= N; i++) {
    const t = i / N;
    const yp = 0.16 + 0.78 * Math.pow(t, 0.9); // con GNP: sube estable
    // sin protección: crece, pero cada imprevisto deja un daño PERMANENTE
    // (ahorros drenados, deudas) además de la caída del momento.
    const pasados = shocks.filter((s) => t >= s - 0.02).length;
    let ye = 0.16 + 0.74 * Math.pow(t, 0.9) - riesgo * 0.09 * pasados;
    for (const s of shocks) ye -= riesgo * 0.3 * Math.exp(-Math.pow((t - s) / 0.05, 2));
    ye = Math.max(ye, 0.02);
    // al inicio de la llamada las dos casi coinciden; se separan con el avance
    const yeMix = yp + (ye - yp) * (0.25 + 0.75 * progreso);
    prot.push(yp);
    exp.push(yeMix);
  }
  return { prot, exp };
}

function _ruta(vals, W, H, pad) {
  const N = vals.length - 1;
  return vals
    .map((v, i) => {
      const x = pad + (i / N) * (W - pad * 2);
      const y = H - pad - v * (H - pad * 2);
      return `${i === 0 ? "M" : "L"}${x.toFixed(1)} ${y.toFixed(1)}`;
    })
    .join(" ");
}

function renderEspejo(sesion, containerId = "espejo-chart") {
  const cont = document.getElementById(containerId);
  if (!cont) return;
  const { riesgo, progreso } = _blindajeYriesgo(sesion);
  const { prot, exp } = _trayectorias(riesgo, progreso);

  const W = 300, H = 150, pad = 14;
  const rutaProt = _ruta(prot, W, H, pad);
  const rutaExp = _ruta(exp, W, H, pad);
  // área entre líneas (la "brecha" = valor de protegerse)
  const areaExpRev = exp
    .map((v, i) => {
      const idx = exp.length - 1 - i;
      const x = pad + (idx / (exp.length - 1)) * (W - pad * 2);
      const y = H - pad - exp[idx] * (H - pad * 2);
      return `L${x.toFixed(1)} ${y.toFixed(1)}`;
    })
    .join(" ");
  const area = rutaProt.replace(/^M/, "M") + " " + areaExpRev + " Z";

  // brecha = mayor distancia entre ambas líneas (el peor momento de exposición)
  let brecha = 0;
  for (let i = 0; i < prot.length; i++) {
    const g = (prot[i] - exp[i]) / Math.max(prot[i], 0.001);
    if (g > brecha) brecha = g;
  }
  brecha = Math.round(brecha * 100);

  cont.innerHTML = `
    <svg viewBox="0 0 ${W} ${H}" class="espejo-svg" preserveAspectRatio="none">
      <defs>
        <linearGradient id="esp-area" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stop-color="#22c55e" stop-opacity="0.22"/>
          <stop offset="100%" stop-color="#22c55e" stop-opacity="0.02"/>
        </linearGradient>
      </defs>
      <line x1="${pad}" y1="${H - pad}" x2="${W - pad}" y2="${H - pad}" stroke="currentColor" stroke-opacity="0.15"/>
      <path d="${area}" fill="url(#esp-area)"/>
      <path d="${rutaExp}" fill="none" stroke="#e5484d" stroke-width="2.4" stroke-dasharray="5 4" stroke-linecap="round" stroke-linejoin="round"/>
      <path d="${rutaProt}" fill="none" stroke="#12a150" stroke-width="2.8" stroke-linecap="round" stroke-linejoin="round"/>
    </svg>
    <div class="espejo-leyenda">
      <span><i class="pt prot"></i> Con tu plan GNP</span>
      <span><i class="pt exp"></i> Sin protección</span>
    </div>
    <div class="espejo-brecha">En el peor momento, sin protección perderías hasta <b>${brecha}%</b> de tu patrimonio</div>
  `;
}
