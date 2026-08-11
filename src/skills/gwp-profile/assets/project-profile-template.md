# Profilo di progetto — {nome-progetto}

Aggiornato: {AAAA-MM-GG} · Scritto da: `gwp-profile` · Unico autore di questo file.

| Campo | Valore |
| ----- | ------ |
| Settore e dominio | {settore e dominio applicativo} |
| Dimensione dell'organizzazione | {dipendenti · fatturato annuo · «non noto»} |
| Tipo di software | {web app · sito/landing · API · mobile · tool interno · libreria · altro} |
| Dati personali trattati | {categorie, oppure «nessuno»} |
| Utenti e mercato | {UE / extra-UE · B2B / B2C · pubblico / interno} |
| Stack e piattaforma | {linguaggi, framework, hosting} |
| Componenti AI | {presenza e ruolo, oppure «nessuno»} |
| Criticità dichiarata | {hobby/prototipo · interno · produzione con clienti · regolamentato} |
| Vincoli noti | {contrattuali, di committente, di piattaforma — oppure «nessuno»} |

La criticità determina la severità di default delle figure Guardrails:
hobby/prototipo → `light` · interno → `normal` · produzione con clienti → `normal` ·
regolamentato → `strict`.

Un campo senza risposta si scrive `non noto`, mai vuoto.

Il linguaggio condiviso del dominio vive separatamente in
`{project-root}/_bmad/memory/grl-shared/domain-glossary.md`, quando serve. Non è un campo del
profilo e non va inventato per completare questa pagina.

## Sanità

{Solo se il progetto è sanitario. Altrimenti si omette la sezione per intero, come `## Note`.}

| Campo | Valore |
| ----- | ------ |
| Finalità del software | {amministrativa · organizzativa · di supporto alla decisione clinica · di monitoraggio · non noto} |
| Contesto d'uso | {studio · poliambulatorio · laboratorio · ospedale · domicilio del paziente · fornitore che vende a strutture} |
| Integrazioni sanitarie | {FSE 2.0 · Sistema TS · ricetta dematerializzata · CUP · LIS/RIS/PACS · nessuna · non noto} |
| Ruolo GDPR | {titolare · responsabile per conto della struttura · non noto} |
| Qualificazione MDR | {esito di `grl-mdsw`, oppure «non valutata»} |

Il ruolo GDPR conta perché cambia chi risponde di cosa: una software house che gestisce il
sistema per conto di una struttura è quasi sempre **responsabile**, non titolare.

Una finalità **di supporto alla decisione clinica** è il segnale che porta al workflow
`grl-mdsw`: è lì che si decide se il software è dispositivo medico e in che classe.

## Note

{Solo se servono: righe brevi su cose che non stanno nella tabella. Altrimenti si omette
la sezione.}

## Storico

- {AAAA-MM-GG} profilo creato.
