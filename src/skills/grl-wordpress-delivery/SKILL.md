---
name: grl-wordpress-delivery
description: Coordina una delivery WordPress fino a uno stato e a un release gate verificabili. Usala quando l'utente invoca "grl-wordpress-delivery" o dice "consegna questo sito WordPress", "riprendi la delivery WordPress", "migra questo sito WordPress", "verifica la delivery in sola lettura", "importa i media e registra gli attachment ID", "orchestra la delivery WordPress" o "portala fino al release gate". Non è un release gate generico per progetti non WordPress.
---

# WordPress Delivery

## Overview

Agisci come coordinatore di consegna. Porta un sito WordPress dal modello dei contenuti a una release verificabile. Conserva stato ed evidenze; delega a `grl-agent-wordpress` ogni giudizio e implementazione WordPress senza duplicarne il sapere.

Il consumatore è chi autorizza la messa online senza aver seguito il lavoro: deve poter leggere dallo stato persistito che cosa è stato fatto, su quale target, con quale prova, e cosa manca ancora.

## Resolution rules

- Bare paths e `{skill-root}` (es. `references/gates.md`, `scripts/check_delivery.py`) risolvono dalla directory installata di questa skill.
- `{project-root}` → la directory di lavoro del progetto.
- `{output_folder}` arriva dalla configurazione core e contiene già `{project-root}`: non anteporlo di nuovo.
- `{delivery}` → `{output_folder}/wordpress/{slug}`, la cartella di questa delivery.

## On Activation

Esegui `uv run {project-root}/_bmad/scripts/resolve_config.py -p {project-root} -k core`; se
fallisce, leggi `{project-root}/_bmad/config.toml` e `{project-root}/_bmad/config.user.toml`. Usa
`{output_folder}` o, se assente, `{project-root}/_bmad-output`. Leggi
`{project-root}/_bmad/memory/grl-shared/project-profile.md` se c'è: settore, criticità e mercato
tarano quanto in basso scende l'asticella dei controlli. Se manca, prosegui senza chiederlo.

Ricava l'intento dalla richiesta. Il nome del sito lo normalizza
`uv run scripts/check_delivery.py --slugify "<nome>"`, ed è quella normalizzazione a definire
`{slug}`: due normalizzazioni diverse dello stesso nome creerebbero due delivery per lo stesso
sito. Se lo script non restituisce uno slug valido, chiedi un nome diverso. Su `create` senza un
nome nella richiesta, però, non aprire chiedendolo: prima l'invito qui sotto, e lo slug si
normalizza quando l'utente nomina il sito.

| Intento | Rotta |
| --- | --- |
| `create` | sito nuovo → resta qui |
| `resume` | delivery esistente → la rotta dell'intento ripreso, che non cambia |
| `migrate` | sito già online → `references/migrate.md` |
| `verify` | sola lettura, non muta niente → `references/verify.md` |

Su `resume` senza slug né path, non chiederlo subito: chi torna dopo una settimana ricorda il
sito, non la stringa normalizzata. Elenca le delivery esistenti e fai scegliere:

```
uv run scripts/check_delivery.py --list {output_folder}/wordpress
```

Su `create` e `migrate`, quando c'è un interlocutore e la richiesta non porta già tutto, apri
invitandolo a versare in una volta quello che ha — brief, mockup, elenco delle pagine, CPT e campi,
asset, target, vincoli — e solo dopo chiedi ciò che manca.

Con un interlocutore, prima di dichiarare `artifacts.content_model: ready`, ricapitola in breve
pagine, CPT, campi, componenti e media raccolti e chiedi se manca qualcosa. Vale anche — e
soprattutto — quando la richiesta iniziale sembrava completa: da lì in poi il modello è il vincolo
contro cui si valida il piano, e un requisito ricordato dopo costa un ritorno a `planning`.

Quando la delivery è pronta per i controlli, carica `references/gates.md`: porta il congelamento del candidato e i tre gate. Lo schema completo dello stato — campi, valori ammessi, transizioni e forma dei file — sta in `references/state-contract.md`.

### Headless

Con intento, slug e target ricavabili dalla richiesta o dallo stato persistito, procedi senza
chiedere nulla e registra in `delivery.md` ogni assunzione con la sua provenienza. Su `resume`, se
`--list` restituisce una sola delivery risolvi su quella e registra l'assunzione; se ne restituisce
più d'una, elencale nei `blockers`. Se manca l'intento, il target o
l'autorizzazione che servirebbe, scrivi `status: blocked` ed elenca in `blockers` i campi mancanti.
Chiudi sempre con una riga sola, che l'automatore legge senza interpretare la prosa:

```json
{"status": "complete|blocked", "reason": "<una riga, solo se blocked>",
 "folder": "{delivery}", "verdict": "<gates.release>"}
```

## Stato di lavoro

Ogni delivery vive in `{delivery}`. Se la cartella esiste e contiene `delivery.md`, per qualunque
intento leggilo **prima**, valida la coerenza con gli artefatti e non ricostruire lo stato dalla
chat. Una cartella che non ha `delivery.md` non è una delivery: si può inizializzare. Uno slug già
usato richiede `resume` o uno slug nuovo; stato ambiguo o incoerente è un blocco, non
un'autorizzazione a sovrascrivere.

Ogni scrittura passa dal lock della cartella e da un rename atomico:

```
uv run scripts/delivery_write.py --acquire {delivery}
uv run scripts/delivery_write.py --write {delivery}/<file>.md --from <temporaneo>
uv run scripts/delivery_write.py --release {delivery}
```

Se il lock è occupato, interrompi questa esecuzione: un'altra la sta aggiornando. Se la cartella non
è creabile o scrivibile, resta `blocked` e non dichiarare persistenza.

Mantieni questi file, aggiornandoli solo con fatti osservati:

- `delivery.md` — fonte canonica dello stato;
- `content-model.md` — modello approvato, requisiti aperti e provenienza;
- `component-plan.md` — componenti, dipendenze e stato di implementazione;
- `media-map.md` — asset, attachment ID, alt text per le immagini ed evidenza, nella forma che `references/state-contract.md` fissa;
- `release-evidence.md` — versione candidata, ambiente, controlli, risultati e verdetti.

Prima di ogni transizione di stato, di ogni gate e della promozione, verifica quello che hai
persistito:

```
uv run scripts/check_delivery.py {delivery} [--transition-to <stato>] [--expected-media <file>.json]
```

Mentre la delivery sta nascendo aggiungi `--initializing`, così i file non ancora scritti non
risultano mancanti. Le violazioni si correggono prima di proseguire — tranne quando lo stato è
`blocked`: lì le violazioni che i `blockers` già dichiarano sono la registrazione del blocco, e si
consegnano invece di correggerle. **Un controllo che presidia
una transizione, un gate o la promozione e non è eseguibile è un blocker**: scrivilo in `blockers` e
non passare oltre, perché proseguire a mano restituisce al modello il giudizio che lo script
toglieva, e lo fa dove l'errore non si torna indietro.

## Coordinamento WordPress

Invoca `grl-agent-wordpress` sul materiale reale per produrre o giudicare modello, piano,
implementazione, migrazione, media e verifiche. Passagli il percorso della delivery, il target,
l'intento e l'output richiesto; registra il risultato nei quattro artefatti. Se Milo non è
disponibile, blocca il lavoro che richiede giudizio WordPress: questa skill non lo sostituisce.

`create` e `migrate` pianificano per default. Possono modificare sito o repository solo dopo
un'autorizzazione esplicita, registrata in `delivery.md` come `implementation_authorized: true` con
`authorization_scope`, target e provenienza: la frase con cui l'utente ha chiesto il lavoro non è
un'autorizzazione a eseguirlo, e un'autorizzazione per un altro target non vale per questo.
`resume` la eredita solo finché coincidono intento, target e ambito.

Quando il piano è pronto e nessuno ha ancora autorizzato, scrivi `status: awaiting-authorization` e
chiedi mostrando tre cose: il target, che cosa verrà creato, modificato o cancellato, e quali di
quelle operazioni non sono reversibili. Solo su un sì esplicito registri l'autorizzazione.

Prima di implementare, fai validare a Milo che ogni componente del piano abbia origine nel modello
approvato e destinazione dentro l'ambito autorizzato: un componente che punta a un campo mai
definito si scopre così, e non dopo aver toccato il sito.

Una richiesta fuori dal perimetro dell'intento corrente — una correzione durante `verify`, i
redirect a metà migrazione — si annota fra i requisiti aperti di `content-model.md` con la sua
provenienza e l'intento che la prenderebbe in carico — o in `release-evidence.md` quando l'intento
è `verify`, che quel file non ce l'ha — poi si prosegue: sono requisiti veri, e se restano nella
chat chi autorizza la messa online non li vede.

Un media conta come `verified` solo con un attachment ID osservato su WordPress, l'identità
dell'asset registrata in `media-map.md` e confrontata con `--expected-media`, il binding
verificato sul target corretto e, se è un'immagine, un alt text informativo o una dichiarazione
esplicita di immagine decorativa; campi e forma esatta stanno in `references/state-contract.md`. Non
dichiarare upload, modifiche, deploy o test senza evidenza: un ID presunto o un URL non sono un
attachment.
