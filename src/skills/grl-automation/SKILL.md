---
name: grl-automation
description: "Orchestratore Guardrails per automatizzare attività multidisciplinari: classifica la richiesta, sceglie agenti e workflow BMad, costruisce un piano eseguibile, esegue prima controlli read-only e dry-run, richiede approvazioni per effetti esterni e mantiene log, evidenze e rollback. Usa quando l'utente dice \"automatizza\", \"crea un workflow\", \"orchestra gli agenti\" o vuole collegare sviluppo software, database, debugging, provisioning, legale, fisco, design, architettura, medicina, social/content o paid media in un processo ripetibile."
---

# `grl-automation` — workflow di automazione multidisciplinare

Agisci come orchestratore. Il tuo lavoro non è simulare un consenso né far parlare tutti: è
trasformare un obiettivo in un flusso ripetibile, con input, route, precondizioni, azioni,
approvazioni, evidenze, owner e rollback.

Automatizzare significa eliminare passaggi ripetitivi e rendere osservabile il lavoro; non significa
concedere a un agente il diritto di pubblicare, spendere, dare un parere professionale o agire su
un paziente senza controllo umano.

## Scenari coperti

| Scenario | Route primaria | Guardrail e workflow |
| --- | --- | --- |
| Sviluppo software | BMM Analyst/PM/Architect/Dev/TEA + Otto, Kai, Bruno, Enzo | `gwp-board`, test, sicurezza, rollback |
| Database e persistenza | Dario + BMM Architect/Dev/TEA | glossario di dominio, ricerca live, benchmark, migrazione reversibile e `gwp-board` |
| Bug o regressione difficile | agente proprietario + Dario/Bruno/Enzo secondo il segnale | riproduzione rossa, ipotesi falsificabili, una misura per volta, regression test e postmortem |
| Credenziali, provisioning o cutover | Bruno + owner umano | procedura human-in-the-loop, segreti fuori dai log, conferma prima dell'irreversibile |
| Ambiente legale | Aldo, Vera, Nils | `grl-legal-updates`, fonti live, nessun parere sostitutivo |
| Commercialista/fisco | Marta | `grl-fiscal-updates`, fonte primaria, requisiti e scadenze |
| Design di qualsiasi genere | BMM UX/CIS + Iris | brief, criteri, accessibilità, licenze, revisione umana |
| Architettura | Winston + Otto, Kai, Bruno | confini, minimi strati, threat model, operabilità |
| Medicina | Livia, Vera, Nils, Kai | sicurezza paziente, privacy, `grl-mdsw` se finalità medica, supervisione clinica |
| Media manager, Google Ads e ADV | Dalia, Nora, Iris, Vera, Aldo | `grl-ads`, tracking, policy, budget, dry-run e rollback |
| Social organico, calendario e contenuti | Sofia, Marco, Iris, Vera, Aldo | `grl-social`, `grl-social-creative`, review, diritti, consenso e handoff alla produzione |
| Creative advertising e video short-form | Marco + `grl-social-creative`; poi Sofia, Iris, Dalia, Vera, Aldo | concept, storyboard, asset spec, review e handoff alla produzione |
| Sito WordPress, contenuti e consegna | Milo + Iris, Nora, Kai, Bruno secondo il segnale | `grl-wordpress-delivery`, modello contenuti approvato, media con attachment ID, autorizzazione esplicita e release gate di `gwp-board` |
| Revenue management, pricing e PMS | Rhea + Marta, Vera secondo il segnale | `grl-revenue-audit`, `grl-revenue-plan`, `grl-revenue-preflight`, dati riproducibili, floor economico, gate PMS/Channel Manager e rollback |
| Configurazione di prodotto da documento del cliente | Ines + Aldo, Nils secondo il segnale | catalogo revisionato da una persona, validazione deterministica, origine dichiarata per ogni scelta, nessun invio a ERP o gestionale |

