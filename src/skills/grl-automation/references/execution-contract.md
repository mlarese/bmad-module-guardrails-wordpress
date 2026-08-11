# Contratto di esecuzione

## Stati ammessi

`draft`, `pending`, `ready`, `blocked`, `awaiting_approval`, `dry_run`, `applied`, `observing`,
`rolled_back`, `closed`, `EVIDENZA_INSUFFICIENTE`.

Questo elenco è l'unico: vale per il piano, per il singolo passo e per i gate. `blocked` dice che
qualcuno o qualcosa ferma il passo; `EVIDENZA_INSUFFICIENTE` dice che manca la prova per decidere.

Non saltare da `draft` a `applied`. Un passaggio deve avere evidenza nel log.

## Record minimo

```yaml
run_id: automation-...
mode: plan | read_only | dry_run | execute | resume
scope: sistema e risorse esatte
actor: utente o agente
owner: persona o ruolo responsabile del run e del controllo finale
idempotency_key: chiave stabile per evitare di ripetere lo stesso effetto
stop_condition: condizione osservabile che interrompe il run prima di un side effect
approval:
  class: local_write | external_write | money | regulated | irreversible
  by: persona o ruolo
  at: timestamp
  expires_at: timestamp
precondition: controllo eseguito
before: snapshot o hash, quando possibile
action: descrizione e payload senza segreti
after: risultato osservato
rollback: comando o azione inversa
evidence: path, URL, run ID o output
status: stato ammesso
```

## Cosa non automatizzare senza un percorso dedicato

- invio di comunicazioni esterne;
- spesa, budget, ordini, campagne o pubblicazione di annunci;
- cancellazioni o migrazioni senza snapshot e rollback;
- decisioni cliniche, referti, prescrizioni o abilitazioni ad agire su un paziente;
- pareri legali/fiscali o accettazioni di compliance presentati come definitivi;
- caricamento di dati personali, sanitari, liste clienti o credenziali.
