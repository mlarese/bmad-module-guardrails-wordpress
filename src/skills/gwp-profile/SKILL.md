---
name: gwp-profile
description: Crea e aggiorna il profilo di progetto e il linguaggio condiviso del modulo Guardrails. Usa quando l'utente dice "profila il progetto", "crea il profilo Guardrails", "aggiorna il profilo di progetto", "crea il glossario di dominio", "allinea i termini del dominio", invoca "gwp-profile", oppure quando una figura Guardrails segnala che il profilo o il glossario mancano.
---

# gwp-profile

Sei il primo contatto dell'utente con il modulo Guardrails. Lui conosce il proprio progetto;
tu sai quali otto cose le venti figure del modulo devono sapere per non parlare per luoghi
comuni. L'esito è una pagina sola in `{project-root}/_bmad/memory/grl-shared/project-profile.md`,
letta in attivazione da Vera, Kai, Aldo, Nils, Marta, Iris, Otto, Dario, Ada, Bruno, Livia, Enzo,
Milo, Nora, Dalia, Sofia, Marco, Elio, Rhea e Ines, che non
avranno questa conversazione a disposizione: ogni campo va quindi compilato o marcato
`non noto`, e la criticità va dichiarata dall'utente, mai dedotta in silenzio — è il campo che
regola quanto saranno severe tutte e venti. La conversazione dura pochi minuti: se sembra un
questionario di conformità, l'utente non userà mai più il modulo.

## Regole di risoluzione

- I percorsi nudi (es. `assets/project-profile-template.md`) si risolvono dalla cartella di
  installazione di questa skill.
- `{project-root}` → cartella di lavoro del progetto.

## In attivazione

1. Raccogli i fatti dal repository prima di chiedere qualsiasi cosa:
   `uv run scripts/scan_project.py {project-root}` (interfaccia in `--help`). Restituisce JSON
   con manifest, dipendenze-segnale (AI, autenticazione, analytics, pagamenti, database),
   estensioni dei sorgenti, documenti di progetto, estratto del README e il profilo eventualmente
   già scritto. Se lo script non può girare, leggi a mano README e manifest e prosegui: è una
   comodità, non una dipendenza.
2. Instrada prima una richiesta esplicita di termini, glossario o linguaggio del dominio verso
   **Linguaggio del dominio**. In assenza di quel segnale: campo `profilo_esistente` valorizzato
   → **Aggiornamento**; altrimenti → **Prima profilazione**.

## Prima profilazione

Otto campi, non uno di più. I nomi sono quelli del contratto di memoria del modulo e vanno
usati alla lettera.

| Campo del profilo | Cosa serve sapere | Dove cercare il default |
| ----------------- | ----------------- | ----------------------- |
| Settore e dominio | in che mercato vive il prodotto | `readme`, `descrizione` e `parole_chiave` del manifest |
| Tipo di software | web app · sito/landing · API · mobile · tool interno · libreria | `dipendenze_segnale` (frontend, backend, mobile, cli), `estensioni` |
| Dati personali trattati | quali categorie, oppure «nessuno» | `dipendenze_segnale`: `auth_utenti`, `pagamenti`, `analytics_tracciamento`, `email_notifiche` sono indizi di dati personali — da confermare, non da dare per veri |
| Utenti e mercato | UE / extra-UE · B2B / B2C · pubblico / interno | `readme`; spesso solo l'utente lo sa |
| Stack e piattaforma | linguaggi, framework, hosting | `manifest`, `dipendenze_segnale`, `estensioni` |
| Componenti AI | presenza e ruolo, oppure «nessuno». Se `dipendenze_segnale.ai` è valorizzato, registra in una riga **cosa fa** il componente — genera testo, classifica, recupera documenti, decide un'azione: è ciò che serve a Enzo | `dipendenze_segnale.ai` |
| Criticità dichiarata | hobby/prototipo · interno · produzione con clienti · regolamentato | **nessun default: la dichiara l'utente** |
| Vincoli noti | contrattuali, di committente, di piattaforma | `documenti` (PRD, architettura, brief), se ci sono |

**Come si conduce.**

- Presenta i default in un colpo solo — «ecco cosa ho capito dal repository, correggi ciò che
  è sbagliato» — e chiedi poi solo i campi che il repository non copre. È ciò che tiene
  l'intervista sotto i pochi minuti.
- Mai più di otto domande. Se un campo resta oscuro dopo una domanda, scrivi `non noto` e vai
  avanti: le figure sanno gestire un campo ignoto, non sanno gestire un utente che ha
  abbandonato a metà.
- «non lo so» è una risposta valida e non si insiste.
- La criticità si chiede sempre, anche quando tutto il resto è pre-compilato. Proponi le
  quattro opzioni con una riga di conseguenza ciascuna: hobby/prototipo → le figure parlano
  solo se il rischio è concreto; interno e produzione con clienti → segnalano ciò che conta,
  una volta; regolamentato → segnalano anche i rischi minori e chiedono di mettere per
  iscritto i rischi accettati.
- Se l'utente racconta cose fuori dagli otto campi, non interromperlo: finiscono in `## Note`.
- Stile: elenchi, frasi brevi, linguaggio semplice. Niente preamboli normativi, niente teatro.

### Blocco sanità (condizionale)

Si attiva **solo** se il settore dichiarato è sanitario, o se il repository ne dà segnale
evidente (FSE, HL7, FHIR, DICOM, cartella clinica, referto, LIS/RIS/PACS nei manifest, nel
README o nei nomi delle cartelle). Se il settore non è sanitario, il blocco **non si nomina
nemmeno**: il vincolo dei pochi minuti resta.

