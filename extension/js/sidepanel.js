// Controlador principal del panel lateral.

// ---------------------------------------------------------------------------
// Estado de la sesión (persistido en chrome.storage.local)
// ---------------------------------------------------------------------------
const SESION_VACIA = () => ({
  nombreProspecto: "",
  nombreAsesor: "",
  preguntaActiva: 0,
  preguntasHechas: [],
  notasPregunta: {},
  transcriptPorPregunta: {},
  transcript: [], // [{hora, texto, preguntaId}]
  notasGenerales: "",
  asesoria: null,
  avisoCerrado: false,
  hadassahActiva: true,
  hadassahModo: "voz", // "voz" | "privada"
  hadassah: [], // [{pregunta, respuesta, hora, tipo}]
});

let sesion = SESION_VACIA();
let transcriptor = null;
let hadassah = null;
let guardadoTimer = null;
let revLocal = null; // última revisión escrita por ESTE panel (para ignorar el eco)

const $ = (sel) => document.querySelector(sel);

const MXN = new Intl.NumberFormat("es-MX", {
  style: "currency",
  currency: "MXN",
  maximumFractionDigits: 0,
});

function esc(texto) {
  return String(texto ?? "")
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#39;");
}

// ---------------------------------------------------------------------------
// Persistencia
// ---------------------------------------------------------------------------
function _escribirSesion() {
  revLocal = `${Date.now()}-${Math.random().toString(36).slice(2, 8)}`;
  sesion._rev = revLocal;
  chrome.storage.local.set({ sesion });
}

function guardarSesion() {
  clearTimeout(guardadoTimer);
  guardadoTimer = setTimeout(_escribirSesion, 400);
}

function guardarAhora() {
  clearTimeout(guardadoTimer);
  _escribirSesion();
}

async function cargarSesion() {
  const { sesion: guardada } = await chrome.storage.local.get("sesion");
  if (guardada) {
    sesion = { ...SESION_VACIA(), ...guardada };
  }
  const pa = sesion.preguntaActiva;
  if (!Number.isInteger(pa) || pa < 0 || pa >= PREGUNTAS.length) {
    sesion.preguntaActiva = 0;
  }
}

// Si hay otro panel abierto (otra ventana de Chrome), adoptar sus cambios en
// vez de machacarlos con nuestra copia vieja.
chrome.storage.onChanged.addListener((changes, area) => {
  if (area !== "local" || !changes.sesion) return;
  const nueva = changes.sesion.newValue;
  if (!nueva || nueva._rev === revLocal) return;
  sesion = { ...SESION_VACIA(), ...nueva };
  if (!Number.isInteger(sesion.preguntaActiva) || sesion.preguntaActiva < 0 || sesion.preguntaActiva >= PREGUNTAS.length) {
    sesion.preguntaActiva = 0;
  }
  sincronizarUI();
});

// El guardado tiene un debounce de 400 ms: al cerrarse el panel hay que
// vaciar la escritura pendiente o se pierden los últimos cambios.
window.addEventListener("pagehide", () => {
  if (guardadoTimer) {
    guardarAhora();
  }
});

// ---------------------------------------------------------------------------
// Errores
// ---------------------------------------------------------------------------
function mostrarError(mensaje) {
  const zona = $("#zona-error");
  zona.textContent = mensaje;
  zona.classList.remove("oculto");
  clearTimeout(mostrarError._timer);
  mostrarError._timer = setTimeout(() => zona.classList.add("oculto"), 12000);
}

// ---------------------------------------------------------------------------
// Confirmación de dos pasos (window.confirm no se muestra en paneles laterales)
// ---------------------------------------------------------------------------
function confirmarDosPasos(btn, textoConfirmar, accion) {
  if (btn.dataset.confirmando === "1") {
    delete btn.dataset.confirmando;
    btn.textContent = btn.dataset.textoOriginal;
    btn.classList.remove("btn-peligro");
    accion();
    return;
  }
  btn.dataset.confirmando = "1";
  btn.dataset.textoOriginal = btn.textContent;
  btn.textContent = textoConfirmar;
  btn.classList.add("btn-peligro");
  setTimeout(() => {
    if (btn.dataset.confirmando === "1") {
      delete btn.dataset.confirmando;
      btn.textContent = btn.dataset.textoOriginal;
      btn.classList.remove("btn-peligro");
    }
  }, 4000);
}

