"""
Generatore di Preventivi in PDF — Pagina "Generazione Preventivo"
====================================================================

Applicazione web per creare preventivi professionali in formato PDF.
Realizzata con Streamlit (interfaccia utente), FPDF2 (generazione del PDF,
tramite il modulo condiviso `pdf_generator.py`) e un database SQLite
locale (modulo `database.py`) per salvare il profilo del mittente,
l'anagrafica clienti e lo storico dei preventivi generati.

Questa e' la pagina principale dell'app (il nome di questo file determina
l'etichetta mostrata nel menu laterale di Streamlit): da qui si crea un
nuovo preventivo, oppure si modifica/duplica un preventivo gia' salvato
(azione avviata dalla pagina "Storico Preventivi"). Le altre pagine sono
raggiungibili dal menu laterale.
"""

from datetime import date

import streamlit as st

import database
import pdf_generator


# ---------------------------------------------------------------------------
# CONFIGURAZIONE GENERALE DELLA PAGINA
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="Generazione Preventivo",
    page_icon="🧾",
    layout="centered",
)

# Crea le tabelle del database al primo avvio (non fa nulla se esistono gia').
database.inizializza_database()

st.title("🧾 Generatore di Preventivi in PDF")
st.caption(
    "Compila i campi qui sotto: il preventivo verra' generato in formato "
    "PDF pronto da scaricare e inviare al cliente, e salvato automaticamente "
    "nello Storico Preventivi."
)

# Pulsante per svuotare il modulo e iniziare un preventivo nuovo di zecca.
# Senza questo pulsante, dopo aver generato un preventivo l'app continuerebbe
# ad aggiornare quello stesso documento invece di crearne uno nuovo.
if st.button("🆕 Inizia un nuovo preventivo vuoto"):
    for chiave in (
        "cliente_selezionato", "nuovo_cliente_nome", "nuovo_cliente_indirizzo",
        "nuovo_cliente_piva", "nuovo_cliente_email", "numero_preventivo",
        "data_preventivo", "validita_giorni", "note", "righe_voci",
        "preventivo_id_in_modifica",
    ):
        st.session_state.pop(chiave, None)
    for chiave_widget in list(st.session_state.keys()):
        if chiave_widget.startswith(("voce_desc_", "voce_qta_", "voce_prezzo_", "voce_iva_")):
            st.session_state.pop(chiave_widget, None)
    st.rerun()


