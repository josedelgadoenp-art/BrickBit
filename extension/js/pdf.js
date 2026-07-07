// Generación del PDF de asesoría con jsPDF (empaquetado en vendor/).
// Diseño: portada + perfil + análisis financiero + recomendación GNP + plan de pago
// con el monto quincenal como protagonista.
// Nota: la Helvetica estándar de jsPDF solo soporta glifos WinAnsi; los
// marcadores gráficos se dibujan con rect() y las viñetas usan "•".

const PDF_COLORES = {
  naranja: [242, 103, 34], // naranja GNP
  azul: [27, 42, 74],
  gris: [95, 99, 104],
  grisClaro: [232, 234, 237],
  verde: [34, 139, 84],
  ambar: [217, 119, 6],
  rojo: [200, 52, 52],
  blanco: [255, 255, 255],
};

const ETIQUETA_PRIORIDAD = {
  familia: "Familia",
  salud: "Salud",
  retiro: "Retiro",
  patrimonio: "Patrimonio",
  educacion: "Educación",
  equilibrio: "Equilibrio",
};

const _MXN = new Intl.NumberFormat("es-MX", {
  style: "currency",
  currency: "MXN",
  maximumFractionDigits: 0,
});

function _mxn(n) {
  return _MXN.format(Math.round(Number(n) || 0));
}

function _num(n) {
  return Number(n) || 0;
}

// Recorta un arreglo de líneas ya envueltas, añadiendo elipsis si se pasó.
function _acotarLineas(lineas, max) {
  if (lineas.length <= max) return lineas;
  const corte = lineas.slice(0, max);
  corte[max - 1] = corte[max - 1].replace(/.{0,3}$/, "…");
  return corte;
}

class EscritorPDF {
  constructor(doc) {
    this.doc = doc;
    this.margen = 18;
    this.ancho = doc.internal.pageSize.getWidth();
    this.alto = doc.internal.pageSize.getHeight();
    this.anchoUtil = this.ancho - this.margen * 2;
    this.y = this.margen;
  }

  _salto(altura) {
    if (this.y + altura > this.alto - 20) {
      this.doc.addPage();
      this.y = this.margen;
    }
  }

  titulo(texto) {
    this._salto(14);
    this.doc.setFont("helvetica", "bold");
    this.doc.setFontSize(15);
    this.doc.setTextColor(...PDF_COLORES.azul);
    this.doc.text(texto, this.margen, this.y);
    this.y += 3;
    this.doc.setDrawColor(...PDF_COLORES.naranja);
    this.doc.setLineWidth(0.8);
    this.doc.line(this.margen, this.y, this.margen + 28, this.y);
    this.y += 8;
  }

  subtitulo(texto) {
    this._salto(10);
    this.doc.setFont("helvetica", "bold");
    this.doc.setFontSize(11);
    this.doc.setTextColor(...PDF_COLORES.naranja);
    this.doc.text(texto, this.margen, this.y);
    this.y += 6;
  }

  parrafo(texto, { color = PDF_COLORES.azul, tam = 10, indent = 0 } = {}) {
    if (!texto) return;
    this.doc.setFont("helvetica", "normal");
    this.doc.setFontSize(tam);
    this.doc.setTextColor(...color);
    const lineas = this.doc.splitTextToSize(String(texto), this.anchoUtil - indent);
    for (const linea of lineas) {
      this._salto(5.2);
      this.doc.text(linea, this.margen + indent, this.y);
      this.y += 5.2;
    }
    this.y += 1.5;
  }

  vineta(texto, { color = PDF_COLORES.azul, marcador = "•", colorMarcador } = {}) {
    this.doc.setFont("helvetica", "bold");
    this.doc.setFontSize(10);
    this.doc.setTextColor(...(colorMarcador || PDF_COLORES.naranja));
    this._salto(5.2);
    this.doc.text(marcador, this.margen, this.y);
    this.doc.setFont("helvetica", "normal");
    this.doc.setTextColor(...color);
    const lineas = this.doc.splitTextToSize(String(texto), this.anchoUtil - 6);
    for (const linea of lineas) {
      this._salto(5.2);
      this.doc.text(linea, this.margen + 6, this.y);
      this.y += 5.2;
    }
    this.y += 1;
  }