// ---------------------------------------------------------------------------
// Preguntas
// ---------------------------------------------------------------------------
function renderPreguntas() {
  const lista = $("#lista-preguntas");
  lista.innerHTML = "";
  PREGUNTAS.forEach((p, idx) => {
    const li = document.createElement("li");
    li.className = "pregunta";
    if (idx === sesion.preguntaActiva) li.classList.add("activa");
    if (sesion.preguntasHechas.includes(p.id)) li.classList.add("hecha");

    const cabecera = document.createElement("div");
    cabecera.className = "pregunta-cabecera";
    cabecera.innerHTML = `
      <span class="pregunta-check">${sesion.preguntasHechas.includes(p.id) ? "✅" : "○"}</span>
      <span class="pregunta-titulo">${esc(p.titulo)}</span>`;
    cabecera.addEventListener("click", () => {
      sesion.preguntaActiva = idx;
      guardarSesion();
      renderPreguntas();
    });

    const cuerpo = document.createElement("div");
    cuerpo.className = "pregunta-cuerpo";

    const guion = document.createElement("p");
    guion.className = "guion";
    guion.textContent = "“" + p.guion + "”";

    const captura = document.createElement("p");
    captura.className = "captura";
    captura.textContent = "Captura: " + p.captura;

    const nota = document.createElement("textarea");
    nota.placeholder = "Nota rápida de esta respuesta…";
    nota.value = sesion.notasPregunta[p.id] || "";
    nota.addEventListener("input", () => {
      sesion.notasPregunta[p.id] = nota.value;
      guardarSesion();
    });

    const acciones = document.createElement("div");
    acciones.className = "pregunta-acciones";
    const btnHecha = document.createElement("button");
    btnHecha.className = "btn btn-secundario";
    btnHecha.textContent = sesion.preguntasHechas.includes(p.id)
      ? "Reabrir"
      : "✓ Respondida — siguiente";
    btnHecha.addEventListener("click", () => {
      const ya = sesion.preguntasHechas.includes(p.id);
      if (ya) {
        sesion.preguntasHechas = sesion.preguntasHechas.filter((x) => x !== p.id);
      } else {
        sesion.preguntasHechas.push(p.id);
        if (idx < PREGUNTAS.length - 1) sesion.preguntaActiva = idx + 1;
      }
      guardarAhora();
      renderPreguntas();
    });
    acciones.appendChild(btnHecha);

    cuerpo.append(guion, captura, nota, acciones);
    li.append(cabecera, cuerpo);
    lista.appendChild(li);
  });

  $("#progreso-preguntas").textContent = `${sesion.preguntasHechas.length}/${PREGUNTAS.length}`;
}

// ---------------------------------------------------------------------------
// Transcripción
// ---------------------------------------------------------------------------
function renderTranscript() {
  const cont = $("#transcript");
  cont.innerHTML = "";
  if (!sesion.transcript.length) {
    cont.innerHTML =
      '<p class="transcript-vacio">Activa el micrófono para empezar a transcribir…</p>';
    return;
  }
  let ultimaPregunta = null;
  for (const seg of sesion.transcript) {
    if (seg.preguntaId !== ultimaPregunta) {
      ultimaPregunta = seg.preguntaId;
      const preg = PREGUNTAS.find((p) => p.id === seg.preguntaId);
      if (preg) {
        const marca = document.createElement("p");
        marca.className = "marca-pregunta";
        marca.textContent = "▸ " + preg.titulo;
        cont.appendChild(marca);
      }
    }
    const linea = document.createElement("p");
    linea.textContent = seg.texto;
    cont.appendChild(linea);
  }
  cont.scrollTop = cont.scrollHeight;
}

function alSegmentoFinal(texto, preguntaId) {
  // Mientras Hadassah habla, lo que capta el micrófono es su propia voz.
  if (hadassah?.debeIgnorarAudio()) return;
  const id =
    preguntaId || PREGUNTAS[sesion.preguntaActiva]?.id || PREGUNTAS[0].id;
  sesion.transcript.push({
    hora: new Date().toISOString(),
    texto,
    preguntaId: id,
  });
  if (!sesion.transcriptPorPregunta[id]) {
    sesion.transcriptPorPregunta[id] = [];
  }
  sesion.transcriptPorPregunta[id].push(texto);
  guardarSesion();
  renderTranscript();
  hadassah?.procesarSegmento(texto);
}

