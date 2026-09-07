"""
Pagina "Storico Preventivi"
=============================

Mostra l'elenco di tutti i preventivi generati in passato, con filtri di
ricerca (cliente, numero, intervallo di date, importo, stato di
fatturazione) e azioni rapide: duplicare un preventivo, modificarlo,
generare la fattura in PDF corrispondente, annullarne la fatturazione,
eliminarlo o esportare l'elenco in CSV.
"""

import csv
import io
from datetime import date

import streamlit as st

import database
import pdf_generator


st.set_page_config(page_title="Storico Preventivi", page_icon="📚", layout="wide")
database.inizializza_database()

st.title("📚 Storico Preventivi")
st.caption("Consulta, cerca e gestisci tutti i preventivi generati in precedenza.")


# ---------------------------------------------------------------------------
# FILTRI DI RICERCA
# ---------------------------------------------------------------------------
# Le etichette mostrate all'utente sono piu' chiare dei valori "preventivo"/
# "fatturato" salvati internamente nel campo "stato" del database.
OPZIONI_STATO = {
    "Tutti": "Tutti",
    "Da fatturare": "preventivo",
    "Fatturati": "fatturato",
}

with st.expander("🔎 Filtri di ricerca", expanded=True):
    col1, col2, col3 = st.columns(3)
    with col1:
        filtro_cliente = st.text_input("Cliente")
        filtro_numero = st.text_input("Numero preventivo")
    with col2:
        filtro_data_da = st.date_input("Data da", value=None)
        filtro_data_a = st.date_input("Data a", value=None)
    with col3:
        filtro_stato_etichetta = st.selectbox("Stato fatturazione", list(OPZIONI_STATO.keys()))
        filtro_importo_min = st.number_input("Importo minimo (EUR)", min_value=0.0, value=0.0, step=10.0)
        filtro_importo_max = st.number_input(
            "Importo massimo (EUR)", min_value=0.0, value=0.0, step=10.0,
            help="Lascia a 0 per non impostare un limite massimo",
        )

preventivi = database.elenco_preventivi(
    {
        "cliente": filtro_cliente,
        "numero": filtro_numero,
        "data_da": filtro_data_da,
        "data_a": filtro_data_a,
        "stato": OPZIONI_STATO[filtro_stato_etichetta],
        "importo_min": filtro_importo_min or None,
        "importo_max": filtro_importo_max or None,
    }
)

st.divider()
st.subheader(f"Risultati: {len(preventivi)} preventivi")

if not preventivi:
    st.info("Nessun preventivo trovato con i filtri selezionati.")
