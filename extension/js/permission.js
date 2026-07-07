const resultado = document.getElementById("resultado");

async function estadoPermiso() {
  try {
    const st = await navigator.permissions.query({ name: "microphone" });
    return st.state; // "granted" | "prompt" | "denied"
  } catch (_) {
    return "prompt";
  }
}

document.getElementById("pedir").addEventListener("click", async () => {
  try {
    const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
    stream.getTracks().forEach((t) => t.stop());
    resultado.textContent =
      "✓ Permiso concedido. Ya puedes cerrar esta pestaña y usar «Escuchar» en el panel.";
    resultado.className = "ok";
  } catch (err) {
    if (err.name === "NotFoundError" || err.name === "OverconstrainedError") {
      resultado.textContent =
        "✕ No se detecta ningún micrófono. Conecta uno y vuelve a intentar.";
      resultado.className = "error";
      return;
    }
    if (err.name === "NotReadableError") {
      resultado.textContent =
        "✕ El micrófono está ocupado por otra aplicación. Ciérrala y vuelve a intentar.";
      resultado.className = "error";
      return;
    }
    const estado = await estadoPermiso();
    if (estado === "denied") {
      // Con la denegación guardada, Chrome ya no vuelve a mostrar el diálogo:
      // hay que restablecer el permiso desde la configuración del navegador.
      resultado.innerHTML =
        "✕ El permiso está bloqueado para esta extensión. Para restablecerlo copia y abre " +
        "<code>chrome://settings/content/microphone</code> (o entra a Extensiones → detalles " +
        "de «GNP Copiloto» → Configuración del sitio), permite el micrófono y vuelve a intentar.";
      resultado.className = "error";
    } else {
      resultado.textContent =
        "✕ Permiso no concedido. Haz clic de nuevo en el botón y elige «Permitir» en el diálogo.";
      resultado.className = "error";
    }
  }
});