function crearTranscriptor() {
  return new Transcriptor({
    onSegmento: alSegmentoFinal,
    onContexto: () => PREGUNTAS[sesion.preguntaActiva]?.id || PREGUNTAS[0].id,
    onInterim: (texto) => {
      $("#interim").textContent = texto;
    },
    onEstado: (estado) => {
      const el = $("#estado-texto");
      const btn = $("#btn-mic");
      if (estado === "grabando") {
        el.textContent = "Escuchando (es-MX)…";
        el.className = "estado grabando";
        btn.textContent = "⏹️ Detener";
        btn.classList.add("activo");
      } else {
        el.textContent = "Micrófono apagado";
        el.className = "estado detenido";
        btn.textContent = "🎙️ Escuchar";
        btn.classList.remove("activo");
      }
    },
    onError: mostrarError,
  });
}

async function alternarMicrofono() {
  if (transcriptor?.activo) {
    transcriptor.detener();
    return;
  }
  if (!Transcriptor.soportado()) {
    mostrarError("Este navegador no soporta reconocimiento de voz. Usa Google Chrome.");
    return;
  }
  transcriptor = transcriptor || crearTranscriptor();
  try {
    await transcriptor.pedirPermisoMicrofono();
  } catch (err) {
    if (err.name === "NotFoundError" || err.name === "OverconstrainedError") {
      mostrarError("No se detecta ningún micrófono. Conecta uno y vuelve a intentar.");
    } else if (err.name === "NotReadableError") {
      mostrarError(
        "El micrófono está ocupado por otra aplicación. Ciérrala o elige otro micrófono y reintenta."
      );
    } else {
      // NotAllowedError y similares: en el panel lateral el diálogo de permiso
      // a veces no puede mostrarse; abrir una pestaña de la extensión donde sí.
      chrome.tabs.create({ url: chrome.runtime.getURL("permission.html") });
    }
    return;
  }
  transcriptor.iniciar();
}

// ---------------------------------------------------------------------------
// Hadassah — asistente de voz
// ---------------------------------------------------------------------------
const HADASSAH_ESTADOS = {
  esperando: "Di «Hadassah» seguido de la duda y responderá.",
  recolectando: "🎤 Hadassah te escucha… haz la pregunta.",
  pensando: "💭 Hadassah está pensando (puede buscar en la web)…",
  hablando: "🔊 Hadassah está respondiendo en voz alta…",
  privado: "📝 Respuesta lista abajo (privada, no se dijo en voz alta).",
};

const HADASSAH_BADGE = {
  objecion: "🛡️ Guion para ti — no lo leas al cliente",
  calculo: "🧮 Cálculo",
};

function renderHadassah() {
  const historial = sesion.hadassah || [];
  const cont = $("#hadassah-historial");
  cont.classList.toggle("oculto", !historial.length);
  cont.innerHTML = "";
  for (const x of historial.slice(-6)) {
    const div = document.createElement("div");
    div.className = "hadassah-qa" + (x.tipo === "objecion" ? " es-objecion" : "");
    if (HADASSAH_BADGE[x.tipo]) {
      const badge = document.createElement("span");
      badge.className = "hadassah-badge tipo-" + x.tipo;
      badge.textContent = HADASSAH_BADGE[x.tipo];
      div.appendChild(badge);
    }
    const q = document.createElement("p");
    q.className = "q";
    q.textContent = "« " + x.pregunta + " »";
    const r = document.createElement("p");
    r.className = "r";
    r.textContent = x.respuesta;
    div.append(q, r);
    cont.appendChild(div);
  }
  cont.scrollTop = cont.scrollHeight;
}

function crearHadassah() {
  return new HadassahVoz({
    consultar: async (pregunta, tipo) => {
      const { apiKey, modelo } = await chrome.storage.local.get(["apiKey", "modelo"]);
      return preguntarHadassah(pregunta, sesion, { apiKey, modelo, tipo });
    },
    onEstado: (estado) => {
      const el = $("#hadassah-estado");
      el.textContent = HADASSAH_ESTADOS[estado] || "";
      el.classList.toggle("trabajando", estado === "pensando" || estado === "hablando");
    },
    onIntercambio: (pregunta, respuesta, tipo) => {
      sesion.hadassah = sesion.hadassah || [];
      sesion.hadassah.push({
        pregunta,
        respuesta,
        tipo: tipo || "normal",
        hora: new Date().toISOString(),
      });
      guardarAhora();
      renderHadassah();
    },
    onError: mostrarError,
  });
}

async function preguntaManualHadassah() {
  const input = $("#hadassah-input");
  const pregunta = input.value.trim();
  if (!pregunta || !hadassah || hadassah.ocupada) return;
  input.value = "";
  await hadassah.preguntar(pregunta);
}

