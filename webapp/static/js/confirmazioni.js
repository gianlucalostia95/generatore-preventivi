// Richiede conferma prima di inviare un form marcato con data-conferma
// (usato per le azioni distruttive: elimina cliente, elimina preventivo).
document.addEventListener("submit", (evento) => {
  const modulo = evento.target.closest("form[data-conferma]");
  if (modulo && !window.confirm(modulo.dataset.conferma)) {
    evento.preventDefault();
  }
});