# ---------------------------------------------------------------------------
# CARICAMENTO DI UN PREVENTIVO ESISTENTE (MODIFICA O DUPLICAZIONE)
# ---------------------------------------------------------------------------
# Quando dalla pagina "Storico Preventivi" si preme "Modifica" o "Duplica",
# viene salvato in session_state un riferimento all'azione da compiere.
# Qui lo leggiamo (una sola volta, per questo motivo usiamo `.pop`) e
# precompiliamo i campi del modulo con i dati del preventivo scelto.
if "azione_preventivo" in st.session_state:
    azione = st.session_state.pop("azione_preventivo")
    preventivo = database.ottieni_preventivo_completo(azione["id"])

    if preventivo:
        st.session_state["mittente_nome"] = preventivo["mittente_nome"] or ""
        st.session_state["mittente_piva"] = preventivo["mittente_piva"] or ""
        st.session_state["mittente_indirizzo"] = preventivo["mittente_indirizzo"] or ""
        st.session_state["mittente_contatti"] = preventivo["mittente_contatti"] or ""
        st.session_state["mittente_iban"] = preventivo["mittente_iban"] or ""

        # Se il cliente collegato esiste ancora in anagrafica, selezioniamolo;
        # altrimenti mostriamo comunque i suoi dati come "nuovo cliente".
        opzione_cliente_corrispondente = None
        if preventivo["cliente_id"] is not None:
            cliente_esistente = database.ottieni_cliente(preventivo["cliente_id"])
            if cliente_esistente:
                opzione_cliente_corrispondente = f"{cliente_esistente['nome']} (id {cliente_esistente['id']})"

        st.session_state["cliente_selezionato"] = opzione_cliente_corrispondente or "+ Nuovo cliente"
        st.session_state["nuovo_cliente_nome"] = preventivo["cliente_nome"] or ""
        st.session_state["nuovo_cliente_indirizzo"] = preventivo["cliente_indirizzo"] or ""
        st.session_state["nuovo_cliente_piva"] = preventivo["cliente_piva"] or ""
        st.session_state["nuovo_cliente_email"] = preventivo["cliente_email"] or ""

        st.session_state["numero_preventivo"] = (
            preventivo["numero"] if azione["modalita"] == "modifica"
            else database.prossimo_numero_preventivo()
        )
        st.session_state["data_preventivo"] = date.today()
        st.session_state["validita_giorni"] = preventivo["validita_giorni"] or 0
        st.session_state["note"] = preventivo["note"] or ""

        for chiave_widget in list(st.session_state.keys()):
            if chiave_widget.startswith(("voce_desc_", "voce_qta_", "voce_prezzo_", "voce_iva_")):
                st.session_state.pop(chiave_widget, None)
        st.session_state["righe_voci"] = [
            {
                "descrizione": voce["descrizione"],
                "quantita": voce["quantita"],
                "prezzo": voce["prezzo_unitario"],
                "iva": voce["aliquota_iva"],
            }
            for voce in preventivo["voci"]
        ] or [{"descrizione": "", "quantita": 1.0, "prezzo": 0.0, "iva": 22.0}]

        st.session_state["preventivo_id_in_modifica"] = (
            preventivo["id"] if azione["modalita"] == "modifica" else None
        )

        if azione["modalita"] == "modifica":
            st.info(f"Stai modificando il preventivo **{preventivo['numero']}**.")
        else:
            st.info("Preventivo duplicato: controlla i dati e genera il nuovo documento.")


# ---------------------------------------------------------------------------
# SEZIONE A: DATI DEL MITTENTE E DEL CLIENTE
# ---------------------------------------------------------------------------
st.header("1. Dati del Mittente e del Cliente")

profilo_mittente_salvato = database.ottieni_profilo_mittente()

col_mittente, col_cliente = st.columns(2)

with col_mittente:
    st.subheader("Chi emette il preventivo")
    mittente_nome = st.text_input(
        "Nome / Ragione Sociale", value=profilo_mittente_salvato.get("nome", ""), key="mittente_nome"
    )
    mittente_piva = st.text_input(
        "P.IVA / Codice Fiscale", value=profilo_mittente_salvato.get("piva", ""), key="mittente_piva"
    )
    mittente_indirizzo = st.text_input(
        "Indirizzo", value=profilo_mittente_salvato.get("indirizzo", ""), key="mittente_indirizzo"
    )
    mittente_contatti = st.text_input(
        "Contatti (telefono, email)", value=profilo_mittente_salvato.get("contatti", ""), key="mittente_contatti"
    )
    mittente_iban = st.text_input(
        "IBAN per il bonifico", value=profilo_mittente_salvato.get("iban", ""), key="mittente_iban"
    )
    st.caption(
        "Questi dati sono precompilati dal tuo Profilo Mittente. "
        "Per modificarli in modo permanente, vai alla pagina 'Profilo Mittente' dal menu laterale."
    )