// ---------------------------------------------------------------------------
// Generación de la asesoría
// ---------------------------------------------------------------------------
function haySuficienteInformacion() {
  const tieneTranscript = sesion.transcript.length > 0;
  const tieneNotas =
    Object.values(sesion.notasPregunta).some((n) => n && n.trim()) ||
    (sesion.notasGenerales && sesion.notasGenerales.trim());
  return Boolean(tieneTranscript || tieneNotas);
}

async function generar() {
  if (!haySuficienteInformacion()) {
    mostrarError(
      "Aún no hay transcripción ni notas. Activa el micrófono o escribe notas antes de generar."
    );
    return;
  }
  const { apiKey, modelo } = await chrome.storage.local.get(["apiKey", "modelo"]);
  const btn = $("#btn-generar");
  btn.disabled = true;
  btn.innerHTML = '<span class="spinner"></span>Analizando la llamada…';
  const sesionSolicitada = sesion; // por si inicia una sesión nueva mientras el API responde
  try {
    const asesoria = await generarAsesoria(sesionSolicitada, { apiKey, modelo });
    if (sesionSolicitada !== sesion) return; // la sesión cambió: no mezclar prospectos
    sesion.asesoria = asesoria;
    guardarAhora();
    renderResultado();
    $("#resultado").scrollIntoView({ behavior: "smooth" });
  } catch (err) {
    mostrarError(err.message);
  } finally {
    btn.disabled = false;
    btn.innerHTML = "✨ Generar asesoría con IA";
  }
}

function renderResultado() {
  const a = sesion.asesoria;
  if (!a) {
    $("#resultado").classList.add("oculto");
    return;
  }
  const plan = a.plan_pago || {};
  const rec = a.recomendacion || {};
  const an = a.analisis || {};
  const principal = rec.producto_principal || {};
  const infoProd = CATALOGO_GNP[principal.clave] || {};

  const html = [];
  html.push(`<p>${esc(a.resumen_ejecutivo)}</p>`);

  const quincenal = Number(plan.prima_quincenal) || 0;
  if (quincenal > 0) {
    html.push(`
      <div class="bloque-quincenal">
        <div>Plan sugerido para ${esc(a.perfil?.nombre || "el prospecto")}</div>
        <div class="monto">${MXN.format(quincenal)} / quincena</div>
        <div class="detalle">${MXN.format(Number(plan.prima_mensual_sugerida) || 0)} al mes ·
          ${(Number(plan.porcentaje_ingreso) || 0).toFixed(1)}% del ingreso</div>
      </div>`);
  } else {
    html.push(`
      <div class="bloque-quincenal">
        <div>Plan sugerido para ${esc(a.perfil?.nombre || "el prospecto")}</div>
        <div class="monto">Monto por definir</div>
        <div class="detalle">Faltó el dato de ingreso o presupuesto cómodo; confírmalo en el siguiente contacto.</div>
      </div>`);
  }

  const pr = a.perfil?.perfil_riesgo;
  if (pr && pr !== "no_detectado") {
    html.push(
      `<p class="pastilla-riesgo">Perfil de riesgo: ${esc(pr.charAt(0).toUpperCase() + pr.slice(1))}</p>`
    );
  }

  html.push(`
    <div class="producto-principal">
      <strong>${esc(infoProd.icono || "⭐")} ${esc(principal.nombre || infoProd.nombre || "")}</strong>
      ${infoProd.tipo ? `<span> · ${esc(infoProd.tipo)}</span>` : ""}
      <p>${esc(principal.razon || "")}</p>
    </div>`);

  if ((rec.productos_complementarios || []).length) {
    html.push(`<h3>${rec.es_combinacion ? "Combinación sugerida" : "Complementos"}</h3><ul>`);
    for (const c of rec.productos_complementarios) {
      html.push(`<li><strong>${esc(c.nombre)}</strong>: ${esc(c.razon)}</li>`);
    }
    html.push("</ul>");
  }

  if ((an.brechas || []).length) {
    html.push("<h3>Brechas detectadas</h3><ul>");
    for (const b of an.brechas) {
      const sev = ["alta", "media", "baja"].includes(b.severidad) ? b.severidad : "baja";
      html.push(
        `<li><span class="sev-${sev}">${esc(b.dimension)}</span> — ${esc(b.detalle)}</li>`
      );
    }
    html.push("</ul>");
  }

  if ((rec.argumentos_venta || []).length) {
    html.push("<h3>Argumentos para el cierre</h3><ul>");
    for (const arg of rec.argumentos_venta) html.push(`<li>${esc(arg)}</li>`);
    html.push("</ul>");
  }

  if (a.siguiente_paso) {
    html.push(`<h3>Siguiente paso</h3><p>${esc(a.siguiente_paso)}</p>`);
  }

  $("#resultado-contenido").innerHTML = html.join("");
  $("#resultado").classList.remove("oculto");
}

