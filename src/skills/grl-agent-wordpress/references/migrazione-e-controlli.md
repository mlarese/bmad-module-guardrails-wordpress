# Migrazione e controlli di merito

Questa scheda risponde a due domande che un workflow di consegna gira sempre a Milo: **questa
trasformazione regge?** e **cosa prova che il sito è rilasciabile?**

## Migrazione: cosa regge e cosa no

Una migrazione WordPress sposta contenuti, campi e media da un'origine a una destinazione. Il
lavoro non è eseguire lo spostamento — quello lo fa lo script del workflow — ma dire quali
corrispondenze sono sostenibili.

| Trasformazione | Regge | Perché |
| --- | --- | --- |
| Campo di testo → campo di testo dello stesso tipo | sì | nessuna perdita |
| HTML libero → campi custom strutturati | sì, con revisione | il markup va scomposto: dichiara cosa finisce in quale campo e cosa si perde |
| Campi custom → HTML dentro il contenuto | no | è il verso sbagliato: perde struttura e non torna indietro |
| Shortcode di un plugin → blocco core | solo se il blocco copre tutti gli attributi | un attributo scoperto sparisce senza errore |
| URL di media → attachment ID | sì, se il file è nella Media Library di destinazione | senza attachment, l'ID punta al nulla e il template rende vuoto |
| Tassonomia → campo di selezione | no | perde archivi, feed e permalink che qualcuno ha già linkato |
| Template Elementor → template del tema | solo riscrivendolo | non è una conversione: è un rifacimento, e va detto |

Tre controlli prima di autorizzare:

1. **Ogni chiave della mappa esiste nella destinazione.** Una chiave inventata scrive un campo che
   nessun template legge.
2. **Ogni media citato ha un attachment.** Vale la regola di `references/media-library.md`: la
   prova è la rilettura per ID, non l'import riuscito.
3. **Ogni trasformazione ha un verso dichiarato.** Se non si può tornare indietro, va scritto prima,
   non scoperto dopo.

Se uno dei tre non regge, l'esito è `blocked` con il disallineamento nominato. Una migrazione
parziale non si corregge dopo: si è già persa la fonte.

## Controlli di merito prima del rilascio

I controlli che Milo definisce ed esegue riguardano ciò che la sua materia può provare. Ognuno
porta l'evidenza osservata, non l'impressione:

| Controllo | Evidenza |
| --- | --- |
| Ogni componente rende anche con i campi vuoti | la pagina osservata con il campo svuotato, non il codice del fallback |
| Ogni media referenziato esiste | rilettura dell'attachment per ID |
| Ogni immagine ha alt text coerente con la sua classe | elenco informative/decorative, con l'alt letto |
| Nessun valore esce senza escaping | il punto del template, citato |
| Nessuna tecnologia sconfina | i template che mescolano Gutenberg ed Elementor, elencati con il confine dichiarato |
| L'editor può aggiornare ogni contenuto variabile | il campo, e la schermata da cui si aggiorna |

Quello che Milo **non** prova: sicurezza dell'installazione e ruoli (Kai), backup e deploy (Bruno),
dati personali (Vera), accessibilità come obbligo normativo (Nils). Se il gate li pretende, il
verdetto resta sospeso su quella riga e la figura si nomina.
