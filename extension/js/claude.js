// Cliente del API de Claude para generar la asesoría estructurada.
// La llamada se hace directo desde la extensión (host_permissions incluye
// api.anthropic.com y se envía la cabecera de acceso directo desde navegador).
// Se usa streaming SSE: sin él, Chrome corta conexiones que no reciben bytes
// durante ~5 minutos y una generación larga se perdería completa.

const MODELO_DEFAULT = "claude-opus-4-8";

const ESQUEMA_ASESORIA = {
  type: "object",
  additionalProperties: false,
  required: [
    "perfil",
    "respuestas",
    "analisis",
    "recomendacion",
    "plan_pago",
    "resumen_ejecutivo",
    "siguiente_paso",
  ],
  properties: {
    perfil: {
      type: "object",
      additionalProperties: false,
      required: [
        "nombre",
        "edad",
        "ocupacion",
        "dependientes",
        "ingreso_mensual",
        "gastos_mensuales",
        "ahorro_actual",
        "salud",
        "seguros_actuales",
        "metas",
        "prioridad",
        "perfil_riesgo",
      ],
      properties: {
        nombre: { type: "string" },
        edad: { type: "integer", description: "0 si no se mencionó" },
        ocupacion: { type: "string" },
        dependientes: { type: "integer", description: "0 si no tiene o no se mencionó" },
        ingreso_mensual: { type: "number", description: "En MXN; 0 si no se mencionó" },
        gastos_mensuales: { type: "number", description: "En MXN; 0 si no se mencionó" },
        ahorro_actual: { type: "number", description: "En MXN; 0 si no se mencionó" },
        salud: { type: "string", description: "Resumen breve: estado, fumador, ejercicio, antecedentes" },
        seguros_actuales: { type: "string", description: "Seguros vigentes o 'ninguno'" },
        metas: {
          type: "array",
          items: {
            type: "object",
            additionalProperties: false,
            required: ["meta", "horizonte_anios"],
            properties: {
              meta: { type: "string" },
              horizonte_anios: { type: "integer", description: "0 si no se mencionó plazo" },
            },
          },
        },
        prioridad: {
          type: "string",
          enum: ["familia", "salud", "retiro", "patrimonio", "educacion", "equilibrio", "no_detectada"],
        },
        perfil_riesgo: {
          type: "string",
          description:
            "Perfil de riesgo inferido de las preguntas 3, 5 y 6 (inversión, reacción ante imprevistos y ante una crisis)",
          enum: ["conservador", "moderado", "agresivo", "no_detectado"],
        },
      },
    },
    respuestas: {
      type: "array",
      description:
        "Exactamente 10 entradas, una por cada pregunta de la guía en orden (pregunta_num del 1 al 10)",
      items: {
        type: "object",
        additionalProperties: false,
        required: ["pregunta_num", "tema", "respuesta_resumen", "dato_faltante"],
        properties: {
          pregunta_num: { type: "integer", description: "Del 1 al 10" },
          tema: { type: "string" },
          respuesta_resumen: { type: "string" },
          dato_faltante: {
            type: "boolean",
            description: "true si el dato no se obtuvo en la llamada",
          },
        },
      },
    },
    analisis: {
      type: "object",
      additionalProperties: false,
      required: [
        "capacidad_ahorro_mensual",
        "fondo_emergencia_meses",
        "score_proteccion",
        "brechas",
        "fortalezas",
      ],
      properties: {
        capacidad_ahorro_mensual: {
          type: "number",
          description: "Ingreso menos gastos, en MXN",
        },
        fondo_emergencia_meses: {
          type: "number",
          description: "Meses de gastos cubiertos por el ahorro actual",
        },
        score_proteccion: {
          type: "integer",
          description: "Entero entre 0 y 100: qué tan protegido está hoy el prospecto",
        },
        brechas: {
          type: "array",
          items: {
            type: "object",
            additionalProperties: false,
            required: ["dimension", "severidad", "detalle"],
            properties: {
              dimension: {
                type: "string",
                enum: ["Salud", "Vida / Familia", "Retiro", "Educación", "Patrimonio", "Liquidez"],
              },
              severidad: { type: "string", enum: ["alta", "media", "baja"] },
              detalle: {
                type: "string",
                description: "Explicación con los números del propio prospecto",
              },
            },
          },
        },
        fortalezas: { type: "array", items: { type: "string" } },
      },
    },
    recomendacion: {
      type: "object",
      additionalProperties: false,
      required: [
        "producto_principal",
        "productos_complementarios",
        "es_combinacion",
        "estrategia",
        "argumentos_venta",
        "objeciones_probables",
      ],
      properties: {
        producto_principal: {
          type: "object",
          additionalProperties: false,
          required: ["clave", "nombre", "razon"],
          properties: {
            clave: { type: "string", enum: CLAVES_CATALOGO },
            nombre: { type: "string" },
            razon: { type: "string" },
          },
        },
        productos_complementarios: {
          type: "array",
          items: {
            type: "object",
            additionalProperties: false,
            required: ["clave", "nombre", "razon"],
            properties: {
              clave: { type: "string", enum: CLAVES_CATALOGO },
              nombre: { type: "string" },
              razon: { type: "string" },
            },
          },
        },
        es_combinacion: {
          type: "boolean",
          description: "true si la estrategia combina dos o más productos",
        },
        estrategia: {
          type: "string",
          description: "Cómo se articulan los productos con las metas y brechas del prospecto",
        },
        argumentos_venta: {
          type: "array",
          items: { type: "string" },
          description: "Argumentos rankeados: primero lo emocional, luego lo numérico",
        },
        objeciones_probables: {
          type: "array",
          items: {
            type: "object",
            additionalProperties: false,
            required: ["objecion", "respuesta_sugerida"],
            properties: {
              objecion: { type: "string" },
              respuesta_sugerida: {
                type: "string",
                description: "Respuesta usando los números del propio prospecto",
              },
            },
          },
        },
      },
    },
    plan_pago: {
      type: "object",
      additionalProperties: false,
      required: [
        "prima_mensual_sugerida",
        "prima_quincenal",
        "porcentaje_ingreso",
        "monto_comodo_detectado",
        "justificacion",
      ],
      properties: {
        prima_mensual_sugerida: {
          type: "number",
          description: "Presupuesto mensual sugerido en MXN (no es cotización oficial); 0 si no hay datos para proponerlo",
        },
        prima_quincenal: {
          type: "number",
          description: "Exactamente prima_mensual_sugerida / 2",
        },
        porcentaje_ingreso: {
          type: "number",
          description:
            "prima_mensual_sugerida como porcentaje del ingreso mensual, valor entre 0 y 100 (p. ej. 8.5 para 8.5%); 0 si no se conoce el ingreso",
        },
        monto_comodo_detectado: {
          type: "number",
          description:
            "Monto MENSUAL que el cliente declaró cómodo (si lo dijo por quincena, multiplícalo por 2 antes de registrarlo); 0 si no lo declaró",
        },
        justificacion: {
          type: "string",
          description: "Por qué este monto es cómodo y suficiente para el prospecto",
        },
      },
    },
    resumen_ejecutivo: {
      type: "string",
      description: "3-5 frases: situación, riesgo principal, solución y monto quincenal",
    },
    siguiente_paso: {
      type: "string",
      description: "Acción concreta de cierre para el asesor",
    },
  },
};

