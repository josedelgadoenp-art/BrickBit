// Guía de la videollamada: 10 preguntas de descubrimiento para venta consultiva GNP.
// Cada pregunta trae un guion sugerido para el asesor y una pista de qué capturar.
// Basadas en la auditoría VIA de GNP LifeOS (core/advisor.py).

const PREGUNTAS = [
  {
    id: "datos",
    titulo: "1 · Datos básicos",
    guion:
      "Para empezar, cuéntame un poco de ti: ¿cómo te llamas, cuántos años tienes, a qué te dedicas y en qué ciudad vives?",
    captura: "Nombre, edad, ocupación y ciudad/zona.",
  },
  {
    id: "familia",
    titulo: "2 · Familia y dependientes",
    guion:
      "¿Quiénes dependen económicamente de ti hoy? (pareja, hijos y sus edades, papás…)",
    captura: "Número de dependientes, edades de los hijos, situación de pareja.",
  },
  {
    id: "ingresos",
    titulo: "3 · Ingresos",
    guion:
      "Hablemos de flujo: ¿cuál es tu ingreso mensual aproximado? Todo queda entre nosotros.",
    captura: "Ingreso mensual (y si es fijo o variable, uno o dos ingresos en el hogar).",
  },
  {
    id: "gastos",
    titulo: "4 · Gastos y compromisos",
    guion:
      "¿Y más o menos cuánto gastas al mes? ¿Tienes créditos o deudas que estés pagando?",
    captura: "Gasto mensual, deudas (hipoteca, auto, tarjetas) y su mensualidad.",
  },
  {
    id: "patrimonio",
    titulo: "5 · Ahorro y patrimonio",
    guion:
      "¿Cuánto tienes ahorrado o invertido hoy? ¿La casa o el auto son propios?",
    captura: "Ahorro/inversión total, bienes propios, fondo de emergencia.",
  },
  {
    id: "salud",
    titulo: "6 · Salud y hábitos",
    guion:
      "Tu salud es tu primer activo: ¿cómo te sientes en general? ¿Fumas, haces ejercicio? ¿Algún antecedente médico tuyo o familiar?",
    captura: "Estado de salud, fumador sí/no, ejercicio, antecedentes relevantes.",
  },
  {
    id: "proteccion",
    titulo: "7 · Protección actual",
    guion:
      "¿Hoy cuentas con algún seguro? ¿De la empresa o personal? ¿Sabes de cuánto es la suma asegurada?",
    captura: "Seguros vigentes (GMM, vida, auto), si son del trabajo, sumas aseguradas.",
  },
  {
    id: "metas",
    titulo: "8 · Metas de vida",
    guion:
      "Ahora lo importante: ¿qué quieres lograr en los próximos años? (educación de los hijos, retiro, casa, negocio…) ¿Para cuándo?",
    captura: "Metas concretas con horizonte de tiempo (años) y costo estimado si lo menciona.",
  },
  {
    id: "prioridad",
    titulo: "9 · Preocupación principal",
    guion:
      "Si solo pudieras blindar UNA cosa de tu vida, ¿cuál sería? ¿Qué es lo que más te quita el sueño?",
    captura: "Prioridad emocional: familia, salud, retiro, patrimonio, educación o equilibrio.",
  },
  {
    id: "presupuesto",
    titulo: "10 · Presupuesto cómodo",
    guion:
      "Última: pensando en protegerte, ¿qué cantidad podrías destinar al mes —o a la quincena— sin apretar tu presupuesto?",
    captura: "Monto cómodo declarado (mensual o quincenal) y su reacción al hablar de dinero.",
  },
];
