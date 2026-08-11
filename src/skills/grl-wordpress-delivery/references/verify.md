# Verifica in sola lettura

Constatare che cosa c'è davvero sul target, senza toccarlo. Una verifica che corregge quello che trova non è più una verifica: diventa la prova di sé stessa, e nessuno può più dire in che stato fosse il sito prima.

`{delivery}` è la cartella della delivery, `{output_folder}/wordpress/{slug}`. `verify` non scrive niente sul target e niente fuori da questa cartella; unica eccezione prevista, il report del gate 3, che persiste `gwp-board` nella propria destinazione.

## Baseline

Serve uno snapshot atteso **approvato prima** della lettura: conteggi, template assegnati, voci di menu, attachment ID, campi e valori che il target dovrebbe avere. Deriva dallo stato della delivery o da un'approvazione esplicita, mai dallo stato osservato: se la baseline la scrive l'osservazione, la verifica non può fallire e non prova niente.

Senza baseline approvata la verifica resta `blocked`.

## Lettura

Passa a `grl-agent-wordpress` il vincolo `intent=verify_read_only`: solo letture, nessuna scrittura, nessun upload, nessuna cancellazione, nessuna modifica di opzioni. Prendi uno snapshot del target prima e dopo la lettura, poi confronta:

```
uv run scripts/snapshot_diff.py --expected <atteso>.json --observed <osservato>.json \
  --pre <target-prima>.json --post <target-dopo>.json
```

Il secondo confronto è quello che rende valida la verifica: se `target_mutated` è vero, lo strumento ha alterato ciò che doveva misurare e la verifica va rifatta da uno stato noto. Se lo script non è eseguibile non hai quella prova, e la verifica resta `blocked`.

Una delivery nata per `verify` non approva un modello e non pianifica componenti: `artifacts.content_model` e `artifacts.component_plan` valgono `not-applicable`, e i due file corrispondenti non servono.

## Registrazione

Per ogni differenza registra in `release-evidence.md` valore atteso, valore osservato ed evidenza della lettura. Le correzioni richiedono una delivery con un altro intento — `create` o `migrate` — e una nuova autorizzazione esplicita: se l'utente chiede di sistemare al volo quello che emerge, proponi quel percorso e spiega che qui una mutazione verrebbe registrata come verifica.

Aggiorna lo stato con `uv run scripts/check_delivery.py {delivery}` e prosegui verso i gate di `references/gates.md` solo se tutti i controlli attesi risultano superati; altrimenti la delivery resta con i suoi blocchi reali.
