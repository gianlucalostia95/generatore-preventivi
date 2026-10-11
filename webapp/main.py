"""
Sito web locale del Generatore di Preventivi — app FastAPI.

Va avviato dalla cartella del progetto (es. `avvia_sito.bat`, che fa `cd`
nella cartella prima di lanciare uvicorn) cosi' che `database.py` e
`pdf_generator.py`, che vivono nella root del progetto, siano importabili.
Il percorso della root viene comunque aggiunto esplicitamente a sys.path
come rete di sicurezza, nel caso l'app venga avviata da un'altra cartella.
"""
import sys
from pathlib import Path

RADICE_PROGETTO = Path(__file__).resolve().parent.parent
if str(RADICE_PROGETTO) not in sys.path:
    sys.path.insert(0, str(RADICE_PROGETTO))

from fastapi import FastAPI, Request  # noqa: E402
from fastapi.staticfiles import StaticFiles  # noqa: E402

import database  # noqa: E402

from webapp.calcoli import importo_netto_fattura  # noqa: E402
from webapp.routers import clienti, pannello, preventivi, profilo, storico  # noqa: E402
from webapp.templating import templates  # noqa: E402

app = FastAPI(title="Generatore di Preventivi")


@app.on_event("startup")
def avvio() -> None:
    database.inizializza_database()


app.mount(
    "/static",
    StaticFiles(directory=str(Path(__file__).parent / "static")),
    name="static",
)

app.include_router(preventivi.router)
app.include_router(clienti.router)
app.include_router(profilo.router)
app.include_router(storico.router)
app.include_router(pannello.router)


@app.get("/")
def home(request: Request):
    tutti = database.elenco_preventivi({})
    numero_preventivi = len(tutti)
    somma_preventivi = round(sum(p["totale"] for p in tutti), 2)
    fatture = [p for p in tutti if p["stato"] == "fatturato"]
    numero_fatture = len(fatture)
    somma_fatture = round(sum(importo_netto_fattura(p) for p in fatture), 2)
    tasso_conversione = round((numero_fatture / numero_preventivi) * 100, 1) if numero_preventivi else 0.0

    return templates.TemplateResponse(
        request,
        "home.html",
        {
            "numero_preventivi": numero_preventivi,
            "somma_preventivi": somma_preventivi,
            "numero_fatture": numero_fatture,
            "somma_fatture": somma_fatture,
            "tasso_conversione": tasso_conversione,
        },
    )
