"""
Modulo Generazione PDF
========================

Contiene la logica condivisa per costruire i documenti PDF dell'app
(preventivi e fatture), basata su FPDF2. Viene importato sia dalla pagina
"Generazione Preventivo" sia dalla pagina "Storico Preventivi" (per la
generazione delle fatture), cosi' il layout del documento e' definito in
un solo posto invece di essere duplicato in piu' file.
"""

from datetime import date, timedelta

from fpdf import FPDF


def sanifica_testo(testo) -> str:
    """
    I font standard usati da FPDF2 non supportano tutti i caratteri Unicode
    (ad esempio il simbolo dell'euro, alcune emoji o simboli particolari).
    Questa funzione sostituisce il simbolo "€" con "EUR" e converte il
    resto del testo in una codifica compatibile (Latin-1), sostituendo
    con "?" gli eventuali altri caratteri non supportati, cosi' da evitare
    errori durante la creazione del PDF.
    """
    if testo is None:
        return ""
    testo = str(testo).replace("€", "EUR")
    return testo.encode("latin-1", "replace").decode("latin-1")


def calcola_riepilogo_iva_per_aliquota(voci: list) -> dict:
    """
    Raggruppa l'IVA delle voci per aliquota: se tutte le voci hanno la
    stessa percentuale il risultato contiene una sola voce, altrimenti una
    voce per ciascuna aliquota utilizzata. Ogni importo e' arrotondato ai
    centesimi, come si fa normalmente in un documento fiscale.
    """
    riepilogo = {}
    for voce in voci:
        aliquota = voce["aliquota_iva"]
        iva_riga = round(voce["totale_riga"] * (aliquota / 100), 2)
        riepilogo[aliquota] = round(riepilogo.get(aliquota, 0) + iva_riga, 2)
    return riepilogo


