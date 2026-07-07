const campoKey = document.getElementById("api-key");
const campoModelo = document.getElementById("modelo");
const estado = document.getElementById("estado");

chrome.storage.local.get(["apiKey", "modelo"]).then(({ apiKey, modelo }) => {
  if (apiKey) campoKey.value = apiKey;
  if (modelo) campoModelo.value = modelo;
});

document.getElementById("guardar").addEventListener("click", async () => {
  const apiKey = campoKey.value.trim();
  const modelo = campoModelo.value;
  await chrome.storage.local.set({ apiKey, modelo });
  estado.textContent = "✓ Guardado";
  setTimeout(() => (estado.textContent = ""), 2500);
});
