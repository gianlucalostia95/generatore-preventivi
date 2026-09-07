# Istruzioni per lo Sviluppo: Generatore di Preventivi in PDF

Questo file contiene le istruzioni operative per lo sviluppo di un'applicazione web in Python per la generazione di preventivi in formato PDF.

---

## 1. Setup dell'Ambiente di Sviluppo
- Crea un ambiente virtuale Python (`venv`) nella cartella di progetto.
- Attiva l'ambiente virtuale.
- Crea il file `requirements.txt` contenente:
  - `streamlit`
  - `fpdf2`
- Installa tutte le dipendenze contenute in `requirements.txt` all'interno del `venv`.

---

## 2. Struttura dell'Applicazione (`app.py`)
Sviluppa l'interfaccia utente con **Streamlit** dividendo la pagina nelle seguenti sezioni:

### A. Dati del Mittente e del Cliente
- **Dati Mittente:** Nome/Ragione Sociale, P.IVA/Codice Fiscale, Indirizzo, Contatti e IBAN per il bonifico.
- **Dati Cliente:** Nome/Ragione Sociale, Indirizzo, P.IVA/Codice Fiscale, Email.

### B. Voci di Spesa e Calcoli
- Campi per inserire righe dinamiche contenenti: Descrizione, Quantità e Prezzo unitario.
- Calcolo automatico in tempo reale di:
  - Subtotale
  - Importo IVA (con percentuale personalizzabile)
  - Totale finale

---

## 3. Generazione PDF
- Implementa una funzione basata su **FPDF2** per impaginare i dati in un documento PDF dal layout pulito e professionale.
- Aggiungi un pulsante in Streamlit per scaricare direttamente il PDF generato.

---

## 4. Verifica e Avvio
- Controlla che non ci siano errori nel codice.
- Avvia l'applicazione in locale con Streamlit per confermare il funzionamento.
