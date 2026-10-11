"""
Ricalcolo server-side delle voci di un preventivo.

Stessa logica gia' scritta e in uso in `Generazione_Preventivo.py` (righe
circa 280-310): estratta qui per essere l'unica fonte di verita' usata dagli
endpoint dell'API, cosi' il totale salvato nel database e' sempre quello
calcolato dal server, indipendentemente da cosa mostra il calcolo "live"
lato client in JavaScript.
"""
import pdf_generator


def elabora_voci(voci_grezze: list):
    """
    Filtra e normalizza le voci (scarta righe senza descrizione o con
    quantita' non positiva), poi calcola subtotale/IVA per aliquota/totale.

    Restituisce (voci_valide, subtotale, riepilogo_iva_per_aliquota,
    totale_iva, totale).
    """
    voci_valide = []
    for riga in voci_grezze:
        descrizione = str(riga.get("descrizione") or "").strip()
        quantita = float(riga.get("quantita") or 0)
        prezzo_unitario = round(float(riga.get("prezzo_unitario") or 0), 2)
        aliquota_iva_riga = round(float(riga.get("aliquota_iva") or 0), 1)

        if descrizione and quantita > 0:
            totale_riga = round(quantita * prezzo_unitario, 2)
            voci_valide.append(
                {
                    "descrizione": descrizione,
                    "quantita": quantita,
                    "prezzo_unitario": prezzo_unitario,
                    "aliquota_iva": aliquota_iva_riga,
                    "totale_riga": totale_riga,
                }
            )

    subtotale = round(sum(voce["totale_riga"] for voce in voci_valide), 2)
    riepilogo_iva_per_aliquota = pdf_generator.calcola_riepilogo_iva_per_aliquota(voci_valide)
    totale_iva = round(sum(riepilogo_iva_per_aliquota.values()), 2)
    totale = round(subtotale + totale_iva, 2)

    return voci_valide, subtotale, riepilogo_iva_per_aliquota, totale_iva, totale


def calcola_importo_sconto(subtotale: float, sconto_tipo: str, sconto_valore: float) -> float:
    """
    Importo dello sconto in EUR, a partire dal subtotale (imponibile) e dal
    tipo di sconto ("percentuale" o "importo"). Non puo' mai superare il
    subtotale stesso (non ha senso uno sconto che renda il subtotale
    negativo).
    """
    if not sconto_tipo or not sconto_valore or subtotale <= 0:
        return 0.0
    if sconto_tipo == "percentuale":
        importo_sconto = subtotale * (sconto_valore / 100)
    else:
        importo_sconto = sconto_valore
    return round(min(max(importo_sconto, 0.0), subtotale), 2)


def applica_sconto(subtotale: float, riepilogo_iva_per_aliquota: dict, totale_iva: float, totale: float,
                    sconto_tipo: str, sconto_valore: float):
    """
    Applica uno sconto globale al subtotale (prima dell'IVA), riducendo
    proporzionalmente l'IVA di ogni aliquota e il totale della stessa
    proporzione — cosi' uno sconto del 10% riduce del 10% sia il subtotale
    sia l'IVA sia il totale, qualunque sia il numero di aliquote diverse
    presenti nel documento.

    Restituisce (subtotale_netto, riepilogo_iva_netto, totale_iva_netto,
    totale_netto, importo_sconto). Se non c'e' sconto (tipo/valore assenti),
    restituisce i valori originali invariati e importo_sconto 0.0.
    """
    importo_sconto = calcola_importo_sconto(subtotale, sconto_tipo, sconto_valore)
    if importo_sconto <= 0:
        return subtotale, riepilogo_iva_per_aliquota, totale_iva, totale, 0.0

    rapporto = (subtotale - importo_sconto) / subtotale
    subtotale_netto = round(subtotale - importo_sconto, 2)
    riepilogo_iva_netto = {aliquota: round(importo * rapporto, 2) for aliquota, importo in riepilogo_iva_per_aliquota.items()}
    totale_iva_netto = round(totale_iva * rapporto, 2)
    totale_netto = round(subtotale_netto + totale_iva_netto, 2)

    return subtotale_netto, riepilogo_iva_netto, totale_iva_netto, totale_netto, importo_sconto


def importo_netto_fattura(preventivo: dict) -> float:
    """
    Importo effettivo di un preventivo fatturato, considerando l'eventuale
    sconto applicato al momento della fatturazione (colonne sconto_tipo /
    sconto_valore su `preventivi`). Usata per le statistiche della home e
    per i riepiloghi, senza dover ricaricare le voci di ogni fattura.
    """
    sconto_tipo = preventivo.get("sconto_tipo")
    sconto_valore = preventivo.get("sconto_valore")
    subtotale = preventivo.get("subtotale") or 0
    totale = preventivo.get("totale") or 0
    importo_sconto = calcola_importo_sconto(subtotale, sconto_tipo, sconto_valore)
    if importo_sconto <= 0 or subtotale <= 0:
        return totale
    rapporto = (subtotale - importo_sconto) / subtotale
    return round(totale * rapporto, 2)
