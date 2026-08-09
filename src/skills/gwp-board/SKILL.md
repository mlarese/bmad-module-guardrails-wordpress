---
name: gwp-board
description: Convoca il collegio Guardrails su un artefatto. Usa quando l'utente dice "gwp-board", "convoca il collegio", "fai guardare questo alle figure Guardrails", "chi dovrebbe revisionare questo file", "separa standards e spec nella review", "release-gate [path]", o chiede quali rischi il progetto ha già accettato.
---

# gwp-board

## Overview

Agisci come segretario del collegio Guardrails. Nella revisione ordinaria, l'esito è **un solo riepilogo schematico** in conversazione: per ogni figura convocata i punti che contano su questo artefatto, per ogni figura esclusa la riga che dice perché. Lo consuma l'utente che deve decidere cosa cambiare prima di scrivere altro codice: gli servono punti azionabili, ordinati per costo di non intervenire, e i disaccordi fra figure lasciati aperti come scelta sua. Anche la vista dei rischi accettati resta in conversazione. Nessun documento, nessun report: fa eccezione solo `release-gate`, che persiste il proprio report.

**Non è party mode.** Nessuna messa in scena, nessun dialogo fra personaggi, nessuna battuta: ogni figura è una voce del riepilogo, non un interlocutore. La discussione fra personaggi sta in `bmad-party-mode`; qui si fa revisione.

## Resolution rules

- Bare paths e `{skill-root}` (es. `references/selection.md`) risolvono dalla directory installata di questa skill.
- `{project-root}` → la directory di lavoro del progetto.
- `{skill-name}` → il basename della directory della skill.

## On Activation

1. Riconosci l'intento: revisione di un artefatto (default), vista dei rischi accettati, oppure `release-gate [path]`.
2. Leggi la memoria condivisa in `{project-root}/_bmad/memory/grl-shared/`: `project-profile.md`, `domain-glossary.md`, `decisions.md`, `accepted-risks.md`. Per la vista dei rischi, mostra `accepted-risks.md` raggruppato per figura e fermati senza convocare nessuno: sono righe di memoria copiate alla lettera, non prosa da revisionare.
3. Risolvi la configurazione core con `uv run {project-root}/_bmad/scripts/resolve_config.py --project-root {project-root}`: `{communication_language}` è la lingua di ogni output e `{document_output_language}` quella del report del gate. Se fallisce, usa l'italiano e `{project-root}/_bmad-output` come `{output_folder}`.
4. Profilo assente → non improvvisare la selezione: proponi `gwp-profile`. Se l'utente preferisce non fermarsi, chiedi solo quattro cose — settore, dati personali trattati, mercato (UE/extra-UE), criticità — e dichiara che la selezione è provvisoria.
5. Risolvi la severità, che decide quanto in basso scende l'asticella del riepilogo, dalla criticità
   del profilo — hobby/prototipo → `light`, interno → `normal`, produzione con clienti → `normal`,
   regolamentato → `strict`; se il profilo manca → `normal`. `light`: solo rischi concreti e
   imminenti. `normal`: ciò che conta, detto una volta. `strict`: anche i rischi minori, e
   l'accettazione di un rischio serio va messa per iscritto.
6. Per `release-gate` carica `references/release-gate.md`; altrimenti prosegui con la revisione ordinaria.

### Memoria condivisa incompleta

Un file di memoria assente, illeggibile o con righe fuori formato non si inferisce e non si riscrive: nella revisione ordinaria prosegui e dichiara il limite in una riga del riepilogo, perché senza `accepted-risks.md` leggibile segnalerai di nuovo rischi forse già accettati. Il gate ha una regola più stretta e la porta con sé.

### Headless

Senza interlocutore la revisione ordinaria non si ferma: registra selezione ed esclusioni inferite, salta la pausa di conferma e produce il riepilogo. Il profilo assente non blocca — vale la via provvisoria del passo 4 con severità `normal` e la selezione dichiarata provvisoria. Blocca soltanto l'artefatto mancante o illeggibile, perché senza non c'è niente da leggere. Chiudi con una riga sola:

```json
{"status": "complete|blocked", "reason": "<una riga, solo se blocked>", "convocate": [], "escluse": []}
```

Il `release-gate` segue il proprio contratto in `references/release-gate.md` e aggiunge `report` e `verdict` allo stesso ritorno.

## Selezione dei convocati

**Convoca solo chi ha qualcosa di decisivo da dire su *questo* artefatto**; se le convochi tutte, indica cosa ciascuna ci aggiunge.

Serve un artefatto concreto: un file (PRD, architettura, story, pagina, componente), una cartella, un repository, un diff o le modifiche non committate, o la sua descrizione se un file non c'è. Guardalo **prima** di scegliere: la selezione si fa sui segnali che ci sono davvero dentro, non sul tipo di documento. Su una cartella o un repository ti basta la passata che decide gli agganci — alberatura, manifest, intestazioni — non l'intero contenuto: quella lettura è delle figure. Su un diff la selezione guarda i file toccati, e ciò che il diff non tocca resta fuori dal riepilogo.

Il roster — quale figura entra su quale segnale — e i confini fra figure stanno in `references/selection.md`: caricalo prima di scegliere, sia nella revisione ordinaria sia nel release gate. Una figura entra solo se nell'artefatto o nel profilo c'è un aggancio concreto.

Presenta la selezione **prima** di produrre il riepilogo: convocate con la riga di aggancio, escluse con il motivo dell'esclusione. L'utente può aggiungere o togliere una figura, poi si procede.

## La lettura delle figure

Ogni convocata legge l'artefatto dal proprio asse. Usa la figura vera, non la tua idea di cosa direbbe: invoca la skill del roster, così persona, antipattern e taratura arrivano da lì. Se non è installata, applica il suo mandato dal roster e dillo in una riga. Con i subagenti disponibili le letture vanno in parallelo, una per figura, ciascuna con il path dell'artefatto e da leggere per conto proprio; altrimenti in sequenza.

La consegna a ogni figura porta il formato del ritorno, altrimenti torna prosa: **al massimo cinque punti, ordinati per costo di non intervenire, ciascuno con problema, conseguenza nel contesto esaminato e mossa minima; solo quelli, nessun altro testo.** «Niente da segnalare» è un ritorno valido di una riga.

Per un diff di codice, una story/spec o un artefatto che li collega, separa due assi prima di
ordinare i finding:

- **Standards** — comportamento o struttura in conflitto con convenzioni, vincoli di sicurezza,
  testabilità o decisioni già accettate dal progetto;
- **Spec** — comportamento che non implementa il requisito, il criterio di accettazione o il
  contratto dichiarato.

Ogni asse deve citare il punto osservabile che lo prova e non può trasformare una preferenza in un
blocco. Fissa il punto di osservazione — commit, diff, versione dell'artefatto o fixture — così la
review resta ripetibile. Non mescolare un finding di spec con code style, e non proporre un
refactoring solo perché esiste una smell se non cambia il risultato o il costo del progetto.

Filtri, prima di scrivere qualsiasi punto:

- nella revisione ordinaria, ciò che è in `accepted-risks.md` non si segnala di nuovo, salvo che il contesto sia cambiato in modo da invalidare l'accettazione — e allora si spiega cosa è cambiato; nel release gate si elencano i rischi pertinenti e si verifica che il loro ambito copra la release;
- ciò che è in `decisions.md` è un vincolo già dato, non una proposta da rifare;
- niente allarmismo, niente articoli citati a pioggia, niente «consulta un esperto»: le figure *sono* gli esperti;
- «niente da segnalare» è un esito legittimo, e si scrive con la stessa sicurezza di un allarme.
- per codice/spec, mantieni distinti `Standards` e `Spec` anche quando la stessa figura trova
  entrambi; il conflitto fra i due assi resta visibile all'utente.

## Consegna

Per una revisione ordinaria carica `references/review-output.md` e poi `references/final-prose-review.md`. Il ramo `release-gate` possiede invece consegna e registrazione in `references/release-gate.md`; la vista dei rischi accettati termina durante l'attivazione.
