// Iris — asistente de voz dentro de la llamada.
// Al escuchar su nombre en la transcripción, recopila la duda que sigue,
// la consulta con Claude (catálogo GNP + búsqueda web) y responde en voz alta
// con speechSynthesis. Mientras habla, el micrófono se ignora para no
// transcribir su propia voz.

const NOMBRE_ASISTENTE = "Iris";

// Variantes con las que el reconocedor suele transcribir "Iris". Se exige
// frontera de palabra (\b) para no confundirla con partes de otras palabras.
const ASISTENTE_WAKE = /\b(iris|iriss|irish|hiris|irix)\b/g;

// Copia del texto sin acentos preservando la longitud (índices 1:1 con el original).
function _sinAcentos(texto) {
  return [...texto].map((c) => c.normalize("NFD")[0]).join("");
}

// Devuelve { resto } (lo dicho después del nombre) o null si no se nombró.
function detectarNombreAsistente(texto) {
  const t = _sinAcentos(String(texto)).toLowerCase();
  ASISTENTE_WAKE.lastIndex = 0;
  let m,
    ultimo = null;
  while ((m = ASISTENTE_WAKE.exec(t)) !== null) ultimo = m;
  if (!ultimo) return null;
  const fin = ultimo.index + ultimo[0].length; // _sinAcentos preserva la longitud
  const resto = String(texto)
    .slice(fin)
    .replace(/^[\s,.:;!¡]+/, "");
  return { resto };
}

// Objeciones clásicas de venta de seguros (texto ya sin acentos).
const _OBJECIONES = [
  /objecion/,
  /(muy\s+)?car[oa]\b/,
  /carisim/,
  /esta\s+car/,
  /lo\s+(voy|va|van|vamos)\s+a\s+pensar/,
  /pensarl[oa]/,
  /dejame\s+pensarl/,
  /ya\s+teng?o?\s+(un|uno|seguro|el)/,
  /ya\s+tiene\s+(un|uno|seguro|el)/,
  /del\s+trabajo/,
  /no\s+(me\s+)?convence/,
  /no\s+(me\s+)?interesa/,
  /no\s+cre[eo]\s+en\s+(los\s+)?seguros/,
  /no\s+confi/,
  /no\s+lo\s+necesit/,
];

function esObjecion(texto) {
  const s = _sinAcentos(String(texto)).toLowerCase();
  return _OBJECIONES.some((r) => r.test(s));
}

// ---------------------------------------------------------------------------
// Comandos de voz para controlar el copiloto (manos libres)
// ---------------------------------------------------------------------------
const _NUM_PALABRA = {
  uno: 1, una: 1, dos: 2, tres: 3, cuatro: 4, cinco: 5, seis: 6, siete: 7,
  ocho: 8, nueve: 9, diez: 10, primera: 1, segunda: 2, tercera: 3, cuarta: 4,
  quinta: 5, sexta: 6, septima: 7, octava: 8, novena: 9, decima: 10,
};

function _numeroDe(t) {
  const m = t.match(/\b(\d{1,2})\b/);
  if (m) return parseInt(m[1], 10);
  for (const [pal, n] of Object.entries(_NUM_PALABRA)) {
    if (new RegExp("\\b" + pal + "\\b").test(t)) return n;
  }
  return null;
}

// Devuelve {accion, valor} o null. Se evalúa ANTES que cálculo/duda.
function interpretarComando(texto) {
  const orig = String(texto);
  const t = _sinAcentos(orig).toLowerCase();

  if (/\b(callate|calla|guarda silencio|silencio|detente|ya para)\b/.test(t))
    return { accion: "callar" };

  if (/\b(genera|generar|crea|arma|haz)\b.*\b(asesoria|analisis|reporte|informe|pdf)\b/.test(t))
    return { accion: "generar" };

  if (/\b(modo privad\w*|en privado|solo para mi|que no (lo|me) escuche)\b/.test(t))
    return { accion: "modo", valor: "privada" };
  if (/\b(en voz alta|modo normal|que lo escuche|responde en voz)\b/.test(t))
    return { accion: "modo", valor: "voz" };

  if (/\bpregunta anterior\b|\b(anterior|previa|regresa)\b.*\bpregunta\b/.test(t))
    return { accion: "anterior" };
  if (/\bsiguiente pregunta\b|\b(siguiente|proxima)\b.*\bpregunta\b|\bpasa a la siguiente\b/.test(t))
    return { accion: "siguiente" };

  // marcar pregunta N como respondida
  if (
    /\b(marca\w*|termine|contest\w*|respondi\w*|completa\w*|lista)\b/.test(t) &&
    /\b(pregunta|numero|la|\d)\b/.test(t)
  ) {
    const n = _numeroDe(t);
    if (n) return { accion: "marcar", valor: n };
  }

  // tomar nota (se conserva el texto original, con acentos y mayúsculas)
  const mAnota = t.match(/\b(anota|apunta|toma nota|nota)\b\s*(?:que\s+|:\s*)?/);
  if (mAnota) {
    const valor = orig.slice(mAnota.index + mAnota[0].length).trim();
    if (valor) return { accion: "anota", valor };
  }

  return null;
}

