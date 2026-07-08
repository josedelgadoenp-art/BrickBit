const campoKey = document.getElementById("api-key");
const campoModelo = document.getElementById("modelo");
const campoVoz = document.getElementById("voz");
const campoTel = document.getElementById("tel-asesor");
const campoLiga = document.getElementById("liga-cierre");
const estado = document.getElementById("estado");

let vozGuardada = "";

chrome.storage.local
  .get(["apiKey", "modelo", "vozIris", "telAsesor", "ligaCierre"])
  .then(({ apiKey, modelo, vozIris, telAsesor, ligaCierre }) => {
    if (apiKey) campoKey.value = apiKey;
    if (modelo) campoModelo.value = modelo;
    vozGuardada = vozIris || "";
    if (telAsesor) campoTel.value = telAsesor;
    if (ligaCierre) campoLiga.value = ligaCierre;
    poblarVoces();
  });

// Las voces se cargan asíncronamente en Chrome.
function poblarVoces() {
  const voces = speechSynthesis.getVoices();
  const es = voces.filter((v) => v.lang && v.lang.toLowerCase().startsWith("es"));
  const otras = voces.filter((v) => !es.length || !v.lang.toLowerCase().startsWith("es"));
  const lista = es.length ? es : otras; // si no hay español, muestra todas
  campoVoz.innerHTML = '<option value="">Automática (mejor voz femenina)</option>';
  for (const v of lista) {
    const opt = document.createElement("option");
    opt.value = v.name;
    opt.textContent = `${v.name} — ${v.lang}`;
    if (v.name === vozGuardada) opt.selected = true;
    campoVoz.appendChild(opt);
  }
}
speechSynthesis.addEventListener?.("voiceschanged", poblarVoces);

document.getElementById("probar-voz").addEventListener("click", () => {
  speechSynthesis.cancel();
  const u = new SpeechSynthesisUtterance(
    "Hola, soy Iris, tu asistente de GNP. Con gusto te acompaño en esta llamada."
  );
  const voz = speechSynthesis.getVoices().find((v) => v.name === campoVoz.value);
  if (voz) {
    u.voice = voz;
    u.lang = voz.lang;
  } else {
    u.lang = "es-MX";
  }
  u.rate = 0.96;
  u.pitch = 1.15;
  speechSynthesis.speak(u);
});

document.getElementById("guardar").addEventListener("click", async () => {
  const tel = campoTel.value.replace(/\D/g, ""); // solo dígitos
  await chrome.storage.local.set({
    apiKey: campoKey.value.trim(),
    modelo: campoModelo.value,
    vozIris: campoVoz.value,
    telAsesor: tel,
    ligaCierre: campoLiga.value.trim(),
  });
  estado.textContent = "✓ Guardado";
  setTimeout(() => (estado.textContent = ""), 2500);
});
