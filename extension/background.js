// Abre el panel lateral al hacer clic en el icono de la extensión.
// Guardado tras chrome.sidePanel?: en un navegador sin la API, un TypeError
// aquí mataría todo el service worker (incluido el onInstalled de abajo).
if (chrome.sidePanel?.setPanelBehavior) {
  chrome.sidePanel
    .setPanelBehavior({ openPanelOnActionClick: true })
    .catch((err) => console.error("sidePanel.setPanelBehavior:", err));
}

// Al instalar por primera vez, abre la página de opciones para configurar la API key.
chrome.runtime.onInstalled.addListener((details) => {
  if (details.reason === "install") {
    chrome.runtime.openOptionsPage();
  }
});
