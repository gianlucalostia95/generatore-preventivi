"""
Pagina "Profilo Mittente"
===========================

Permette di salvare una volta sola i propri dati aziendali (nome, P.IVA,
indirizzo, contatti, IBAN), cosi' da non doverli reinserire ogni volta che
si crea un nuovo preventivo nella pagina principale: verranno proposti
automaticamente come valori precompilati.
"""

import streamlit as st

import database


st.set_page_config(page_title="Profilo Mittente", page_icon="🏢", layout="centered")
database.inizializza_database()

st.title("🏢 Profilo Mittente")
st.caption(
    "Compila i tuoi dati aziendali una sola volta: verranno proposti "
    "automaticamente ogni volta che crei un nuovo preventivo."
)

profilo_attuale = database.ottieni_profilo_mittente()

with st.form("profilo_mittente"):
    nome = st.text_input("Nome / Ragione Sociale", value=profilo_attuale.get("nome", ""))
    piva = st.text_input("P.IVA / Codice Fiscale", value=profilo_attuale.get("piva", ""))
    indirizzo = st.text_input("Indirizzo", value=profilo_attuale.get("indirizzo", ""))
    contatti = st.text_input("Contatti (telefono, email)", value=profilo_attuale.get("contatti", ""))
    iban = st.text_input("IBAN per il bonifico", value=profilo_attuale.get("iban", ""))

    salva_premuto = st.form_submit_button("💾 Salva profilo", type="primary")

if salva_premuto:
    database.salva_profilo_mittente(
        {"nome": nome, "piva": piva, "indirizzo": indirizzo, "contatti": contatti, "iban": iban}
    )
    st.success("Profilo salvato: i tuoi dati verranno proposti automaticamente nei prossimi preventivi.")
