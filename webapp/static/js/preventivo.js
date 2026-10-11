(() => {
  "use strict";

  const dati = JSON.parse(document.getElementById("dati-iniziali").textContent);
  let modalita = dati.modalita; // "nuovo" | "modifica" | "duplica"
  let preventivoId = dati.preventivoId;

  const clientiPerId = {};
  for (const c of dati.clienti) clientiPerId[String(c.id)] = c;

  const corpoVoci = document.getElementById("corpo-voci");
  const modelloRiga = document.getElementById("modello-riga-voce");
  const formatoValuta = new Intl.NumberFormat("it-IT", { minimumFractionDigits: 2, maximumFractionDigits: 2 });

  // ---------------- Righe voce: creazione, rimozione, calcolo ----------------
  function creaRiga(voce) {
    const frammento = modelloRiga.content.cloneNode(true);
    const riga = frammento.querySelector(".riga-voce");
    riga.querySelector(".voce-descrizione").value = voce.descrizione || "";
    riga.querySelector(".voce-quantita").value = voce.quantita ?? 1;
    riga.querySelector(".voce-prezzo").value = (voce.prezzo_unitario ?? 0).toFixed(2);
    riga.querySelector(".voce-iva").value = voce.aliquota_iva ?? 22;
    corpoVoci.appendChild(riga);
  }

  function totaleRiga(riga) {
    const quantita = parseFloat(riga.querySelector(".voce-quantita").value) || 0;
    const prezzo = parseFloat(riga.querySelector(".voce-prezzo").value) || 0;
    return quantita * prezzo;
  }

  function ricalcolaTutto() {
    let subtotale = 0;
    let totaleIva = 0;
    for (const riga of corpoVoci.querySelectorAll(".riga-voce")) {
      const descrizione = riga.querySelector(".voce-descrizione").value.trim();
      const quantita = parseFloat(riga.querySelector(".voce-quantita").value) || 0;
      const totRiga = descrizione && quantita > 0 ? totaleRiga(riga) : 0;
      riga.querySelector(".riga-totale-voce").textContent = formatoValuta.format(totRiga);
      if (descrizione && quantita > 0) {
        const iva = parseFloat(riga.querySelector(".voce-iva").value) || 0;
        subtotale += totRiga;
        totaleIva += totRiga * (iva / 100);
      }
    }
    document.getElementById("val-subtotale").textContent = formatoValuta.format(subtotale) + " EUR";
    document.getElementById("val-iva").textContent = formatoValuta.format(totaleIva) + " EUR";
    document.getElementById("val-totale").textContent = formatoValuta.format(subtotale + totaleIva) + " EUR";
  }

  function aggiornaStatoRimozione() {
    const righe = corpoVoci.querySelectorAll(".riga-voce");
    const disabilita = righe.length <= 1;
    for (const riga of righe) riga.querySelector(".rimuovi-riga").disabled = disabilita;
  }

  corpoVoci.addEventListener("input", ricalcolaTutto);
  corpoVoci.addEventListener("click", (evento) => {
    const bottone = evento.target.closest(".rimuovi-riga");
    if (!bottone || bottone.disabled) return;
    bottone.closest(".riga-voce").remove();
    aggiornaStatoRimozione();
    ricalcolaTutto();
  });

  document.getElementById("btn-aggiungi-voce").addEventListener("click", () => {
    creaRiga({ descrizione: "", quantita: 1, prezzo_unitario: 0, aliquota_iva: 22 });
    aggiornaStatoRimozione();
    ricalcolaTutto();
  });

  const vociIniziali = dati.voci.length ? dati.voci : [{ descrizione: "", quantita: 1, prezzo_unitario: 0, aliquota_iva: 22 }];
  for (const voce of vociIniziali) creaRiga(voce);
  aggiornaStatoRimozione();
  ricalcolaTutto();

  // ---------------- Selettore cliente: nuovo vs esistente ----------------
  const selettoreCliente = document.getElementById("c-selettore");
  const campiCliente = ["c-nome", "c-indirizzo", "c-piva", "c-email"].map((id) => document.getElementById(id));
  const areaSalvaAnagrafica = document.getElementById("area-salva-anagrafica");

  function applicaModalitaCliente() {
    const selezionato = selettoreCliente.value;
    if (selezionato && clientiPerId[selezionato]) {
      const c = clientiPerId[selezionato];
      document.getElementById("c-nome").value = c.nome;
      document.getElementById("c-indirizzo").value = c.indirizzo;
      document.getElementById("c-piva").value = c.piva;
      document.getElementById("c-email").value = c.email;
      for (const campo of campiCliente) campo.readOnly = true;
      areaSalvaAnagrafica.hidden = true;
    } else {
      for (const campo of campiCliente) campo.readOnly = false;
      areaSalvaAnagrafica.hidden = false;
    }
  }
  selettoreCliente.addEventListener("change", applicaModalitaCliente);
  applicaModalitaCliente();

  // ---------------- Avviso di modifiche non salvate ----------------
  let formModificato = false;
  const modulo = document.getElementById("form-preventivo");
  modulo.addEventListener("input", () => { formModificato = true; });
  modulo.addEventListener("change", () => { formModificato = true; });
  window.addEventListener("beforeunload", (evento) => {
    if (formModificato) {
      evento.preventDefault();
      evento.returnValue = "";
    }
  });

  // ---------------- Invio: salva (crea/aggiorna) e scarica il PDF ----------------
  const bottoneSalva = document.getElementById("btn-salva");
  const areaErrore = document.getElementById("area-errore");

  function mostraErrore(messaggio) {
    areaErrore.textContent = messaggio;
    areaErrore.hidden = false;
  }
  function nascondiErrore() {
    areaErrore.hidden = true;
  }

  function raccogliVoci() {
    const voci = [];
    for (const riga of corpoVoci.querySelectorAll(".riga-voce")) {
      voci.push({
        descrizione: riga.querySelector(".voce-descrizione").value,
        quantita: parseFloat(riga.querySelector(".voce-quantita").value) || 0,
        prezzo_unitario: parseFloat(riga.querySelector(".voce-prezzo").value) || 0,
        aliquota_iva: parseFloat(riga.querySelector(".voce-iva").value) || 0,
      });
    }
    return voci;
  }

  modulo.addEventListener("submit", async (evento) => {
    evento.preventDefault();
    nascondiErrore();
    bottoneSalva.disabled = true;

    const clienteId = selettoreCliente.value ? parseInt(selettoreCliente.value, 10) : null;
    const corpo = {
      numero: document.getElementById("p-numero").value,
      data: document.getElementById("p-data").value,
      validita_giorni: parseInt(document.getElementById("p-validita").value, 10) || 0,
      note: document.getElementById("p-note").value,
      mittente: {
        nome: document.getElementById("m-nome").value,
        piva: document.getElementById("m-piva").value,
        indirizzo: document.getElementById("m-indirizzo").value,
        contatti: document.getElementById("m-contatti").value,
        iban: document.getElementById("m-iban").value,
      },
      cliente: {
        id: clienteId,
        nome: document.getElementById("c-nome").value,
        indirizzo: document.getElementById("c-indirizzo").value,
        piva: document.getElementById("c-piva").value,
        email: document.getElementById("c-email").value,
        salva_in_anagrafica: clienteId === null && document.getElementById("c-salva-anagrafica").checked,
      },
      voci: raccogliVoci(),
    };

    const url = modalita === "modifica" ? `/api/preventivi/${preventivoId}` : "/api/preventivi";
    const metodo = modalita === "modifica" ? "PUT" : "POST";

    try {
      const risposta = await fetch(url, {
        method: metodo,
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(corpo),
      });

      if (risposta.status === 409) {
        const dettaglio = await risposta.json();
        mostraErrore(dettaglio.errore || "Numero preventivo già in uso.");
        return;
      }
      if (!risposta.ok) {
        let messaggio = "Si è verificato un errore durante il salvataggio.";
        try {
          const dettaglio = await risposta.json();
          messaggio = dettaglio.detail || dettaglio.errore || messaggio;
        } catch (_) { /* risposta senza corpo JSON */ }
        mostraErrore(messaggio);
        return;
      }

      const idSalvato = risposta.headers.get("X-Preventivo-Id");
      if (idSalvato) {
        modalita = "modifica";
        preventivoId = idSalvato;
        bottoneSalva.textContent = "Salva modifiche e rigenera PDF";
      }

      const blob = await risposta.blob();
      const nomeFile = (risposta.headers.get("Content-Disposition") || "").match(/filename="?([^"]+)"?/);
      const collegamento = document.createElement("a");
      collegamento.href = URL.createObjectURL(blob);
      collegamento.download = nomeFile ? nomeFile[1] : "preventivo.pdf";
      document.body.appendChild(collegamento);
      collegamento.click();
      collegamento.remove();
      formModificato = false;
    } catch (errore) {
      mostraErrore("Impossibile contattare il server. Riprova.");
    } finally {
      bottoneSalva.disabled = false;
    }
  });
})();
