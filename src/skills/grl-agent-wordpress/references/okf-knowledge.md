# Conoscenza WordPress compilata

Le decisioni qui sotto sono già risolte e valgono senza consultare altro. Sono la prima fonte per
scegliere fra Gutenberg, Block Bindings, ACF Blocks ed Elementor.

## Decisioni operative

- per un campo dentro un blocco core, preferire una Block Binding quando gli attributi sono
  supportati;
- per markup o logica propri, usare un ACF Block con `block.json` e template di render;
- usare Elementor solo dentro un confine esplicito, spesso una landing, e non contaminare i
  template condivisi del tema;
- per immagini e file, preferire l'attachment ID e le API native WordPress che generano URL,
  dimensioni e markup responsive;
- usare Local JSON per versionare lo schema dei gruppi di campi quando il progetto lo consente;
- distinguere ACF da Secure Custom Fields: sono due distribuzioni diverse, e la differenza conta
  quando si dichiara una dipendenza;
- su `wp_postmeta` la `meta_query` non scala come un indice: prima di costruirci sopra una lista
  filtrata, verificare object cache, volume delle righe e alternative in tassonomia.

## Bundle OKF di progetto (facoltativo)

Se il progetto contiene un bundle OKF — una cartella `.okf/` nella radice, o un percorso indicato
dall'utente — e la domanda riguarda una decisione WordPress, leggine l'indice e poi solo le pagine
pertinenti. Il bundle è un'aggiunta: senza, le decisioni qui sopra bastano.

Quando esiste, le pagine tipicamente utili portano nomi come `advanced-custom-fields`,
`acf-blocks`, `wordpress-block-bindings`, `gutenberg-vs-elementor` e
`wordpress-postmeta-prestazioni`. Cerca per titolo nell'indice, non per percorso fisso.

Regole:

- non cercare un bundle fuori dal progetto e non risolvere percorsi relativi che escono da
  `{project-root}`;
- non leggere tutto il bundle per una domanda puntuale;
- cita nella risposta le pagine usate;
- tratta versioni, requisiti e funzioni opt-in come fatti da verificare, non come eterni: per
  quelli vale la documentazione ufficiale corrente;
- non modificare mai il bundle da questa skill.
