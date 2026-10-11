"""
Pagina "Generazione Preventivo": crea, modifica, duplica un preventivo e
genera/annulla la fattura corrispondente.

Le pagine di form (nuovo/modifica/duplica) sono GET che renderizzano un
template; il salvataggio vero e proprio passa per l'API JSON sotto
`/api/preventivi` (serve per poter scaricare il PDF binario risultante
senza perdere lo stato del form e per mostrare un eventuale errore di
numero duplicato senza una navigazione a pagina intera).
"""
from datetime import date
from typing import List, Optional

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import JSONResponse, RedirectResponse, Response
from pydantic import BaseModel

import database
import pdf_generator
from webapp.calcoli import applica_sconto, elabora_voci
from webapp.templating import templates

router = APIRouter()


# ---------------------------------------------------------------------------
# Pagine (GET): mostrano il form di preventivo in una delle 3 modalita'
# ---------------------------------------------------------------------------
@router.get("/preventivi/nuovo")
def form_nuovo(request: Request):
    mittente = database.ottieni_profilo_mittente()
    contesto = {
        "modalita": "nuovo",
        "preventivo_id": None,
        "mittente": mittente,
        "numero": database.prossimo_numero_preventivo(),
        "data": date.today().isoformat(),
        "validita_giorni": 30,
        "note": "",
        "cliente": {"id": None, "nome": "", "indirizzo": "", "piva": "", "email": ""},
        "voci": [{"descrizione": "", "quantita": 1, "prezzo_unitario": 0, "aliquota_iva": 22}],
        "clienti": database.elenco_clienti(),
    }
    return templates.TemplateResponse(request, "preventivo_form.html", contesto)


@router.get("/preventivi/{preventivo_id}/modifica")
def form_modifica(request: Request, preventivo_id: int):
    return _form_da_preventivo_esistente(request, preventivo_id, modalita="modifica")


@router.get("/preventivi/{preventivo_id}/duplica")
def form_duplica(request: Request, preventivo_id: int):
    return _form_da_preventivo_esistente(request, preventivo_id, modalita="duplica")


def _form_da_preventivo_esistente(request: Request, preventivo_id: int, modalita: str):
    preventivo = database.ottieni_preventivo_completo(preventivo_id)
    if preventivo is None:
        raise HTTPException(status_code=404, detail="Preventivo non trovato")

    contesto = {
        "modalita": modalita,
        "preventivo_id": preventivo_id if modalita == "modifica" else None,
        "mittente": {
            "nome": preventivo["mittente_nome"] or "",
            "piva": preventivo["mittente_piva"] or "",
            "indirizzo": preventivo["mittente_indirizzo"] or "",
            "contatti": preventivo["mittente_contatti"] or "",
            "iban": preventivo["mittente_iban"] or "",
        },
        "numero": preventivo["numero"] if modalita == "modifica" else database.prossimo_numero_preventivo(),
        "data": date.today().isoformat(),
        "validita_giorni": preventivo["validita_giorni"] or 0,
        "note": preventivo["note"] or "",
        "cliente": {
            "id": preventivo["cliente_id"],
            "nome": preventivo["cliente_nome"] or "",
            "indirizzo": preventivo["cliente_indirizzo"] or "",
            "piva": preventivo["cliente_piva"] or "",
            "email": preventivo["cliente_email"] or "",
        },
        "voci": [
            {
                "descrizione": v["descrizione"],
                "quantita": v["quantita"],
                "prezzo_unitario": v["prezzo_unitario"],
                "aliquota_iva": v["aliquota_iva"],
            }
            for v in preventivo["voci"]
        ]
        or [{"descrizione": "", "quantita": 1, "prezzo_unitario": 0, "aliquota_iva": 22}],
        "clienti": database.elenco_clienti(),
    }
    if modalita == "duplica":
        contesto["avviso"] = "Preventivo duplicato: controlla i dati prima di generare il nuovo documento."
    return templates.TemplateResponse(request, "preventivo_form.html", contesto)


# ---------------------------------------------------------------------------
# API JSON: salvataggio (crea/aggiorna) con generazione PDF in risposta
# ---------------------------------------------------------------------------
class VoceInput(BaseModel):
    descrizione: str = ""
    quantita: float = 0
    prezzo_unitario: float = 0
    aliquota_iva: float = 22.0