with col_cliente:
    st.subheader("Cliente destinatario")

    clienti_salvati = database.elenco_clienti()
    mappa_opzione_cliente = {f"{c['nome']} (id {c['id']})": c for c in clienti_salvati}
    opzioni_cliente = ["+ Nuovo cliente"] + list(mappa_opzione_cliente.keys())

    scelta_cliente = st.selectbox(
        "Seleziona un cliente salvato oppure inserisci un nuovo cliente",
        opzioni_cliente,
        key="cliente_selezionato",
    )

    if scelta_cliente == "+ Nuovo cliente":
        cliente_nome = st.text_input("Nome / Ragione Sociale", key="nuovo_cliente_nome")
        cliente_indirizzo = st.text_input("Indirizzo", key="nuovo_cliente_indirizzo")
        cliente_piva = st.text_input("P.IVA / Codice Fiscale", key="nuovo_cliente_piva")
        cliente_email = st.text_input("Email", key="nuovo_cliente_email")
        cliente_id_selezionato = None
        salva_nuovo_cliente_in_anagrafica = st.checkbox(
            "Salva questo cliente in anagrafica per riutilizzarlo in futuro", value=True
        )
    else:
        cliente_dati = mappa_opzione_cliente[scelta_cliente]
        cliente_nome = cliente_dati["nome"]
        cliente_indirizzo = cliente_dati["indirizzo"] or ""
        cliente_piva = cliente_dati["piva"] or ""
        cliente_email = cliente_dati["email"] or ""
        cliente_id_selezionato = cliente_dati["id"]
        salva_nuovo_cliente_in_anagrafica = False

        st.text_input("Indirizzo", value=cliente_indirizzo, disabled=True)
        st.text_input("P.IVA / Codice Fiscale", value=cliente_piva, disabled=True)
        st.text_input("Email", value=cliente_email, disabled=True)
        st.caption("Per modificare questi dati vai alla pagina 'Anagrafica Clienti' dal menu laterale.")

st.divider()

# Riferimenti del preventivo: numero identificativo, data e validita' dell'offerta.
col_rif1, col_rif2, col_rif3 = st.columns(3)
with col_rif1:
    numero_preventivo = st.text_input(
        "Numero preventivo", value=database.prossimo_numero_preventivo(), key="numero_preventivo"
    )
with col_rif2:
    data_preventivo = st.date_input("Data preventivo", value=date.today(), key="data_preventivo")
with col_rif3:
    validita_giorni = st.number_input(
        "Validita' offerta (giorni)", min_value=0, value=30, step=1, key="validita_giorni"
    )

st.divider()


# ---------------------------------------------------------------------------
# SEZIONE B: VOCI DI SPESA E CALCOLI (IVA impostabile per singola voce)
# ---------------------------------------------------------------------------
st.header("2. Voci di Spesa")
st.write(
    "Inserisci una riga per ogni prodotto o servizio, con la propria "
    "aliquota IVA. Usa i pulsanti della tabella (in basso a sinistra) per "
    "aggiungere o rimuovere righe: il totale si aggiorna automaticamente."
)

# Righe di spesa modificabili liberamente dall'utente, con la propria aliquota
# IVA. L'aliquota predefinita per le nuove righe e' il 22%, la piu' comune in
# Italia. Le righe sono gestite manualmente (invece di st.data_editor) perche'
# st.data_editor richiede la libreria "pyarrow", la cui DLL viene bloccata da
# Smart App Control su questo PC (vedi Code Integrity, evento 3077).
if "righe_voci" not in st.session_state:
    st.session_state.righe_voci = [{"descrizione": "", "quantita": 1.0, "prezzo": 0.0, "iva": 22.0}]

intestazione_voci = st.columns([5, 2, 2, 1.5, 1])
intestazione_voci[0].markdown("**Descrizione**")
intestazione_voci[1].markdown("**Quantita'**")
intestazione_voci[2].markdown("**Prezzo unitario (EUR)**")
intestazione_voci[3].markdown("**IVA %**")

