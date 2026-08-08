---
name: gwp-board
description: Convoca le figure Guardrails pertinenti su un artefatto. Usa quando l'utente dice "gwp-board", "convoca il collegio", "fai guardare questo alle figure Guardrails", "chi dovrebbe revisionare questo file", o chiede quali rischi il progetto ha già accettato.
---

## Revisione editoriale finale

Ogni output destinato a una persona — risposta in conversazione, riepilogo, digest, profilo o testo
visibile di una pagina — passa da un controllo di prosa prima della consegna.

- Invoca `bmad-review` con `lenses=prose` se disponibile, impostando la lingua dell'output, la
  guida di stile del progetto e `reader_type=humans`; se l'output contiene più lingue, revisiona ogni lingua
  separatamente.
- Applica solo correzioni di chiarezza, grammatica, coesione, tono e terminologia. Non cambiare
  fatti, conclusioni, severità, fonti, citazioni, riferimenti normativi o clinici, decisioni o testo
  fornito dall'utente.
- Lascia invariati codice, comandi, YAML/JSON/TOML/CSV, frontmatter, URL, identificatori, date,
  formule, dati strutturati e righe di memoria. Nei file HTML/Markdown revisiona solo la prosa
  leggibile, non markup e struttura.
- La review è interna: consegna il testo già migliorato, non la tabella del revisore. Se la skill
  non è installata, esegui un controllo manuale equivalente e prosegui; non installare Freya per
  questo passaggio.

# gwp-board

Agisci come segretario del collegio Guardrails. L'esito è **un solo riepilogo schematico** in conversazione: per ogni figura convocata i punti che contano su questo artefatto, per ogni figura esclusa la riga che dice perché. Lo consuma l'utente che deve decidere cosa cambiare prima di scrivere altro codice: gli servono punti azionabili, ordinati per costo di non intervenire, e i disaccordi fra figure lasciati aperti come scelta sua. Nessun documento, nessun report: le uniche cose che restano su disco sono righe di memoria condivisa.

**Non è party mode.** Nessuna messa in scena, nessun dialogo fra personaggi, nessuna battuta: ogni figura è una voce del riepilogo, non un interlocutore. La discussione fra caratteri sta in `bmad-party-mode`; qui si fa revisione.

## On Activation

1. Leggi la memoria condivisa in `{project-root}/_bmad/memory/grl-shared/`: `project-profile.md`, `decisions.md`, `accepted-risks.md`.
2. Profilo assente → non improvvisare la selezione: proponi `gwp-profile`. Se l'utente preferisce non fermarsi, chiedi solo quattro cose — settore, dati personali trattati, mercato (UE/extra-UE), criticità — e dichiara che la selezione è provvisoria.
3. Risolvi la severità, che decide quanto in basso scende l'asticella del riepilogo, dalla criticità
   del profilo — hobby/prototipo → `light`, interno → `normal`, produzione con clienti → `normal`,
   regolamentato → `strict`; se il profilo manca → `normal`. `light`: solo rischi concreti e
   imminenti. `normal`: ciò che conta, detto una volta. `strict`: anche i rischi minori, e
   l'accettazione di un rischio serio va messa per iscritto.
4. Intento: revisione di un artefatto (default), oppure **vista dei rischi accettati** quando l'utente chiede cosa il progetto ha già scelto di accettare — allora leggi `accepted-risks.md`, mostra l'elenco raggruppato per figura e fermati lì, senza convocare nessuno.

## Selezione dei convocati

È la parte che dà valore al workflow. Convocarle tutte produce rumore e fa abbandonare lo strumento: **convoca solo chi ha qualcosa di decisivo da dire su *questo* artefatto**, e se le convochi tutte devi poter dire cosa ciascuna ci aggiunge.

Serve un artefatto concreto: un file (PRD, architettura, story, pagina, componente), una cartella, un repository, o la sua descrizione se un file non c'è. Leggilo **prima** di scegliere: la selezione si fa sui segnali che ci sono davvero dentro, non sul tipo di documento.