def genera_pdf_documento(
    tipo_documento: str,
    numero_documento: str,
    data_documento: date,
    mittente: dict,
    cliente: dict,
    voci: list,
    subtotale: float,
    riepilogo_iva_per_aliquota: dict,
    totale_iva: float,
    totale: float,
    note: str = "",
    validita_giorni: int = None,
    riferimento_preventivo: str = None,
) -> bytes:
    """
    Costruisce un documento PDF (preventivo o fattura) con un layout pulito
    e professionale, usando FPDF2.

    Parametri specifici:
        tipo_documento: "PREVENTIVO" oppure "FATTURA" (titolo del documento).
        validita_giorni: usato solo per i preventivi, per mostrare la data
            di scadenza dell'offerta; va lasciato a None per le fatture.
        riferimento_preventivo: usato solo per le fatture, per indicare da
            quale preventivo derivano (numero del preventivo di origine).

    Ogni voce puo' avere una propria aliquota IVA: il riepilogo finale
    mostra il totale IVA raggruppato per ciascuna aliquota utilizzata.

    Restituisce il contenuto del PDF come bytes, pronto per il download.
    """
    pdf = FPDF(orientation="P", unit="mm", format="A4")
    pdf.set_auto_page_break(auto=True, margin=20)
    pdf.add_page()

    # --- Intestazione: dati di chi emette il documento ---------------
    pdf.set_font("Helvetica", "B", 16)
    pdf.cell(0, 8, sanifica_testo(mittente["nome"]), new_x="LMARGIN", new_y="NEXT")

    pdf.set_font("Helvetica", "", 10)
    for riga in (mittente.get("piva"), mittente.get("indirizzo"), mittente.get("contatti")):
        if riga:
            pdf.cell(0, 5, sanifica_testo(riga), new_x="LMARGIN", new_y="NEXT")

    pdf.ln(6)

    # --- Titolo del documento e riferimenti (numero, data, validita') --
    pdf.set_font("Helvetica", "B", 18)
    pdf.cell(0, 10, sanifica_testo(tipo_documento), new_x="LMARGIN", new_y="NEXT")

    pdf.set_font("Helvetica", "", 10)
    pdf.cell(0, 5, f"Numero: {sanifica_testo(numero_documento)}", new_x="LMARGIN", new_y="NEXT")
    pdf.cell(0, 5, f"Data: {data_documento.strftime('%d/%m/%Y')}", new_x="LMARGIN", new_y="NEXT")
    if validita_giorni:
        scadenza = data_documento + timedelta(days=validita_giorni)
        pdf.cell(0, 5, f"Valido fino al: {scadenza.strftime('%d/%m/%Y')}", new_x="LMARGIN", new_y="NEXT")
    if riferimento_preventivo:
        pdf.cell(
            0, 5, f"Riferimento preventivo: {sanifica_testo(riferimento_preventivo)}",
            new_x="LMARGIN", new_y="NEXT",
        )

    pdf.ln(6)

    # --- Dati del cliente destinatario del documento -------------------
    pdf.set_font("Helvetica", "B", 11)
    pdf.cell(0, 6, "Destinatario:", new_x="LMARGIN", new_y="NEXT")

    pdf.set_font("Helvetica", "", 10)
    for riga in (cliente.get("nome"), cliente.get("indirizzo"), cliente.get("piva"), cliente.get("email")):
        if riga:
            pdf.cell(0, 5, sanifica_testo(riga), new_x="LMARGIN", new_y="NEXT")

    pdf.ln(8)

    # --- Tabella delle voci di spesa (con IVA per singola voce) ----------
    larghezza_descrizione = 70
    larghezza_qta = 22
    larghezza_prezzo = 28
    larghezza_iva = 20
    larghezza_totale = 30

    pdf.set_font("Helvetica", "B", 10)
    pdf.set_fill_color(230, 230, 230)
    pdf.cell(larghezza_descrizione, 8, "Descrizione", border=1, fill=True)
    pdf.cell(larghezza_qta, 8, "Quantita'", border=1, align="C", fill=True)
    pdf.cell(larghezza_prezzo, 8, "Prezzo unit.", border=1, align="C", fill=True)
    pdf.cell(larghezza_iva, 8, "IVA %", border=1, align="C", fill=True)
    pdf.cell(larghezza_totale, 8, "Totale", border=1, align="C", fill=True, new_x="LMARGIN", new_y="NEXT")

    pdf.set_font("Helvetica", "", 10)
    for voce in voci:
        pdf.cell(larghezza_descrizione, 8, sanifica_testo(voce["descrizione"]), border=1)
        pdf.cell(larghezza_qta, 8, f"{voce['quantita']:g}", border=1, align="C")
        pdf.cell(larghezza_prezzo, 8, f"{voce['prezzo_unitario']:.2f} EUR", border=1, align="C")
        pdf.cell(larghezza_iva, 8, f"{voce['aliquota_iva']:g}%", border=1, align="C")
        pdf.cell(
            larghezza_totale, 8, f"{voce['totale_riga']:.2f} EUR", border=1, align="C",
            new_x="LMARGIN", new_y="NEXT",
        )

    pdf.ln(4)

    # --- Riepilogo dei totali, allineato a destra sotto la tabella ------
    larghezza_etichetta = larghezza_descrizione + larghezza_qta + larghezza_prezzo
    larghezza_valore = larghezza_iva + larghezza_totale

    pdf.set_font("Helvetica", "", 10)
    pdf.cell(larghezza_etichetta, 7, "Subtotale (imponibile)")
    pdf.cell(larghezza_valore, 7, f"{subtotale:.2f} EUR", align="C", new_x="LMARGIN", new_y="NEXT")

    # L'IVA viene mostrata suddivisa per aliquota, nel caso il documento
    # contenga voci con percentuali diverse.
    for aliquota, importo in sorted(riepilogo_iva_per_aliquota.items()):
        pdf.cell(larghezza_etichetta, 7, f"IVA {aliquota:g}%")
        pdf.cell(larghezza_valore, 7, f"{importo:.2f} EUR", align="C", new_x="LMARGIN", new_y="NEXT")

    pdf.set_font("Helvetica", "B", 12)
    pdf.cell(larghezza_etichetta, 9, "TOTALE", border="T")
    pdf.cell(larghezza_valore, 9, f"{totale:.2f} EUR", border="T", align="C", new_x="LMARGIN", new_y="NEXT")

    # --- Note aggiuntive (facoltative) ------------------------------------
    if note:
        pdf.ln(8)
        pdf.set_font("Helvetica", "B", 10)
        pdf.cell(0, 6, "Note:", new_x="LMARGIN", new_y="NEXT")
        pdf.set_font("Helvetica", "", 10)
        pdf.multi_cell(0, 5, sanifica_testo(note))

    # --- Coordinate bancarie per il pagamento tramite bonifico -----------
    if mittente.get("iban"):
        pdf.ln(8)
        pdf.set_font("Helvetica", "B", 10)
        pdf.cell(0, 6, "Coordinate bancarie per il bonifico:", new_x="LMARGIN", new_y="NEXT")
        pdf.set_font("Helvetica", "", 10)
        pdf.cell(0, 5, f"IBAN: {sanifica_testo(mittente['iban'])}", new_x="LMARGIN", new_y="NEXT")

    # pdf.output() restituisce un bytearray: lo convertiamo in bytes
    # per renderlo compatibile con st.download_button.
    return bytes(pdf.output())