function construirSystemPrompt() {
  return `Eres un asesor financiero senior de GNP Seguros en México, experto en venta consultiva. \
Acabas de escuchar una videollamada de descubrimiento entre un asesor GNP y un prospecto, \
estructurada en 10 preguntas. Tu trabajo es producir la asesoría completa y personalizada en JSON.

CATÁLOGO GNP DISPONIBLE (usa exclusivamente estas claves):
${catalogoComoTexto()}

SOBRE LA GUÍA: las 10 preguntas son consultivas y evocativas (el "Mapa de Ruta Financiera"), \
centradas en la mentalidad, las metas y el perfil de riesgo del prospecto. No preguntan cifras \
de forma directa: los datos duros (edad, ingreso, gastos, ahorro, número de dependientes) \
aparecen en las notas del asesor o se infieren de las respuestas (p. ej. la pregunta 9 da el % \
de ahorro, la 7 los meses de colchón, la 1 y la 10 revelan dependientes). Úsalos cuando estén; \
si un número realmente no se conoce, usa 0 y marca dato_faltante=true, sin inventar.

REGLAS:
1. Basa TODO en lo dicho en la llamada y las notas del asesor. No inventes datos.
1b. Deduce perfil_riesgo (conservador / moderado / agresivo) a partir de las preguntas 3, 5 y 6 \
(preferencia de inversión, reacción ante el imprevisto de la montaña y ante una crisis de mercado). \
Alinéalo con la recomendación: un perfil conservador favorece ahorro garantizado (Consolida, \
Trasciende) y protección; uno agresivo tolera vehículos indexados a mercado (Proyecta) además \
de la protección base.
2. El plan de pago es un PRESUPUESTO SUGERIDO de protección, no una cotización oficial de GNP. \
Nunca presentes cifras como primas oficiales.
3. Si el cliente declaró un monto con el que se siente cómodo, respétalo: la prima mensual \
sugerida no debe excederlo. Si lo declaró POR QUINCENA, mensualízalo (multiplícalo por 2) antes \
de compararlo y regístralo ya mensualizado en monto_comodo_detectado. Si no declaró monto, \
sugiere entre 5% y 12% del ingreso mensual según la severidad de sus brechas y su capacidad de \
ahorro. Si no se conoce ni el ingreso ni un monto cómodo, usa 0 en prima_mensual_sugerida, \
prima_quincenal y porcentaje_ingreso, y explica en justificacion que falta ese dato para \
proponer un presupuesto.
4. prima_quincenal = prima_mensual_sugerida / 2 (en México se cobran 24 quincenas al año). \
El monto quincenal es el que se presenta al cliente porque se percibe más pequeño y se alinea \
con cómo recibe su ingreso.
5. Recomienda UN producto principal alineado a la prioridad y brecha más crítica del prospecto. \
Agrega complementarios solo si las brechas y el presupuesto lo justifican (es_combinacion=true).
6. Los argumentos de venta van rankeados: primero lo emocional (sus metas, su familia, sus \
propias palabras), después lo numérico. Usa los números del propio prospecto.
7. Escribe en español mexicano, cálido, directo y profesional. Trata al prospecto por su nombre.
8. respuestas debe tener exactamente 10 entradas con pregunta_num del 1 al 10 en orden; en las \
preguntas que no se tocaron, pon dato_faltante=true y resume qué falta.
9. Datos de contexto útiles para el análisis: inflación médica en México ~11.5% anual, \
inflación educativa ~8.2% anual, fondo de emergencia recomendado = 6 meses de gastos, \
necesidad de protección familiar ≈ 5 años de gastos totales del hogar mientras haya \
dependientes económicos (ajusta al alza si los hijos son pequeños o los dependientes son varios).`;
}

