"""Istanza condivisa di Jinja2Templates, usata da tutti i router."""
import json
from pathlib import Path

from fastapi.templating import Jinja2Templates
from markupsafe import Markup

templates = Jinja2Templates(directory=str(Path(__file__).parent / "templates"))


def _tojson(valore) -> Markup:
    """
    Filtro "tojson" per i template: Jinja2 "puro" (quello usato da
    Starlette/FastAPI) non lo include di default, a differenza di Flask.
    Rimpiazza anche "</" con "<\\/" per evitare che un valore contenente
    "</script>" (es. un nome cliente) chiuda il tag <script> prima del
    previsto.
    """
    return Markup(json.dumps(valore).replace("</", "<\\/"))


templates.env.filters["tojson"] = _tojson
