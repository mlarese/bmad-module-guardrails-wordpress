# Matrice di routing di `grl-automation`

Questa matrice è una guida di selezione, non un invito a convocare tutte le figure. Parti dal
segnale decisivo e aggiungi una seconda route solo se modifica la decisione.

| Dominio | Prima route | Seconda route | Gate tipico |
| --- | --- | --- | --- |
| Software | BMM + Otto | Kai, Bruno, Enzo, TEA | test/release `gwp-board` |
| Database e persistenza | Dario + BMM Architect | Otto, Bruno, Kai, Enzo, TEA | workload/glossario, ricerca live, benchmark, migrazione e release `gwp-board` |
| Bug o regressione tecnica | owner del componente | Dario se tocca dati/query, Bruno se tocca runtime, Enzo se tocca AI | riproduzione rossa, ipotesi falsificabili, regression test |
| Credenziali, provisioning o cutover | Bruno + owner umano | Dario se cambia persistenza, Kai se cambia superficie | procedura human-only, segreto fuori dai log, conferma e rollback |
| Legale | Aldo | Vera, Nils | fonte primaria o review legale |
| Fiscale | Marta | Aldo | fonte primaria, requisiti, data |
| Design | Iris o UX/CIS | `grl-web`, Nora | brief, accessibilità, licenze |
| Architettura | Winston + Otto | Kai, Bruno, Enzo | ADR, threat model, rollback |
| Medicina | Livia | Vera, Nils, Kai | sicurezza paziente; `grl-mdsw` |
| Paid media | Dalia + `grl-ads` | Nora, Iris, Vera, Aldo | tracking, policy, budget, approvazione |
| Social organico e contenuti | Sofia + `grl-social` | Marco, Iris, Nora, Vera, Aldo | brief, calendario, review, diritti, consenso, nessuna pubblicazione implicita |
| Creative advertising e short-form video | Marco + `grl-social-creative` | Sofia, Iris, Dalia, Vera, Aldo | concept, storyboard, asset spec, review e handoff alla produzione |

Se una domanda attraversa due righe, lascia scritto il motivo del passaggio e quale figura ha il
verdetto decisivo.
