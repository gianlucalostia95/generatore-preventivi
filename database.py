"""
Modulo Database
================

Gestisce il salvataggio permanente dei dati dell'applicazione in un
database SQLite locale (un unico file, `preventivi.db`, creato nella
cartella del progetto). SQLite è incluso in Python: non serve installare
nessuna libreria aggiuntiva.

Questo modulo viene importato sia dalla pagina principale
(`Generazione_Preventivo.py`) sia dalle pagine aggiuntive nella cartella
`pages/`, cosi' che tutte condividano lo stesso database.

Tabelle gestite:
- `profilo_mittente`: i dati della propria azienda/attivita' (un solo profilo).
- `clienti`: l'anagrafica dei clienti salvati.
- `preventivi`: i preventivi generati (dati di testata, totali e, se
  emessa, numero/data della fattura corrispondente).
- `preventivo_voci`: le righe (descrizione/quantita'/prezzo/IVA) di ogni preventivo.
"""

import sqlite3
from datetime import date, datetime
from pathlib import Path

# Il file del database viene creato nella stessa cartella di questo modulo,
# cosi' che funzioni indipendentemente da dove viene lanciata l'app.
PERCORSO_DATABASE = Path(__file__).parent / "preventivi.db"


class NumeroPreventivoEsistente(Exception):
    """Sollevata quando si cerca di salvare un preventivo con un numero gia' in uso."""


def ottieni_connessione() -> sqlite3.Connection:
    """Apre una connessione al database, con i risultati restituiti come dizionari."""
    connessione = sqlite3.connect(PERCORSO_DATABASE)
    connessione.row_factory = sqlite3.Row
    # Necessario affinche' l'eliminazione di un preventivo elimini anche le sue voci.
    connessione.execute("PRAGMA foreign_keys = ON")
    return connessione


def inizializza_database() -> None:
    """
    Crea le tabelle del database se non esistono ancora.
    Va richiamata all'avvio di ogni pagina: se le tabelle esistono gia',
    non fa nulla.
    """
    connessione = ottieni_connessione()
    connessione.executescript(
        """
        CREATE TABLE IF NOT EXISTS profilo_mittente (
            id INTEGER PRIMARY KEY CHECK (id = 1),
            nome TEXT,
            piva TEXT,
            indirizzo TEXT,
            contatti TEXT,
            iban TEXT
        );

        CREATE TABLE IF NOT EXISTS clienti (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            indirizzo TEXT,
            piva TEXT,
            email TEXT
        );

        CREATE TABLE IF NOT EXISTS preventivi (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            numero TEXT NOT NULL UNIQUE,
            data TEXT NOT NULL,
            validita_giorni INTEGER,
            stato TEXT NOT NULL DEFAULT 'preventivo',
            note TEXT,
            mittente_nome TEXT,
            mittente_piva TEXT,
            mittente_indirizzo TEXT,
            mittente_contatti TEXT,
            mittente_iban TEXT,
            cliente_id INTEGER REFERENCES clienti(id) ON DELETE SET NULL,
            cliente_nome TEXT,
            cliente_indirizzo TEXT,
            cliente_piva TEXT,
            cliente_email TEXT,
            subtotale REAL NOT NULL DEFAULT 0,
            totale_iva REAL NOT NULL DEFAULT 0,
            totale REAL NOT NULL DEFAULT 0,
            creato_il TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS preventivo_voci (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            preventivo_id INTEGER NOT NULL REFERENCES preventivi(id) ON DELETE CASCADE,
            descrizione TEXT NOT NULL,
            quantita REAL NOT NULL,
            prezzo_unitario REAL NOT NULL,
            aliquota_iva REAL NOT NULL,
            totale_riga REAL NOT NULL
        );

        -- Contatore dedicato per la numerazione delle fatture: cresce sempre,
        -- anche se una fattura viene in seguito annullata, cosi' che lo
        -- stesso numero non venga mai riassegnato a due fatture diverse.
        CREATE TABLE IF NOT EXISTS contatori_fattura (
            anno INTEGER PRIMARY KEY,
            ultimo_progressivo INTEGER NOT NULL DEFAULT 0
        );
        """
    )

    # Migrazione: aggiunge le colonne per la fatturazione se non esistono
    # ancora (necessario per i database creati con una versione precedente
    # dell'app, che non le prevedeva). SQLite non supporta
    # "ADD COLUMN IF NOT EXISTS", quindi controlliamo manualmente.
    colonne_esistenti = {
        riga["name"] for riga in connessione.execute("PRAGMA table_info(preventivi)").fetchall()
    }
    if "numero_fattura" not in colonne_esistenti:
        connessione.execute("ALTER TABLE preventivi ADD COLUMN numero_fattura TEXT")
    if "data_fattura" not in colonne_esistenti:
        connessione.execute("ALTER TABLE preventivi ADD COLUMN data_fattura TEXT")
    # Sconto applicato al momento della fatturazione (non al preventivo
    # originale): "percentuale" o "importo", con il relativo valore.
    if "sconto_tipo" not in colonne_esistenti:
        connessione.execute("ALTER TABLE preventivi ADD COLUMN sconto_tipo TEXT")
    if "sconto_valore" not in colonne_esistenti:
        connessione.execute("ALTER TABLE preventivi ADD COLUMN sconto_valore REAL")

    connessione.commit()
    connessione.close()


