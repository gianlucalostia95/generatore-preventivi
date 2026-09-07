"""
Pagina "Anagrafica Clienti"
=============================

Permette di consultare, cercare, aggiungere, modificare ed eliminare i
clienti salvati nel database, cosi' da non doverli reinserire ogni volta
che si crea un nuovo preventivo nella pagina principale.
"""

import streamlit as st

import database


st.set_page_config(page_title="Anagrafica Clienti", page_icon="👥", layout="centered")
database.inizializza_database()

st.title("👥 Anagrafica Clienti")
st.caption("Qui puoi consultare, aggiungere, modificare o eliminare i clienti salvati.")


# ---------------------------------------------------------------------------
# RICERCA CLIENTI
# ---------------------------------------------------------------------------
ricerca = st.text_input("🔎 Cerca cliente per nome", placeholder="Es. Bianchi")
clienti = database.elenco_clienti(ricerca)

st.divider()


# ---------------------------------------------------------------------------
# ELENCO CLIENTI ESISTENTI, CON MODIFICA ED ELIMINAZIONE
# ---------------------------------------------------------------------------
st.subheader(f"Clienti salvati ({len(clienti)})")

if not clienti:
    st.info("Nessun cliente trovato. Aggiungine uno nel modulo qui sotto.")

for cliente in clienti:
    with st.expander(cliente["nome"]):
        with st.form(f"modifica_cliente_{cliente['id']}"):
            nome = st.text_input("Nome / Ragione Sociale", value=cliente["nome"] or "")
            indirizzo = st.text_input("Indirizzo", value=cliente["indirizzo"] or "")
            piva = st.text_input("P.IVA / Codice Fiscale", value=cliente["piva"] or "")
            email = st.text_input("Email", value=cliente["email"] or "")

            col_salva, col_elimina = st.columns(2)
            salva_premuto = col_salva.form_submit_button("💾 Salva modifiche", type="primary")
            elimina_premuto = col_elimina.form_submit_button("🗑️ Elimina cliente")

        if salva_premuto:
            if nome.strip():
                database.salva_cliente(
                    {"nome": nome, "indirizzo": indirizzo, "piva": piva, "email": email},
                    cliente_id=cliente["id"],
                )
                st.success("Cliente aggiornato.")
                st.rerun()
            else:
                st.warning("Il nome del cliente non puo' essere vuoto.")

        if elimina_premuto:
            database.elimina_cliente(cliente["id"])
            st.success("Cliente eliminato.")
            st.rerun()

st.divider()


# ---------------------------------------------------------------------------
# AGGIUNTA DI UN NUOVO CLIENTE
# ---------------------------------------------------------------------------
st.subheader("Aggiungi un nuovo cliente")

with st.form("nuovo_cliente", clear_on_submit=True):
    nome_nuovo = st.text_input("Nome / Ragione Sociale")
    indirizzo_nuovo = st.text_input("Indirizzo")
    piva_nuovo = st.text_input("P.IVA / Codice Fiscale")
    email_nuovo = st.text_input("Email")
    aggiungi_premuto = st.form_submit_button("➕ Aggiungi cliente", type="primary")

if aggiungi_premuto:
    if nome_nuovo.strip():
        database.salva_cliente(
            {"nome": nome_nuovo, "indirizzo": indirizzo_nuovo, "piva": piva_nuovo, "email": email_nuovo}
        )
        st.success(f"Cliente '{nome_nuovo}' aggiunto con successo.")
        st.rerun()
    else:
        st.warning("Inserisci almeno il nome del cliente.")
