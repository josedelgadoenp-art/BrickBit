// Catálogo de soluciones GNP para el análisis y para Hadassah.
//
// Datos tomados de las páginas oficiales de gnp.com.mx (2026-07): los ocho
// productos traen coberturas, sumas y notas fiscales REALES. El flag
// `referencial: true` se reserva para entradas sin fuente oficial (hoy
// ninguna). En todos los casos, las primas y condiciones exactas dependen de
// la cotización oficial de GNP; nunca se presentan como oferta.

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
  vida_basico: {
    nombre: "Seguro Básico Estandarizado de Vida",
    tipo: "Vida (básico regulado, económico)",
    pilar: "vida",
    desc:
      "Seguro de vida individual básico estandarizado y regulado por la CNSF (registro S0043-0011-2016) y CONDUSEF. Cubre fallecimiento por enfermedad o accidente. Suma asegurada de $100,000, $200,000 o $300,000 MXN. Plazo de 5 años con renovación automática de por vida. Muy económico y de contratación simple (solo la solicitud). Para personas de 18 a 65 años. Ideal como primera protección para presupuestos ajustados.",
    icono: "🪶",
  },
  linea_azul: {
    nombre: "GNP Línea Azul (Platino)",
    tipo: "Gastos Médicos Mayores",
    pilar: "salud",
    desc:
      "Gastos médicos mayores con cobertura nacional en todos los hospitales y protección en el extranjero por emergencias. Cubre consultas, cirugías, sala de operaciones, laboratorio y medicamentos; maternidad sin deducible ni coaseguro y recién nacido gratis hasta la siguiente renovación. Coaseguro topado sin importar el nivel hospitalario. Incluye Línea GNP (asesoría 24/7), Médica Móvil para urgencias, asistencia en viajes (repatriación, hospedaje por convalecencia) y reconocimiento de lealtad (cubre preexistencias a partir del 5° año). Prima deducible de impuestos. Para personas de 0 a 70 años (65-70 con estudios médicos).",
    fiscal: "Prima deducible de impuestos (gastos médicos).",
    icono: "🏥",
  },
  autos: {
    nombre: "Auto Accesible — Básico Estandarizado de RC",
    tipo: "Patrimonio (auto, responsabilidad civil)",
    pilar: "patrimonio",
    desc:
      "Seguro obligatorio de responsabilidad civil regulado por la CNSF. Cubre hasta $250,000 MXN por daños a terceros (gastos médicos, daños al vehículo y bienes de terceros), sin deducible al usarlo, con renovación automática y pago anual, semestral, trimestral o mensual. Para autos particulares con licencia vigente. No aplica a flotillas, vehículos comerciales, autos de más de 20 años ni especiales (blindados, clásicos, importados). Para cobertura amplia (daños propios, robo total), GNP ofrece planes superiores que se cotizan aparte.",
    icono: "🚗",
  },
  hogar: {
    nombre: "Hogar Versátil",
    tipo: "Patrimonio (casa habitación)",
    pilar: "patrimonio",
    desc:
      "Seguro de casa habitación integral para propietarios e inquilinos. Cubre incendio/rayo/explosión (todo riesgo), robo (contenidos, obras de arte, joyas), cristales, equipo electrónico y aparatos, bienes en exteriores (albercas, paneles solares) y desastres naturales sin restricción de zona (huracán, inundación, sismo, erupción). Incluye responsabilidad civil familiar y de empleados domésticos, y asistencias al hogar (plomero, cerrajero, electricista, vidriero, orientación legal) y médica familiar. Valuación del inmueble hasta 30 millones de pesos. Incluye protección para mascotas: asistencia veterinaria telefónica, apoyo por mascota extraviada y servicios funerarios opcionales.",
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
