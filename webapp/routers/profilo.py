"""Pagina "Profilo Mittente": i dati della propria azienda, salvati una sola volta."""
from fastapi import APIRouter, Form, Request
from fastapi.responses import RedirectResponse

import database
from webapp.templating import templates

router = APIRouter()


def contesto_profilo(salvato: bool) -> dict:
    return {"profilo": database.ottieni_profilo_mittente(), "salvato": salvato}


@router.get("/profilo")
def mostra_profilo(request: Request, salvato: bool = False):
    return templates.TemplateResponse(request, "profilo.html", contesto_profilo(salvato))


@router.post("/profilo")
def salva_profilo(
    nome: str = Form(""),
    piva: str = Form(""),
    indirizzo: str = Form(""),
    contatti: str = Form(""),
    iban: str = Form(""),
):
    database.salva_profilo_mittente(
        {
            "nome": nome.strip(),
            "piva": piva.strip(),
            "indirizzo": indirizzo.strip(),
            "contatti": contatti.strip(),
            "iban": iban.strip(),
        }
    )
    return RedirectResponse(url="/profilo?salvato=1", status_code=303)