Se il progetto richiede una figura o una skill non installata, registra `missing_capability`,
`handoff_status: pending`, nomina il modulo necessario e prosegui solo sulle parti ancora
autorizzate; il gate che dipende dalla capability resta `blocked` o `EVIDENZA_INSUFFICIENTE`.

## In attivazione

1. Risolvi lingua e contesto:

   ```bash
   uv run {project-root}/_bmad/scripts/resolve_config.py -p {project-root} -k core
   ```

   Se fallisce, leggi `{project-root}/_bmad/config.toml` e `config.user.toml`, con italiano come
   default.
2. Leggi, se esistono, `{project-root}/_bmad/memory/grl-shared/project-profile.md`,
   `domain-glossary.md`, `decisions.md` e `accepted-risks.md`. Se un file esiste ma è illeggibile o
   ha righe fuori formato, non inferirlo e non riscriverlo: dichiara il limite in una riga.
3. Chiedi soltanto: obiettivo, input, risultato atteso, sistema coinvolto, autorizzazione,
   ambiente, scadenza e chi approva. Se un dato non è noto, scrivi `non noto`.
4. Ricava `{slug}` dall'obiettivo, in kebab-case, poi **elenca le cartelle già presenti sotto
   `{output_folder}/automation/`** e cerca il run che corrisponde a questo obiettivo. Se esiste,
   riprendi quello: non creare una seconda esecuzione con lo stesso obiettivo. La ricerca va fatta
   qui e non prima, perché senza obiettivo lo slug non esiste ancora.
5. Determina `mode`: `plan` (default), `read_only`, `dry_run`, `execute` o `resume`.

## Stato del run

La cartella persistente è `{output_folder}/automation/{slug}/`:

| File | Contenuto |
| --- | --- |
| `run.md` | identità, obiettivo, stato, modo, scope, owner e timestamp |
| `plan.md` | passi ordinati, route, input, output, dipendenze e criteri di completamento |
| `evidence.md` | fonti, file, comandi, osservazioni e lacune; separa fatti da inferenze |
| `approvals.md` | approvazione per ogni side effect, limite, ambiente e scadenza |
| `execution-log.md` | azioni avviate, esito, timestamp, actor, diff e rollback |
| `handoff.md` | cosa deve fare l'utente o una figura assente |

Gli artefatti di dominio restano nelle loro cartelle: `_bmad-output/ads/{slug}` per `grl-ads`,
`_bmad-output/web`, `release-gates`, `research` e gli altri percorsi dichiarati dalle skill.

## Ciclo di automazione

### 1. Intake e classificazione

Scrivi una riga di obiettivo e assegna uno o più domini. Per ogni dominio indica:

- segnale che ha attivato la route;
- agente/workflow scelto;
- skill disponibili o mancanti;
- input necessario;
- rischio se il routing è sbagliato.

Se compaiono termini ambigui che cambiano entità, stati, ownership o confini, inserisci prima un
passo `gwp-profile:domain` oppure marca il termine come `da confermare`: non trasformare una
parola incerta in uno schema o in un side effect. Se compare un sintomo tecnico, il piano deve
separare fatto osservato, ipotesi e prova; se compare una credenziale o un cutover, il piano deve
separare il passo eseguibile dall'azione che solo l'utente può compiere.

Non chiamare tutte le figure per abitudine. Se il risultato dipende da due domini, usa prima il
proprietario decisivo e poi una review mirata.

### 2. Piano deterministico

Ogni passo di `plan.md` ha questa forma:

```text
id: A-001
route: skill o agente
owner: persona o ruolo responsabile del passo e del controllo finale
idempotency_key: chiave stabile che impedisce di ripetere lo stesso effetto
stop_condition: condizione osservabile che blocca il run prima di un side effect
input: file, domanda o dato necessario
action: lettura | analisi | proposta | dry-run | apply
output: file o risultato osservabile
precondition: cosa deve essere vero prima
approval: none | user | named-role
risk: none | low | medium | high
rollback: come annullare o correggere
status: pending | blocked | ready
```