class ClienteInput(BaseModel):
    id: Optional[int] = None
    nome: str = ""
    indirizzo: str = ""
    piva: str = ""
    email: str = ""
    salva_in_anagrafica: bool = False


class MittenteInput(BaseModel):
    nome: str = ""
    piva: str = ""
    indirizzo: str = ""
    contatti: str = ""
    iban: str = ""


class PreventivoInput(BaseModel):
    numero: str
    data: str
    validita_giorni: int = 0
    note: str = ""
    mittente: MittenteInput
    cliente: ClienteInput
    voci: List[VoceInput]


def _salva_e_genera_pdf(dati: PreventivoInput, preventivo_id: Optional[int]):
    voci_grezze = [v.model_dump() for v in dati.voci]
    voci_valide, subtotale, riepilogo_iva, totale_iva, totale = elabora_voci(voci_grezze)

    numero = dati.numero.strip()
    nome_mittente = dati.mittente.nome.strip()
    nome_cliente = dati.cliente.nome.strip()

    if not nome_mittente or not nome_cliente or not voci_valide:
        raise HTTPException(
            status_code=400,
            detail="Servono almeno: nome del mittente, nome del cliente e una voce di spesa completa.",
        )

    cliente_id = dati.cliente.id
    if cliente_id is None and dati.cliente.salva_in_anagrafica and nome_cliente:
        cliente_id = database.salva_cliente(
            {
                "nome": nome_cliente,
                "indirizzo": dati.cliente.indirizzo.strip(),
                "piva": dati.cliente.piva.strip(),
                "email": dati.cliente.email.strip(),
            }
        )

    dati_preventivo = {
        "numero": numero,
        "data": dati.data,
        "validita_giorni": dati.validita_giorni,
        "note": dati.note,
        "mittente_nome": nome_mittente,
        "mittente_piva": dati.mittente.piva.strip(),
        "mittente_indirizzo": dati.mittente.indirizzo.strip(),
        "mittente_contatti": dati.mittente.contatti.strip(),
        "mittente_iban": dati.mittente.iban.strip(),
        "cliente_id": cliente_id,
        "cliente_nome": nome_cliente,
        "cliente_indirizzo": dati.cliente.indirizzo.strip(),
        "cliente_piva": dati.cliente.piva.strip(),
        "cliente_email": dati.cliente.email.strip(),
        "subtotale": subtotale,
        "totale_iva": totale_iva,
        "totale": totale,
    }

    try:
        id_salvato = database.salva_preventivo(dati_preventivo, voci_valide, preventivo_id=preventivo_id)
    except database.NumeroPreventivoEsistente:
        return JSONResponse(
            status_code=409,
            content={"errore": f"Esiste già un preventivo con il numero '{numero}'. Cambia il numero e riprova."},
        )

    pdf_bytes = pdf_generator.genera_pdf_documento(
        tipo_documento="PREVENTIVO",
        numero_documento=numero,
        data_documento=date.fromisoformat(dati.data),
        mittente={
            "nome": nome_mittente,
            "piva": dati.mittente.piva.strip(),
            "indirizzo": dati.mittente.indirizzo.strip(),
            "contatti": dati.mittente.contatti.strip(),
            "iban": dati.mittente.iban.strip(),
        },
        cliente={
            "nome": nome_cliente,
            "indirizzo": dati.cliente.indirizzo.strip(),
            "piva": dati.cliente.piva.strip(),
            "email": dati.cliente.email.strip(),
        },
        voci=voci_valide,
        subtotale=subtotale,
        riepilogo_iva_per_aliquota=riepilogo_iva,
        totale_iva=totale_iva,
        totale=totale,
        note=dati.note,
        validita_giorni=dati.validita_giorni,
    )

    return Response(
        content=bytes(pdf_bytes),
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'attachment; filename="preventivo_{numero}.pdf"',
            "X-Preventivo-Id": str(id_salvato),
            "X-Preventivo-Numero": numero,
        },
    )


@router.post("/api/preventivi")
def crea_preventivo(dati: PreventivoInput):
    return _salva_e_genera_pdf(dati, preventivo_id=None)


@router.put("/api/preventivi/{preventivo_id}")
def aggiorna_preventivo(preventivo_id: int, dati: PreventivoInput):
    return _salva_e_genera_pdf(dati, preventivo_id=preventivo_id)


