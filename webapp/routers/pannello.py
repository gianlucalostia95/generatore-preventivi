"""
Frammenti HTML (senza il layout di base) usati dal pannello "Gestione
profilo" che scorre da destra: la stessa logica/contesto delle pagine
standalone /profilo e /storico, riusata via le funzioni contesto_profilo()
e contesto_storico() definite in quei router, per non duplicarla.
"""
from fastapi import APIRouter, Request

from webapp.routers.profilo import contesto_profilo
from webapp.routers.storico import contesto_storico
from webapp.templating import templates

router = APIRouter(prefix="/pannello")


@router.get("/profilo")
def frammento_profilo(request: Request, salvato: bool = False):
    return templates.TemplateResponse(request, "_profilo_fragment.html", contesto_profilo(salvato))


@router.get("/storico")
def frammento_storico(
    request: Request,
    cliente: str = "",
    numero: str = "",
    data_da: str = "",
    data_a: str = "",
    stato: str = "Tutti",
    importo_min: str = "",
    importo_max: str = "",
):
    contesto = contesto_storico(cliente, numero, data_da, data_a, stato, importo_min, importo_max)
    return templates.TemplateResponse(request, "_storico_fragment.html", contesto)
