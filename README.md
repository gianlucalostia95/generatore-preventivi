# 🧾 Generatore di Preventivi

Applicazione web locale per creare preventivi professionali in PDF, con
anagrafica clienti, profilo mittente riutilizzabile, IVA impostabile per
singola voce di spesa, storico dei preventivi e generazione delle relative
fatture. Scritta in Python con [Streamlit](https://streamlit.io) e
[FPDF2](https://pypi.org/project/fpdf2/), con un database locale SQLite
(nessun servizio esterno, nessun account richiesto: i tuoi dati restano solo
sul tuo computer).

## Funzionalita'

- **Profilo Mittente**: inserisci una volta sola i tuoi dati aziendali
  (nome, P.IVA, indirizzo, contatti, IBAN); verranno proposti automaticamente
  in ogni nuovo preventivo.
- **Anagrafica Clienti**: salva, cerca, modifica ed elimina i clienti, cosi'
  da selezionarli da un menu invece di reinserirli ogni volta.
- **Voci di spesa con IVA per riga**: ogni voce puo' avere una propria
  aliquota IVA (es. una riga al 22% e un'altra al 10%); il riepilogo mostra
  il totale IVA suddiviso per aliquota.
- **PDF pronto da inviare**: genera e scarica il preventivo in PDF con un
  click, salvato automaticamente nello storico.
- **Storico Preventivi**: consulta, filtra (per cliente, numero, data,
  importo, stato), duplica o modifica i preventivi passati; esporta l'elenco
  in CSV.
- **Fatturazione**: trasforma un preventivo in fattura con numerazione
  progressiva dedicata e genera il PDF corrispondente.

## Requisiti

- [Python 3.10 o superiore](https://www.python.org/downloads/) (durante
  l'installazione su Windows, spunta "Add python.exe to PATH")

Non serve nient'altro: il database e' un singolo file SQLite creato
automaticamente al primo avvio, incluso in Python.

## Installazione

```bash
git clone <url-di-questo-repository>
cd creazione_preventivi
python -m venv venv
```

Attiva l'ambiente virtuale:

- **Windows (PowerShell)**: `.\venv\Scripts\Activate.ps1`
- **macOS / Linux**: `source venv/bin/activate`

Installa le dipendenze:

```bash
pip install -r requirements.txt
```

### Windows: installazione guidata

In alternativa ai comandi sopra, fai doppio click su **`installa.bat`**:
crea l'ambiente virtuale e installa tutte le dipendenze automaticamente.

## Avvio dell'applicazione

Con l'ambiente virtuale attivo:

```bash
streamlit run Generazione_Preventivo.py
```

L'app si apre automaticamente nel browser su `http://localhost:8501`.

### Windows: avvio rapido

- Doppio click su **`avvia_preventivi.bat`** per avviare il server e aprire
  il browser in un solo passaggio.
- Oppure esegui una sola volta **`crea_icona_desktop.bat`** per creare
  un'icona **"Generatore Preventivi"** sul Desktop: da quel momento basta
  un doppio click sull'icona, anche dopo un riavvio del PC. Il server viene
  avviato senza finestre extra (nessun prompt dei comandi visibile).

Per fermare il server avviato in questo modo (nascosto, senza finestra),
usa **`ferma_preventivi.bat`**.

## Struttura del progetto

```
Generazione_Preventivo.py   Pagina principale: crea un nuovo preventivo
pages/
  1_Anagrafica_Clienti.py   Gestione clienti salvati
  2_Profilo_Mittente.py     Dati della propria azienda/attivita'
  3_Storico_Preventivi.py   Storico, filtri, duplicazione, fatturazione
database.py                 Accesso al database SQLite locale (preventivi.db)
pdf_generator.py             Generazione dei PDF (preventivi e fatture)
requirements.txt            Dipendenze Python
```

## Guida completa

Per una guida passo-passo all'uso di ogni pagina (profilo mittente,
anagrafica clienti, storico preventivi, fatturazione, ecc.) vedi
[MANUALE.md](MANUALE.md).

## Dati e privacy

Tutti i dati (profilo mittente, clienti, preventivi) vengono salvati in un
unico file locale, `preventivi.db`, creato automaticamente nella cartella del
progetto al primo avvio. Non viene inviato nulla a servizi esterni. Questo
file **non e' incluso nel repository** (vedi `.gitignore`): ogni persona che
scarica il progetto parte con un database vuoto.

## Licenza

Distribuito con licenza MIT, vedi [LICENSE](LICENSE).
