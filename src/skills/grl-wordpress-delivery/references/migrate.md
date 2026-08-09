# Migrazione di un sito esistente

Portare un sito già online al modello e ai componenti approvati. Il rischio non è sbagliare un componente: è cancellare qualcosa che nessuno aveva inventariato. Per questo la migrazione produce un piano, lo valida contro la realtà osservata e solo dopo esegue.

`{delivery}` è la cartella della delivery, `{output_folder}/wordpress/{slug}`.

## Piano

Registra in `component-plan.md`, prima di qualunque mutazione:

- l'**inventario** del sito di origine: pagine, custom post type e conteggi, campi, template, menu, slug indicizzati, media con i loro attachment ID;
- la **mappa origine-destinazione**: per ogni elemento dell'inventario, dove finisce nel modello approvato, e con quale trasformazione;
- l'**impatto**: cosa cambia per gli slug indicizzati, per i permalink, per i redirect, per i media già referenziati;
- il **rollback**: da quale snapshot si torna indietro, chi lo esegue, quanto tempo richiede;
- lo **snapshot della sorgente**, che è anche la baseline del confronto dopo il cutover.

Un elemento senza destinazione non è un dettaglio da risolvere strada facendo: è una riga del piano che manca, e finché manca il piano non è validato.

## Validazione

Prima di eseguire, il piano deve reggere contro tre cose, tutte e tre:

- l'**inventario osservato** — ogni voce dell'inventario compare nella mappa, e ogni voce della mappa esiste davvero nell'origine;
- il **modello approvato** in `content-model.md` — ogni destinazione esiste come CPT, campo, componente o template già definito;
- l'**ambito autorizzato** in `delivery.md` — nessuna destinazione cade fuori dal target e dall'ambito registrati.

Il primo confronto lo fa lo script: metti inventario e mappa in due file, e leggi `missing` come le voci inventariate senza destinazione, `unexpected` come le destinazioni che nell'origine non esistono.

```
uv run scripts/snapshot_diff.py --expected <inventario>.json --observed <mappa>.json --keys-only
```

`--keys-only` è obbligatorio qui: inventario e mappa hanno per costruzione le stesse chiavi e valori diversi, perché l'uno descrive l'origine e l'altra la destinazione.

Fai eseguire la verifica di merito a `grl-agent-wordpress`, che sa quali trasformazioni WordPress reggono e quali no, e verifica lo stato con `uv run scripts/check_delivery.py {delivery}`. Se una delle tre non regge, resta `blocked` con il disallineamento in `blockers`: non eseguire una migrazione parziale sperando di correggerla dopo. Se uno dei due script non è eseguibile, la validazione non è avvenuta e la migrazione non parte.

## Esecuzione

Solo dopo una validazione riuscita, e solo con autorizzazione esplicita registrata:

- migra **prima sullo staging**, mai direttamente sul sito live;
- conserva gli slug indicizzati e l'identità degli elementi migrati: un contenuto che cambia identità è un contenuto perso per chi lo aveva linkato;
- prepara il rollback **prima** del cutover e verificane la disponibilità, non solo l'esistenza;
- i media contano come migrati solo dopo aver risolto e registrato i rispettivi attachment ID sul target: la presenza di un URL non è una prova;
- non cancellare niente sul sito live prima del cutover. Una richiesta di «fare prima» cancellando in produzione si rifiuta e si spiega: il costo dell'ordine inverso è un sito rotto senza via di ritorno.

Dopo il cutover, confronta il risultato con lo snapshot della sorgente:

```
uv run scripts/snapshot_diff.py --expected <snapshot-sorgente>.json --observed <snapshot-migrato>.json
```

Ogni differenza va spiegata dal piano o è una regressione. Registra conteggi, mapping, rendering ed esito del rollback in `release-evidence.md`; solo allora la migrazione può passare ai gate di `references/gates.md`.