function construirMensajeUsuario(sesion) {
  const partes = [];
  partes.push(`FECHA DE LA LLAMADA: ${new Date().toLocaleDateString("es-MX")}`);
  if (sesion.nombreProspecto) {
    partes.push(`PROSPECTO: ${sesion.nombreProspecto}`);
  }

  partes.push(
    "\n=== GUÍA DE 10 PREGUNTAS: NOTAS DEL ASESOR Y TRANSCRIPCIÓN POR PREGUNTA ==="
  );
  PREGUNTAS.forEach((p, i) => {
    const notas = sesion.notasPregunta[p.id] || "";
    const trans = (sesion.transcriptPorPregunta[p.id] || []).join(" ");
    partes.push(`\n${p.titulo} — ${p.captura}`);
    partes.push(`Respondida: ${sesion.preguntasHechas.includes(p.id) ? "sí" : "no"}`);
    if (notas) partes.push(`Nota del asesor: ${notas}`);
    if (trans) partes.push(`Transcripción durante esta pregunta: ${trans}`);
    if (!notas && !trans) partes.push("(sin captura específica)");
  });

  if (sesion.notasGenerales) {
    partes.push("\n=== NOTAS GENERALES DEL ASESOR ===");
    partes.push(sesion.notasGenerales);
  }

  if ((sesion.hadassah || []).length) {
    partes.push(
      "\n=== DUDAS QUE HADASSAH (ASISTENTE DE VOZ) RESPONDIÓ DURANTE LA LLAMADA ==="
    );
    for (const x of sesion.hadassah.slice(-10)) {
      partes.push(`Duda: ${x.pregunta}\nRespuesta dada: ${x.respuesta}`);
    }
  }

  partes.push(
    "\nGenera la asesoría completa y personalizada en el formato JSON solicitado."
  );
  return partes.join("\n");
}

