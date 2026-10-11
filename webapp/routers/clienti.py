"""Pagina "Anagrafica Clienti": ricerca, aggiunta, modifica ed eliminazione."""
from fastapi import APIRouter, Form, Request
from fastapi.responses import RedirectResponse, StreamingResponse

import database
from webapp.esportazione_xlsx import crea_foglio_xlsx
from webapp.templating import templates

router = APIRouter()


@router.get("/clienti")
def mostra_clienti(request: Request, ricerca: str = ""):
    clienti = database.elenco_clienti(ricerca)
    return templates.TemplateResponse(
        request, "clienti.html", {"clienti": clienti, "ricerca": ricerca}
    )


@router.get("/clienti/export.xlsx")
def esporta_clienti_xlsx(ricerca: str = ""):
    clienti = database.elenco_clienti(ricerca)
    righe = [[c["nome"], c["indirizzo"] or "", c["piva"] or "", c["email"] or ""] for c in clienti]
    buffer = crea_foglio_xlsx(
        titolo_foglio="Clienti",
        intestazioni=["Nome / Ragione Sociale", "Indirizzo", "P.IVA / Codice Fiscale", "Email"],
        righe=righe,
        larghezze=[30, 34, 20, 28],
    )
    return StreamingResponse(
        buffer,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": "attachment; filename=anagrafica_clienti.xlsx"},
    )


@router.post("/clienti")
def crea_cliente(
    nome: str = Form(...),
    indirizzo: str = Form(""),
    piva: str = Form(""),
    email: str = Form(""),
):
    nome = nome.strip()
    if nome:
        database.salva_cliente(
            {"nome": nome, "indirizzo": indirizzo.strip(), "piva": piva.strip(), "email": email.strip()}
        )
    return RedirectResponse(url="/clienti", status_code=303)


@router.post("/clienti/{cliente_id}")
def aggiorna_cliente(
    cliente_id: int,
    nome: str = Form(...),
    indirizzo: str = Form(""),
    piva: str = Form(""),
    email: str = Form(""),
):
    nome = nome.strip()
    if nome:
        database.salva_cliente(
            {"nome": nome, "indirizzo": indirizzo.strip(), "piva": piva.strip(), "email": email.strip()},
            cliente_id=cliente_id,
        )
    return RedirectResponse(url="/clienti", status_code=303)


@router.post("/clienti/{cliente_id}/elimina")
def elimina_cliente(cliente_id: int):
    database.elimina_cliente(cliente_id)
    return RedirectResponse(url="/clienti", status_code=303)
