(() => {
  "use strict";

  const SUPPORTA_CONDIVISIONE_FILE = typeof navigator.share === "function" && typeof navigator.canShare === "function";

  function mostraMenuAlternativo(testoMessaggio, urlPdf, nomeFile, emailCliente) {
    const modale = document.getElementById("modale-condividi");

    modale.querySelector("[data-condividi-messaggio]").textContent = testoMessaggio;

    const linkScarica = modale.querySelector("[data-condividi-scarica]");
    linkScarica.href = urlPdf;
    linkScarica.download = nomeFile;

    const corpoEmail = encodeURIComponent(
      `${testoMessaggio}\n\n(Ricordati di allegare il PDF scaricato al passo 1.)`
    );
    const linkEmail = modale.querySelector("[data-condividi-email]");
    linkEmail.href = `mailto:${emailCliente || ""}?subject=${encodeURIComponent(testoMessaggio)}&body=${corpoEmail}`;

    const linkWhatsapp = modale.querySelector("[data-condividi-whatsapp]");
    linkWhatsapp.href = `https://wa.me/?text=${encodeURIComponent(testoMessaggio + " — ti allego il PDF a parte.")}`;

    document.getElementById("sfondo-modale-condividi").hidden = false;
    modale.hidden = false;
  }

  function chiudiMenuAlternativo() {
    document.getElementById("modale-condividi").hidden = true;
    document.getElementById("sfondo-modale-condividi").hidden = true;
  }

  document.addEventListener("click", async (evento) => {
    const bottone = evento.target.closest("[data-condividi]");
    if (!bottone) return;

    const { preventivoId, tipo, numero, cliente, clienteEmail } = bottone.dataset;
    const urlPdf = tipo === "fattura"
      ? `/preventivi/${preventivoId}/fattura.pdf`
      : `/preventivi/${preventivoId}/preventivo.pdf`;
    const nomeFile = `${tipo}_${numero}.pdf`;
    const etichettaTipo = tipo === "fattura" ? "Fattura" : "Preventivo";
    const testoMessaggio = `${etichettaTipo} ${numero} — ${cliente}`;

    if (SUPPORTA_CONDIVISIONE_FILE) {
      try {
        const risposta = await fetch(urlPdf);
        if (risposta.ok) {
          const blob = await risposta.blob();
          const file = new File([blob], nomeFile, { type: "application/pdf" });
          if (navigator.canShare({ files: [file] })) {
            await navigator.share({ files: [file], title: nomeFile, text: testoMessaggio });
            return;
          }
        }
      } catch (errore) {
        if (errore && errore.name === "AbortError") return; // l'utente ha annullato il menu di condivisione
        // altrimenti procede con il menu alternativo sotto
      }
    }

    mostraMenuAlternativo(testoMessaggio, urlPdf, nomeFile, clienteEmail);
  });

  document.addEventListener("click", (evento) => {
    if (evento.target.closest("[data-chiudi-condividi]") || evento.target === document.getElementById("sfondo-modale-condividi")) {
      chiudiMenuAlternativo();
    }
  });

  document.addEventListener("keydown", (evento) => {
    if (evento.key === "Escape" && !document.getElementById("modale-condividi").hidden) chiudiMenuAlternativo();
  });
})();