indice_voce_da_rimuovere = None
for indice_voce, riga_voce in enumerate(st.session_state.righe_voci):
    col1, col2, col3, col4, col5 = st.columns([5, 2, 2, 1.5, 1])
    riga_voce["descrizione"] = col1.text_input(
        "Descrizione", value=riga_voce["descrizione"], key=f"voce_desc_{indice_voce}",
        label_visibility="collapsed",
    )
    riga_voce["quantita"] = col2.number_input(
        "Quantita'", value=float(riga_voce["quantita"]), min_value=0.0, step=1.0,
        key=f"voce_qta_{indice_voce}", label_visibility="collapsed",
    )
    riga_voce["prezzo"] = col3.number_input(
        "Prezzo unitario", value=float(riga_voce["prezzo"]), min_value=0.0, step=0.01, format="%.2f",
        key=f"voce_prezzo_{indice_voce}", label_visibility="collapsed",
    )
    riga_voce["iva"] = col4.number_input(
        "IVA (%)", value=float(riga_voce["iva"]), min_value=0.0, max_value=100.0, step=0.5, format="%.1f",
        key=f"voce_iva_{indice_voce}", label_visibility="collapsed",
    )
    if col5.button("🗑️", key=f"voce_del_{indice_voce}") and len(st.session_state.righe_voci) > 1:
        indice_voce_da_rimuovere = indice_voce

if indice_voce_da_rimuovere is not None:
    st.session_state.righe_voci.pop(indice_voce_da_rimuovere)
    st.rerun()

if st.button("➕ Aggiungi voce"):
    st.session_state.righe_voci.append({"descrizione": "", "quantita": 1.0, "prezzo": 0.0, "iva": 22.0})
    st.rerun()

note = st.text_area(
    "Note aggiuntive (facoltative)",
    placeholder="Es. condizioni di pagamento, tempi di consegna...",
    key="note",
)

st.divider()


# ---------------------------------------------------------------------------
# CALCOLI AUTOMATICI IN TEMPO REALE: SUBTOTALE, IVA PER ALIQUOTA, TOTALE
# ---------------------------------------------------------------------------
st.header("3. Riepilogo Preventivo")

# Consideriamo valide solo le righe con una descrizione e una quantita' > 0,
# in modo da ignorare automaticamente le righe vuote o incomplete.
voci_valide = []
for riga in st.session_state.righe_voci:
    descrizione = str(riga.get("descrizione") or "").strip()
    quantita = float(riga.get("quantita") or 0)

    # Arrotondiamo prezzo e aliquota alla stessa precisione mostrata nella
    # tabella (2 e 1 decimali): senza questo passaggio il calcolo potrebbe
    # usare decimali nascosti non visibili all'utente (es. si vede "20.00"
    # ma si e' digitato "19.999"), facendo tornare le somme "storte".
    prezzo_unitario = round(float(riga.get("prezzo") or 0), 2)
    aliquota_iva_riga = round(float(riga.get("iva") or 0), 1)

    if descrizione and quantita > 0:
        # Ogni riga viene arrotondata ai centesimi singolarmente, come si fa
        # normalmente in fattura, invece di accumulare decimali nascosti e
        # arrotondare soltanto il totale finale.
        totale_riga = round(quantita * prezzo_unitario, 2)
        voci_valide.append(
            {
                "descrizione": descrizione,
                "quantita": quantita,
                "prezzo_unitario": prezzo_unitario,
                "aliquota_iva": aliquota_iva_riga,
                "totale_riga": totale_riga,
            }
        )

subtotale = round(sum(voce["totale_riga"] for voce in voci_valide), 2)
riepilogo_iva_per_aliquota = pdf_generator.calcola_riepilogo_iva_per_aliquota(voci_valide)
totale_iva = round(sum(riepilogo_iva_per_aliquota.values()), 2)
totale = round(subtotale + totale_iva, 2)

col_a, col_b, col_c = st.columns(3)
col_a.metric("Subtotale (imponibile)", f"{subtotale:.2f} EUR")
col_b.metric("Totale IVA", f"{totale_iva:.2f} EUR")
col_c.metric("TOTALE PREVENTIVO", f"{totale:.2f} EUR")

if len(riepilogo_iva_per_aliquota) > 1:
    st.caption("Dettaglio IVA per aliquota:")
    for aliquota, importo in sorted(riepilogo_iva_per_aliquota.items()):
        st.write(f"- IVA {aliquota:g}%: {importo:.2f} EUR")

