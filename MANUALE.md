# Manuale d'Uso — Generatore di Preventivi in PDF

Questo documento spiega cos'è l'applicazione, come installarla, come usarla
passo per passo e come è organizzato il codice sorgente. È pensato sia per
chi deve semplicemente **usare** il programma, sia per chi in futuro dovrà
**modificarlo o mantenerlo**.

---

## 1. Cos'è questa applicazione

È un'applicazione web che permette di creare un **preventivo professionale
in formato PDF** in pochi minuti, senza bisogno di competenze informatiche:

- si compilano dei campi a schermo (dati dell'azienda, dati del cliente,
  elenco di prodotti/servizi);
- i totali (subtotale, IVA, totale) vengono calcolati **automaticamente**
  mentre si scrive, anche quando prodotti diversi hanno un'**aliquota IVA
  diversa**;
- con un click si genera un file PDF pronto da scaricare e inviare al
  cliente;
- ogni preventivo generato viene **salvato automaticamente** in uno
  storico consultabile, ricercabile e riutilizzabile;
- da un preventivo salvato si può generare, con un click, il **PDF della
  fattura corrispondente**, con una propria numerazione.

L'applicazione gira **in locale sul proprio computer** (non serve
connessione internet una volta installata, né si inviano dati a server
esterni) e si usa dal browser, con un'interfaccia semplice e guidata. Tutti
i dati (profilo, clienti, preventivi, fatture) restano salvati in un unico
file sul computer, anche chiudendo e riaprendo l'applicazione.

### Tecnologie utilizzate

| Componente  | A cosa serve                                                     |
|-------------|-------------------------------------------------------------------|
| Python      | Linguaggio di programmazione con cui è scritta l'app               |
| Streamlit   | Crea l'interfaccia grafica (i campi, i pulsanti, le pagine web)     |
| FPDF2       | Genera i file PDF (preventivi e fatture)                            |
| SQLite      | Database locale (incluso in Python) che conserva i dati salvati     |

---

## 2. Struttura del progetto

```
creazione_preventivi/
├── Generazione_Preventivo.py       # Pagina principale: crea/modifica un preventivo
├── database.py                     # Logica di salvataggio dati (database SQLite)
├── pdf_generator.py                # Logica condivisa di generazione PDF (preventivi e fatture)
├── pages/
│   ├── 1_Anagrafica_Clienti.py     # Pagina: gestione clienti salvati
│   ├── 2_Profilo_Mittente.py       # Pagina: dati della propria azienda
│   └── 3_Storico_Preventivi.py     # Pagina: elenco, ricerca, fatturazione
├── preventivi.db                   # Database SQLite (creato automaticamente al primo avvio)
├── requirements.txt                # Elenco delle librerie Python necessarie
├── venv/                           # Ambiente virtuale Python (creato in fase di installazione)
├── istruzioni_preventivi.md        # Specifiche originali del progetto
└── MANUALE.md                      # Questo manuale
```

