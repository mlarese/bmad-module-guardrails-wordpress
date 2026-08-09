---
name: gwp-setup
description: Installa il modulo Guardrails in un progetto. Usa quando l'utente chiede di installare il modulo grl, configurare Guardrails, registrare le figure Guardrails, o dice "setup Guardrails".
---

## Revisione editoriale finale

Ogni output destinato a una persona — risposta in conversazione, riepilogo, digest, profilo o testo
visibile di una pagina — passa da un controllo di prosa prima della consegna.

- Invoca `bmad-review` con `lenses=prose` se disponibile, impostando la lingua dell'output, la
  guida di stile del progetto e `reader_type=humans`; se l'output contiene più lingue, revisiona ogni lingua
  separatamente.
- Applica solo correzioni di chiarezza, grammatica, coesione, tono e terminologia. Non cambiare
  fatti, conclusioni, severità, fonti, citazioni, riferimenti normativi o clinici, decisioni o testo
  fornito dall'utente.
- Lascia invariati codice, comandi, YAML/JSON/TOML/CSV, frontmatter, URL, identificatori, date,
  formule, dati strutturati e righe di memoria. Nei file HTML/Markdown revisiona solo la prosa
  leggibile, non markup e struttura.
- La review è interna: consegna il testo già migliorato, non la tabella del revisore. Se la skill
  non è installata, esegui un controllo manuale equivalente e prosegui; non installare Freya per
  questo passaggio.

# Setup del modulo Guardrails

Installi Guardrails in un progetto: la registrazione delle figure nel roster degli agenti, l'installazione delle stanze tematiche di party mode e la
proposta del passo di profilazione. L'esito che conta non è il file di config — è che l'utente
sappia come eseguire `gwp-profile`, perché senza profilo di progetto le figure parlano per luoghi
comuni; il profilo non viene eseguito senza accettazione esplicita.

Identità del modulo e roster stanno in `./assets/module.yaml`: leggilo, non dedurli.

## Regole di risoluzione

- I percorsi nudi (es. `./scripts/register-agents.py`) si risolvono dalla cartella di
  installazione di questa skill.
- `{project-root}` è un **token letterale** nei *valori* di configurazione: nei file di config
  si scrive così com'è, perché segnala che il percorso è relativo alla radice del progetto.
  Negli **argomenti degli script** (`--project-root`, `--config-path`, `--target`, …) è invece
  un percorso vero: risolvilo alla radice reale prima di eseguire, altrimenti gli script si
  fermano con un errore.

## In attivazione

1. Leggi `./assets/module.yaml`: `code` (`grl`), identità e blocco `agents`.
2. Riconosci il formato di configurazione del progetto — decide tutto il resto:
   - `{project-root}/_bmad/config.toml` esiste → **installazione TOML** (BMad 6.10+), il caso
     normale. Segui *Percorso TOML*.
   - esiste solo `{project-root}/_bmad/config.yaml` → **installazione YAML**, più vecchia.
     Segui *Percorso YAML*.
   - non esiste né l'uno né l'altro → il progetto non ha un'installazione BMad. Dillo e fermati.
3. Se il config contiene già una sezione `grl`, avvisa che questa è una riconfigurazione, non
   una prima installazione.
4. Procedi senza domande di configurazione. La severità si deriva dalla criticità dichiarata nel
   profilo di progetto, che è il posto dove quell'informazione appartiene. Se il profilo manca,
   il default operativo resta `normal` e il setup propone `gwp-profile`.

Tutto il resto del contesto (settore, dati trattati, mercato, stack e vincoli) vive nella memoria
condivisa del progetto, non nella configurazione: la config è unica per installazione, il profilo
cambia da progetto a progetto.

## Percorso TOML

Un solo comando registra il roster. Risolvi `{project-root}` prima di eseguirlo.

```bash
python3 ./scripts/register-agents.py \
  --project-root "{project-root}" \
  --module-yaml ./assets/module.yaml

python3 ./scripts/merge-party-groups.py \
  --project-root "{project-root}" \
  --source ./assets/party-groups.toml
```

Cosa fa, e perché così:

- **Roster** → `{project-root}/_bmad/custom/config.toml`, una tabella `[agents.grl-agent-*]`
  per figura. È il passo che porta le figure nel party mode: `resolve_party.py` costruisce
  la stanza di default dagli agenti registrati nel config, senza filtrare per modulo o per team.
  Si scrive nel layer `custom/` perché `_bmad/config.toml` e `_bmad/config.user.toml` sono
  rigenerati dall'installer a ogni installazione, mentre `custom/` non viene toccato mai.
- I metadati delle figure sono letti dai `customize.toml` delle skill installate, che restano
  la fonte di verità; `--module-yaml` serve solo da ripiego se le skill non si trovano su disco.
- I gruppi tematici vengono scritti in `{project-root}/_bmad/custom/bmad-party-mode.toml`.
  Il merger sostituisce solo il blocco marcato da Guardrails e preserva gli override e i gruppi
  creati dall'utente fuori da quel blocco.
- Le scritture sono anti-zombie e idempotente: le tabelle `grl` precedenti vengono rimosse prima
  di riscrivere, e il risultato viene riparsato prima di toccare il disco.

Poi registra le voci di help **nel catalogo che BMad legge davvero**:

```bash
python3 ./scripts/merge-help-csv.py \
  --target "{project-root}/_bmad/_config/bmad-help.csv" \
  --source ./assets/module-help.csv \
  --module-code Guardrails
```

Tre cose da sapere, tutte verificate sul campo:

