# Contratto dello stato della delivery

`delivery.md` è la fonte canonica di una delivery WordPress: quando la chat sparisce, resta questo. Il frontmatter dice dove si è arrivati, il corpo dice come ci si è arrivati.

## Frontmatter

```yaml
schema: grl-wordpress-delivery/v1
slug: ""
intent: create
status: planning
target: ""
release_identity: {version: null, commit: null, artifact: null, digest: null, target: null, content_snapshot: null}
implementation_authorized: false
authorization_scope: ""
artifacts: {content_model: pending, component_plan: pending, media_map: pending, release_evidence: pending}
gates: {substantive_review: pending, prose_review: pending, release: pending}
blockers: []
updated_at: ""
```

I `blockers` si scrivono come lista a blocchi, una voce per riga sotto `blockers:`: una frase ha quasi sempre una virgola dentro, e nella forma inline la virgola separa due voci. Vale per ogni valore con virgole — un `authorization_scope` che nomina due ambienti va fra virgolette.

`slug` coincide con il nome della cartella. `intent` resta `create`, `migrate` o `verify`: `resume` continua quell'intento e non è un valore dello stato. `release_identity.target` deve coincidere con `target`: un candidato congelato per un altro ambiente non vale qui.

| Campo | Valori ammessi |
| --- | --- |
| `artifacts.*` | `pending`, `ready`, `blocked` — più `not-applicable`, ma solo per `content_model` e `component_plan` quando `intent: verify`, dove quei due file non esistono e non sono richiesti |
| `gates.substantive_review` | `pending`, `passed`, `blocked` |
| `gates.prose_review` | `pending`, `passed`, `blocked` |
| `gates.release` | `pending`, `blocked`, `GO`, `GO_CON_CONDIZIONI`, `NO_GO`, `EVIDENZA_INSUFFICIENTE` |
| `status` | `planning`, `awaiting-authorization`, `implementing`, `verification-pending`, `blocked`, `gate-pending`, `release-approved`, `released` |

`gates.release` porta il verdetto restituito da `gwp-board`, non una sua interpretazione. `not-applicable` esiste perché `verify` non approva un modello e non pianifica componenti: senza, quei due artefatti resterebbero `pending` per sempre e nessun gate potrebbe partire.

## La tabella dei media

`media-map.md` porta una tabella con queste intestazioni, in quest'ordine e con queste parole esatte; colonne aggiuntive — di norma `Identità` — sono ammesse:

```markdown
| Asset | Target e binding | Attachment | Identità | Stato | Evidenza |
| --- | --- | --- | --- | --- | --- |
| logo.png | produzione · site-logo | 42 | image/png · 640×320 | verified | GET media/42 |
```

`Stato` vale `pending`, `verified` o `blocked`. `verified` richiede un `Attachment` numerico, un `Target e binding` compilato e un'`Evidenza` non vuota; lo stesso attachment ID non può comparire su due asset diversi. Una tabella che non ha queste colonne non è una delivery senza media: è una delivery di cui non si sa niente, e blocca la promozione.

L'identità attesa si passa come JSON `{"<asset>": {"<campo>": "<valore>"}}` a `check_delivery.py --expected-media`. `attachment` e `filename` si confrontano con la loro cella per uguaglianza; `mime`, `dimensions` e `checksum` si cercano come token interi fra `Identità` ed `Evidenza`, quindi vanno registrati lì.

## Il lock e le transizioni

`.lock` dentro la cartella è tenuto da `scripts/delivery_write.py`, che lo acquisisce, scrive e lo rilascia: non si crea né si cancella a mano.

Quali transizioni siano ammesse lo dice `uv run scripts/check_delivery.py <cartella> --transition-to <stato>`, che quando rifiuta elenca gli stati raggiungibili da quello corrente. Un salto non ammesso è un controllo non fatto: `planning → released` ne salta cinque. Un ritorno all'indietro è legittimo — una correzione che cambia il candidato riporta a `implementing` e i gate a `pending` — ma va scritto come transizione, non applicato in silenzio.

## Evidenza di ogni valore

Ogni valore diverso da `pending` deve poter essere riletto da chi non c'era:

| Valore | Cosa lo prova |
| --- | --- |
| `artifacts.<nome>: ready` | il file corrispondente esiste e contiene il contenuto approvato |
| `gates.substantive_review: passed` | in `release-evidence.md`, l'esito di ogni finding sostanziale: corretto, confutato o accettato |
| `gates.prose_review: passed` | in `release-evidence.md`, sotto un'intestazione `File revisionati`, l'elenco dei path revisionati, e l'esito del confronto delle invarianti |
| `gates.release: <verdetto>` | il path del report di `gwp-board`, che deve esistere come file, e l'identità immutabile a cui si riferisce |
| `status: released` | l'evidenza del deploy o della pubblicazione di quella identità |

Un valore `passed`, `verified`, `release-approved` o `released` senza evidenza citabile è invalido e torna `pending` o `blocked`.

## Cronologia

Nel corpo di `delivery.md` conserva una cronologia append-only di transizioni con data, azione, evidenza e stato risultante. Una correzione aggiunge una transizione compensativa; le righe precedenti non si riscrivono, perché la cronologia è l'unico posto dove si vede che una cosa era stata dichiarata e poi disfatta.