- **`Generazione_Preventivo.py`**: la pagina che si apre per prima (il nome
  di questo file e' anche quello mostrato nel menu laterale di Streamlit).
  Contiene il modulo per creare, modificare o duplicare un preventivo.
- **`database.py`**: contiene tutte le funzioni che leggono e scrivono nel
  database (profilo, clienti, preventivi, fatture). È condiviso da tutte
  le pagine.
- **`pdf_generator.py`**: contiene la funzione che costruisce il layout dei
  documenti PDF (usata sia per i preventivi sia per le fatture, per non
  duplicare lo stesso codice in più punti).
- **`pages/`**: cartella riconosciuta automaticamente da Streamlit, che
  mostra ogni file al suo interno come voce aggiuntiva nel menu laterale.
- **`preventivi.db`**: il file che contiene davvero tutti i dati salvati
  (un singolo file SQLite). Eliminandolo si perdono profilo, clienti,
  storico e fatture: **va conservato/backuppato** come si farebbe con un
  archivio Excel importante.
- **`requirements.txt`**: elenca le librerie da installare (`streamlit` e
  `fpdf2`; SQLite e Pandas sono già inclusi/installati come dipendenze).
- **`venv/`**: una copia isolata di Python con solo le librerie necessarie
  a questo progetto, per non interferire con altri programmi installati
  sul computer.

---

## 3. Installazione (da fare una sola volta)

Questi passaggi vanno eseguiti una volta sola, al primo utilizzo su un
nuovo computer.

1. **Installare Python** (se non è già presente) da [python.org](https://www.python.org/).
2. Aprire un terminale nella cartella del progetto (`creazione_preventivi`).
3. Creare l'ambiente virtuale:
   ```
   python -m venv venv
   ```
4. Installare le librerie necessarie:
   ```
   .\venv\Scripts\pip.exe install -r requirements.txt
   ```
   (su macOS/Linux: `./venv/bin/pip install -r requirements.txt`)

Al termine, la cartella `venv/` conterrà tutto il necessario per far
funzionare l'app. Il file `preventivi.db` verrà creato automaticamente al
primo avvio.

---

## 4. Come avviare l'applicazione

Ogni volta che si vuole usare il generatore di preventivi:

1. Aprire un terminale nella cartella del progetto.
2. Eseguire:
   ```
   .\venv\Scripts\streamlit.exe run Generazione_Preventivo.py
   ```
   (su macOS/Linux: `./venv/bin/streamlit run Generazione_Preventivo.py`)
3. Si aprirà automaticamente il browser all'indirizzo `http://localhost:8501`
   con l'applicazione pronta all'uso. Se non si apre da solo, basta copiare
   quell'indirizzo in un browser qualsiasi (Chrome, Edge, Firefox...).
4. Nel menu laterale (a sinistra) si trovano le altre pagine: **Anagrafica
   Clienti**, **Profilo Mittente** e **Storico Preventivi**.
5. Per chiudere l'applicazione, tornare al terminale e premere `Ctrl+C`.

---

## 5. Guida all'uso

### 5.1 — Prima di iniziare: Profilo Mittente

La prima volta conviene aprire la pagina **"Profilo Mittente"** dal menu
laterale e compilare i propri dati aziendali (Nome/Ragione Sociale, P.IVA,
Indirizzo, Contatti, IBAN) premendo poi **"Salva profilo"**. Da quel
momento, questi dati compariranno già precompilati in ogni nuovo
preventivo, senza doverli riscrivere ogni volta.

### 5.2 — Pagina "Generazione Preventivo" (pagina principale)

In cima alla pagina si trova il pulsante **"🆕 Inizia un nuovo preventivo
vuoto"**: usalo quando, nella stessa sessione, hai appena generato un
preventivo e vuoi crearne subito un altro completamente nuovo (svuota il
modulo e assegna un nuovo numero automatico, senza dover ricaricare la
pagina). Senza premerlo, generare di nuovo il PDF continuerebbe ad
aggiornare l'ultimo preventivo creato invece di crearne uno separato.

#### A. Dati del Mittente e del Cliente

- **Colonna sinistra — Mittente**: precompilata con il Profilo Mittente
  salvato. Puoi comunque modificare i campi solo per questo preventivo,
  senza cambiare il profilo salvato.
- **Colonna destra — Cliente**: un menu a tendina permette di scegliere un
  cliente già salvato in anagrafica (i suoi dati vengono mostrati in sola
  lettura) oppure di selezionare **"+ Nuovo cliente"** e compilarne i dati
  al volo. In quest'ultimo caso, una casella di spunta permette di
  salvarlo automaticamente in anagrafica per i preventivi futuri.

Subito sotto si trovano tre campi di riferimento del documento:
- **Numero preventivo**: proposto automaticamente in modo progressivo
  (es. `2026-001`, `2026-002`, ...), ma modificabile liberamente.
- **Data preventivo** (precompilata con la data odierna).
- **Validità offerta (giorni)**: se impostata, nel PDF comparirà anche la
  data di scadenza dell'offerta, calcolata automaticamente.

#### B. Voci di Spesa

Si inseriscono le righe del preventivo (prodotti o servizi): ogni riga ha
quattro campi affiancati:

- **Descrizione**: cosa si sta vendendo/offrendo.
- **Quantità**: numero di unità.
- **Prezzo unitario (EUR)**: prezzo di una singola unità.
- **IVA (%)**: aliquota IVA di **quella specifica voce** (precompilata al
  22%, la più comune, ma modificabile riga per riga — utile quando un
  preventivo contiene sia prodotti/servizi ordinari sia voci con IVA
  agevolata).

Per **aggiungere una riga** usa il pulsante **"➕ Aggiungi voce"** sotto la
tabella. Per **rimuovere una riga**, usa l'icona del cestino 🗑️ accanto ad
essa. Le righe incomplete (senza descrizione o quantità) vengono
automaticamente ignorate nei calcoli e nel PDF.

Sotto la tabella si trova il campo facoltativo **Note aggiuntive**, per
condizioni di pagamento, tempi di consegna o altre informazioni utili.

#### C. Riepilogo Preventivo

Vengono mostrati, aggiornati in tempo reale:
- **Subtotale (imponibile)**: somma di tutte le righe.
- **Totale IVA**: somma dell'IVA di tutte le righe.
- **TOTALE PREVENTIVO**: subtotale + IVA.

Se nel preventivo sono presenti voci con aliquote IVA diverse, viene
mostrato anche un **dettaglio IVA per aliquota** (es. "IVA 10%: ... EUR",
"IVA 22%: ... EUR"), cosi' come compare anche nel PDF finale. Ogni riga e
ogni totale vengono arrotondati ai centesimi, in modo che il valore
visualizzato in tabella corrisponda sempre esattamente a quello usato nei
calcoli (evitando differenze di qualche centesimo dovute a decimali
digitati ma non visibili).

#### D. Genera, Salva e Scarica il Preventivo

- Il pulsante resta disattivato finché non sono compilati almeno: nome
  del mittente, nome del cliente e una voce di spesa valida.
- Al click, il preventivo viene **salvato nello Storico** (e il cliente
  nuovo, se richiesto, salvato in anagrafica) e viene generato il PDF,
  scaricabile con il pulsante **"Scarica il PDF"**.
- Se si sta **modificando** o **duplicando** un preventivo esistente
  (vedi sotto), il pulsante cambia etichetta in "Salva modifiche e
  rigenera PDF": in quel caso il preventivo viene aggiornato invece di
  crearne uno nuovo.

### 5.3 — Pagina "Anagrafica Clienti"

Permette di:
- **Cercare** un cliente per nome.
- **Consultare** l'elenco dei clienti salvati (ognuno in un riquadro
  espandibile).
- **Modificarne** i dati o **eliminarlo**.
- **Aggiungerne uno nuovo** tramite l'apposito modulo in fondo alla pagina.

### 5.4 — Pagina "Profilo Mittente"

Un unico modulo con i propri dati aziendali, da compilare una sola volta
(vedi punto 5.1). Si può tornare qui in qualsiasi momento per aggiornarli.

### 5.5 — Pagina "Storico Preventivi"

Mostra l'elenco di tutti i preventivi generati, con un pannello di
**filtri di ricerca**: cliente, numero preventivo, intervallo di date,
importo minimo/massimo e **stato di fatturazione** (menu a tendina con
"Tutti" / "Da fatturare" / "Fatturati") — utile per capire a colpo
d'occhio quali preventivi sono già stati fatturati e quali no.

Per ogni preventivo trovato (in un riquadro espandibile) sono disponibili
queste azioni:

- **📄 Duplica**: apre la pagina di generazione precompilata con gli
  stessi dati, ma con un numero preventivo nuovo e data odierna — utile
  per creare un preventivo simile a uno già fatto.
- **✏️ Modifica**: apre la pagina di generazione precompilata per
  correggere quel preventivo specifico; salvando, l'originale viene
  aggiornato invece di crearne uno nuovo.
- **🗑️ Elimina**: rimuove definitivamente il preventivo dallo storico.

Più sotto, nella sezione **"🧾 Fatturazione"**:

- **🧾 Genera Fattura PDF**: trasforma il preventivo in fattura, assegnando
  una numerazione dedicata e progressiva (es. `FT-2026-001`, indipendente
  dal numero del preventivo) e la data odierna, poi genera il PDF della
  fattura — scaricabile con il pulsante che compare subito dopo. Il
  preventivo viene automaticamente marcato come "Fatturato" nello storico.
- Rigenerando il PDF di un preventivo già fatturato (pulsante **"🔄
  Rigenera PDF Fattura"**), viene riutilizzato lo **stesso numero di
  fattura**: non ne viene creato uno nuovo ogni volta che si riscarica il
  documento.
- **↩️ Annulla fatturazione** (visibile solo se già fatturato): riporta il
  preventivo allo stato "Da fatturare". Se in seguito si genera di nuovo
  la fattura, viene assegnato un **numero completamente nuovo**: un
  numero di fattura annullato non viene mai riutilizzato, per non avere
  due fatture diverse con lo stesso numero nella numerazione fiscale.

  > ⚠️ **Attenzione**: il PDF generato con "Genera Fattura PDF" è un
  > documento pratico (da inviare al cliente o archiviare), **non
  > sostituisce l'obbligo di fatturazione elettronica (SdI)** quando
  > previsto dalla normativa italiana. Per le fatture che richiedono
  > invio allo SdI, va comunque usato il proprio canale abituale
  > (commercialista, software gestionale, ecc.).

In cima ai risultati, il pulsante **"⬇️ Esporta elenco in CSV"** scarica
la lista dei preventivi filtrati (incluso numero e data fattura, se
presenti) in formato CSV, utile per la contabilità o per aprirla in Excel.

---

## 6. Struttura dei PDF generati

Sia il PDF di un **preventivo** sia quello di una **fattura** condividono
lo stesso layout pulito e professionale (costruito da `pdf_generator.py`),
e contengono, in quest'ordine:

1. Intestazione con i dati del mittente.
2. Titolo del documento ("PREVENTIVO" oppure "FATTURA") con numero e data;
   nel preventivo compare anche la data di validità (se impostata), nella
   fattura compare invece il **riferimento al numero del preventivo di
   origine**.
3. Dati del destinatario (cliente).
4. Tabella delle voci di spesa (descrizione, quantità, prezzo unitario,
   **aliquota IVA della riga**, totale riga).
5. Riepilogo dei totali: subtotale (imponibile), **IVA suddivisa per ogni
   aliquota presente nel documento**, e totale finale in grassetto.
6. Eventuali note aggiuntive.
7. Coordinate bancarie (IBAN) per il bonifico, se inserite.

---

## 7. Note tecniche per chi modifica il codice

- **`database.py`** contiene tutta la logica di lettura/scrittura sul
  database SQLite (`preventivi.db`): profilo mittente, anagrafica clienti,
  preventivi, voci e fatturazione. Ogni funzione ha un nome che ne
  descrive lo scopo (es. `salva_cliente`, `elenco_preventivi`,
  `genera_fattura_da_preventivo`). Questo file viene importato sia da
  `Generazione_Preventivo.py` sia dalle pagine in `pages/`.
  - La numerazione delle fatture (`prossimo_numero_fattura`) si basa su un
    contatore dedicato (tabella `contatori_fattura`) che aumenta sempre e
    non torna mai indietro, nemmeno annullando una fattura: questo evita
    che due fatture diverse ricevano nel tempo lo stesso numero.
  - Le nuove colonne introdotte per la fatturazione (`numero_fattura`,
    `data_fattura`) vengono aggiunte automaticamente da
    `inizializza_database()` anche a un database creato con una versione
    precedente dell'app, senza perdere i dati già presenti.
- **`pdf_generator.py`** contiene `genera_pdf_documento()`, che costruisce
  il PDF (sia per i preventivi sia per le fatture) con FPDF2: è il punto
  da modificare per cambiare il layout del documento (colori, loghi,
  disposizione dei blocchi). Contiene anche `sanifica_testo()` (gestisce i
  caratteri non supportati dal font di base, es. il simbolo `€` convertito
  in `EUR`) e `calcola_riepilogo_iva_per_aliquota()` (raggruppa l'IVA delle
  voci per aliquota).
- **`Generazione_Preventivo.py`** contiene la logica per **precompilare il
  modulo** quando si arriva da un'azione di "modifica" o "duplica" avviata
  dallo Storico (tramite `st.session_state["azione_preventivo"]`).
- Le pagine in **`pages/`** sono riconosciute automaticamente da
  Streamlit in base al nome del file: il numero iniziale ne determina
  l'ordine nel menu laterale. Anche l'etichetta della pagina principale
  nel menu laterale deriva dal nome del suo file
  (`Generazione_Preventivo.py` → "Generazione Preventivo").
- I dati storici dei preventivi conservano una **copia (snapshot)** dei
  dati del cliente e del mittente al momento della creazione: se in
  seguito un cliente viene modificato o eliminato dall'anagrafica, i
  preventivi già generati restano storicamente corretti e invariati.
- Il file `preventivi.db` è un database SQLite: può essere aperto e
  ispezionato con qualsiasi strumento compatibile (es. "DB Browser for
  SQLite"), utile in fase di debug.

---

## 8. Limiti attuali e possibili miglioramenti futuri

Le funzionalità di base per un utilizzo quotidiano da parte di un singolo
utente/azienda sono coperte: salvataggio del profilo, anagrafica clienti,
IVA per singola voce, storico con ricerca, duplicazione, modifica,
generazione fatture con numerazione dedicata ed esportazione CSV. Restano
fuori dallo scope attuale alcune funzionalità più complesse, perché
richiedono servizi esterni o un'architettura più articolata:

- **Fatturazione elettronica (SdI)**: il PDF di fattura generato dall'app
  è un documento pratico, **non** un'e-fattura conforme trasmessa allo SdI
  come richiesto dalla normativa italiana per la maggior parte delle
  operazioni. Per quello resta necessario il proprio canale abituale
  (commercialista, software gestionale certificato, ecc.).
- **Personalizzazione grafica del PDF**: possibilità di caricare un logo
  aziendale e scegliere un colore principale per il documento (oggi il
  PDF usa un layout fisso in bianco e nero/grigio).
- **Invio diretto via email**: inviare il PDF al cliente direttamente
  dall'applicazione, senza doverlo scaricare e allegare manualmente.
  Richiederebbe di configurare le credenziali SMTP della propria casella
  di posta (o un servizio terzo di invio email) in modo sicuro.
- **Gestione multi-utente**: se l'applicazione venisse usata da più
  persone/postazioni con dati separati, servirebbe un sistema di login e
  di permessi — oggi l'app è pensata per un singolo utente/azienda su un
  singolo computer.

Per qualsiasi di questi punti, la base dati già introdotta (SQLite) resta
comunque un buon punto di partenza: non servirebbe ripensare
l'architettura da zero, ma solo estenderla.