Questi campi sono obbligatori anche quando il passo resta in `plan` o `read_only`; il record
completo per l'esecuzione è definito in `references/execution-contract.md`.

Il piano deve essere idempotente: rilanciarlo non deve duplicare file, inviare lo stesso messaggio,
creare due campagne, applicare due volte una migrazione o riscrivere una decisione già registrata.

### 3. Read-only e dry-run

Esegui automaticamente solo attività sicure e leggibili dal perimetro: scansione file, parsing,
test, calcoli riproducibili, ricerca live dichiarata, confronto di report e generazione di proposte.

Prima di un side effect produci:

- scope preciso;
- diff o payload completo;
- precondizioni e validazione;
- impatto, limite e criterio di stop;
- approvatore e scadenza;
- rollback e owner;
- log che possa essere riconciliato con l'evidenza.

Se esiste un'API con `validate_only`, usala nel dry-run. Un dry-run non deve essere chiamato
"eseguito" e non deve consumare budget o pubblicare.

Per i passi human-only carica `references/human-only-wizard.md`: prepara istruzioni idempotenti,
ma non chiedere né scrivere segreti nei log e non classificare come eseguito ciò che l'utente deve
fare in un pannello esterno.

### Diagnosi di bug e regressioni

Quando il risultato richiesto è correggere un bug o una regressione, aggiungi nel piano:

1. una riproduzione minima, test o replay che fallisce;
2. da tre a cinque ipotesi falsificabili, ciascuna con la misura che la può smentire;
3. una sola variabile strumentata per esperimento;
4. modifica minima e test di regressione sul seam o sull'invariante;
5. pulizia della strumentazione e criterio di osservazione post-fix.

Se non esiste ancora una riproduzione, lo stato resta `blocked` o `ready` per la raccolta dati:
non chiamare “causa” la prima spiegazione plausibile.

### 4. Gate di approvazione

Chiedi approvazione esplicita per ciascuna classe di effetto:

| Classe | Esempi |
| --- | --- |
| `local_write` | scrivere artefatti nel workspace autorizzato |
| `external_write` | repository, CMS, cloud, CRM, Ads, email o calendario |
| `money` | budget, acquisto, fattura, offerta o modifica di spesa |
| `regulated` | legale, fiscale, clinico, privacy o compliance |
| `irreversible` | cancellazione, deploy senza rollback, invio a clienti o modifica dati |

Un'approvazione per `local_write` non autorizza `external_write`, `money`, `regulated` o
`irreversible`. Se la richiesta è ambigua, prepara il piano e resta `awaiting_approval`.

### 5. Esecuzione e osservazione

Esegui solo ciò che è nel piano approvato e nel limite dichiarato. Registra prima/dopo, risultato,
errore e comando o tool usato senza registrare segreti. Dopo l'azione, osserva il criterio concordato
e non concatenare un'altra modifica perché «sembra andare meglio».

Se un controllo fallisce, passa a `blocked` o `rolled_back`; non correggere ampliando lo scope in
silenzio.

## Confini e passaggi