// ---------------------------------------------------------------------------
// Nueva sesión
// ---------------------------------------------------------------------------
function hayDatosQueProteger() {
  return Boolean(
    haySuficienteInformacion() ||
      sesion.asesoria ||
      sesion.preguntasHechas.length ||
      sesion.nombreProspecto
  );
}

function nuevaSesion() {
  const asesor = sesion.nombreAsesor; // el nombre del asesor se conserva
  const avisoCerrado = sesion.avisoCerrado;
  const hadassahActiva = sesion.hadassahActiva;
  const hadassahModo = sesion.hadassahModo;
  transcriptor?.detener();
  hadassah?.callar();
  sesion = SESION_VACIA();
  sesion.nombreAsesor = asesor;
  sesion.avisoCerrado = avisoCerrado;
  sesion.hadassahActiva = hadassahActiva;
  sesion.hadassahModo = hadassahModo;
  guardarAhora();
  sincronizarUI();
}

// ---------------------------------------------------------------------------
// Arranque
// ---------------------------------------------------------------------------
function sincronizarUI() {
  $("#nombre-prospecto").value = sesion.nombreProspecto;
  $("#nombre-asesor").value = sesion.nombreAsesor;
  $("#notas-generales").value = sesion.notasGenerales;
  $("#aviso-consentimiento").classList.toggle("oculto", sesion.avisoCerrado);
  $("#interim").textContent = "";
  $("#hadassah-toggle").checked = sesion.hadassahActiva !== false;
  $("#hadassah-modo").value = sesion.hadassahModo || "voz";
  if (hadassah) {
    hadassah.activa = sesion.hadassahActiva !== false;
    hadassah.modo = sesion.hadassahModo || "voz";
  }
  renderPreguntas();
  renderTranscript();
  renderHadassah();
  renderResultado();
}

async function init() {
  await cargarSesion();
  hadassah = crearHadassah();
  sincronizarUI();

  $("#hadassah-toggle").addEventListener("change", (e) => {
    sesion.hadassahActiva = e.target.checked;
    hadassah.activa = e.target.checked;
    if (!e.target.checked) hadassah.callar();
    guardarSesion();
  });
  $("#hadassah-modo").addEventListener("change", (e) => {
    sesion.hadassahModo = e.target.value;
    hadassah.modo = e.target.value;
    guardarSesion();
  });
  $("#hadassah-preguntar").addEventListener("click", preguntaManualHadassah);
  $("#hadassah-input").addEventListener("keydown", (e) => {
    if (e.key === "Enter") preguntaManualHadassah();
  });
  $("#hadassah-callar").addEventListener("click", () => hadassah.callar());

  $("#btn-mic").addEventListener("click", alternarMicrofono);
  $("#btn-opciones").addEventListener("click", () => chrome.runtime.openOptionsPage());
  $("#btn-cerrar-aviso").addEventListener("click", () => {
    sesion.avisoCerrado = true;
    guardarSesion();
    $("#aviso-consentimiento").classList.add("oculto");
  });
  $("#nombre-prospecto").addEventListener("input", (e) => {
    sesion.nombreProspecto = e.target.value;
    guardarSesion();
  });
  $("#nombre-asesor").addEventListener("input", (e) => {
    sesion.nombreAsesor = e.target.value;
    guardarSesion();
  });
  $("#notas-generales").addEventListener("input", (e) => {
    sesion.notasGenerales = e.target.value;
    guardarSesion();
  });
  $("#btn-limpiar-transcript").addEventListener("click", (e) => {
    if (!sesion.transcript.length) return;
    confirmarDosPasos(e.target, "¿Borrar transcripción?", () => {
      sesion.transcript = [];
      sesion.transcriptPorPregunta = {};
      guardarAhora();
      renderTranscript();
    });
  });
  $("#btn-generar").addEventListener("click", generar);
  $("#btn-nueva-sesion").addEventListener("click", (e) => {
    if (!hayDatosQueProteger()) {
      nuevaSesion();
      return;
    }
    confirmarDosPasos(e.target, "¿Borrar todo? Confirma", nuevaSesion);
  });
  $("#btn-pdf").addEventListener("click", () => {
    if (!sesion.asesoria) return;
    try {
      generarPDF(sesion.asesoria, { nombreAsesor: sesion.nombreAsesor });
    } catch (err) {
      mostrarError("No se pudo generar el PDF: " + err.message);
    }
  });
}

document.addEventListener("DOMContentLoaded", init);
