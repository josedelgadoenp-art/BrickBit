// Hadassah — asistente de voz dentro de la llamada.
// Al escuchar su nombre en la transcripción, recopila la duda que sigue,
// la consulta con Claude (catálogo GNP + búsqueda web) y responde en voz alta
// con speechSynthesis. Mientras habla, el micrófono se ignora para no
// transcribir su propia voz.

// Variantes con las que el reconocedor suele transcribir "Hadassah".
const HADASSAH_NOMBRES = [
  "hadassah", "hadasah", "hadassa", "hadasa", "hadaza",
  "adassah", "adasah", "adassa", "adasa",
  "jadassah", "jadasa", "hada sa", "ada sa",
];

// Copia del texto sin acentos preservando la longitud (índices 1:1 con el original).
function _sinAcentos(texto) {
  return [...texto].map((c) => c.normalize("NFD")[0]).join("");
}

// Devuelve { resto } (lo dicho después del nombre) o null si no se nombró.
function detectarNombreHadassah(texto) {
  const t = _sinAcentos(String(texto)).toLowerCase();
  let mejor = null;
  for (const nombre of HADASSAH_NOMBRES) {
    const idx = t.lastIndexOf(nombre);
    if (idx !== -1 && (!mejor || idx > mejor.idx)) {
      mejor = { idx, fin: idx + nombre.length };
    }
  }
  if (!mejor) return null;
  const resto = String(texto)
    .slice(mejor.fin)
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

function _elegirVozEspanol() {
  const voces = speechSynthesis.getVoices();
  const es = voces.filter((v) => v.lang && v.lang.toLowerCase().startsWith("es"));
  if (!es.length) return null;
  const pref = ["es-mx", "es-us", "es-419", "es-es"];
  for (const lang of pref) {
    const v = es.find((x) => x.lang.toLowerCase().startsWith(lang));
    if (v) return v;
  }
  return es[0];
}

class HadassahVoz {
  constructor({ consultar, onEstado, onIntercambio, onError }) {
    this.consultar = consultar; // async (pregunta) => respuesta (texto)
    this.onEstado = onEstado; // (estado, detalle) => void
    this.onIntercambio = onIntercambio; // (pregunta, respuesta) => void
    this.onError = onError;
    this.activa = true;
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
    const det = detectarNombreHadassah(texto);
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
      this.onError("Hadassah no pudo responder: " + err.message);
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

  _hablar(texto) {
    if (!this.activa || !("speechSynthesis" in window)) {
      this._setEstado("esperando");
      return;
    }
    this._setEstado("hablando");
    speechSynthesis.cancel();

    // Chrome puede atascarse con locuciones largas: trocear por oraciones.
    const trozos = String(texto).match(/[^.!?]+[.!?]*/g) || [String(texto)];
    const voz = _elegirVozEspanol();
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
      u.rate = 1.04;
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