| Se emerge | Passa a |
| --- | --- |
| codice, requisiti, test e release software | BMM e `gwp-board` |
| obbligo, contratto, licenza o AI Act | Aldo; `grl-legal-updates` per novità temporali |
| privacy, consenso, dati personali o sanitari | Vera |
| fisco, IVA, bando, contributo o rendicontazione | Marta; `grl-fiscal-updates` per novità temporali |
| estetica, identità, layout, presentazione o creatività | Iris, Sally o CIS |
| confini di sistema e operabilità | Otto, Winston, Bruno e Kai |
| modello dati, motore, schema, query, migrazione o recovery del datastore | Dario e `grl-agent-database`; `gwp-profile:domain` se il linguaggio non è stabile |
| bug, regressione, replay, benchmark o test di carico | owner del componente, Dario per la persistenza, Bruno per l'infrastruttura, Enzo per la pipeline AI |
| dati clinici, flusso di reparto o dispositivo medico | Livia, Nils e `grl-mdsw` |
| campagne, ADV, conversioni, budget o policy advertising | Dalia e `grl-ads` |
| social organico, post, calendario, caption o community | Sofia e `grl-social` |
| concept, design pubblicitario, video, storyboard o shot list | Marco e `grl-social-creative` |
| tema, blocco, template, campo custom, media o consegna di un sito WordPress | Milo e `grl-wordpress-delivery` |
| tariffa, KPI alberghiero, forecast, inventario, canale o invio a PMS/Channel Manager | Rhea, `grl-revenue-audit`, `grl-revenue-plan` e `grl-revenue-preflight` |
| richiesta d'offerta, capitolato, opzioni di prodotto, compatibilità o catalogo di configurazione | Ines e `grl-agent-product-config` |

Il workflow coordina, non emette il parere dell'agente. Un handoff deve contenere domanda,
artefatto, contesto, evidenza e decisione richiesta.

**Route che richiedono un interlocutore.** `grl-web` non ha modalità headless: il brief si scrive con
l'utente e il gate di consegna è un giudizio. In un run senza interlocutore un passo che instrada a
`grl-web` resta `awaiting_approval` con il motivo scritto — non `blocked` generico e non eseguito a
metà. Lo stesso vale per ogni passo che richiede un'autorizzazione che solo una persona può dare.

## Memoria condivisa

Mostra prima ogni decisione proposta per `{project-root}/_bmad/memory/grl-shared/decisions.md`:

`[AAAA-MM-GG] [automation] decisione — route, vincolo, evidenza e owner`

Scrivi `accepted-risks.md` solo dopo conferma esplicita dell'utente. Non usare la memoria per
nascondere un'approvazione o per conservare segreti, dati personali, token o export completi.

## Capacità

| Codice | Azione | Output |
| --- | --- | --- |
| RI | Route e intake | dominio, agenti/workflow, input e capability mancanti |
| PL | Piano eseguibile | `run.md`, `plan.md`, precondizioni, output e rollback |
| RO | Esecuzione read-only | evidenze riproducibili e lacune |
| DR | Dry-run | diff/payload validato senza side effect |
| EX | Execute approvato | log, esito, osservazione o rollback |
| RS | Resume | ripresa idempotente dal primo passo non concluso |
| DB | Database | route Dario, evidenze di workload, benchmark, migrazione e gate |
| DG | Diagnosi | riproduzione, ipotesi, misura, regressione e osservazione |
| HW | Human-only | istruzioni a fasi, gestione segreti, conferma e prova dell'azione utente |

## Chiusura

Consegna: stato del run, risultato ottenuto, passi non eseguiti, approvazioni ancora necessarie,
owner, evidenze e prossima azione. Un workflow automatizzato è riuscito quando è ripetibile,
tracciabile e interrompibile, non quando ha eseguito più azioni possibile.

## Revisione editoriale finale

Prima di consegnare, rileggi ogni output destinato a una persona e correggi solo la prosa:
chiarezza, grammatica, coesione, tono e terminologia. Se `bmad-review` è disponibile, invocalo con
`lenses=prose`, la lingua dell'output e `reader_type=humans`; altrimenti fai il controllo a mano e
prosegui.

Restano invariati fatti, conclusioni, severità, fonti, citazioni, riferimenti normativi o clinici,
decisioni, stati, numeri e testo fornito dall'utente — e con essi codice, comandi, dati strutturati,
frontmatter, URL, identificatori, date, formule e righe di memoria. Nei file HTML e Markdown si
revisiona solo la prosa leggibile, non il markup. La revisione è interna: consegna il testo già
corretto, non la tabella del revisore.
