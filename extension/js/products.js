// Catálogo referencial de soluciones GNP (portado de core/products.py de GNP LifeOS).
// Nombres y coberturas deben validarse contra el portafolio vigente de GNP antes
// de usarse en producción; no constituye cotización ni oferta.

const CATALOGO_GNP = {
  linea_azul: {
    nombre: "GNP Línea Azul",
    tipo: "Gastos Médicos Mayores",
    pilar: "salud",
    desc: "Cobertura médica amplia con red hospitalaria premium, deducible flexible y cobertura internacional opcional.",
    icono: "🏥",
  },
  vida_privilegio: {
    nombre: "Privilegio Universal",
    tipo: "Vida + Ahorro",
    pilar: "vida",
    desc: "Protección por fallecimiento con componente de ahorro flexible y liquidez parcial.",
    icono: "🛡️",
  },
  magnolia: {
    nombre: "GNP Magnolia",
    tipo: "Protección integral",
    pilar: "vida",
    desc: "Solución de protección pensada para el bienestar integral de la familia.",
    icono: "🌸",
  },
  proyecta: {
    nombre: "Proyecta",
    tipo: "Ahorro / Educación",
    pilar: "educacion",
    desc: "Plan de ahorro a mediano-largo plazo ideal para metas educativas, indexable a UDIs o dólares.",
    icono: "🎓",
  },
  consolida: {
    nombre: "Consolida",
    tipo: "Ahorro garantizado",
    pilar: "patrimonio",
    desc: "Ahorro con capital garantizado para metas a corto y mediano plazo.",
    icono: "🏦",
  },
  trasciende: {
    nombre: "Trasciende",
    tipo: "Retiro (PPR)",
    pilar: "retiro",
    desc: "Plan personal de retiro con beneficios fiscales (Art. 151 LISR) y gestión institucional.",
    icono: "🌅",
  },
  autos: {
    nombre: "GNP Autos Amplia",
    tipo: "Patrimonio",
    pilar: "patrimonio",
    desc: "Cobertura amplia de auto con asistencia total y app de siniestros en tiempo real.",
    icono: "🚗",
  },
  hogar: {
    nombre: "Hogar Versátil",
    tipo: "Patrimonio",
    pilar: "patrimonio",
    desc: "Protección del hogar y contenidos ante sismo, robo e imprevistos.",
    icono: "🏠",
  },
};

// Texto plano del catálogo para inyectarlo en el prompt del análisis.
function catalogoComoTexto() {
  return Object.entries(CATALOGO_GNP)
    .map(
      ([clave, p]) =>
        `- clave: "${clave}" | ${p.nombre} (${p.tipo}, pilar: ${p.pilar}): ${p.desc}`
    )
    .join("\n");
}

const CLAVES_CATALOGO = Object.keys(CATALOGO_GNP);