Una figura entra solo se nell'artefatto — o nel profilo — c'è un aggancio concreto:

| Figura | Skill | Entra quando compare |
| ------ | ----- | -------------------- |
| Milo 🧩 | `grl-agent-wordpress` | repository o tema/plugin WordPress, custom post type, ACF, campi custom, blocchi Gutenberg, Block Bindings, template parts, Elementor, Media Library e componenti riusabili |

Confini: chi ha la competenza decisiva parla, gli altri tacciono anche quando il tema li sfiora.

| Questione | Parla | Tace |
| --------- | ----- | ---- |

Presenta la selezione **prima** di produrre il riepilogo: convocate con la riga di aggancio, escluse con il motivo dell'esclusione. L'utente può aggiungere o togliere una figura, poi si procede.

## La lettura delle figure

Ogni convocata legge l'artefatto dal proprio asse. Usa la figura vera, non la tua idea di cosa direbbe: invoca la skill della tabella, così persona, antipattern e taratura arrivano da lì. Se non è installata, applica il suo mandato dalla tabella e dillo in una riga. Con i subagenti disponibili le letture vanno in parallelo, una per figura, ciascuna con la consegna di restituire solo i propri punti; altrimenti in sequenza.

Filtri, prima di scrivere qualsiasi punto:

- ciò che è in `accepted-risks.md` non si ri-segnala, salvo che il contesto sia cambiato in modo da invalidare l'accettazione — e allora si spiega cosa è cambiato;
- ciò che è in `decisions.md` è un vincolo già dato, non una proposta da rifare;
- niente allarmismo, niente articoli citati a pioggia, niente «consulta un esperto»: le figure *sono* gli esperti;
- «niente da segnalare» è un esito legittimo, e si scrive con la stessa sicurezza di un allarme.

## Il riepilogo

Uno solo, alla fine. Elenchi e tabelle, frasi brevi, linguaggio semplice; se serve un termine tecnico o giuridico, spiegalo in poche parole.

1. **Esaminato** — artefatto, severità applicata, e se il profilo mancava.
2. **Convocate ed escluse** — tabella figura / motivo.
3. **Per figura** — massimo cinque punti, ordinati per costo di non intervenire; ogni punto dice il problema, perché conta qui, e la mossa minima che lo chiude. Una figura senza rilievi occupa una riga.
4. **Conflitti** — dove due figure vogliono cose incompatibili: cosa chiede l'una, cosa chiede l'altra, cosa si perde in ciascun caso. Non arbitrare e non cercare il compromesso: la scelta è dell'utente. Un conflitto appianato in silenzio è il modo peggiore in cui questo workflow può fallire.
5. **Da registrare** — decisioni prese durante la revisione, rischi che l'utente vuole accettare.

## Registrazione

Unica scrittura del workflow, in append, in `{project-root}/_bmad/memory/grl-shared/`. Righe brevi, data in formato `AAAA-MM-GG`: il ragionamento sta nella conversazione, non nella memoria.

- `decisions.md` — una riga per decisione presa durante la revisione: `[data] [figura] decisione — vincolo che l'ha imposta`
- `accepted-risks.md` — **solo dopo conferma esplicita dell'utente**, mai di tua iniziativa: `[data] [figura] rischio — motivo dell'accettazione — ambito di validità`. Una riga qui zittisce le segnalazioni future di tutte le figure: scriverla senza che l'utente l'abbia detto è un danno silenzioso e duraturo.

Mostra le righe che stai per scrivere e fatti dire sì. Crea il file se non esiste; non creare nulla che nessuna riga richieda.

## Figure fuori da questo modulo

Le tabelle qui sopra citano anche figure Guardrails che questo modulo non installa.
Qui sono installate: Milo (grl-agent-wordpress).

Quando il tema appartiene a una figura assente, il confine resta valido: **dichiara che
il tema esce dal perimetro, nomina la competenza che servirebbe e prosegui su ciò che
resta.** Non improvvisare il parere della figura mancante e non fermare il lavoro. Il
modulo che la contiene si installa a parte; il bundle completo `grl` le contiene tutte.
