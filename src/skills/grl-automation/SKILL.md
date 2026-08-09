---
name: grl-automation
description: Orchestratore Guardrails per automatizzare attività multidisciplinari: classifica la richiesta, sceglie agenti e workflow BMad, costruisce un piano eseguibile, esegue prima controlli read-only e dry-run, richiede approvazioni per effetti esterni e mantiene log, evidenze e rollback. Usa quando l'utente dice "automatizza", "crea un workflow", "orchestra gli agenti" o vuole collegare sviluppo software, legale, fisco, design, architettura, medicina o paid media in un processo ripetibile.
---

## Revisione editoriale finale

Ogni output leggibile da una persona — piano, runbook, stato, handoff o riepilogo — passa da
`bmad-review` con `lenses=prose` se disponibile. Correggi solo la prosa: non cambiare comandi,
configurazioni, dati, fonti, stati, autorizzazioni, decisioni, formule, URL o identificatori.
Se la skill non è disponibile, esegui un controllo manuale equivalente.

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
| Ambiente legale | Aldo, Vera, Nils | `grl-legal-updates`, fonti live, nessun parere sostitutivo |
| Commercialista/fisco | Marta | `grl-fiscal-updates`, fonte primaria, requisiti e scadenze |
| Design di qualsiasi genere | BMM UX/CIS + Iris | brief, criteri, accessibilità, licenze, revisione umana |
| Architettura | Winston + Otto, Kai, Bruno | confini, minimi strati, threat model, operabilità |
| Medicina | Livia, Vera, Nils, Kai | sicurezza paziente, privacy, `grl-mdsw` se finalità medica, supervisione clinica |
| Media manager, Google Ads e ADV | Dalia, Nora, Iris, Vera, Aldo | `grl-ads`, tracking, policy, budget, dry-run e rollback |

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
   `decisions.md` e `accepted-risks.md`.
3. Cerca un run esistente in `{output_folder}/automation/{slug}/`. Se esiste, riprendi quello:
   non creare una seconda esecuzione con lo stesso obiettivo.
4. Chiedi soltanto: obiettivo, input, risultato atteso, sistema coinvolto, autorizzazione,
   ambiente, scadenza e chi approva. Se un dato non è noto, scrivi `non noto`.
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
| dati clinici, flusso di reparto o dispositivo medico | Livia, Nils e `grl-mdsw` |
| campagne, ADV, conversioni, budget o policy advertising | Dalia e `grl-ads` |

Il workflow coordina, non emette il parere dell'agente. Un handoff deve contenere domanda,
artefatto, contesto, evidenza e decisione richiesta.

## Memoria condivisa

Mostra prima ogni decisione proposta per `{project-root}/_bmad/memory/grl-shared/decisions.md`:

`[AAAA-MM-GG] [automation] decisione — route, vincolo, evidenza e owner`

Scrivi `accepted-risks.md` solo dopo conferma esplicita dell'utente. Non usare la memoria per
nascondere un'approvazione o per conservare segreti, dati personali, token o export completi.

## Capabilities

| Codice | Azione | Output |
| --- | --- | --- |
| RI | Route e intake | dominio, agenti/workflow, input e capability mancanti |
| PL | Piano eseguibile | `run.md`, `plan.md`, precondizioni, output e rollback |
| RO | Esecuzione read-only | evidenze riproducibili e lacune |
| DR | Dry-run | diff/payload validato senza side effect |
| EX | Execute approvato | log, esito, osservazione o rollback |
| RS | Resume | ripresa idempotente dal primo passo non concluso |

## Chiusura

Consegna: stato del run, risultato ottenuto, passi non eseguiti, approvazioni ancora necessarie,
owner, evidenze e prossima azione. Un workflow automatizzato è riuscito quando è ripetibile,
tracciabile e interrompibile, non quando ha eseguito più azioni possibile.