// Lee el stream SSE de /v1/messages y devuelve { texto, stopReason }.
async function _consumirStream(res) {
  const reader = res.body.getReader();
  const decoder = new TextDecoder();
  const tipoBloque = {};
  let buffer = "";
  let texto = "";
  let stopReason = null;

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });
    let sep;
    while ((sep = buffer.indexOf("\n\n")) !== -1) {
      const crudo = buffer.slice(0, sep);
      buffer = buffer.slice(sep + 2);
      const lineaDatos = crudo.split("\n").find((l) => l.startsWith("data:"));
      if (!lineaDatos) continue;
      let evento;
      try {
        evento = JSON.parse(lineaDatos.slice(5).trim());
      } catch (_) {
        continue; // ping u otro evento no-JSON
      }
      if (evento.type === "content_block_start") {
        tipoBloque[evento.index] = evento.content_block?.type;
      } else if (evento.type === "content_block_delta") {
        if (evento.delta?.type === "text_delta" && tipoBloque[evento.index] === "text") {
          texto += evento.delta.text;
        }
      } else if (evento.type === "message_delta") {
        stopReason = evento.delta?.stop_reason || stopReason;
      } else if (evento.type === "error") {
        throw new Error(
          "El API interrumpió la generación: " + (evento.error?.message || "error desconocido")
        );
      }
    }
  }
  return { texto, stopReason };
}

// Ajusta en código los invariantes que el esquema no puede garantizar.
function _normalizarAsesoria(a) {
  const plan = a.plan_pago;
  if (plan) {
    plan.prima_mensual_sugerida = Math.max(Number(plan.prima_mensual_sugerida) || 0, 0);
    plan.prima_quincenal = plan.prima_mensual_sugerida / 2;
    const ingreso = Number(a.perfil?.ingreso_mensual) || 0;
    if (ingreso > 0) {
      plan.porcentaje_ingreso = (plan.prima_mensual_sugerida / ingreso) * 100;
    } else {
      plan.porcentaje_ingreso = 0;
    }
  }
  if (a.analisis) {
    const s = Number(a.analisis.score_proteccion) || 0;
    a.analisis.score_proteccion = Math.min(Math.max(Math.round(s), 0), 100);
  }
  return a;
}

const _ESPERA = (ms) => new Promise((r) => setTimeout(r, ms));

const _CABECERAS = (apiKey) => ({
  "content-type": "application/json",
  "x-api-key": apiKey,
  "anthropic-version": "2023-06-01",
  "anthropic-dangerous-direct-browser-access": "true",
});

async function _lanzarErrorHTTP(res) {
  const requestId = res.headers.get("request-id");
  let detalle = "";
  try {
    const errBody = await res.json();
    detalle = errBody?.error?.message || "";
  } catch (_) {
    /* cuerpo no-JSON */
  }
  console.error(`API ${res.status}`, { requestId, detalle });
  const mensajes = {
    401: "API key inválida o revocada. Revisa las opciones de la extensión.",
    403: "La API key no tiene permisos para este modelo.",
    404: "Modelo no encontrado. Revisa el modelo configurado en opciones.",
    413: "La sesión es demasiado grande para el API. Recorta la transcripción o las notas.",
    429: "Límite de uso alcanzado. Espera un momento y vuelve a intentar.",
    529: "El API está saturado. Espera unos segundos y vuelve a intentar.",
  };
  throw new Error(
    (mensajes[res.status] || `Error ${res.status} del API.`) +
      (detalle ? ` (${detalle})` : "")
  );
}

