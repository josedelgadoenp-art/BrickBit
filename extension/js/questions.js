// Guía de la videollamada: las 10 preguntas del "Mapa de Ruta Financiera" de
// BrickBit (en alianza con GNP Seguros). Guion consultivo centrado en la
// mentalidad, las metas y el perfil de riesgo del prospecto; los datos duros
// (ingreso, gastos, dependientes) el asesor los anota conforme surgen.
// El "guion" es lo que el asesor lee/dice; la "captura" indica qué señal y qué
// dato registrar.

const PREGUNTAS = [
  {
    id: "vision",
    titulo: "1 · Visión a 10–15 años",
    guion:
      "Si el dinero y el tiempo no fueran problema, ¿cómo te imaginas tu vida en 10 o 15 años? Platícame qué te gustaría estar haciendo, dónde te gustaría estar y con quién.",
    captura:
      "Sueños y metas de vida a 10–15 años. El «con quién» revela familia/dependientes y prioridades.",
  },
  {
    id: "motivacion",
    titulo: "2 · Foco y motivación",
    guion:
      "De todos los proyectos que traes ahorita, ¿a cuál le estás metiendo más energía? Ya sea en tu trabajo, un negocio propio o metas familiares. ¿Qué es lo que más te motiva hoy?",
    captura:
      "Ocupación/negocio, proyecto principal y motor emocional del prospecto.",
  },
  {
    id: "perfil_inversion",
    titulo: "3 · Perfil de inversión",
    guion:
      "Cuando piensas en hacer crecer tu dinero, ¿hacia dónde te inclinas de forma natural? ¿Te laten más los bienes raíces, la bolsa, meterle a tu negocio, o prefieres esquemas más conservadores?",
    captura:
      "Apetito de riesgo y preferencia de inversión: conservador, moderado o agresivo.",
  },
  {
    id: "deuda",
    titulo: "4 · Crédito y deuda",
    guion:
      "¿Cómo te llevas con los créditos y las deudas? ¿Eres de los que prefiere pagar todo de contado para vivir tranquilo, o usas los créditos para apalancarte y crecer?",
    captura:
      "Deudas actuales (hipoteca, auto, tarjetas) y postura ante el crédito.",
  },
  {
    id: "adversidad",
    titulo: "5 · Reacción ante imprevistos",
    guion:
      "Imaginemos que vas subiendo a una cumbre: llevas cinco horas de subida, ya sientes el cansancio y tu meta está a menos de un kilómetro. De pronto cae una tormenta fuerte y un deslave bloquea por completo el único sendero seguro. ¿Qué haces en ese momento? ¿Das media vuelta, buscas una ruta alternativa peligrosa, o buscas refugio?",
    captura:
      "Cómo reacciona ante lo inesperado: prudencia vs. riesgo. Refuerza el perfil de protección.",
  },
  {
    id: "volatilidad",
    titulo: "6 · Ante una crisis",
    guion:
      "Si hubiera otra crisis fuerte y tus inversiones o propiedades bajaran de valor de un día para otro, ¿qué harías? ¿Vendes rápido para no perder más, compras más porque está barato, o te quedas quieto a esperar?",
    captura:
      "Tolerancia real a la volatilidad; confirma el perfil de riesgo de la pregunta 3.",
  },
  {
    id: "liquidez",
    titulo: "7 · Colchón / independencia",
    guion:
      "Si por alguna razón mañana tuvieras que dejar de trabajar por completo, ¿cuánto tiempo podrías mantener tu estilo de vida actual? Con toda sinceridad, ¿cuántos meses aguantarían tus ahorros y activos antes de tener que hacer recortes drásticos?",
    captura:
      "Meses de colchón (fondo de emergencia). Indicio del ahorro acumulado y del gasto mensual.",
  },
  {
    id: "salud",
    titulo: "8 · Salud y GMM",
    guion:
      "Sabemos que la salud es el motor de todo. Si enfrentaras una enfermedad fuerte, ¿tienes con qué defender tu cartera? ¿Te atenderías por tu cuenta, en el sistema público, o cuentas con una póliza fuerte de gastos médicos mayores que reciba el golpe por ti?",
    captura:
      "Gastos médicos mayores vigentes (sí/no y qué tan sólida), salud general y exposición médica.",
  },
  {
    id: "ahorro",
    titulo: "9 · Capacidad de ahorro",
    guion:
      "Para lograr toda esa tranquilidad de la que hablamos, ¿qué porcentaje de lo que ganas al mes estás logrando guardar o invertir realmente? Sé que a veces los gastos operativos nos comen, pero de tu 100%, ¿cuánto se va a construir tu futuro?",
    captura:
      "Porcentaje de ahorro/inversión mensual. Indicio del ingreso y de la capacidad real de aporte.",
  },
  {
    id: "legado",
    titulo: "10 · Legado y protección",
    guion:
      "Tocando un tema un poco más delicado: si tú llegaras a faltar mañana, ¿qué pasaría con los tuyos? ¿Dejas broncas financieras, o tienes todo organizado —seguros, testamento, fideicomisos— para que el estilo de vida de tu familia y tus proyectos sigan adelante sin ti?",
    captura:
      "Dependientes, seguro de vida vigente, testamento/fideicomiso y patrimonio a proteger.",
  },
];
