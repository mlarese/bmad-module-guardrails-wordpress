# Conoscenza OKF per WordPress

Questa skill usa la wiki OKF personale come prima fonte compilata per le decisioni su WordPress,
Gutenberg, Elementor e ACF. Il file di ingresso è:

`{project-root}/../../development_obsidian/wiki/index.md`

Leggi prima l'indice e poi solo le pagine necessarie:

- `wiki/entities/advanced-custom-fields.md` — ruolo di ACF, versioni e distinzione da Secure
  Custom Fields;
- `wiki/concepts/acf-blocks.md` — `block.json`, `render.php`, ACF Blocks, `usePostMeta` e
  `InnerBlocks`;
- `wiki/concepts/wordpress-block-bindings.md` — collegamento fra campi ACF e attributi dei blocchi
  core, requisiti e limiti del Datastore;
- `wiki/concepts/gutenberg-vs-elementor.md` — criteri strutturali per scegliere o confinare i
  due layer;
- `wiki/concepts/wordpress-postmeta-prestazioni.md` — `wp_postmeta`, `meta_query`, object cache,
  Local JSON e immagini come attachment ID;
- `wiki/sources/wordpress-acf-gutenberg-elementor-summary.md` — sintesi estesa e decisioni
  operative;
- `wiki/sources/acf-documentazione-ufficiale-2026.md` — fatti di versione e limiti verificati,
  con link alle fonti ufficiali.

Regole:

- non leggere tutta la wiki per una domanda puntuale;
- cita nella risposta le pagine OKF usate;
- tratta versioni, requisiti e funzioni opt-in come fatti da verificare, non come eterni;
- se la pagina non copre il tema, dichiaralo e cerca la documentazione ufficiale;
- non modificare mai la wiki da questo progetto.

Decisioni operative già compilate dalla wiki:

- per un campo dentro un blocco core, preferire una Block Binding quando gli attributi sono
  supportati;
- per markup o logica propri, usare un ACF Block con `block.json` e template di render;
- usare Elementor solo dentro un confine esplicito, spesso una landing, e non contaminare i
  template condivisi del tema;
- per immagini e file, preferire l'attachment ID e le API native WordPress che generano URL,
  dimensioni e markup responsive;
- usare Local JSON per versionare lo schema dei gruppi di campi quando il progetto lo consente.