async function generarAsesoria(sesion, { apiKey, modelo }) {
  if (!apiKey) {
    throw new Error(
      "Falta la API key de Anthropic. Configúrala en las opciones de la extensión."
    );
  }

  const cuerpo = {
    model: modelo || MODELO_DEFAULT,
    max_tokens: 32000,
    stream: true,
    thinking: { type: "adaptive" },
    system: construirSystemPrompt(),
    messages: [{ role: "user", content: construirMensajeUsuario(sesion) }],
    output_config: { format: { type: "json_schema", schema: ESQUEMA_ASESORIA } },
  };

  const REINTENTABLES = new Set([429, 500, 529]);
  let res;
  for (let intento = 0; ; intento++) {
    try {
      res = await fetch("https://api.anthropic.com/v1/messages", {
        method: "POST",
        headers: {
          "content-type": "application/json",
          "x-api-key": apiKey,
          "anthropic-version": "2023-06-01",
          "anthropic-dangerous-direct-browser-access": "true",
        },
        body: JSON.stringify(cuerpo),
      });
    } catch (err) {
      throw new Error("Error de red al contactar el API de Anthropic: " + err.message);
    }
    if (res.ok) break;

    const requestId = res.headers.get("request-id");
    let detalle = "";
    try {
      const errBody = await res.json();
      detalle = errBody?.error?.message || "";
    } catch (_) {
      /* cuerpo no-JSON */
    }
    console.error(`API ${res.status}`, { requestId, detalle });

    if (REINTENTABLES.has(res.status) && intento < 1) {
      const retryAfter = Number(res.headers.get("retry-after"));
      await _ESPERA((retryAfter > 0 && retryAfter < 60 ? retryAfter : 3) * 1000);
      continue;
    }

    const mensajes = {
      401: "API key inválida o revocada. Revisa las opciones de la extensión.",
      403: "La API key no tiene permisos para este modelo.",
      404: "Modelo no encontrado. Revisa el modelo configurado en opciones.",
      413: "La sesión es demasiado grande para el API. Recorta la transcripción o las notas.",
      429: "Límite de uso alcanzado y el reintento también falló. Espera un minuto y vuelve a intentar.",
      529: "El API está saturado. Ya se reintentó; espera unos segundos y vuelve a intentar.",
    };
    throw new Error(
      (mensajes[res.status] || `Error ${res.status} del API.`) +
        (detalle ? ` (${detalle})` : "")
    );
  }

  const { texto, stopReason } = await _consumirStream(res);

  if (stopReason === "refusal") {
    throw new Error(
      "El modelo declinó procesar esta solicitud. Revisa si la transcripción o las notas " +
        "contienen contenido sensible ajeno a la asesoría y edítalas antes de reintentar."
    );
  }
  if (stopReason === "max_tokens") {
    throw new Error(
      "La respuesta quedó incompleta (se agotó el límite de salida del modelo). Vuelve a intentar."
    );
  }
  if (!texto) {
    throw new Error("El API no devolvió contenido de texto.");
  }

  try {
    return _normalizarAsesoria(JSON.parse(texto));
  } catch (err) {
    console.error("Respuesta no interpretable como JSON", {
      error: String(err),
      stopReason,
      inicio: texto.slice(0, 500),
    });
    throw new Error("No se pudo interpretar la respuesta del modelo como JSON.");
  }
}

// ---------------------------------------------------------------------------
// Hadassah: respuestas de voz durante la llamada (catálogo GNP + búsqueda web)
// ---------------------------------------------------------------------------
function construirSystemHadassah(sesion) {
  const prospecto = sesion.nombreProspecto || "el prospecto";
  return `Eres Hadassah, la asistente de voz de GNP que participa EN VIVO en una videollamada \
entre un asesor GNP y ${prospecto}. Te acaban de hacer una pregunta en voz alta y tu respuesta \
se leerá con un sintetizador de voz frente al cliente.

CATÁLOGO GNP DE REFERENCIA:
${catalogoComoTexto()}

REGLAS DE RESPUESTA:
1. Máximo 80 palabras. Es una respuesta HABLADA: prosa natural, sin listas, sin markdown, \
sin asteriscos, sin encabezados. Español mexicano cálido, claro y profesional.
2. Si la duda es sobre un producto GNP, usa el catálogo de referencia. Nunca inventes primas, \
precios ni condiciones de contrato: si preguntan un precio, explica que depende de la \
cotización oficial y del perfil.
3. Puedes usar la búsqueda web para datos actuales (tipos de cambio, UDIs, inflación, reglas \
fiscales como el Art. 151 LISR, comparativas del sector). Si buscaste, di brevemente de dónde \
viene el dato ("según datos recientes de...").
4. Si no sabes o el dato es delicado (médico, legal, fiscal complejo), dilo con honestidad y \
sugiere confirmarlo después de la llamada.
5. No repitas la pregunta; ve directo a la respuesta. Cierra devolviendo la palabra al asesor \
cuando tenga sentido (por ejemplo: "...y aquí su asesor puede afinarlo a tu caso").`;
}

