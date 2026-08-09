# Release gate

Decidi se una release identificata può avanzare in un ambiente e per un perimetro dichiarati. Il consumatore è chi autorizza il rilascio anche senza poter consultare questa conversazione: il report deve rendere verificabili oggetto, prove, blocchi e validità del verdetto.

Il path indica codice o artefatti da esaminare, non l'identità della release. Se manca o non è leggibile, chiedi un path valido; se resta indisponibile, emetti `EVIDENZA_INSUFFICIENTE`.

## Oggetto e collegio

Identifica commit, tag, build o versione; conserva tutti gli identificatori disponibili e privilegia quello immutabile. Fissa un solo ambiente e il perimetro incluso ed escluso.

Il pre-pass fa i controlli esatti — formato e corrispondenza dello SHA-256, etichette mobili, tag che non punta al commit dichiarato, slug e destinazione del report:

```
uv run scripts/release_prepass.py --output-folder {output_folder} \
  --artifact <file> --digest <sha256> --id commit=<hash> --id tag=<tag> \
  --environment "<ambiente>" --scope "<perimetro>" [--repo {project-root}]
```

Interpreta il suo `blocking`: ogni voce è una prova che non regge, non un verdetto. Distingui `identity.well_formed` da `identity.verified`: un hash ben formato che nessuno ha risolto in un repository non è un'identità provata, e le voci in `warnings` vanno dichiarate fra le lacune del report. Identificatori incoerenti sono un blocco; identità, ambiente o perimetro non dimostrabili impediscono `GO`. Se lo script non è eseguibile, esegui gli stessi controlli a mano e dichiaralo nel report fra le lacune.

Usa `{project-root}/_bmad/memory/grl-shared/project-profile.md`, `decisions.md`, `accepted-risks.md`, il diff e i segnali del deploy. Un file di memoria assente, illeggibile o con righe fuori formato non si inferisce: impedisce `GO` e `GO_CON_CONDIZIONI`, e se il rischio accettato è la prova che regge il verdetto porta a `EVIDENZA_INSUFFICIENTE`.

Convoca da una a quattro figure Guardrails installate, ciascuna con un aggancio concreto; una sola figura applicabile è un collegio valido. Roster e confini stanno in `references/selection.md`: caricalo prima di scegliere, anche quando riprendi un gate interrotto. Presenta la selezione prima delle letture e, in modalità interattiva, lascia che l'utente la corregga; in headless registra selezione ed esclusioni e prosegui senza pausa. Un profilo assente o soltanto provvisorio impedisce sia `GO` sia `GO_CON_CONDIZIONI`.

## Evidenze e verdetto

Verifica risultati dei test pertinenti, deploy, rollback, ripristino del servizio e dei dati, rischi applicabili e mitigazioni. Ogni prova deve riferirsi alla release, all'ambiente e al perimetro e portare un riferimento controllabile: comando con esito, run, log, file, URL, hash o timestamp. Una decisione o un rischio accettato vale solo se il suo ambito copre questo gate.

Emetti un solo verdetto:

- `GO`: prove decisive complete, nessun blocco;
- `GO_CON_CONDIZIONI`: nessun blocco o prova decisiva mancante; restano azioni non bloccanti con responsabile, verifica e scadenza futura;
- `NO_GO`: almeno un blocco provato;
- `EVIDENZA_INSUFFICIENTE`: nessun blocco già provato, ma manca identità, ambiente, perimetro o una prova decisiva.

Una prova mancante non diventa una condizione. Il verdetto vale solo per identificatori, ambiente e perimetro riportati; ogni modifica richiede un nuovo gate.

## Stato riprendibile

Il gate attraversa selezione, evidenze, review sostanziale, risoluzione dei finding e review di prosa: se si interrompe a metà, quel lavoro non va perso e non deve somigliare a un verdetto. Tieni un draft in `{output_folder}/release-gates/.draft-{release_slug}-{gate_started_at_utc}.md`, con frontmatter `gate: gwp-board/release-gate/draft`, `verdict: null` e una riga per ogni checkpoint raggiunto (identità congelata, collegio convocato, evidenze raccolte, review sostanziale chiusa, review di prosa chiusa). Aggiornalo a ogni checkpoint.

All'avvio, un draft con la stessa `release_slug` e la stessa identità è il punto di ripartenza: riprendi dal primo checkpoint mancante invece di rifare le letture. Se l'identità è cambiata, il draft è scaduto e il gate riparte da capo. Il draft non è mai la consegna: cancellalo quando il report finale è persistito.

## Report e registrazione

La destinazione è `report.path` del pre-pass: usala come la restituisce, non ricomporla. Se `report.already_exists` è vero, non sovrascrivere un gate precedente: fermati e chiedi un nuovo timestamp. Il frontmatter è questo:

```yaml
---
gate: gwp-board/release-gate/v1
verdict: GO
release_identity: {commit: "", tag: "", artifact: "", digest: ""}
environment: ""
scope: ""
gate_started_at_utc: ""
---
```

Il corpo porta, come sezioni di secondo livello **in quest'ordine**: `Identità e validità`, `Convocate ed escluse`, `Decisioni e rischi applicabili`, `Evidenze e lacune`, `Rilievi e blocchi`, `Condizioni`, `Verdetto e motivazione`. L'ultima sezione apre con la riga `**Verdetto:** <VALORE>`, uguale al frontmatter; sotto, la motivazione resta libera di spiegare perché non è un altro dei quattro.

Persisti tramite file temporaneo e rename atomico, poi valida quello che hai scritto:

```
uv run scripts/check_gate_report.py <report.path>
```

Una violazione va corretta prima della consegna; non dichiarare scritto ciò che non lo è. Se lo script non è eseguibile, verifica a mano frontmatter, presenza e ordine delle sette sezioni, riga del verdetto e scadenze future delle condizioni, e dichiara fra le lacune che la validazione è stata manuale.

Il report non autorizza scritture in memoria. Per aggiungere decisioni o rischi in `{project-root}/_bmad/memory/grl-shared/`, mostra prima le righe e chiedi conferma esplicita; senza conferma non scrivere.

## Le due review

Prima di fissare il verdetto invoca `bmad-review` senza `lenses=` sul diff o snapshot, sul dossier delle evidenze e sulla bozza del report. Risolvi ogni finding sostanziale con una correzione verificata, una confutazione fondata oppure un rischio accettato il cui ambito copre il gate; un finding decisivo irrisolto impedisce `GO` e `GO_CON_CONDIZIONI`. Se la review manca o fallisce, usa `EVIDENZA_INSUFFICIENTE` e registrane il motivo.

Quando contenuto e verdetto sono congelati, conserva una copia del report e invoca separatamente `bmad-review lenses=prose` con output in italiano e `reader_type=humans`. Applica soltanto correzioni editoriali, poi confronta le due copie:

```
uv run scripts/check_prose_invariants.py <copia-prima>.md <report-dopo>.md
```

Ogni differenza in frontmatter, codice, URL, identificatori, date, numeri, righe di memoria o verdetti va annullata: la revisione di prosa cambia come una cosa è detta, non cosa dice. Un cambiamento di fatti, evidenze, condizioni o verdetto riapre la review sostanziale. Se il passaggio di prosa manca o fallisce, non consegnare un gate come completato. Persisti e consegna il report corretto, non i risultati delle review.
