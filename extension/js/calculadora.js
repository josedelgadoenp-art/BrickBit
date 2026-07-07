// Calculadora financiera local para Hadassah. Interpreta las cuentas más
// comunes de una llamada de venta y las resuelve de forma DETERMINISTA (sin
// llamar al API: los LLM fallan en aritmética y aquí el resultado siempre es
// exacto e instantáneo). Si no reconoce un cálculo devuelve null y Hadassah
// sigue por su ruta normal.

const _MXN_CALC = new Intl.NumberFormat("es-MX", {
  style: "currency",
  currency: "MXN",
  maximumFractionDigits: 0,
});
const _mxnC = (n) => _MXN_CALC.format(Math.round(n));
const _pctFmt = (n) =>
  Number.isInteger(n) ? String(n) : n.toFixed(1).replace(/\.0$/, "");

// Convierte "45", "45,000", "45.000", "1.2", "45 mil", "1.5 millones", "45k".
function _parseImporte(numStr, cola = "") {
  let s = String(numStr).replace(/\s/g, "");
  let val;
  if (/^\d{1,3}(,\d{3})+(\.\d+)?$/.test(s)) {
    val = parseFloat(s.replace(/,/g, "")); // 45,000 -> 45000
  } else if (/^\d{1,3}(\.\d{3})+$/.test(s)) {
    val = parseFloat(s.replace(/\./g, "")); // 45.000 -> 45000
  } else {
    val = parseFloat(s.replace(/,/g, ".")); // 1,2 -> 1.2
  }
  if (!Number.isFinite(val)) return null;
  const c = cola.toLowerCase().slice(0, 12);
  if (/^\s*(mill|mdp)/.test(c)) val *= 1e6;
  else if (/^\s*(mil\b|k\b|mil |k )/.test(c) || /^\s*mil$/.test(c)) val *= 1e3;
  return val;
}

// Número + su "cola" (para captar el multiplicador que viene después).
const _RE_NUM = /(\d+(?:[.,]\d+)*)([^0-9]{0,8})/g;

function interpretarCalculo(texto) {
  const t = " " + String(texto).toLowerCase().replace(/\$/g, " ") + " ";

  // Debe haber una señal de cálculo para siquiera intentarlo (evita falsos
  // positivos en preguntas normales).
  const señalCalculo =
    /%|por\s*ciento|quincen|proyect|a[nñ]os?\s+(?:al|con|a)\s|(?:al|con)\s+\d/.test(t) ||
    /cu[aá]nto (?:es|ser[ií]a|son|da)/.test(t);
  if (!señalCalculo) return null;

  // --- 1) Porcentaje de un monto: "10% de 45 mil", "8 por ciento de 45000" ---
  let m = t.match(
    /(\d+(?:[.,]\d+)?)\s*(?:%|por\s*ciento)\s*(?:de|del)\s+(\d+(?:[.,]\d+)*)([^0-9]{0,10})/
  );
  if (m) {
    const pct = parseFloat(m[1].replace(",", "."));
    const base = _parseImporte(m[2], m[3]);
    if (base != null) {
      const res = (pct / 100) * base;
      const quinc = res / 2;
      return {
        tipo: "calculo",
        texto:
          `El ${_pctFmt(pct)}% de ${_mxnC(base)} son ${_mxnC(res)} al mes, ` +
          `que serían ${_mxnC(quinc)} a la quincena.`,
      };
    }
  }

  // --- 2) Proyección de ahorro mensual (valor futuro de una anualidad) ---
  // "proyecta 500 al mes a 20 años al 8%", "si ahorro 1000 mensuales 15 años"
  if (/proyect|ahorr|guard|invier|invert|aport/.test(t)) {
    const mm = t.match(
      /(\d+(?:[.,]\d+)*)([^0-9]{0,8}?)(?:al\s*mes|mensual(?:es)?|cada\s*mes|por\s*mes)/
    );
    const ma = t.match(/(\d+(?:[.,]\d+)?)\s*a[nñ]os?/);
    if (mm && ma) {
      const pmt = _parseImporte(mm[1], mm[2]);
      const años = parseFloat(ma[1].replace(",", "."));
      const mr = t.match(/(\d+(?:[.,]\d+)?)\s*(?:%|por\s*ciento)/);
      const tasaAnual = mr ? parseFloat(mr[1].replace(",", ".")) : 8; // 8% por defecto
      if (pmt != null && años > 0) {
        const i = tasaAnual / 100 / 12;
        const n = Math.round(años * 12);
        const fv = i === 0 ? pmt * n : pmt * ((Math.pow(1 + i, n) - 1) / i);
        const aportado = pmt * n;
        return {
          tipo: "calculo",
          texto:
            `Ahorrando ${_mxnC(pmt)} al mes durante ${_pctFmt(años)} años ` +
            `a una tasa estimada del ${_pctFmt(tasaAnual)}% anual, acumularías ` +
            `alrededor de ${_mxnC(fv)}. De esos, ${_mxnC(aportado)} son tus ` +
            `aportaciones y el resto, ${_mxnC(fv - aportado)}, es el rendimiento. ` +
            `Es una estimación, no una cifra garantizada.`,
        };
      }
    }
  }

  // --- 3) Crecimiento de un monto único: "100 mil en 10 años al 7%" ---
  const mc = t.match(
    /(\d+(?:[.,]\d+)*)([^0-9]{0,8}?)\s*en\s*(\d+(?:[.,]\d+)?)\s*a[nñ]os?\s*(?:al|con|a)\s*(\d+(?:[.,]\d+)?)\s*(?:%|por\s*ciento)/
  );
  if (mc) {
    const pv = _parseImporte(mc[1], mc[2]);
    const años = parseFloat(mc[3].replace(",", "."));
    const tasa = parseFloat(mc[4].replace(",", "."));
    if (pv != null && años > 0) {
      const fv = pv * Math.pow(1 + tasa / 100, años);
      return {
        tipo: "calculo",
        texto:
          `${_mxnC(pv)} invertidos a ${_pctFmt(tasa)}% anual durante ` +
          `${_pctFmt(años)} años crecerían a cerca de ${_mxnC(fv)}. ` +
          `Es una estimación con rendimiento constante.`,
      };
    }
  }

  // --- 4) Mensual <-> quincenal ---
  if (/quincen/.test(t)) {
    // captura el primer monto de la frase
    _RE_NUM.lastIndex = 0;
    const mn = _RE_NUM.exec(t);
    if (mn) {
      const monto = _parseImporte(mn[1], mn[2]);
      if (monto != null) {
        // ¿el número está expresado por mes o por quincena?
        const esMensual = /al\s*mes|mensual|por\s*mes/.test(t);
        if (esMensual) {
          return {
            tipo: "calculo",
            texto: `${_mxnC(monto)} al mes equivalen a ${_mxnC(monto / 2)} por quincena.`,
          };
        }
        return {
          tipo: "calculo",
          texto: `${_mxnC(monto)} por quincena equivalen a ${_mxnC(monto * 2)} al mes.`,
        };
      }
    }
  }

  return null;
}