# ---------------------------------------------------------------------------
# PROFILO MITTENTE (i propri dati aziendali, salvati una sola volta)
# ---------------------------------------------------------------------------
def ottieni_profilo_mittente() -> dict:
    """Restituisce il profilo salvato, oppure campi vuoti se non e' mai stato compilato."""
    connessione = ottieni_connessione()
    riga = connessione.execute("SELECT * FROM profilo_mittente WHERE id = 1").fetchone()
    connessione.close()
    if riga is None:
        return {"nome": "", "piva": "", "indirizzo": "", "contatti": "", "iban": ""}
    return dict(riga)


def salva_profilo_mittente(dati: dict) -> None:
    """Salva (creando o sovrascrivendo) il profilo del mittente."""
    connessione = ottieni_connessione()
    connessione.execute(
        """
        INSERT INTO profilo_mittente (id, nome, piva, indirizzo, contatti, iban)
        VALUES (1, :nome, :piva, :indirizzo, :contatti, :iban)
        ON CONFLICT(id) DO UPDATE SET
            nome = excluded.nome,
            piva = excluded.piva,
            indirizzo = excluded.indirizzo,
            contatti = excluded.contatti,
            iban = excluded.iban
        """,
        dati,
    )
    connessione.commit()
    connessione.close()


# ---------------------------------------------------------------------------
# ANAGRAFICA CLIENTI
# ---------------------------------------------------------------------------
def elenco_clienti(ricerca: str = "") -> list:
    """Restituisce i clienti salvati, filtrati per nome se viene indicato un testo di ricerca."""
    connessione = ottieni_connessione()
    if ricerca:
        righe = connessione.execute(
            "SELECT * FROM clienti WHERE nome LIKE ? ORDER BY nome", (f"%{ricerca}%",)
        ).fetchall()
    else:
        righe = connessione.execute("SELECT * FROM clienti ORDER BY nome").fetchall()
    connessione.close()
    return [dict(riga) for riga in righe]


def ottieni_cliente(cliente_id: int):
    """Restituisce un cliente dato il suo id, oppure None se non esiste."""
    connessione = ottieni_connessione()
    riga = connessione.execute("SELECT * FROM clienti WHERE id = ?", (cliente_id,)).fetchone()
    connessione.close()
    return dict(riga) if riga else None