  filaDato(etiqueta, valor) {
    this.doc.setFont("helvetica", "normal");
    this.doc.setFontSize(10);
    const lineas = this.doc.splitTextToSize(String(valor ?? "—"), this.anchoUtil - 62);
    this._salto(Math.max(lineas.length * 5.2, 6));
    this.doc.setFont("helvetica", "bold");
    this.doc.setTextColor(...PDF_COLORES.gris);
    this.doc.text(etiqueta, this.margen, this.y);
    this.doc.setFont("helvetica", "normal");
    this.doc.setTextColor(...PDF_COLORES.azul);
    this.doc.text(lineas, this.margen + 62, this.y);
    this.y += Math.max(lineas.length * 5.2, 6);
  }

  espacio(mm = 4) {
    this.y += mm;
  }
}

function _bloqueQuincenal(doc, w, plan, { alto, tamMonto, encabezado, color }) {
  const quincenal = _num(plan.prima_quincenal);
  doc.setFillColor(...color);
  doc.roundedRect(w.margen, w.y, w.anchoUtil, alto, 3, 3, "F");
  doc.setTextColor(...PDF_COLORES.blanco);
  doc.setFont("helvetica", "normal");
  doc.setFontSize(11);
  doc.text(encabezado, w.margen + 8, w.y + 11);
  doc.setFont("helvetica", "bold");
  doc.setFontSize(tamMonto);
  if (quincenal > 0) {
    doc.text(`${_mxn(quincenal)} por quincena`, w.margen + 8, w.y + alto - 9);
  } else {
    doc.setFontSize(Math.max(tamMonto - 8, 14));
    doc.text("Monto por definir con el prospecto", w.margen + 8, w.y + alto - 9);
  }
  w.y += alto + 10;
}

function _portada(doc, w, asesoria, nombreAsesor) {
  const perfil = asesoria.perfil || {};
  // Banda superior naranja
  doc.setFillColor(...PDF_COLORES.naranja);
  doc.rect(0, 0, w.ancho, 58, "F");
  doc.setFillColor(...PDF_COLORES.azul);
  doc.rect(0, 58, w.ancho, 3, "F");

  doc.setTextColor(...PDF_COLORES.blanco);
  doc.setFont("helvetica", "bold");
  doc.setFontSize(24);
  doc.text("Análisis financiero personalizado", w.margen, 28);
  doc.setFontSize(12);
  doc.setFont("helvetica", "normal");
  doc.text("Asesoría de protección y ahorro · GNP Seguros", w.margen, 38);

  w.y = 78;
  doc.setTextColor(...PDF_COLORES.azul);
  doc.setFont("helvetica", "bold");
  doc.setFontSize(18);
  const lineasNombre = _acotarLineas(
    doc.splitTextToSize(`Preparado para: ${perfil.nombre || "Prospecto"}`, w.anchoUtil),
    2
  );
  doc.text(lineasNombre, w.margen, w.y);
  w.y += lineasNombre.length * 8 + 1;
  doc.setFont("helvetica", "normal");
  doc.setFontSize(11);
  doc.setTextColor(...PDF_COLORES.gris);
  doc.text(
    `Fecha: ${new Date().toLocaleDateString("es-MX", {
      year: "numeric",
      month: "long",
      day: "numeric",
    })}`,
    w.margen,
    w.y
  );
  w.y += 6;
  if (nombreAsesor) {
    doc.text(`Asesor: ${nombreAsesor}`.slice(0, 90), w.margen, w.y);
    w.y += 6;
  }

  // Resumen ejecutivo en tarjeta (acotado para que el bloque quincenal
  // siempre quepa en la portada)
  w.y += 8;
  doc.setFont("helvetica", "normal");
  doc.setFontSize(10);
  const resumen = _acotarLineas(
    doc.splitTextToSize(asesoria.resumen_ejecutivo || "", w.anchoUtil - 12),
    16
  );
  const altoCaja = resumen.length * 5.4 + 18;
  doc.setFillColor(248, 244, 240);
  doc.setDrawColor(...PDF_COLORES.naranja);
  doc.setLineWidth(0.4);
  doc.roundedRect(w.margen, w.y, w.anchoUtil, altoCaja, 3, 3, "FD");
  doc.setFont("helvetica", "bold");
  doc.setFontSize(11);
  doc.setTextColor(...PDF_COLORES.naranja);
  doc.text("Resumen ejecutivo", w.margen + 6, w.y + 9);
  doc.setFont("helvetica", "normal");
  doc.setFontSize(10);
  doc.setTextColor(...PDF_COLORES.azul);
  doc.text(resumen, w.margen + 6, w.y + 16);
  w.y += altoCaja + 10;

  // Monto quincenal protagonista en portada
  _bloqueQuincenal(doc, w, asesoria.plan_pago || {}, {
    alto: 34,
    tamMonto: 26,
    encabezado: "Tu plan de protección desde",
    color: PDF_COLORES.azul,
  });
}