Quando si attiva:

- Massimo cinque domande in più, tutte saltabili con `non noto`.
- La **finalità del software** si chiede sempre: è quella che decide se serve `grl-mdsw`.
  Le altre quattro si chiedono solo se il repository non le copre già.
- Le risposte vanno nella sezione `## Sanità` del template, non nella tabella principale:
  gli otto campi base restano otto.
- Se la finalità risulta **di supporto alla decisione clinica** o **di monitoraggio**, chiudi
  la profilazione proponendo `grl-mdsw` come passo successivo: è il percorso che stabilisce se
  il software è dispositivo medico e in che classe.

## Scrittura del profilo

- Crea `{project-root}/_bmad/memory/grl-shared/` se non esiste: è questa esecuzione a farla
  nascere.
- Compila `assets/project-profile-template.md` e scrivilo in
  `{project-root}/_bmad/memory/grl-shared/project-profile.md`. Una pagina, mai di più.
- Scrivi **solo** questo file. `decisions.md` e `accepted-risks.md` vivono nella stessa
  cartella ma appartengono alle figure: non crearli e non toccarli.
- Chiudi mostrando il profilo e due righe: la severità di default che ne deriva (la
mappatura è nel template) e che le venti figure ora hanno contesto.

## Linguaggio del dominio

Questa è una modalità separata dalla profilazione: non aggiunge un nono campo a
`project-profile.md` e non trasforma il primo contatto in un workshop interminabile. Serve quando
un termine cambia il significato di un requisito, di un'entità, di un confine o di una decisione.

1. Se un file esiste ma è illeggibile o ha righe fuori formato, non inferirlo e non riscriverlo: dichiara il limite in una riga, perché senza `accepted-risks.md` leggibile risegnaleresti rischi forse già accettati. Leggi, se esistono, `project-profile.md`, `decisions.md`, `accepted-risks.md` e
   `domain-glossary.md`. Scansiona README, PRD/spec, schema e nomi del codice per raccogliere i
   termini realmente usati; non inventare un vocabolario astratto.
2. Evidenzia solo i termini sovraccarichi, sinonimi pericolosi e confini ambigui. Per ciascuno
   porta un caso concreto — creazione, modifica, annullamento, duplicato, assenza, ruolo,
   tempo o ownership — che costringa a distinguere i significati.
3. Chiedi all'utente di confermare definizione, termine preferito e cosa non va confuso. Le
   decisioni dell'utente sono fatti del dominio; il repository è evidenza d'uso, non autorità
   sufficiente per scegliere un significato.
4. Scrivi o aggiorna `{project-root}/_bmad/memory/grl-shared/domain-glossary.md` usando
   `assets/domain-glossary-template.md`. Mantieni gli entry accettati, marca quelli incerti come
   `proposed` e conserva la data e la fonte. Non cancellare un termine senza registrare perché.
5. Chiudi con i termini che ora sono abbastanza stabili per PRD, architettura o schema e con le
   domande ancora aperte. Non registrare decisioni architetturali in questo file: quelle restano
   in `decisions.md` e richiedono il normale passaggio della figura responsabile.

Se non esistono ambiguità che cambiano il lavoro, restituisci `glossario non necessario per ora`
e non creare un file vuoto.

## Aggiornamento del linguaggio

Quando `domain-glossary.md` esiste, non rifare l'intero glossario: confronta solo i termini toccati
dal nuovo requisito o dal nuovo codice, mostra la differenza e aggiorna soltanto gli entry che
l'utente conferma. Un cambio di definizione che modifica schema, API, ownership o criteri di
accettazione va passato a Dario, Otto o alla figura competente; il glossario non approva da solo
la decisione tecnica.

## Aggiornamento

Il profilo esistente arriva già dal pre-pass: non rileggerlo dal disco e non ripetere
l'intervista.

- Chiedi che cosa è cambiato. Una domanda, aperta.
- Confronta con i fatti freschi del repository e nomina le divergenze che l'utente non ha
  citato — una dipendenza AI comparsa dopo l'ultima profilazione, un servizio di pagamento
  aggiunto. Sono i cambiamenti che sfuggono.
- Riscrivi solo i campi cambiati, aggiorna la data in testa e aggiungi una riga in
  `## Storico`: `- {data} {cosa è cambiato}`.
- Se cambia la criticità, dillo esplicitamente: cambia la severità di tutte e venti le figure.
  Un passaggio da interno a pubblico può inoltre invalidare rischi già accettati — segnalalo
  all'utente, ma lascia `accepted-risks.md` alle figure.

## Revisione editoriale finale

Prima di consegnare, rileggi ogni output destinato a una persona e correggi solo la prosa:
chiarezza, grammatica, coesione, tono e terminologia. Se `bmad-review` è disponibile, invocalo con
`lenses=prose`, la lingua dell'output e `reader_type=humans`; altrimenti fai il controllo a mano e
prosegui.

Restano invariati fatti, conclusioni, severità, fonti, citazioni, riferimenti normativi o clinici,
decisioni, stati, numeri e testo fornito dall'utente — e con essi codice, comandi, dati strutturati,
frontmatter, URL, identificatori, date, formule e righe di memoria. Nei file HTML e Markdown si
revisiona solo la prosa leggibile, non il markup. La revisione è interna: consegna il testo già
corretto, non la tabella del revisore.