def salva_cliente(dati: dict, cliente_id: int = None) -> int:
    """
    Salva un cliente in anagrafica: lo aggiorna se viene passato `cliente_id`,
    altrimenti ne crea uno nuovo. Restituisce l'id del cliente salvato.
    """
    connessione = ottieni_connessione()
    if cliente_id:
        connessione.execute(
            "UPDATE clienti SET nome = :nome, indirizzo = :indirizzo, "
            "piva = :piva, email = :email WHERE id = :id",
            {**dati, "id": cliente_id},
        )
        id_salvato = cliente_id
    else:
        cursore = connessione.execute(
            "INSERT INTO clienti (nome, indirizzo, piva, email) "
            "VALUES (:nome, :indirizzo, :piva, :email)",
            dati,
        )
        id_salvato = cursore.lastrowid
    connessione.commit()
    connessione.close()
    return id_salvato


def elimina_cliente(cliente_id: int) -> None:
    """Elimina un cliente dall'anagrafica. I preventivi gia' emessi non vengono modificati."""
    connessione = ottieni_connessione()
    connessione.execute("DELETE FROM clienti WHERE id = ?", (cliente_id,))
    connessione.commit()
    connessione.close()


# ---------------------------------------------------------------------------
# PREVENTIVI E STORICO
# ---------------------------------------------------------------------------
def prossimo_numero_preventivo() -> str:
    """
    Genera il primo numero di preventivo disponibile nell'anno in corso, nel
    formato "ANNO-PROGRESSIVO" (es. "2026-004"): il primo progressivo (a
    partire da 001) non ancora usato da nessun preventivo esistente.

    Cerca il primo "buco" libero invece di contare semplicemente i
    preventivi gia' emessi: un semplice conteggio propone un numero gia'
    esistente (e viene rifiutato al salvataggio) se manca un progressivo nel
    mezzo, ad esempio perche' un preventivo e' stato eliminato.
    """
    anno_corrente = datetime.now().year
    connessione = ottieni_connessione()
    numeri_esistenti = {
        riga["numero"]
        for riga in connessione.execute(
            "SELECT numero FROM preventivi WHERE numero LIKE ?", (f"{anno_corrente}-%",)
        ).fetchall()
    }
    connessione.close()

    progressivo = 1
    while f"{anno_corrente}-{progressivo:03d}" in numeri_esistenti:
        progressivo += 1
    return f"{anno_corrente}-{progressivo:03d}"