// Nombres de voces femeninas en español conocidas por plataforma (Windows,
// macOS, Google/Chrome). Se usan para elegir automáticamente una voz de mujer.
const _VOCES_FEMENINAS = [
  "sabina", "dalia", "ximena", "paloma", "helena", "laura", "nuria", "marisol",
  "paulina", "monica", "mónica", "angelica", "angélica", "esperanza", "yolanda",
  "google español", "female", "mujer",
];
const _VOCES_MASCULINAS = [
  "jorge", "juan", "diego", "pablo", "carlos", "raul", "raúl", "alvaro", "álvaro",
  "male", "hombre",
];

// Elige la mejor voz femenina en español disponible en el navegador.
function _elegirVozEspanol() {
  const voces = speechSynthesis.getVoices();
  const es = voces.filter((v) => v.lang && v.lang.toLowerCase().startsWith("es"));
  if (!es.length) return null;

  const pesoIdioma = (lang) => {
    const l = lang.toLowerCase();
    if (l.startsWith("es-mx")) return 40;
    if (l.startsWith("es-us") || l.startsWith("es-419")) return 30;
    if (l.startsWith("es-es")) return 20;
    return 10;
  };

  const puntuar = (v) => {
    const nombre = v.name.toLowerCase();
    let p = pesoIdioma(v.lang);
    if (_VOCES_FEMENINAS.some((n) => nombre.includes(n))) p += 100;
    if (_VOCES_MASCULINAS.some((n) => nombre.includes(n))) p -= 100;
    // Las voces "natural"/"online"/"premium" suenan más humanas y suaves.
    if (/natural|online|premium|enhanced|neural/.test(nombre)) p += 25;
    return p;
  };

  return es.slice().sort((a, b) => puntuar(b) - puntuar(a))[0];
}

class HadassahVoz {
  constructor({ consultar, onEstado, onIntercambio, onError, onComando }) {
    this.consultar = consultar; // async (pregunta, tipo) => respuesta (texto)
    this.onEstado = onEstado; // (estado) => void
    this.onIntercambio = onIntercambio; // (pregunta, respuesta, tipo) => void
    this.onError = onError;
    this.onComando = onComando; // (cmd) => void — comandos de voz
    this.activa = true;
    this.vozPreferida = ""; // nombre de voz elegido en opciones ("" = automática)
    this.modo = "voz"; // "voz" (en voz alta) | "privada" (solo texto para el asesor)
    this.estado = "esperando"; // esperando | recolectando | pensando | hablando | privado
    this._pregunta = "";
    this._timer = null;
    this._ttsSafety = null;
    this._finHablaTs = 0;
    // Las voces se cargan asíncronamente; precalentar la lista.
    if ("speechSynthesis" in window) {
      speechSynthesis.getVoices();
      speechSynthesis.addEventListener?.("voiceschanged", () => {}, { once: true });
    }
  }

  get ocupada() {
    return this.estado === "pensando" || this.estado === "hablando";
  }

  // true mientras Hadassah habla (y un respiro después): esos segmentos del
  // micrófono son su propia voz y no deben ir a la transcripción.
  debeIgnorarAudio() {
    return this.estado === "hablando" || Date.now() - this._finHablaTs < 900;
  }

  _setEstado(estado) {
    this.estado = estado;
    this.onEstado(estado);
  }

  // Recibe cada segmento final de la transcripción.
  procesarSegmento(texto) {
    if (!this.activa || this.ocupada) return;
    if (this.estado === "recolectando") {
      this._pregunta = (this._pregunta + " " + texto).trim();
      this._reprogramar();
      return;
    }
    const det = detectarNombreAsistente(texto);
    if (!det) return;
    this._pregunta = det.resto.trim();
    this._setEstado("recolectando");
    this._reprogramar();
  }

