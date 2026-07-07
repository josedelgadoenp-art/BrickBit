// Catálogo de soluciones GNP para el análisis y para Hadassah.
//
// Datos tomados de gnp.com.mx (2026-07): Trasciende, Vive, Proyecta y
// Capitaliza traen coberturas, sumas y notas fiscales REALES de las páginas
// oficiales. Los de gastos médicos (Línea Azul), auto y hogar quedan como
// REFERENCIALES —marcados con `referencial: true`— hasta contar con la URL
// oficial de cada uno. En todos los casos, primas y condiciones exactas
// dependen de la cotización oficial de GNP; nunca se presentan como oferta.

const CATALOGO_GNP = {
  trasciende: {
    nombre: "Trasciende",
    tipo: "Vida + Ahorro (protección vitalicia)",
    pilar: "vida",
    desc:
      "Seguro de vida con ahorro y protección de por vida. Cubre fallecimiento, últimos gastos y anticipo por enfermedad terminal (Seguridad en Vida); opcionales: invalidez, muerte accidental, Cobertura Mujer y Vidas Conjuntas. Suma asegurada desde $400,000 MXN o $20,000 USD; plazos de pago de 1, 5, 10, 15, 20 años o a edad alcanzada. El ahorro queda libre de impuestos al cumplir los requisitos. Para personas de 0 a 80 años.",
    fiscal: "Ahorro libre de impuestos al cumplir requisitos.",
    icono: "🌅",
  },
  proyecta: {
    nombre: "Proyecta",
    tipo: "Vida + Ahorro para el retiro",
    pilar: "retiro",
    desc:
      "Seguro de vida con ahorro garantizado para el retiro, disponible para recibirse a los 55, 60, 65 o 70 años. Cubre supervivencia (entrega del ahorro al final del plazo), fallecimiento, últimos gastos e enfermedad terminal; opcionales: invalidez, muerte accidental y Cobertura Mujer. Suma desde $400,000 MXN o $20,000 USD que no pierde valor con el tiempo; plazos de 10 o 15 años. Deducible de impuestos vía Proyecta Afecto (Art. 185 LISR). Para personas de 18 a 60 años.",
    fiscal: "Deducible de ISR vía Proyecta Afecto (Art. 185 LISR).",
    icono: "🎯",
  },
  capitaliza: {
    nombre: "Capitaliza",
    tipo: "Vida + Ahorro indexado a mercado",
    pilar: "patrimonio",
    desc:
      "Seguro de vida con ahorro flexible que accede a rendimientos del mercado financiero mediante distintas opciones de inversión. Cubre fallecimiento, últimos gastos y anticipo por enfermedad terminal; opcionales: invalidez, muerte accidental y Cobertura Mujer. Plazo flexible (temporal o hasta edad 100). Ideal para acumular capital para metas de mediano y largo plazo con estrategia de ahorro definible. Para personas de 18 a 70 años.",
    icono: "🏦",
  },
  vive: {
    nombre: "Vida Vive",
    tipo: "Vida temporal (accesible)",
    pilar: "vida",
    desc:
      "Seguro de vida de protección por fallecimiento a plazo de 1 año, accesible y renovable. Coberturas básicas: fallecimiento, apoyo para últimos gastos, Seguridad en Vida (enfermedad terminal) y asistencia funeraria para el asegurado y un familiar directo; opcionales: muerte accidental e invalidez. Suma asegurada de $100,000 a $2,500,000 MXN. Para personas de 18 a 74 años. Se contrata en sucursal Banca Mifel.",
    icono: "🛡️",
  },
  linea_azul: {
    nombre: "GNP Línea Azul",
    tipo: "Gastos Médicos Mayores",
    pilar: "salud",
    desc:
      "Gastos médicos mayores de GNP con red hospitalaria amplia, deducible y coaseguro configurables y opción de cobertura internacional. Recibe el golpe económico de una enfermedad o accidente mayor en vez del paciente.",
    referencial: true,
    icono: "🏥",
  },
  autos: {
    nombre: "GNP Autos",
    tipo: "Patrimonio (auto)",
    pilar: "patrimonio",
    desc:
      "Cobertura de auto (amplia/limitada) con asistencia vial y atención de siniestros. Protege uno de los patrimonios más expuestos del hogar.",
    referencial: true,
    icono: "🚗",
  },
  hogar: {
    nombre: "GNP Hogar",
    tipo: "Patrimonio (hogar)",
    pilar: "patrimonio",
    desc:
      "Protección del inmueble y sus contenidos ante sismo, incendio, robo e imprevistos. Blinda el patrimonio familiar.",
    referencial: true,
    icono: "🏠",
  },
};

// Texto plano del catálogo para inyectarlo en el prompt (asesoría y Hadassah).
function catalogoComoTexto() {
  return Object.entries(CATALOGO_GNP)
    .map(([clave, p]) => {
      const marca = p.referencial ? " [REFERENCIAL: confirmar con GNP]" : "";
      const fiscal = p.fiscal ? ` Beneficio fiscal: ${p.fiscal}` : "";
      return `- clave: "${clave}" | ${p.nombre} (${p.tipo}, pilar: ${p.pilar})${marca}: ${p.desc}${fiscal}`;
    })
    .join("\n");
}

const CLAVES_CATALOGO = Object.keys(CATALOGO_GNP);