def salva_preventivo(dati: dict, voci: list, preventivo_id: int = None) -> int:
    """
    Salva un preventivo insieme alle sue voci di spesa.

    Se `preventivo_id` viene indicato, aggiorna il preventivo esistente
    (sostituendo tutte le sue voci); altrimenti ne crea uno nuovo.
    Restituisce l'id del preventivo salvato.

    Solleva `NumeroPreventivoEsistente` se il numero scelto e' gia' usato
    da un altro preventivo.
    """
    connessione = ottieni_connessione()
    try:
        if preventivo_id:
            connessione.execute(
                """
                UPDATE preventivi SET
                    numero = :numero, data = :data, validita_giorni = :validita_giorni,
                    note = :note,
                    mittente_nome = :mittente_nome, mittente_piva = :mittente_piva,
                    mittente_indirizzo = :mittente_indirizzo, mittente_contatti = :mittente_contatti,
                    mittente_iban = :mittente_iban,
                    cliente_id = :cliente_id, cliente_nome = :cliente_nome,
                    cliente_indirizzo = :cliente_indirizzo, cliente_piva = :cliente_piva,
                    cliente_email = :cliente_email,
                    subtotale = :subtotale, totale_iva = :totale_iva, totale = :totale
                WHERE id = :id
                """,
                {**dati, "id": preventivo_id},
            )
            connessione.execute(
                "DELETE FROM preventivo_voci WHERE preventivo_id = ?", (preventivo_id,)
            )
            id_salvato = preventivo_id
        else:
            cursore = connessione.execute(
                """
                INSERT INTO preventivi (
                    numero, data, validita_giorni, note,
                    mittente_nome, mittente_piva, mittente_indirizzo, mittente_contatti, mittente_iban,
                    cliente_id, cliente_nome, cliente_indirizzo, cliente_piva, cliente_email,
                    subtotale, totale_iva, totale, creato_il
                ) VALUES (
                    :numero, :data, :validita_giorni, :note,
                    :mittente_nome, :mittente_piva, :mittente_indirizzo, :mittente_contatti, :mittente_iban,
                    :cliente_id, :cliente_nome, :cliente_indirizzo, :cliente_piva, :cliente_email,
                    :subtotale, :totale_iva, :totale, :creato_il
                )
                """,
                {**dati, "creato_il": datetime.now().isoformat(timespec="seconds")},
            )
            id_salvato = cursore.lastrowid

        for voce in voci:
            connessione.execute(
                """
                INSERT INTO preventivo_voci
                    (preventivo_id, descrizione, quantita, prezzo_unitario, aliquota_iva, totale_riga)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    id_salvato,
                    voce["descrizione"],
                    voce["quantita"],
                    voce["prezzo_unitario"],
                    voce["aliquota_iva"],
                    voce["totale_riga"],
                ),
            )

        connessione.commit()
    except sqlite3.IntegrityError as errore:
        connessione.close()
        raise NumeroPreventivoEsistente(dati["numero"]) from errore

    connessione.close()
    return id_salvato


def ottieni_preventivo_completo(preventivo_id: int):
    """Restituisce un preventivo (dati di testata + elenco voci), oppure None se non esiste."""
    connessione = ottieni_connessione()
    testata = connessione.execute(
        "SELECT * FROM preventivi WHERE id = ?", (preventivo_id,)
    ).fetchone()
    if testata is None:
        connessione.close()
        return None

    voci = connessione.execute(
        "SELECT * FROM preventivo_voci WHERE preventivo_id = ? ORDER BY id", (preventivo_id,)
    ).fetchall()
    connessione.close()

    risultato = dict(testata)
    risultato["voci"] = [dict(voce) for voce in voci]
    return risultato


def elenco_preventivi(filtri: dict) -> list:
    """
    Restituisce l'elenco dei preventivi salvati, applicando i filtri di
    ricerca indicati nel dizionario `filtri`. Chiavi riconosciute:
    "cliente", "numero", "data_da", "data_a", "stato", "importo_min", "importo_max".
    Un filtro viene ignorato se il suo valore e' vuoto/None.
    """
    condizioni = []
    parametri = []

    if filtri.get("cliente"):
        condizioni.append("cliente_nome LIKE ?")
        parametri.append(f"%{filtri['cliente']}%")
    if filtri.get("numero"):
        condizioni.append("numero LIKE ?")
        parametri.append(f"%{filtri['numero']}%")
    if filtri.get("data_da"):
        condizioni.append("data >= ?")
        parametri.append(filtri["data_da"].isoformat())
    if filtri.get("data_a"):
        condizioni.append("data <= ?")
        parametri.append(filtri["data_a"].isoformat())
    if filtri.get("stato") and filtri["stato"] != "Tutti":
        condizioni.append("stato = ?")
        parametri.append(filtri["stato"])
    if filtri.get("importo_min") is not None:
        condizioni.append("totale >= ?")
        parametri.append(filtri["importo_min"])
    if filtri.get("importo_max") is not None:
        condizioni.append("totale <= ?")
        parametri.append(filtri["importo_max"])

    query = "SELECT * FROM preventivi"
    if condizioni:
        query += " WHERE " + " AND ".join(condizioni)
    query += " ORDER BY data DESC, numero DESC"

    connessione = ottieni_connessione()
    righe = connessione.execute(query, parametri).fetchall()
    connessione.close()
    return [dict(riga) for riga in righe]


def prossimo_numero_fattura() -> str:
    """
    Assegna e restituisce il prossimo numero di fattura disponibile, nel
    formato "FT-ANNO-PROGRESSIVO" (es. "FT-2026-004"). Il progressivo viene
    letto da un contatore dedicato che aumenta sempre e non viene mai fatto
    tornare indietro, nemmeno se una fattura viene successivamente
    annullata: questo evita che due fatture diverse ricevano in tempi
    diversi lo stesso numero, cosa da evitare nella numerazione fiscale.

    Attenzione: ogni chiamata consuma un numero (il contatore avanza),
    quindi va richiamata solo nel momento in cui si genera davvero una
    nuova fattura, non per una semplice anteprima.
    """
    anno_corrente = datetime.now().year
    connessione = ottieni_connessione()
    connessione.execute(
        "INSERT INTO contatori_fattura (anno, ultimo_progressivo) VALUES (?, 0) "
        "ON CONFLICT(anno) DO NOTHING",
        (anno_corrente,),
    )
    connessione.execute(
        "UPDATE contatori_fattura SET ultimo_progressivo = ultimo_progressivo + 1 WHERE anno = ?",
        (anno_corrente,),
    )
    riga = connessione.execute(
        "SELECT ultimo_progressivo FROM contatori_fattura WHERE anno = ?", (anno_corrente,)
    ).fetchone()
    connessione.commit()
    connessione.close()
    return f"FT-{anno_corrente}-{riga['ultimo_progressivo']:03d}"


def genera_fattura_da_preventivo(preventivo_id: int, sconto_tipo: str = None, sconto_valore: float = None):
    """
    Trasforma un preventivo in fattura: se non e' mai stato fatturato, gli
    assegna un nuovo numero di fattura progressivo, la data odierna e lo
    stato 'fatturato'; se vengono indicati, salva anche lo sconto da
    applicare in fattura (non modifica il preventivo originale, solo come
    viene fatturato). Se era gia' stato fatturato in precedenza, riutilizza
    lo stesso numero, la stessa data e lo stesso sconto gia' salvato (cosi'
    si puo' riscaricare lo stesso PDF piu' volte senza che cambi): eventuali
    nuovi `sconto_tipo`/`sconto_valore` passati qui vengono ignorati in quel
    caso (per cambiare lo sconto va prima annullata la fatturazione).

    Restituisce il preventivo aggiornato (con le sue voci), oppure None se
    il preventivo indicato non esiste.
    """
    preventivo = ottieni_preventivo_completo(preventivo_id)
    if preventivo is None:
        return None

    if not preventivo.get("numero_fattura"):
        numero_fattura = prossimo_numero_fattura()
        data_fattura = date.today().isoformat()

        connessione = ottieni_connessione()
        connessione.execute(
            """
            UPDATE preventivi
            SET numero_fattura = ?, data_fattura = ?, stato = 'fatturato',
                sconto_tipo = ?, sconto_valore = ?
            WHERE id = ?
            """,
            (numero_fattura, data_fattura, sconto_tipo, sconto_valore, preventivo_id),
        )
        connessione.commit()
        connessione.close()

        preventivo["numero_fattura"] = numero_fattura
        preventivo["data_fattura"] = data_fattura
        preventivo["stato"] = "fatturato"
        preventivo["sconto_tipo"] = sconto_tipo
        preventivo["sconto_valore"] = sconto_valore

    return preventivo


def annulla_fattura(preventivo_id: int) -> None:
    """
    Annulla la fatturazione di un preventivo: rimuove numero, data e
    l'eventuale sconto della fattura, riportando lo stato a 'preventivo'.
    Il preventivo stesso non viene toccato.
    """
    connessione = ottieni_connessione()
    connessione.execute(
        """
        UPDATE preventivi
        SET numero_fattura = NULL, data_fattura = NULL, stato = 'preventivo',
            sconto_tipo = NULL, sconto_valore = NULL
        WHERE id = ?
        """,
        (preventivo_id,),
    )
    connessione.commit()
    connessione.close()


def elimina_preventivo(preventivo_id: int) -> None:
    """Elimina definitivamente un preventivo e tutte le sue voci di spesa."""
    connessione = ottieni_connessione()
    connessione.execute("DELETE FROM preventivi WHERE id = ?", (preventivo_id,))
    connessione.commit()
    connessione.close()
