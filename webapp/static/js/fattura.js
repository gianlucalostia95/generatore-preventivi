(() => {
  "use strict";

  const modale = document.getElementById("modale-fattura");
  const sfondo = document.getElementById("sfondo-modale-fattura");
  if (!modale) return;

  const formatoValuta = new Intl.NumberFormat("it-IT", { minimumFractionDigits: 2, maximumFractionDigits: 2 });
  const formatta = (v) => formatoValuta.format(v) + " EUR";

  const campoTipo = modale.querySelector("[data-sconto-tipo]");
  const campoValore = modale.querySelector("[data-sconto-valore]");
  let datiCorrenti = null; // { preventivoId, subtotale, totaleIva, totale, dentroPannello }

  function aggiornaAnteprimaSconto() {
    if (!datiCorrenti) return;
    const tipo = campoTipo.value;
    const valore = parseFloat(campoValore.value) || 0;
    let importoSconto = 0;
    if (tipo === "percentuale") importoSconto = datiCorrenti.subtotale * (valore / 100);
    else if (tipo === "importo") importoSconto = valore;
    importoSconto = Math.min(Math.max(importoSconto, 0), datiCorrenti.subtotale);

    const rapporto = datiCorrenti.subtotale > 0 ? (datiCorrenti.subtotale - importoSconto) / datiCorrenti.subtotale : 1;
    const totaleNetto = datiCorrenti.totale * rapporto;

    modale.querySelector("[data-rif-sconto-importo]").textContent = importoSconto > 0 ? "-" + formatta(importoSconto) : "—";
    modale.querySelector("[data-rif-totale-netto]").textContent = formatta(totaleNetto);
  }

  async function apriModale(preventivoId, dentroPannello) {
    const risposta = await fetch(`/preventivi/${preventivoId}/fattura/anteprima`);
    if (!risposta.ok) return;
    const dati = await risposta.json();

    datiCorrenti = {
      preventivoId,
      dentroPannello,
      subtotale: dati.subtotale,
      totaleIva: dati.totale_iva,
      totale: dati.totale,
    };

    modale.querySelector("[data-rif-numero]").textContent = dati.numero;
    modale.querySelector("[data-rif-cliente]").textContent = dati.cliente_nome;
    modale.querySelector("[data-rif-subtotale]").textContent = formatta(dati.subtotale);
    modale.querySelector("[data-rif-iva]").textContent = formatta(dati.totale_iva);
    modale.querySelector("[data-rif-totale]").textContent = formatta(dati.totale);
    campoTipo.value = "";
    campoValore.value = "0";
    aggiornaAnteprimaSconto();

    sfondo.hidden = false;
    modale.hidden = false;
    requestAnimationFrame(() => sfondo.classList.add("visibile"));
  }

  function chiudiModale() {
    sfondo.classList.remove("visibile");
    modale.hidden = true;
    setTimeout(() => { sfondo.hidden = true; }, 220);
    datiCorrenti = null;
  }

  async function confermaGenerazione() {
    if (!datiCorrenti) return;
    const { preventivoId, dentroPannello } = datiCorrenti;
    const tipo = campoTipo.value;
    const valore = parseFloat(campoValore.value) || 0;

    let url = `/preventivi/${preventivoId}/fattura.pdf`;
    if (tipo && valore > 0) {
      url += `?sconto_tipo=${encodeURIComponent(tipo)}&sconto_valore=${encodeURIComponent(valore)}`;
    }

    const bottoneConferma = modale.querySelector("[data-conferma-fattura]");
    bottoneConferma.disabled = true;
    try {
      const risposta = await fetch(url);
      if (risposta.ok) {
        const blob = await risposta.blob();
        const nomeFile = (risposta.headers.get("Content-Disposition") || "").match(/filename="?([^"]+)"?/);
        const collegamento = document.createElement("a");
        collegamento.href = URL.createObjectURL(blob);
        collegamento.download = nomeFile ? nomeFile[1] : "fattura.pdf";
        document.body.appendChild(collegamento);
        collegamento.click();
        collegamento.remove();
      }
    } finally {
      bottoneConferma.disabled = false;
    }

    chiudiModale();
    if (dentroPannello) {
      document.dispatchEvent(new CustomEvent("storico:aggiorna"));
    } else {
      window.location.reload();
    }
  }

  // Delega globale: i bottoni "Genera fattura PDF" vivono dentro frammenti
  // che vengono ricaricati dinamicamente (pannello "Gestione profilo"),
  // quindi li intercettiamo a livello di documento invece di agganciarli
  // uno per uno ad ogni ricarica.
  document.addEventListener("click", (evento) => {
    const bottoneApri = evento.target.closest("[data-apri-modale-fattura]");
    if (bottoneApri) {
      const dentroPannello = bottoneApri.closest("#pannello-profilo") !== null;
      apriModale(bottoneApri.dataset.preventivoId, dentroPannello);
      return;
    }
    if (evento.target.closest("[data-chiudi-modale]")) {
      chiudiModale();
      return;
    }
    if (evento.target.closest("[data-conferma-fattura]")) {
      confermaGenerazione();
    }
  });

  campoTipo.addEventListener("change", aggiornaAnteprimaSconto);
  campoValore.addEventListener("input", aggiornaAnteprimaSconto);

  document.addEventListener("keydown", (evento) => {
    if (evento.key === "Escape" && !modale.hidden) chiudiModale();
  });
})();