function _severidadColor(sev) {
  if (sev === "alta") return PDF_COLORES.rojo;
  if (sev === "media") return PDF_COLORES.ambar;
  return PDF_COLORES.verde;
}

function generarPDF(asesoria, { nombreAsesor = "" } = {}) {
  const { jsPDF } = window.jspdf;
  const doc = new jsPDF({ unit: "mm", format: "a4" });
  const w = new EscritorPDF(doc);
  const p = asesoria.perfil || {};
  const an = asesoria.analisis || {};
  const rec = asesoria.recomendacion || {};
  const plan = asesoria.plan_pago || {};

  // ---------- Página 1: portada ----------
  _portada(doc, w, asesoria, nombreAsesor);

  // ---------- Página 2: perfil ----------
  doc.addPage();
  w.y = w.margen;
  w.titulo("1 · Perfil del prospecto");
  w.filaDato("Nombre", p.nombre);
  if (p.edad) w.filaDato("Edad", `${p.edad} años`);
  if (p.ocupacion) w.filaDato("Ocupación", p.ocupacion);
  w.filaDato("Dependientes", String(p.dependientes ?? 0));
  if (p.ingreso_mensual) w.filaDato("Ingreso mensual", _mxn(p.ingreso_mensual));
  if (p.gastos_mensuales) w.filaDato("Gastos mensuales", _mxn(p.gastos_mensuales));
  if (p.ahorro_actual || p.ahorro_actual === 0)
    w.filaDato("Ahorro actual", _mxn(p.ahorro_actual));
  if (p.salud) w.filaDato("Salud y hábitos", p.salud);
  if (p.seguros_actuales) w.filaDato("Protección actual", p.seguros_actuales);
  if (p.prioridad && p.prioridad !== "no_detectada")
    w.filaDato("Prioridad declarada", ETIQUETA_PRIORIDAD[p.prioridad] || p.prioridad);
  w.espacio(3);

  if (Array.isArray(p.metas) && p.metas.length) {
    w.subtitulo("Metas de vida detectadas");
    for (const m of p.metas) {
      w.vineta(
        m.horizonte_anios
          ? `${m.meta} — horizonte: ${m.horizonte_anios} año(s)`
          : m.meta
      );
    }
  }

  const faltantes = (asesoria.respuestas || []).filter((r) => r.dato_faltante);
  if (faltantes.length) {
    w.espacio(2);
    w.subtitulo("Datos pendientes de confirmar");
    for (const f of faltantes) {
      w.vineta(`${f.tema}`, { colorMarcador: PDF_COLORES.ambar, marcador: "!" });
    }
  }

  // ---------- Página 3: análisis financiero ----------
  doc.addPage();
  w.y = w.margen;
  w.titulo("2 · Análisis financiero");

  // Tarjetas de indicadores
  const indicadores = [
    ["Score de protección", `${an.score_proteccion ?? "—"}/100`],
    ["Capacidad de ahorro", `${_mxn(an.capacidad_ahorro_mensual)}/mes`],
    ["Fondo de emergencia", `${_num(an.fondo_emergencia_meses).toFixed(1)} meses`],
  ];
  const anchoTarjeta = (w.anchoUtil - 8) / 3;
  indicadores.forEach(([etq, val], i) => {
    const x = w.margen + i * (anchoTarjeta + 4);
    doc.setFillColor(...PDF_COLORES.grisClaro);
    doc.roundedRect(x, w.y, anchoTarjeta, 22, 2, 2, "F");
    doc.setFont("helvetica", "normal");
    doc.setFontSize(8.5);
    doc.setTextColor(...PDF_COLORES.gris);
    doc.text(etq, x + 4, w.y + 7);
    doc.setFont("helvetica", "bold");
    doc.setFontSize(13);
    doc.setTextColor(...PDF_COLORES.azul);
    doc.text(String(val), x + 4, w.y + 16);
  });
  w.y += 30;

  w.subtitulo("Brechas de protección detectadas");
  for (const b of an.brechas || []) {
    doc.setFont("helvetica", "bold");
    doc.setFontSize(10);
    w._salto(6);
    // marcador cuadrado dibujado (la Helvetica de jsPDF no tiene el glifo ■)
    doc.setFillColor(..._severidadColor(b.severidad));
    doc.rect(w.margen, w.y - 2.6, 2.6, 2.6, "F");
    doc.setTextColor(..._severidadColor(b.severidad));
    doc.text(`${b.dimension} - severidad ${b.severidad}`, w.margen + 4.5, w.y);
    w.y += 5.4;
    w.parrafo(b.detalle, { indent: 5 });
  }

  if ((an.fortalezas || []).length) {
    w.subtitulo("Fortalezas");
    for (const f of an.fortalezas) {
      w.vineta(f, { colorMarcador: PDF_COLORES.verde });
    }
  }

  // ---------- Página 4: recomendación GNP ----------
  doc.addPage();
  w.y = w.margen;
  w.titulo("3 · Recomendación GNP");

  const principal = rec.producto_principal || {};
  const infoPrincipal = CATALOGO_GNP[principal.clave] || {};

  // Tarjeta del producto principal: título envuelto y razón acotada para que
  // la caja nunca rebase la página.
  doc.setFont("helvetica", "bold");
  doc.setFontSize(14);
  const tituloProd = _acotarLineas(
    doc.splitTextToSize(
      `Producto principal: ${principal.nombre || infoPrincipal.nombre || "—"}`,
      w.anchoUtil - 12
    ),
    2
  );
  doc.setFont("helvetica", "normal");
  doc.setFontSize(10);
  const razonLineas = _acotarLineas(
    doc.splitTextToSize(principal.razon || "", w.anchoUtil - 12),
    18
  );
  const altoTitulo = tituloProd.length * 6.5;
  const altoCajaProd = 8 + altoTitulo + (infoPrincipal.tipo ? 6 : 2) + razonLineas.length * 5 + 6;
  w._salto(altoCajaProd + 4);
  doc.setFillColor(248, 244, 240);
  doc.setDrawColor(...PDF_COLORES.naranja);
  doc.setLineWidth(0.5);
  doc.roundedRect(w.margen, w.y, w.anchoUtil, altoCajaProd, 3, 3, "FD");
  doc.setFont("helvetica", "bold");
  doc.setFontSize(14);
  doc.setTextColor(...PDF_COLORES.naranja);
  doc.text(tituloProd, w.margen + 6, w.y + 10);
  let yCursor = w.y + 10 + altoTitulo;
  if (infoPrincipal.tipo) {
    doc.setFont("helvetica", "normal");
    doc.setFontSize(9.5);
    doc.setTextColor(...PDF_COLORES.gris);
    doc.text(infoPrincipal.tipo, w.margen + 6, yCursor);
    yCursor += 6;
  }
  doc.setFont("helvetica", "normal");
  doc.setFontSize(10);
  doc.setTextColor(...PDF_COLORES.azul);
  doc.text(razonLineas, w.margen + 6, yCursor);
  w.y += altoCajaProd + 8;

  if ((rec.productos_complementarios || []).length) {
    w.subtitulo(
      rec.es_combinacion ? "Combinación sugerida" : "Complementos a considerar"
    );
    for (const c of rec.productos_complementarios) {
      const info = CATALOGO_GNP[c.clave] || {};
      w.vineta(`${c.nombre || info.nombre}: ${c.razon}`);
    }
  }

  if (rec.estrategia) {
    w.subtitulo("Estrategia");
    w.parrafo(rec.estrategia);
  }

  if ((rec.argumentos_venta || []).length) {
    w.subtitulo("Argumentos clave");
    rec.argumentos_venta.forEach((a, i) => {
      w.vineta(a, { marcador: String(i + 1) + "." });
    });
  }

  if ((rec.objeciones_probables || []).length) {
    w.subtitulo("Manejo de objeciones");
    for (const o of rec.objeciones_probables) {
      w.parrafo(`«${o.objecion}»`, { tam: 10 });
      w.parrafo(o.respuesta_sugerida, { indent: 5, color: PDF_COLORES.gris });
    }
  }

  // ---------- Página 5: plan de pago ----------
  doc.addPage();
  w.y = w.margen;
  w.titulo("4 · Plan de inversión en tu protección");

  // Gran bloque quincenal
  const quincenal = _num(plan.prima_quincenal);
  doc.setFillColor(...PDF_COLORES.naranja);
  doc.roundedRect(w.margen, w.y, w.anchoUtil, 44, 3, 3, "F");
  doc.setTextColor(...PDF_COLORES.blanco);
  doc.setFont("helvetica", "normal");
  doc.setFontSize(12);
  doc.text(
    quincenal > 0 ? "Tu protección completa por solo" : "Tu plan de protección",
    w.margen + 8,
    w.y + 12
  );
  doc.setFont("helvetica", "bold");
  if (quincenal > 0) {
    doc.setFontSize(32);
    doc.text(`${_mxn(quincenal)} / quincena`, w.margen + 8, w.y + 28);
    doc.setFont("helvetica", "normal");
    doc.setFontSize(10);
    doc.text(
      `Equivale a ${_mxn(plan.prima_mensual_sugerida)} al mes · ${_num(
        plan.porcentaje_ingreso
      ).toFixed(1)}% de tu ingreso`,
      w.margen + 8,
      w.y + 38
    );
  } else {
    doc.setFontSize(20);
    doc.text("Monto por definir contigo", w.margen + 8, w.y + 27);
    doc.setFont("helvetica", "normal");
    doc.setFontSize(10);
    doc.text(
      "En la siguiente conversación definiremos el presupuesto que te acomode.",
      w.margen + 8,
      w.y + 38
    );
  }
  w.y += 54;

  if (_num(plan.monto_comodo_detectado) > 0) {
    w.vineta(
      `Este plan respeta el presupuesto que tú mismo definiste como cómodo (${_mxn(
        plan.monto_comodo_detectado
      )}/mes).`,
      { colorMarcador: PDF_COLORES.verde }
    );
  }
  if (plan.justificacion) {
    w.subtitulo("¿Por qué este monto?");
    w.parrafo(plan.justificacion);
  }

  if (asesoria.siguiente_paso) {
    w.subtitulo("Siguiente paso");
    w.parrafo(asesoria.siguiente_paso);
  }

  // Disclaimer
  w.espacio(8);
  doc.setDrawColor(...PDF_COLORES.grisClaro);
  doc.setLineWidth(0.3);
  w._salto(30);
  doc.line(w.margen, w.y, w.margen + w.anchoUtil, w.y);
  w.y += 5;
  w.parrafo(
    "Documento de trabajo generado con apoyo de inteligencia artificial a partir de la " +
      "conversación con el prospecto. Los montos mostrados son presupuestos sugeridos de " +
      "protección y NO constituyen cotización, prima oficial ni oferta de GNP Seguros. " +
      "Las condiciones finales dependen de la suscripción y tarificación oficial de GNP.",
    { color: PDF_COLORES.gris, tam: 8 }
  );

  // Pie de página en todas las hojas
  const nombreCorto = String(p.nombre || "Prospecto").slice(0, 40);
  const paginas = doc.getNumberOfPages();
  for (let i = 1; i <= paginas; i++) {
    doc.setPage(i);
    doc.setFont("helvetica", "normal");
    doc.setFontSize(8);
    doc.setTextColor(...PDF_COLORES.gris);
    doc.text(
      `Análisis financiero personalizado · ${nombreCorto} · Página ${i} de ${paginas}`,
      w.margen,
      w.alto - 8
    );
  }

  const nombreArchivo = `Asesoria_GNP_${(p.nombre || "prospecto")
    .replace(/[^\wáéíóúñÁÉÍÓÚÑ]+/g, "_")
    .slice(0, 40)}_${new Date().toISOString().slice(0, 10)}.pdf`;
  doc.save(nombreArchivo);
  return nombreArchivo;
}