else:
    # --- Esportazione CSV, utile per la contabilita' -------------------
    # Usa il modulo "csv" della libreria standard (invece di pandas) cosi'
    # da non dover importare numpy/pandas solo per questa esportazione: le
    # loro librerie compilate possono essere bloccate da software di
    # sicurezza come Smart App Control su Windows.
    buffer_csv = io.StringIO()
    intestazioni = [
        "Numero", "Data", "Cliente", "Subtotale", "IVA", "Totale",
        "Stato", "Numero Fattura", "Data Fattura",
    ]
    scrittore_csv = csv.DictWriter(buffer_csv, fieldnames=intestazioni)
    scrittore_csv.writeheader()
    for p in preventivi:
        scrittore_csv.writerow(
            {
                "Numero": p["numero"],
                "Data": p["data"],
                "Cliente": p["cliente_nome"],
                "Subtotale": p["subtotale"],
                "IVA": p["totale_iva"],
                "Totale": p["totale"],
                "Stato": "Fatturato" if p["stato"] == "fatturato" else "Da fatturare",
                "Numero Fattura": p["numero_fattura"] or "",
                "Data Fattura": p["data_fattura"] or "",
            }
        )
    st.download_button(
        "⬇️ Esporta elenco in CSV",
        data=buffer_csv.getvalue().encode("utf-8-sig"),
        file_name="storico_preventivi.csv",
        mime="text/csv",
    )

    st.divider()

    # --- Elenco preventivi, con azioni rapide su ciascuno ----------------
    for p in preventivi:
        indicatore_stato = "🧾 Fatturato" if p["stato"] == "fatturato" else "Da fatturare"
        etichetta = f"{p['numero']} — {p['cliente_nome']} — {p['totale']:.2f} EUR — {indicatore_stato}"

        with st.expander(etichetta):
            st.write(f"**Data:** {p['data']}")
            st.write(
                f"**Subtotale:** {p['subtotale']:.2f} EUR — "
                f"**IVA:** {p['totale_iva']:.2f} EUR — "
                f"**Totale:** {p['totale']:.2f} EUR"
            )
            if p["note"]:
                st.write(f"**Note:** {p['note']}")
            if p["stato"] == "fatturato":
                st.write(f"**Fattura:** {p['numero_fattura']} del {p['data_fattura']}")

            # --- Azioni sul preventivo -----------------------------------
            col_dup, col_mod, col_elim = st.columns(3)

            if col_dup.button("📄 Duplica", key=f"duplica_{p['id']}"):
                # Salviamo l'azione richiesta e torniamo alla pagina principale,
                # dove il modulo verra' precompilato con questi dati.
                st.session_state["azione_preventivo"] = {"modalita": "duplica", "id": p["id"]}
                st.switch_page("Generazione_Preventivo.py")

            if col_mod.button("✏️ Modifica", key=f"modifica_{p['id']}"):
                st.session_state["azione_preventivo"] = {"modalita": "modifica", "id": p["id"]}
                st.switch_page("Generazione_Preventivo.py")

            if col_elim.button("🗑️ Elimina", key=f"elimina_{p['id']}"):
                database.elimina_preventivo(p["id"])
                st.session_state.pop(f"pdf_fattura_{p['id']}", None)
                st.success("Preventivo eliminato.")
                st.rerun()

            st.divider()

            # --- Fatturazione: genera la fattura in PDF a partire da questo
            # preventivo, oppure annulla una fatturazione gia' fatta ---------
            st.subheader("🧾 Fatturazione")
            st.caption(
                "Genera un documento PDF di fattura a partire da questo preventivo, "
                "con una propria numerazione progressiva. Questo PDF e' pensato per "
                "un uso pratico (es. da inviare o archiviare) e **non sostituisce** "
                "l'obbligo di fatturazione elettronica (SdI) quando previsto dalla "
                "normativa italiana."
            )

            col_fattura1, col_fattura2 = st.columns(2)

            with col_fattura1:
                etichetta_pulsante_fattura = (
                    "🔄 Rigenera PDF Fattura" if p["stato"] == "fatturato" else "🧾 Genera Fattura PDF"
                )
                if st.button(etichetta_pulsante_fattura, key=f"genera_fattura_{p['id']}"):
                    preventivo_completo = database.genera_fattura_da_preventivo(p["id"])
                    riepilogo_iva = pdf_generator.calcola_riepilogo_iva_per_aliquota(preventivo_completo["voci"])

                    pdf_bytes = pdf_generator.genera_pdf_documento(
                        tipo_documento="FATTURA",
                        numero_documento=preventivo_completo["numero_fattura"],
                        data_documento=date.fromisoformat(preventivo_completo["data_fattura"]),
                        mittente={
                            "nome": preventivo_completo["mittente_nome"],
                            "piva": preventivo_completo["mittente_piva"],
                            "indirizzo": preventivo_completo["mittente_indirizzo"],
                            "contatti": preventivo_completo["mittente_contatti"],
                            "iban": preventivo_completo["mittente_iban"],
                        },
                        cliente={
                            "nome": preventivo_completo["cliente_nome"],
                            "indirizzo": preventivo_completo["cliente_indirizzo"],
                            "piva": preventivo_completo["cliente_piva"],
                            "email": preventivo_completo["cliente_email"],
                        },
                        voci=preventivo_completo["voci"],
                        subtotale=preventivo_completo["subtotale"],
                        riepilogo_iva_per_aliquota=riepilogo_iva,
                        totale_iva=preventivo_completo["totale_iva"],
                        totale=preventivo_completo["totale"],
                        note=preventivo_completo["note"],
                        riferimento_preventivo=preventivo_completo["numero"],
                    )
                    st.session_state[f"pdf_fattura_{p['id']}"] = pdf_bytes
                    st.session_state[f"numero_fattura_{p['id']}"] = preventivo_completo["numero_fattura"]
                    st.rerun()

            with col_fattura2:
                if p["stato"] == "fatturato":
                    if st.button("↩️ Annulla fatturazione", key=f"annulla_fattura_{p['id']}"):
                        database.annulla_fattura(p["id"])
                        st.session_state.pop(f"pdf_fattura_{p['id']}", None)
                        st.session_state.pop(f"numero_fattura_{p['id']}", None)
                        st.rerun()

            chiave_pdf_fattura = f"pdf_fattura_{p['id']}"
            if chiave_pdf_fattura in st.session_state:
                numero_fattura_generata = st.session_state[f"numero_fattura_{p['id']}"]
                st.download_button(
                    "⬇️ Scarica Fattura PDF",
                    data=st.session_state[chiave_pdf_fattura],
                    file_name=f"fattura_{numero_fattura_generata}.pdf",
                    mime="application/pdf",
                    key=f"scarica_fattura_{p['id']}",
                )