st.divider()


# ---------------------------------------------------------------------------
# SEZIONE 4: GENERAZIONE, SALVATAGGIO E DOWNLOAD DEL PDF
# ---------------------------------------------------------------------------
st.header("4. Genera, Salva e Scarica il Preventivo")

campi_obbligatori_mancanti = not mittente_nome or not cliente_nome or not voci_valide

if campi_obbligatori_mancanti:
    st.warning(
        "Per generare il PDF servono almeno: il Nome del Mittente, "
        "il Nome del Cliente e una voce di spesa completa "
        "(descrizione, quantita' e prezzo)."
    )

in_modifica = bool(st.session_state.get("preventivo_id_in_modifica"))
etichetta_pulsante = "💾 Salva modifiche e rigenera PDF" if in_modifica else "📄 Genera e Salva Preventivo PDF"

if st.button(etichetta_pulsante, type="primary", disabled=campi_obbligatori_mancanti):
    # Se e' stato inserito un nuovo cliente e si e' scelto di salvarlo,
    # lo registriamo in anagrafica prima di salvare il preventivo.
    cliente_id_da_usare = cliente_id_selezionato
    if scelta_cliente == "+ Nuovo cliente" and salva_nuovo_cliente_in_anagrafica and cliente_nome:
        cliente_id_da_usare = database.salva_cliente(
            {"nome": cliente_nome, "indirizzo": cliente_indirizzo, "piva": cliente_piva, "email": cliente_email}
        )

    dati_preventivo = {
        "numero": numero_preventivo,
        "data": data_preventivo.isoformat(),
        "validita_giorni": validita_giorni,
        "note": note,
        "mittente_nome": mittente_nome,
        "mittente_piva": mittente_piva,
        "mittente_indirizzo": mittente_indirizzo,
        "mittente_contatti": mittente_contatti,
        "mittente_iban": mittente_iban,
        "cliente_id": cliente_id_da_usare,
        "cliente_nome": cliente_nome,
        "cliente_indirizzo": cliente_indirizzo,
        "cliente_piva": cliente_piva,
        "cliente_email": cliente_email,
        "subtotale": subtotale,
        "totale_iva": totale_iva,
        "totale": totale,
    }

    try:
        id_preventivo_salvato = database.salva_preventivo(
            dati_preventivo,
            voci_valide,
            preventivo_id=st.session_state.get("preventivo_id_in_modifica"),
        )
    except database.NumeroPreventivoEsistente:
        st.error(
            f"Esiste gia' un preventivo con il numero '{numero_preventivo}'. "
            "Cambia il numero preventivo e riprova."
        )
        st.stop()

    # Da questo momento in poi, generare di nuovo il PDF aggiornera' lo
    # stesso preventivo invece di crearne uno nuovo.
    st.session_state["preventivo_id_in_modifica"] = id_preventivo_salvato

    pdf_bytes = pdf_generator.genera_pdf_documento(
        tipo_documento="PREVENTIVO",
        numero_documento=numero_preventivo,
        data_documento=data_preventivo,
        mittente={
            "nome": mittente_nome,
            "piva": mittente_piva,
            "indirizzo": mittente_indirizzo,
            "contatti": mittente_contatti,
            "iban": mittente_iban,
        },
        cliente={
            "nome": cliente_nome,
            "indirizzo": cliente_indirizzo,
            "piva": cliente_piva,
            "email": cliente_email,
        },
        voci=voci_valide,
        subtotale=subtotale,
        riepilogo_iva_per_aliquota=riepilogo_iva_per_aliquota,
        totale_iva=totale_iva,
        totale=totale,
        note=note,
        validita_giorni=validita_giorni,
    )

    st.success("Preventivo generato e salvato nello Storico Preventivi!")
    st.download_button(
        label="⬇️ Scarica il PDF",
        data=pdf_bytes,
        file_name=f"preventivo_{numero_preventivo}.pdf",
        mime="application/pdf",
    )
