(() => {
  "use strict";

  const bottoneApri = document.getElementById("apri-pannello-profilo");
  const bottoneChiudi = document.getElementById("chiudi-pannello");
  const pannello = document.getElementById("pannello-profilo");
  const sfondo = document.getElementById("sfondo-pannello");
  const tabs = pannello.querySelectorAll(".tab-profilo");
  const contenuti = {
    azienda: pannello.querySelector('[data-contenuto="azienda"]'),
    storico: pannello.querySelector('[data-contenuto="storico"]'),
  };

  const caricato = { azienda: false, storico: false };
  let ultimaQueryStorico = "";

  function querySenzaFile(modulo) {
    return new URLSearchParams(new FormData(modulo)).toString();
  }

  function agganciaFormAzienda() {
    const modulo = contenuti.azienda.querySelector("[data-form-profilo]");
    if (!modulo) return;
    modulo.addEventListener("submit", async (evento) => {
      evento.preventDefault();
      await fetch("/profilo", { method: "POST", body: new FormData(modulo) });
      await caricaAzienda();
      const avviso = contenuti.azienda.querySelector("[data-messaggio-salvato]");
      if (avviso) avviso.hidden = false;
    });
  }

  function agganciaStorico() {
    const formFiltri = contenuti.storico.querySelector("[data-form-filtri]");
    if (formFiltri) {
      formFiltri.addEventListener("submit", (evento) => {
        evento.preventDefault();
        caricaStorico(querySenzaFile(formFiltri));
      });
    }
    const azzera = contenuti.storico.querySelector("[data-azzera-filtri]");
    if (azzera) {
      azzera.addEventListener("click", (evento) => {
        evento.preventDefault();
        caricaStorico("");
      });
    }
    for (const modulo of contenuti.storico.querySelectorAll("[data-azione-storico]")) {
      modulo.addEventListener("submit", async (evento) => {
        evento.preventDefault();
        evento.stopPropagation(); // la conferma, se serve, la gestiamo qui sotto
        const messaggioConferma = modulo.dataset.conferma;
        if (messaggioConferma && !window.confirm(messaggioConferma)) return;
        await fetch(modulo.action, { method: "POST" });
        await caricaStorico(ultimaQueryStorico);
      });
    }
    const bottoneEspandi = contenuti.storico.querySelector("[data-pannello-espandi]");
    if (bottoneEspandi) {
      bottoneEspandi.textContent = pannello.classList.contains("espanso") ? "Riduci" : "Schermo intero";
      bottoneEspandi.addEventListener("click", () => {
        const espanso = pannello.classList.toggle("espanso");
        bottoneEspandi.textContent = espanso ? "Riduci" : "Schermo intero";
      });
    }
  }

  // Una fattura generata dal modale (fattura.js) può cambiare lo stato
  // mostrato nello storico: se la tab è già stata caricata, la ricarichiamo.
  document.addEventListener("storico:aggiorna", () => {
    if (caricato.storico) caricaStorico(ultimaQueryStorico);
  });

  async function caricaAzienda() {
    const risposta = await fetch("/pannello/profilo");
    contenuti.azienda.innerHTML = await risposta.text();
    agganciaFormAzienda();
    caricato.azienda = true;
  }

  async function caricaStorico(query = "") {
    ultimaQueryStorico = query;
    const risposta = await fetch("/pannello/storico" + (query ? `?${query}` : ""));
    contenuti.storico.innerHTML = await risposta.text();
    agganciaStorico();
    caricato.storico = true;
  }

  function mostraTab(nome) {
    for (const tab of tabs) {
      const attiva = tab.dataset.tab === nome;
      tab.classList.toggle("attiva", attiva);
      tab.setAttribute("aria-selected", attiva ? "true" : "false");
    }
    for (const [chiave, elemento] of Object.entries(contenuti)) {
      elemento.hidden = chiave !== nome;
    }
    if (nome === "azienda" && !caricato.azienda) caricaAzienda();
    if (nome === "storico" && !caricato.storico) caricaStorico();
  }

  for (const tab of tabs) {
    tab.addEventListener("click", () => mostraTab(tab.dataset.tab));
  }

  function chiudiConEsc(evento) {
    if (evento.key === "Escape") chiudiPannello();
  }

  function apriPannello() {
    sfondo.hidden = false;
    requestAnimationFrame(() => {
      sfondo.classList.add("visibile");
      pannello.classList.add("aperto");
    });
    pannello.setAttribute("aria-hidden", "false");
    bottoneApri.setAttribute("aria-expanded", "true");
    if (!caricato.azienda) caricaAzienda();
    document.addEventListener("keydown", chiudiConEsc);
  }

  function chiudiPannello() {
    sfondo.classList.remove("visibile");
    pannello.classList.remove("aperto");
    pannello.setAttribute("aria-hidden", "true");
    bottoneApri.setAttribute("aria-expanded", "false");
    document.removeEventListener("keydown", chiudiConEsc);
    setTimeout(() => {
      if (!pannello.classList.contains("aperto")) sfondo.hidden = true;
    }, 300);
  }

  bottoneApri.addEventListener("click", apriPannello);
  bottoneChiudi.addEventListener("click", chiudiPannello);
  sfondo.addEventListener("click", chiudiPannello);
})();
