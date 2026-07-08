/**
 * BrickBit · Receptor de leads y eventos → Google Sheets + aviso por correo
 * ------------------------------------------------------------------------
 * Este script vive DENTRO de una hoja de Google (Extensiones → Apps Script).
 * Recibe los POST de la función de Netlify (o directos), guarda cada lead
 * en la pestaña "Leads", cada evento del loop viral en "Eventos", y te
 * manda un correo al instante cuando entra un lead con datos de contacto.
 *
 * ⚙️ CONFIGURA ESTAS DOS LÍNEAS:
 */
var SECRET = "CAMBIA-ESTE-SECRETO";              // el mismo que pondrás en Netlify (LEAD_SECRET)
var NOTIFY_EMAIL = "jose.delgado.enp@gmail.com"; // a dónde te llega el aviso de cada lead

var LEAD_HEADERS = [
  "Fecha", "Nombre", "Apellido", "Edad", "Ingreso", "Teléfono", "Correo",
  "Producto", "Línea", "Hueco", "Score", "Origen", "Ref", "Respuestas"
];
var EVENT_HEADERS = [
  "Fecha", "Evento", "Score", "Arquetipo", "Percentil", "Ref", "Origen", "Extra"
];

function doPost(e) {
  try {
    var data = JSON.parse(e.postData.contents);

    if (String(data.secret || "") !== SECRET) {
      return _json({ ok: false, error: "unauthorized" });
    }

    var ss = SpreadsheetApp.getActiveSpreadsheet();
    var fecha = Utilities.formatDate(new Date(), "America/Mexico_City", "yyyy-MM-dd HH:mm:ss");

    if (data.tipo === "evento") {
      var hojaE = _getOrCreateSheet(ss, "Eventos", EVENT_HEADERS);
      hojaE.appendRow([
        fecha,
        _s(data.evento), _s(data.score), _s(data.arquetipo), _s(data.percentil),
        _s(data.ref), _s(data.origen), _s(data.extra)
      ]);
      return _json({ ok: true });
    }

    // lead completo (desde /financial o /destino)
    var hoja = _getOrCreateSheet(ss, "Leads", LEAD_HEADERS);
    hoja.appendRow([
      fecha,
      _s(data.nombre), _s(data.apellido), _s(data.edad), _s(data.ingreso),
      _s(data.telefono), _s(data.correo), _s(data.producto), _s(data.linea),
      _s(data.hueco), _s(data.score), _s(data.origen), _s(data.ref),
      _s(Array.isArray(data.respuestas) ? data.respuestas.join(" · ") : data.respuestas)
    ]);

    // aviso inmediato solo si trae un dato de contacto
    if (NOTIFY_EMAIL && (data.telefono || data.correo)) {
      var quien = [_s(data.nombre), _s(data.apellido)].join(" ").trim() || "Prospecto sin nombre";
      MailApp.sendEmail({
        to: NOTIFY_EMAIL,
        subject: "🔥 Nuevo lead BrickBit: " + quien + (data.producto ? " · " + data.producto : ""),
        body:
          "Nuevo lead desde " + _s(data.origen || "web") + "\n\n" +
          "Nombre: " + quien + "\n" +
          "Edad: " + _s(data.edad) + "\n" +
          "Teléfono: " + _s(data.telefono) + "\n" +
          "Correo: " + _s(data.correo) + "\n" +
          "Ingreso: " + _s(data.ingreso) + "\n" +
          "Producto de interés: " + _s(data.producto) + " (" + _s(data.linea) + ")\n" +
          "Área menos protegida: " + _s(data.hueco) + "\n" +
          "Score de protección: " + _s(data.score) + "%\n" +
          "Código de referido: " + _s(data.ref) + "\n" +
          "Respuestas: " + _s(Array.isArray(data.respuestas) ? data.respuestas.join(" · ") : data.respuestas) + "\n\n" +
          "— Guardado en tu hoja 'Leads'."
      });
    }

    return _json({ ok: true });
  } catch (err) {
    return _json({ ok: false, error: String(err) });
  }
}

/* Permite probar el despliegue abriendo la URL en el navegador */
function doGet() {
  return _json({ ok: true, servicio: "BrickBit leads", hora: new Date().toISOString() });
}

function _getOrCreateSheet(ss, nombre, headers) {
  var hoja = ss.getSheetByName(nombre);
  if (!hoja) {
    hoja = ss.insertSheet(nombre);
    hoja.appendRow(headers);
    hoja.getRange(1, 1, 1, headers.length).setFontWeight("bold").setBackground("#FFF1E6");
    hoja.setFrozenRows(1);
  }
  return hoja;
}

function _s(v) {
  if (v === undefined || v === null) return "";
  return String(v).slice(0, 500);
}

function _json(obj) {
  return ContentService.createTextOutput(JSON.stringify(obj))
    .setMimeType(ContentService.MimeType.JSON);
}