- **Il catalogo è `_bmad/_config/bmad-help.csv`**, non `_bmad/module-help.csv`. È il file che
  `bmad-help` dichiara di leggere («assembled manifest of all installed module skills»), ed è
  quello in cui compaiono le voci di Core, BMad Method e BMad Builder. Scrivere solo in
  `_bmad/module-help.csv` — come fa il comando del template generico — lascia le voci in un file
  che nessuno consulta.
- **La colonna `module` porta il nome leggibile del modulo**, `Guardrails`, non il codice `grl`:
  è la convenzione del catalogo, dove gli altri moduli compaiono come `Core`, `BMad Method`,
  `BMad Builder`. Da qui `--module-code Guardrails`, che è anche la chiave con cui le righe
  vecchie vengono rimosse prima di riscrivere.
- **Niente `--legacy-dir`.** Quel flag non migra nulla: cancella `{project-root}/_bmad/core/module-help.csv`
  e `{project-root}/_bmad/{codice}/module-help.csv`. Sul CSV del core significa **perdere le voci
  di help del core** senza averle prima copiate altrove. Se il tuo progetto ha già subìto questa
  cancellazione, il file si recupera da un'altra installazione BMad o reinstallando.

Limite dichiarato, non nascosto: `_bmad/_config/` è gestito dall'installer e viene rigenerato a
ogni installazione o aggiornamento di BMad. Le voci di Guardrails vanno quindi riscritte dopo un
reinstall — basta rieseguire questo setup.

Se il comando esce con codice diverso da zero, mostra l'errore e fermati.

**Non eseguire `./scripts/merge-config.py` su un'installazione TOML**: scrive `config.yaml`, che
il resolver a quattro layer non legge — la configurazione finirebbe in un file che nessuno guarda.

**Verifica prima di dichiarare fatto.** Il roster va controllato, non dato per scritto:

```bash
python3 {project-root}/_bmad/scripts/resolve_config.py -p "{project-root}" -k agents
```

Devono comparire tutte le chiavi `grl-agent-*` accanto agli agenti già installati. Se
mancano, il party mode non le vedrà: mostra l'output e fermati, invece di chiudere il setup.

Non serve una verifica separata della severità: le figure la derivano dal profilo condiviso,
non dal config del modulo.

## Percorso YAML

Su un'installazione più vecchia valgono gli script generici del template. Nella procedura
normale, che non migra configurazioni legacy, usa i target YAML condivisi senza `--legacy-dir`:

```bash
python3 ./scripts/merge-config.py --config-path "{project-root}/_bmad/config.yaml" --user-config-path "{project-root}/_bmad/config.user.yaml" --module-yaml ./assets/module.yaml --answers {file-temp}
python3 ./scripts/merge-help-csv.py --target "{project-root}/_bmad/module-help.csv" --source ./assets/module-help.csv
python3 ./scripts/merge-party-groups.py --project-root "{project-root}" --source ./assets/party-groups.toml
```

Questi comandi non cancellano i vecchi file per-modulo. Se esistono configurazioni o cataloghi
legacy, lasciali intatti e segnala che resta una migrazione da fare. Aggiungi `--legacy-dir` solo
quando l'utente ha chiesto esplicitamente quella migrazione e hai verificato i file da trasferire:
il flag legge i valori legacy come fallback e, dopo un merge riuscito, li elimina. Non usarlo
solo perché l'installazione è YAML.

Il file temporaneo delle risposte può avere una sezione `module` vuota (più una chiave `core` se
i valori di base non sono ancora stati raccolti); i valori conservano il token `{project-root}`
letterale.

Avverti però l'utente di un limite reale: `merge-config.py` scrive la sezione del modulo ma
**non** la tabella degli agenti. Su un'installazione YAML le figure vanno quindi registrate
con il meccanismo di quella versione di BMad, altrimenti non compaiono nel party mode.
`register-agents.py` non copre questo caso e lo dichiara invece di fingere.

## Cosa il setup non fa

- **Non crea `{project-root}/_bmad/memory/grl-shared/`.** La crea `gwp-profile` alla prima
  esecuzione, quando ha qualcosa da scriverci. Una cartella vuota in `_bmad/memory/` è rumore.
- **Non imposta una stanza di default.** Le figure restano nella stanza principale insieme
  agli agenti BMM; in più `gwp-setup` installa stanze tematiche richiamabili con
  `bmad-party-mode --party <id>`. Il default resta quello deciso dal progetto o dal team.
- **Non tocca le skill BMM.** Vedi il passo facoltativo qui sotto.

## Chiusura

1. Mostra cosa è stato scritto: le figure registrate (nome, icona, titolo), le voci di
   help aggiunte e i file toccati.
2. Mostra il `module_greeting` di `module.yaml`.
3. **Proponi `gwp-profile` e, se l'utente accetta, eseguilo subito.** È il passo che rende utile
   tutto il resto: otto campi, pochi minuti, quasi tutti pre-compilati leggendo il repository.
   L'unico che deve dichiarare l'utente è la criticità del progetto, perché è quella che regola
   quanto saranno severe tutte le figure. Se rifiuta, va bene: digli che ogni figura
   proporrà la profilazione da sé quando troverà il profilo mancante.
4. Nomina il passo **facoltativo e reversibile**, senza eseguirlo: le figure possono essere
   consultate automaticamente dentro i flussi BMM (`bmad-prd`, `bmad-architecture`, `bmad-ux`,
   `bmad-code-review`) aggiungendo override di customizzazione con `bmad-customize` in
   `{project-root}/_bmad/custom/`. Spiega che toccano il comportamento di skill che non
   appartengono a questo modulo, e che si tolgono cancellando il file di override. Non scrivere
   nulla in `_bmad/custom/` per conto tuo: è una scelta dell'utente, da fare quando la vuole.