# ---------------------------------------------------------------------------
# Azioni da Storico: elimina preventivo, genera/annulla fattura
# (form HTML tradizionali con redirect, nessun JS necessario)
# ---------------------------------------------------------------------------
@router.post("/preventivi/{preventivo_id}/elimina")
def elimina_preventivo(preventivo_id: int):
    database.elimina_preventivo(preventivo_id)
    return RedirectResponse(url="/storico", status_code=303)


@router.get("/preventivi/{preventivo_id}/fattura/anteprima")
def anteprima_fattura(preventivo_id: int):
    """Dati di riepilogo per il pop-up di conferma, prima di generare davvero la fattura."""
    preventivo = database.ottieni_preventivo_completo(preventivo_id)
    if preventivo is None:
        raise HTTPException(status_code=404, detail="Preventivo non trovato")
    return {
        "numero": preventivo["numero"],
        "cliente_nome": preventivo["cliente_nome"],
        "subtotale": preventivo["subtotale"],
        "totale_iva": preventivo["totale_iva"],
        "totale": preventivo["totale"],
        "gia_fatturato": bool(preventivo.get("numero_fattura")),
        "sconto_tipo": preventivo.get("sconto_tipo"),
        "sconto_valore": preventivo.get("sconto_valore"),
    }


@router.get("/preventivi/{preventivo_id}/fattura.pdf")
def scarica_fattura(preventivo_id: int, sconto_tipo: str = None, sconto_valore: float = None):
    if sconto_tipo not in (None, "percentuale", "importo"):
        raise HTTPException(status_code=400, detail="Tipo di sconto non valido.")

    preventivo = database.genera_fattura_da_preventivo(preventivo_id, sconto_tipo=sconto_tipo, sconto_valore=sconto_valore)
    if preventivo is None:
        raise HTTPException(status_code=404, detail="Preventivo non trovato")

    riepilogo_iva = pdf_generator.calcola_riepilogo_iva_per_aliquota(preventivo["voci"])
    subtotale = preventivo["subtotale"]
    totale_iva = preventivo["totale_iva"]
    totale = preventivo["totale"]

    info_sconto = None
    sconto_tipo_salvato = preventivo.get("sconto_tipo")
    sconto_valore_salvato = preventivo.get("sconto_valore")
    if sconto_tipo_salvato and sconto_valore_salvato:
        subtotale, riepilogo_iva, totale_iva, totale, importo_sconto = applica_sconto(
            subtotale, riepilogo_iva, totale_iva, totale, sconto_tipo_salvato, sconto_valore_salvato
        )
        if importo_sconto > 0:
            descrizione = (
                f"Sconto {sconto_valore_salvato:g}%" if sconto_tipo_salvato == "percentuale" else "Sconto"
            )
            info_sconto = {
                "descrizione": descrizione,
                "importo": importo_sconto,
                "subtotale_originale": preventivo["subtotale"],
            }

    pdf_bytes = pdf_generator.genera_pdf_documento(
        tipo_documento="FATTURA",
        numero_documento=preventivo["numero_fattura"],
        data_documento=date.fromisoformat(preventivo["data_fattura"]),
        mittente={
            "nome": preventivo["mittente_nome"],
            "piva": preventivo["mittente_piva"],
            "indirizzo": preventivo["mittente_indirizzo"],
            "contatti": preventivo["mittente_contatti"],
            "iban": preventivo["mittente_iban"],
        },
        cliente={
            "nome": preventivo["cliente_nome"],
            "indirizzo": preventivo["cliente_indirizzo"],
            "piva": preventivo["cliente_piva"],
            "email": preventivo["cliente_email"],
        },
        voci=preventivo["voci"],
        subtotale=subtotale,
        riepilogo_iva_per_aliquota=riepilogo_iva,
        totale_iva=totale_iva,
        totale=totale,
        note=preventivo["note"] or "",
        riferimento_preventivo=preventivo["numero"],
        info_sconto=info_sconto,
    )
    return Response(
        content=bytes(pdf_bytes),
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="fattura_{preventivo["numero_fattura"]}.pdf"'},
    )


@router.post("/preventivi/{preventivo_id}/fattura/annulla")
def annulla_fattura(preventivo_id: int):
    database.annulla_fattura(preventivo_id)
    return RedirectResponse(url="/storico", status_code=303)
