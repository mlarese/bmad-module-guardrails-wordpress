# Gate obbligatori della delivery

Tre controlli in sequenza sulla stessa `release_identity`. Non iniziarli mentre un artefatto, un media o un controllo obbligatorio è `pending` o `blocked`.

I perimetri non si sovrappongono: `gwp-board` legge il dossier delle evidenze e il proprio report, non rifà la revisione dei cinque file della delivery. Registra in `release-evidence.md` l'esito di ciascun gate con accanto il perimetro esaminato.

`{delivery}` è la cartella della delivery, `{output_folder}/wordpress/{slug}`. Se uno degli script qui sotto non è eseguibile, il gate che presidia resta bloccato: va scritto in `blockers`, non aggirato a mano.

## 0. Il candidato

Prima dei controlli congela `release_identity`:

```
uv run scripts/release_identity.py --commit <hash> --artifact <file> --digest <sha256> \
  --version <tag> --target <target> [--content-snapshot <revisione>]
```

Ogni mutazione del candidato crea una nuova identità e riporta tutti i gate a `pending`. Se il candidato non può essere identificato esattamente, resta `blocked`: un'etichetta approssimativa non è evidenza di release. Invoca `grl-agent-wordpress` per definire ed eseguire i controlli; separa in `release-evidence.md` fatti osservati, inferenze e punti non verificati.

## 1. Review sostanziale

Invoca `bmad-review lenses=adversarial,edge-case-hunter,verification-gap,structure` su diff o snapshot del candidato e sui cinque file della delivery: la prosa è del gate 2 e non va revisionata qui.

Registra in `release-evidence.md` l'esito di ogni finding sostanziale, in una delle tre forme:

- **corretto** in un candidato con una nuova identità — e allora congela la nuova identità e riparti da qui;
- **confutato** da evidenza citabile;
- **accettato** con una riga del registro condiviso il cui ambito copre candidato, target e ambiente.

Le righe pertinenti del registro le trova lo script, che filtra per identità e target e separa quelle scadute:

```
uv run scripts/accepted_risks.py {project-root}/_bmad/memory/grl-shared/accepted-risks.md \
  --match <commit> --match <target>
```

Se l'ambito di una riga viva copra davvero questo finding resta un giudizio tuo. Registro assente, illeggibile, `rows_matching` vuoto, riga scaduta o riga in `rows_expiry_unclear` significano che il finding non è accettato. Quel registro è memoria condivisa del progetto: la riga si propone, si mostra e si scrive solo dopo un sì esplicito dell'utente, come previsto da `gwp-board`. Una delivery non accetta rischi per conto proprio.

Un finding decisivo irrisolto blocca. Se `bmad-review` non è disponibile o fallisce, blocca: la review è un gate, non una nota.

## 2. Review di prosa

Invoca separatamente `bmad-review lenses=prose` con `reader_type=humans` sui file della delivery destinati alla lettura umana, che sono esattamente questi:

- `content-model.md`
- `component-plan.md`
- `release-evidence.md`
- il corpo di `delivery.md` — la cronologia; il frontmatter non è prosa e resta invariato

Con `intent: verify` restano gli ultimi due: gli altri non esistono. `media-map.md` non entra in nessun caso — è una tabella di fatti, e il gate 1 la copre già con la lente `structure`.

Registra in `release-evidence.md` i path effettivamente revisionati, sotto un'intestazione `File revisionati` seguita dall'elenco: un nome citato dentro una frase non è una dichiarazione, e un elenco parziale con `prose_review: passed` dichiara una copertura che non c'è stata.

Applica soltanto correzioni di prosa. Conserva una copia di ogni file prima della revisione e confronta le due versioni:

```
uv run scripts/snapshot_diff.py --invariants <copia-prima>.md {delivery}/<file>.md
```

Lo script elenca ogni differenza in frontmatter, codice, celle di tabella, URL, date, hash, id e ogni altro token che contenga una cifra. Ogni differenza va annullata, oppure — quando è una correzione di prosa legittima, come un numero scritto in lettere — spiegata in `release-evidence.md`. Un cambiamento sostanziale riporta al punto 1. Se la review fallisce, blocca prima del release gate.

## 3. Release gate

Invoca `gwp-board` con `release-gate {delivery}/release-evidence.md` e la `release_identity` esatta, dopo aver verificato che candidato e target non siano cambiati. Accetta solo `GO`, `GO_CON_CONDIZIONI`, `NO_GO` o `EVIDENZA_INSUFFICIENTE`, e registralo in `gates.release` insieme al path del report, che deve esistere come file, e all'identità a cui si riferisce. Se il gate manca o non identifica candidato e verdetto, imposta `gates.release=blocked`: non simulare il verdetto.

## Promozione

Prima di scrivere `release-approved` verifica lo stato:

```
uv run scripts/check_delivery.py {delivery} --transition-to release-approved
```

Lo script controlla artefatti, media, gate e identità; non può vedere una cosa sola, che il verdetto del gate sia stato emesso per l'identità congelata adesso e non per quella di ieri. Con `GO_CON_CONDIZIONI` registra condizioni, responsabili e scadenze. `released` richiede in più l'evidenza del deploy o della pubblicazione di quella identità.

Eseguire il deploy è fuori dal perimetro di questa skill: la delivery registra l'evidenza di un rilascio avvenuto, non lo esegue e non lo pianifica. Chi deve farlo lo chiede a `grl-agent-ops`.

Il report del release gate resta invariato e costituisce l'ultimo controllo; consegna la sua formulazione già revisionata. Negli altri casi consegna i blocchi reali senza promuovere il candidato.