  _reprogramar() {
    clearTimeout(this._timer);
    // Si ya hay una pregunta con sustancia, espera corta; si solo dijo el
    // nombre, dale más tiempo a que formule la duda.
    const espera = this._pregunta.length > 12 ? 2200 : 3500;
    this._timer = setTimeout(() => this._enviar(), espera);
  }

  async _enviar() {
    const pregunta = this._pregunta.trim();
    this._pregunta = "";
    if (!pregunta) {
      this._setEstado("esperando");
      return;
    }
    await this.preguntar(pregunta);
  }

  // Punto de entrada compartido por la voz y el campo de texto manual.
  async preguntar(pregunta) {
    if (this.ocupada) return;
    clearTimeout(this._timer);

    // 0) ¿Es un comando de control? (manos libres, no gasta API)
    const cmd = interpretarComando(pregunta);
    if (cmd && this.onComando) {
      this.onComando(cmd);
      this._setEstado("esperando");
      return;
    }

    // 1) ¿Es un cálculo? Se resuelve local: instantáneo y siempre exacto.
    const calc =
      typeof interpretarCalculo === "function" ? interpretarCalculo(pregunta) : null;
    if (calc) {
      this.onIntercambio(pregunta, calc.texto, "calculo");
      if (this.modo === "privada") this._mostrarPrivado();
      else this._hablar(calc.texto);
      return;
    }

    // 2) ¿Es una objeción? La respuesta es coaching y SIEMPRE va en privado,
    //    para que el cliente no escuche el guion de rebate.
    const objecion = esObjecion(pregunta);
    const privado = objecion || this.modo === "privada";
    const tipo = objecion ? "objecion" : "normal";

    this._setEstado("pensando");
    let respuesta;
    try {
      respuesta = await this.consultar(pregunta, tipo);
    } catch (err) {
      this.onError(NOMBRE_ASISTENTE + " no pudo responder: " + err.message);
      this._setEstado("esperando");
      return;
    }
    this.onIntercambio(pregunta, respuesta, tipo);
    if (privado) this._mostrarPrivado();
    else this._hablar(respuesta);
  }

  _mostrarPrivado() {
    this._finHablaTs = 0;
    this._setEstado("privado");
  }

  // Voz a usar: la elegida en opciones si está disponible; si no, automática.
  _voz() {
    const voces = "speechSynthesis" in window ? speechSynthesis.getVoices() : [];
    if (this.vozPreferida) {
      const v = voces.find((x) => x.name === this.vozPreferida);
      if (v) return v;
    }
    return _elegirVozEspanol();
  }

  _hablar(texto) {
    if (!this.activa || !("speechSynthesis" in window)) {
      this._setEstado("esperando");
      return;
    }
    this._setEstado("hablando");
    speechSynthesis.cancel();

    // Chrome puede atascarse con locuciones largas: trocear por oraciones.
    const trozos = String(texto).match(/[^.!?]+[.!?]*/g) || [String(texto)];
    const voz = this._voz();
    let pendientes = trozos.length;
    const terminar = () => {
      clearTimeout(this._ttsSafety);
      this._finHablaTs = Date.now();
      if (this.estado === "hablando") this._setEstado("esperando");
    };
    for (const trozo of trozos) {
      const u = new SpeechSynthesisUtterance(trozo.trim());
      u.lang = voz?.lang || "es-MX";
      if (voz) u.voice = voz;
      // Tono suave y femenino: ritmo tranquilo y pitch ligeramente alto.
      u.rate = 0.96;
      u.pitch = 1.15;
      u.onend = u.onerror = () => {
        pendientes--;
        if (pendientes <= 0) terminar();
      };
      speechSynthesis.speak(u);
    }
    // Red de seguridad por si el motor de voz nunca notifica el final.
    clearTimeout(this._ttsSafety);
    this._ttsSafety = setTimeout(terminar, 4000 + texto.length * 90);
  }

  callar() {
    if ("speechSynthesis" in window) speechSynthesis.cancel();
    clearTimeout(this._timer);
    clearTimeout(this._ttsSafety);
    this._pregunta = "";
    this._finHablaTs = Date.now();
    this._setEstado("esperando");
  }
}
