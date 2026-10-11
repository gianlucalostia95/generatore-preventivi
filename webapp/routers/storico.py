"""Pagina "Storico Preventivi": filtri, elenco, export CSV ed esito fatturazione."""
import csv
import io
from datetime import date

from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse

import database
from webapp.esportazione_xlsx import crea_foglio_xlsx
from webapp.templating import templates

router = APIRouter()


def _costruisci_filtri(cliente, numero, data_da, data_a, stato, importo_min, importo_max) -> dict:
    filtri: dict = {"cliente": cliente or None, "numero": numero or None, "stato": stato or "Tutti"}
    if data_da:
        filtri["data_da"] = date.fromisoformat(data_da)
    if data_a:
        filtri["data_a"] = date.fromisoformat(data_a)
    if importo_min:
        filtri["importo_min"] = float(importo_min)
    if importo_max:
        filtri["importo_max"] = float(importo_max)
    return filtri


def contesto_storico(cliente, numero, data_da, data_a, stato, importo_min, importo_max) -> dict:
    filtri = _costruisci_filtri(cliente, numero, data_da, data_a, stato, importo_min, importo_max)
    preventivi = database.elenco_preventivi(filtri)
    return {
        "preventivi": preventivi,
        "filtri": {
            "cliente": cliente,
            "numero": numero,
            "data_da": data_da,
            "data_a": data_a,
            "stato": stato,
            "importo_min": importo_min,
            "importo_max": importo_max,
        },
    }


@router.get("/storico")
def mostra_storico(
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
    return templates.TemplateResponse(request, "storico.html", contesto)


@router.get("/storico/export.csv")
def esporta_csv(
    cliente: str = "",
    numero: str = "",
    data_da: str = "",
    data_a: str = "",
    stato: str = "Tutti",
    importo_min: str = "",
    importo_max: str = "",
):
    filtri = _costruisci_filtri(cliente, numero, data_da, data_a, stato, importo_min, importo_max)
    preventivi = database.elenco_preventivi(filtri)

    buffer = io.StringIO()
    buffer.write("﻿")  # BOM: stessa scelta della versione Streamlit (utf-8-sig) per compatibilita' Excel
    scrittore = csv.writer(buffer)
    scrittore.writerow(
        ["Numero", "Data", "Cliente", "Subtotale", "IVA", "Totale", "Stato", "Numero Fattura", "Data Fattura"]
    )
    for preventivo in preventivi:
        scrittore.writerow(
            [
                preventivo["numero"],
                preventivo["data"],
                preventivo["cliente_nome"],
                f"{preventivo['subtotale']:.2f}",
                f"{preventivo['totale_iva']:.2f}",
                f"{preventivo['totale']:.2f}",
                preventivo["stato"],
                preventivo.get("numero_fattura") or "",
                preventivo.get("data_fattura") or "",
            ]
        )

    return StreamingResponse(
        iter([buffer.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=storico_preventivi.csv"},
    )


@router.get("/storico/export.xlsx")
def esporta_xlsx(
    cliente: str = "",
    numero: str = "",
    data_da: str = "",
    data_a: str = "",
    stato: str = "Tutti",
    importo_min: str = "",
    importo_max: str = "",
):
    filtri = _costruisci_filtri(cliente, numero, data_da, data_a, stato, importo_min, importo_max)
    preventivi = database.elenco_preventivi(filtri)

    righe = []
    for preventivo in preventivi:
        righe.append(
            [
                preventivo["numero"],
                date.fromisoformat(preventivo["data"]),
                preventivo["cliente_nome"],
                preventivo["subtotale"],
                preventivo["totale_iva"],
                preventivo["totale"],
                "Fatturato" if preventivo["stato"] == "fatturato" else "Da fatturare",
                preventivo.get("numero_fattura") or "",
                date.fromisoformat(preventivo["data_fattura"]) if preventivo.get("data_fattura") else "",
            ]
        )

    buffer = crea_foglio_xlsx(
        titolo_foglio="Storico",
        intestazioni=["Numero", "Data", "Cliente", "Subtotale", "IVA", "Totale", "Stato", "Numero Fattura", "Data Fattura"],
        righe=righe,
        larghezze=[14, 12, 26, 12, 12, 12, 14, 16, 14],
        formati_colonna={2: "DD/MM/YYYY", 4: "#,##0.00", 5: "#,##0.00", 6: "#,##0.00", 9: "DD/MM/YYYY"},
    )
    return StreamingResponse(
        buffer,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": "attachment; filename=storico_preventivi.xlsx"},
    )
