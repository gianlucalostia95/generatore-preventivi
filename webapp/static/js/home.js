(() => {
  "use strict";

  const elementoTotale = document.getElementById("vetrina-totale-valore");
  if (!elementoTotale) return;

  const valoreFinale = parseFloat(elementoTotale.dataset.finale) || 0;
  const suffisso = elementoTotale.dataset.suffisso || "";
  const formatoNumero = new Intl.NumberFormat("it-IT", { minimumFractionDigits: 0, maximumFractionDigits: 1 });

  const preferenzaMovimentoRidotto = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  if (preferenzaMovimentoRidotto) {
    elementoTotale.textContent = formatoNumero.format(valoreFinale) + suffisso;
    return;
  }

  const durata = 900; // ms, in linea con l'ingresso delle righe sopra
  const ritardo = 1150; // parte dopo che le righe della vetrina sono apparse
  const inizio = performance.now() + ritardo;

  function aggiorna(adesso) {
    const progresso = Math.min(1, Math.max(0, (adesso - inizio) / durata));
    elementoTotale.textContent = formatoNumero.format(valoreFinale * progresso) + suffisso;
    if (progresso < 1) requestAnimationFrame(aggiorna);
  }
  requestAnimationFrame(aggiorna);
})();
