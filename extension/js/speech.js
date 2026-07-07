// Transcripción en vivo con Web Speech API (es-MX).
// El reconocimiento se detiene solo tras silencios largos, así que se reinicia
// automáticamente mientras la sesión esté activa. Errores persistentes
// (sin red, sin micrófono) detienen la sesión con un aviso en vez de
// reintentar en silencio para siempre.
//
// Nota: captura el micrófono del asesor. Si el audio del cliente sale por
// bocinas, también se captura razonablemente; con audífonos solo se escucha
// al asesor (parafrasear las respuestas clave del cliente resuelve esto y es
// buena práctica de venta de todos modos).
//
// Privacidad: el reconocimiento de voz de Chrome procesa el audio en los
// servidores de Google mientras el micrófono está activo.

const _ERRORES_VOZ = {
  network:
    "Sin conexión con el servicio de voz de Chrome. Revisa tu internet; la transcripción se detuvo.",
  "audio-capture":
    "No se pudo capturar audio del micrófono (¿desconectado u ocupado por otra app?). La transcripción se detuvo.",
  "language-not-supported":
    "Este navegador no soporta reconocimiento de voz en español. La transcripción se detuvo.",
};

class Transcriptor {
  constructor({ onSegmento, onInterim, onEstado, onError, onContexto }) {
    this.onSegmento = onSegmento; // (textoFinal, contexto) => void
    this.onInterim = onInterim; // (textoParcial) => void
    this.onEstado = onEstado; // ("grabando"|"detenido") => void
    this.onError = onError; // (mensaje) => void
    this.onContexto = onContexto; // () => valor a adjuntar al segmento (id de pregunta activa)
    this.activo = false;
    this.rec = null;
    this._reinicioTimer = null;
    this._fallosSeguidos = 0;
    this._ctxUtterance = null; // contexto capturado al INICIO de la intervención en curso
  }

  static soportado() {
    return "webkitSpeechRecognition" in window || "SpeechRecognition" in window;
  }

  async pedirPermisoMicrofono() {
    // getUserMedia dispara el diálogo de permiso; el permiso queda concedido
    // para el origen chrome-extension:// completo.
    const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
    stream.getTracks().forEach((t) => t.stop());
  }

  iniciar() {
    if (this.activo) return;
    const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SR) {
      this.onError(
        "Este navegador no soporta reconocimiento de voz. Usa Google Chrome."
      );
      return;
    }
    this.activo = true;
    this._fallosSeguidos = 0;
    this._ctxUtterance = null;
    this._crearReconocedor(SR);
    this.onEstado("grabando");
  }

  _capturarContexto() {
    return this.onContexto ? this.onContexto() : null;
  }

  _crearReconocedor(SR) {
    this._matarReconocedor();
    const rec = new SR();
    rec.lang = "es-MX";
    rec.continuous = true;
    rec.interimResults = true;
    rec.maxAlternatives = 1;

    rec.onresult = (event) => {
      if (rec !== this.rec || !this.activo) return;
      this._fallosSeguidos = 0;
      // El contexto (pregunta activa) se fija cuando la persona EMPIEZA a
      // hablar, no cuando Chrome finaliza el segmento: si el asesor avanza de
      // pregunta a media frase, la frase queda en la pregunta correcta.
      if (this._ctxUtterance == null) this._ctxUtterance = this._capturarContexto();
      let interim = "";
      let huboFinal = false;
      for (let i = event.resultIndex; i < event.results.length; i++) {
        const r = event.results[i];
        const texto = r[0].transcript.trim();
        if (!texto) continue;
        if (r.isFinal) {
          huboFinal = true;
          this.onSegmento(texto, this._ctxUtterance);
        } else {
          interim += texto + " ";
        }
      }
      if (huboFinal) {
        // La siguiente intervención (si ya empezó como interim) recaptura contexto ahora.
        this._ctxUtterance = interim ? this._capturarContexto() : null;
      }
      this.onInterim(interim.trim());
    };

    rec.onerror = (event) => {
      if (rec !== this.rec) return;
      if (event.error === "not-allowed" || event.error === "service-not-allowed") {
        this.activo = false;
        this.onEstado("detenido");
        this.onError(
          "Micrófono sin permiso. Pulsa «Escuchar» de nuevo para volver a solicitarlo."
        );
        return;
      }
      if (event.error in _ERRORES_VOZ) {
        this._fallosSeguidos++;
        if (this._fallosSeguidos >= 3) {
          this.activo = false;
          this.onEstado("detenido");
          this.onError(_ERRORES_VOZ[event.error]);
        }
        return;
      }
      if (event.error !== "no-speech" && event.error !== "aborted") {
        console.warn("SpeechRecognition error:", event.error);
      }
    };

    rec.onend = () => {
      if (rec !== this.rec) return;
      this.onInterim("");
      this._ctxUtterance = null;
      if (this.activo) {
        // Chrome corta la sesión tras silencios; reiniciar con backoff si está fallando.
        const espera = Math.min(250 * 2 ** this._fallosSeguidos, 4000);
        clearTimeout(this._reinicioTimer);
        this._reinicioTimer = setTimeout(() => {
          if (!this.activo || rec !== this.rec) return;
          try {
            rec.start();
          } catch (_) {
            this._crearReconocedor(SR);
          }
        }, espera);
      } else {
        this.onEstado("detenido");
      }
    };

    this.rec = rec;
    try {
      rec.start();
    } catch (err) {
      this.activo = false;
      this.onEstado("detenido");
      this.onError("No se pudo iniciar el reconocimiento de voz: " + err.message);
    }
  }

  _matarReconocedor() {
    const viejo = this.rec;
    if (!viejo) return;
    this.rec = null;
    viejo.onresult = viejo.onerror = viejo.onend = null;
    try {
      viejo.abort();
    } catch (_) {
      /* ya detenido */
    }
  }

  detener() {
    this.activo = false;
    clearTimeout(this._reinicioTimer);
    // abort() descarta resultados pendientes: nada de la llamada anterior
    // puede "gotear" hacia una sesión nueva después de detener.
    this._matarReconocedor();
    this.onInterim("");
    this.onEstado("detenido");
  }
}