function construirSystemObjecion(sesion) {
  const prospecto = sesion.nombreProspecto || "el prospecto";
  return `Eres Hadassah, coach de ventas de GNP. El asesor está EN VIVO con ${prospecto} y \
te reporta una objeción del cliente. Tu respuesta es SOLO para el asesor (no se dice en voz \
alta al cliente): dale un guion breve para rebatir con inteligencia y empatía.

CATÁLOGO GNP DE REFERENCIA:
${catalogoComoTexto()}

REGLAS:
1. Máximo 90 palabras, en prosa, sin listas ni markdown. Español mexicano.
2. Usa los NÚMEROS Y DATOS del propio prospecto (los del contexto) para rebatir; el mejor \
argumento es su propia realidad, no frases genéricas.
3. Nunca inventes primas ni condiciones. Reencuadra el precio como costo del riesgo, no como gasto.
4. Da una o dos frases listas para decir ("puedes decirle: ...") y, si aplica, una pregunta \
de cierre para devolver la conversación al valor.
5. Tono de estratega tranquilo: la objeción es una señal de compra, no un rechazo.`;
}

async function preguntarHadassah(pregunta, sesion, { apiKey, modelo, tipo = "normal" }) {
  if (!apiKey) {
    throw new Error(
      "Falta la API key de Anthropic. Configúrala en las opciones de la extensión."
    );
  }

  const esObj = tipo === "objecion";

  let contexto = "";
  const notas = Object.values(sesion.notasPregunta || {})
    .filter(Boolean)
    .join(" · ");
  if (sesion.nombreProspecto || notas) {
    contexto =
      "Contexto de la llamada (úsalo para personalizar): " +
      (sesion.nombreProspecto ? `prospecto ${sesion.nombreProspecto}. ` : "") +
      (notas ? `Notas del asesor: ${notas}` : "");
    contexto = contexto.slice(0, 1200) + "\n\n";
  }

  const etiqueta = esObj ? "Objeción del cliente: " : "Pregunta dicha en voz alta: ";
  let mensajes = [{ role: "user", content: contexto + etiqueta + pregunta }];

  // La búsqueda web corre en el servidor; si agota su ciclo, el API devuelve
  // pause_turn y hay que reenviar la conversación para que continúe.
  for (let vuelta = 0; vuelta < 4; vuelta++) {
    let res;
    try {
      res = await fetch("https://api.anthropic.com/v1/messages", {
        method: "POST",
        headers: _CABECERAS(apiKey),
        body: JSON.stringify({
          model: modelo || MODELO_DEFAULT,
          max_tokens: 2000,
          thinking: { type: "adaptive" },
          output_config: { effort: "low" }, // respuesta rápida: prioriza latencia
          system: esObj ? construirSystemObjecion(sesion) : construirSystemHadassah(sesion),
          messages: mensajes,
          // La búsqueda web solo aplica a dudas informativas; las objeciones se
          // rebaten con los datos del prospecto, sin red.
          ...(esObj
            ? {}
            : { tools: [{ type: "web_search_20260209", name: "web_search", max_uses: 2 }] }),
        }),
      });
    } catch (err) {
      throw new Error("Error de red al contactar el API: " + err.message);
    }
    if (!res.ok) await _lanzarErrorHTTP(res);

    const data = await res.json();
    if (data.stop_reason === "pause_turn") {
      mensajes = [mensajes[0], { role: "assistant", content: data.content }];
      continue;
    }
    if (data.stop_reason === "refusal") {
      throw new Error("no puede responder esa pregunta en la llamada.");
    }
    const texto = (data.content || [])
      .filter((b) => b.type === "text")
      .map((b) => b.text)
      .join(" ")
      .trim();
    if (!texto) throw new Error("no obtuvo respuesta del modelo.");
    return texto;
  }
  throw new Error("la búsqueda tardó demasiado. Intenta de nuevo.");
}
