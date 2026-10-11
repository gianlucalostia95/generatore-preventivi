# Da app locale a prodotto web — Preventivi Cloud

Piano di progetto — non vincolante. Aggiornato: 13 settembre 2026.
Fase attuale: **pianificazione — nessuno sviluppo avviato**.

Percorso, architettura, costi e rischi per trasformare il Generatore di
Preventivi in un servizio multi-utente accessibile via browser, con un
mittente per profilo e accesso semplificato tramite Google.

---

## Indice

1. [Stato attuale del progetto](#stato-attuale-del-progetto)
2. [Visione del prodotto](#visione-del-prodotto)
3. [Architettura per la fase di validazione](#architettura-per-la-fase-di-validazione)
4. [Login con Google](#login-con-google)
5. [Cookie e gestione della privacy](#cookie-e-gestione-della-privacy)
6. [Roadmap a fasi](#roadmap-a-fasi)
7. [Costi indicativi](#costi-indicativi)
8. [Criticità da tenere presenti](#criticità-da-tenere-presenti)
9. [Domande aperte per decidere il seguito](#domande-aperte-per-decidere-il-seguito)

---

## Stato attuale del progetto

Un'applicazione Streamlit funzionante, ma pensata per un solo utente su un
solo computer.

Oggi il Generatore di Preventivi gira in locale con un database SQLite
(`preventivi.db`), avviato tramite `avvia_preventivi.bat`. Le funzionalità
già solide:

- Profilo mittente unico, riproposto automaticamente in ogni preventivo
- Anagrafica clienti con ricerca, modifica ed eliminazione
- Voci di spesa con IVA impostabile per singola riga, riepilogo per aliquota
- PDF pronto da scaricare, salvato automaticamente nello storico
- Storico con filtri (cliente, numero, data, importo, stato) ed export CSV
- Conversione preventivo → fattura, con numerazione progressiva dedicata
  che non torna mai indietro

Il vincolo "un solo mittente" è già presente nel database
(`CHECK (id = 1)` sulla tabella `profilo_mittente`) — oggi significa *un
solo mittente in assoluto*, non ancora *un mittente per ogni utente*. È la
base da cui partire, non da riscrivere da zero.

## Visione del prodotto

Un sito web dove ogni persona crea un account, inserisce una volta sola i
propri dati aziendali (il "mittente") e da lì genera preventivi e fatture
per i propri clienti — con i dati isolati da quelli di chiunque altro usi
lo stesso servizio.

- **Un account = un mittente.** Vincolo di prodotto, non solo tecnico:
  ogni utente registrato può avere un solo profilo mittente.
- **Accesso con email o con Google.** Il login Google riduce l'attrito in
  fase di iscrizione: niente password da scegliere, un click e si è dentro.
- **Dati privati per ogni utente.** Nessuno può vedere clienti o
  preventivi di un altro account, anche in caso di errore applicativo
  (isolamento garantito a livello di database, non solo di interfaccia).

## Architettura per la fase di validazione

Obiettivo: capire se il mercato lo vuole, spendendo il meno possibile in
infrastruttura e riscrittura.

Si resta su Streamlit per l'interfaccia — riscrivere ora sarebbe lavoro
sprecato se la validazione dovesse dire "non interessa a nessuno". Si
aggiungono due servizi gestiti (nessun server da amministrare) per
risolvere autenticazione e isolamento dati in un colpo solo: **Supabase**
fornisce sia il database Postgres sia l'autenticazione (email/password e
Google), con Row Level Security che isola i dati per utente direttamente
nel database.

```
Browser utente
      |
      v
Streamlit (Community Cloud)  ---------->  Google OAuth (login)
      |
      v
Supabase: Auth + Postgres (regione UE)
      |
      v
Resend (invio email) -- fase 2
```

I dati persistono solo in Supabase. Streamlit resta uno strato di
interfaccia senza stato proprio.

## Login con Google

Supabase Auth include un provider Google pronto all'uso: la parte di
scambio token è gestita da loro, ma la configurazione iniziale va fatta a
mano su Google Cloud Console.

### Passi da seguire

1. Creare un progetto su Google Cloud Console e configurare la schermata
   di consenso OAuth (tipo "Esterno")
2. Compilare i campi richiesti da Google: nome app, logo, **link a
   Privacy Policy e Termini di Servizio pubblici** — sono obbligatori,
   non opzionali
3. Creare le credenziali OAuth (tipo "Applicazione web") e impostare come
   redirect URI quello fornito da Supabase
   (`https://<progetto>.supabase.co/auth/v1/callback`)
4. Inserire Client ID e Client Secret nelle impostazioni "Auth Providers"
   di Supabase e attivare il provider Google
5. Gestire il redirect di ritorno dentro l'app Streamlit: da verificare
   presto, perché Streamlit non è pensato per flussi di redirect OAuth
   come una webapp JavaScript tradizionale — è il punto tecnico più
   incerto di questa integrazione

> **Da considerare per i tempi.** Finché l'app resta in modalità
> "Testing" su Google Cloud, funziona solo per gli utenti email inseriti
> manualmente in una lista di test. Per aprirla a chiunque, Google
> richiede una verifica dell'app che può richiedere da qualche giorno a
> diverse settimane, e pretende Privacy Policy e Termini pubblicati
> *prima* di sottoporla. Va messo in roadmap come attività a sé, non come
> ultimo dettaglio prima del lancio.

## Cookie e gestione della privacy

### Cosa serve davvero

Il client Supabase salva per default il token di sessione in
`localStorage`, non in un cookie. Che sia cookie o storage simile, la
normativa ePrivacy tratta allo stesso modo ciò che è **strettamente
necessario** a erogare il servizio richiesto dall'utente (mantenere la
sessione dopo il login): questo rientra nell'esenzione dal consenso,
esattamente come un cookie tecnico di sessione. **Il banner cookie non
serve solo per gestire il login.**

Diventa necessario un banner con scelta esplicita (accetta/rifiuta per
categoria) solo se si aggiungono strumenti non strettamente necessari:
analytics (es. Google Analytics), pixel pubblicitari, chat di supporto
con tracciamento di terze parti. Un'alternativa che evita del tutto il
banner: strumenti di analytics "cookieless" (es. Plausible), se bastano
per gli obiettivi del prodotto.

### Documenti pubblici da avere pronti

- **Informativa Privacy** (Art. 13 GDPR): dati raccolti (account, dati
  del mittente e dei clienti inseriti dall'utente), finalità, base
  giuridica, titolare del trattamento, elenco dei sub-responsabili
  (Supabase, Google, eventualmente Resend), diritti dell'interessato,
  tempi di conservazione
- **Cookie Policy**, anche minimale se non si usano cookie non essenziali
- **Termini di Servizio**

Questi tre documenti servono comunque per la verifica dell'app Google
(sezione precedente), quindi conviene prepararli insieme a quell'attività,
non separatamente.

### Residenza dei dati

In fase di creazione del progetto Supabase va scelta esplicitamente una
regione europea, per tenere i dati anagrafici di mittenti e clienti in UE.
Resta da verificare in quale area geografica gira l'infrastruttura di
Streamlit Community Cloud: i dati vi transitano (anche se non vi
risiedono in modo permanente), il che può avere rilevanza se il server è
fuori UE.

> **Non è consulenza legale.** Quanto sopra è un'indicazione tecnica di
> partenza, non un parere legale. Prima della pubblicazione pubblica
> conviene far rivedere informativa privacy, cookie policy e termini da
> un consulente, soprattutto trattandosi di dati di partite IVA e
> documenti a rilevanza fiscale.

## Roadmap a fasi

Ogni fase è pensata per produrre un segnale prima di investire nella
successiva.

**Fase 0 — Validazione** *(in corso, nessun codice)*
Prima di costruire qualunque cosa: parlare con 5-10 liberi professionisti
o piccole imprese che oggi fanno preventivi a mano o con altri strumenti,
capire cosa li farebbe passare a questo tool e se sarebbero disposti a
pagarlo.

**Fase 1 — MVP multi-utente** *(fondamenta)*
Migrazione dati da SQLite a Supabase Postgres, login email/password, Row
Level Security per isolare i dati per utente, vincolo "un mittente per
account".

- Ogni tabella (`clienti`, `preventivi`, `profilo_mittente`) guadagna una
  colonna `utente_id`
- Il vincolo passa da `CHECK (id = 1)` a `UNIQUE(utente_id)`
- Deploy su Streamlit Community Cloud
- Il PDF "fattura" resta etichettato chiaramente come documento di
  cortesia, non fiscale (vedi Criticità)

**Fase 2 — Iscrizione senza attrito** *(crescita utenti)*
Login con Google attivo, pagine pubbliche minime di Privacy Policy e
Termini, cookie policy se nel frattempo si è aggiunto un analytics.

**Fase 3 — Ascolto dei primi utenti** *(solo funzionalità richieste)*
Costruire solo ciò che i primi utenti reali chiedono esplicitamente:
candidati probabili sono il logo aziendale sul PDF, l'invio del
preventivo via email direttamente dal tool, l'accettazione online con un
click da parte del cliente.

**Fase 4 — Monetizzazione** *(solo se c'è domanda confermata)*
Integrazione Stripe, piano gratuito con limiti (es. numero di preventivi
al mese) e piano a pagamento senza limiti.

**Fase 5 — Eventuale** *(solo se il prodotto regge)*
Fatturazione elettronica reale via Sistema di Interscambio, o riscrittura
verso uno stack più scalabile (es. FastAPI/Django + frontend dedicato) se
Streamlit inizia a essere un limite reale all'esperienza utente.

## Costi indicativi

In fase di validazione (fasi 0-2) il costo può restare vicino a zero. Le
cifre sotto sono i prezzi pubblici dei piani a pagamento, da considerare
solo quando i limiti gratuiti vengono superati.

| Servizio | Limite gratuito | Oltre il limite | Note |
|---|---|---|---|
| Supabase | 500 MB database, 50.000 utenti auth/mese; progetto in pausa dopo 7 giorni di inattività | da 25 $/mese | Piano Pro rimuove la pausa automatica e aggiunge backup giornalieri |
| Streamlit Community Cloud | Gratuito, risorse condivise, repository pubblico | — | Nessun piano a pagamento diretto (ora parte di Snowflake); se serve repo privato o più risorse, alternative come Render/Railway, indicativamente 7-20 $/mese |
| Google Cloud (OAuth) | Gratuito per il solo login | — | Nessun costo legato all'uso come provider di accesso |
| Dominio personalizzato | Facoltativo | 10-15 €/anno | Consigliato prima della verifica Google e per credibilità del prodotto |
| Resend (email) | 3.000 email/mese | da 20 $/mese | Necessario solo dalla fase 3 (invio preventivi via email) |
| Stripe | Nessun costo fisso | ~1,5% + 0,25 €/transazione | Solo fase 4, attivato quando c'è un piano a pagamento |

## Criticità da tenere presenti

> **La più importante.** La "fattura" generata oggi è un PDF, **non un
> documento fiscalmente valido**. In Italia le fatture verso altre
> partite IVA o privati devono passare dal Sistema di Interscambio (SDI)
> in formato XML — un PDF, per quanto ben fatto, non sostituisce questo
> obbligo per chi è tenuto alla fatturazione elettronica. Se il tool
> resta così, va etichettato chiaramente come "documento di cortesia" per
> evitare che un utente lo scambi per una fattura valida. Integrare
> l'emissione elettronica reale è un lavoro a parte, non incluso in
> questa roadmap salvo validazione esplicita della domanda.

| Rischio | Impatto | Come attenuarlo |
|---|---|---|
| Row Level Security configurata male | Alto | Un utente vedrebbe i dati di un altro. Da testare esplicitamente (non solo "sembra funzionare") prima di qualunque apertura pubblica. |
| Streamlit non pensato per SaaS pubblici | Medio | UX di login, pagine di marketing e performance con molti utenti concorrenti restano quelle di uno "strumento", non di un prodotto curato. Accettabile in validazione, da rivalutare in fase 5. |
| Verifica Google OAuth non istantanea | Medio | Pianificare Privacy Policy/Termini con anticipo rispetto al lancio pubblico, non l'ultimo giorno. |
| Nessun backup automatico in fase gratuita | Medio | Supabase fa backup giornalieri solo dal piano Pro. In fase gratuita, prevedere un export manuale periodico finché il volume di utenti resta piccolo. |
| Vincolo "un mittente per account" può essere troppo rigido | Medio | Un commercialista o un'agenzia che gestisce più partite IVA di clienti non ci rientra. Va deciso consapevolmente se è il modello di mercato voluto (vedi Domande aperte) prima di irrigidire lo schema dati. |

## Domande aperte per decidere il seguito

**Il target è solo il mercato italiano o anche internazionale?**
Cambia lingua dell'interfaccia, valuta, e se l'IVA italiana resta l'unico
regime gestito o va generalizzata.

**Serve davvero la fatturazione elettronica valida, o il tool resta
focalizzato su preventivi + "fatture" di cortesia?**
Decisione che pesa molto sullo scope: integrare l'SDI è un progetto a sé,
non un'estensione incrementale.

**Un account potrà mai gestire più mittenti?**
Da fissare prima di irrigidire lo schema dati: cambiare rotta dopo il
lancio costa più che deciderlo ora.

**Qual è il modello di prezzo pensato?**
Freemium con limite di preventivi/mese, prova gratuita a tempo, o solo a
pagamento fin da subito — condiziona cosa costruire nella fase 4.

---

*Documento preparato come base di discussione a partire dall'analisi del
codice esistente e dal confronto avuto in sessione. Non sostituisce una
consulenza legale, fiscale o di sicurezza professionale prima del lancio
pubblico.*
