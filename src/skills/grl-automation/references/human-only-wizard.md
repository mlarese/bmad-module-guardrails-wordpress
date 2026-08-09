---
name: human-only-wizard
description: Preparare procedure interattive per credenziali, provisioning, migrazioni e cutover che richiedono un'azione umana.
code: HW
added: 2026-08-09
type: prompt
---

# Procedura human-in-the-loop

Usala quando un passaggio richiede credenziali, un pannello web, un account cloud, una conferma
di cutover o un'azione irreversibile che l'agente non deve compiere in autonomia.

## Struttura

Ogni procedura ha:

1. **Prerequisiti**: owner, ambiente, URL o comando, permessi, backup/snapshot e stop condition.
2. **Passi numerati**: una sola azione per passo; apri il contesto prima di chiedere il valore.
3. **Segreti**: inserimento nascosto nel pannello o nel prompt; mai echo, clipboard non
   controllato, Markdown, log o screenshot; il run registra solo `secret_set: true`.
4. **Idempotenza**: verifica se la variabile, il secret o la risorsa esiste prima di crearla;
   aggiorna solo il nome dichiarato e non sovrascrivere valori estranei.
5. **Conferma**: mostra scope, ambiente, impatto e rollback subito prima di deploy, cutover,
   rotazione, cancellazione o prima scrittura.
6. **Prova**: l'utente riporta un esito osservabile — versione, health check, diff, ID del run o
   screenshot senza dati sensibili — e l'automazione lo registra come evidenza.

La procedura può generare uno script o una checklist, ma non simula il click dell'utente, non
conserva credenziali e non concatena automaticamente il passo successivo dopo un'azione
irreversibile. Se il controllo fallisce, torna `blocked` e consegna il rollback previsto.
