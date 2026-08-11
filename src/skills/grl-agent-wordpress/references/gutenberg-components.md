# Componenti Gutenberg

Scegli il livello minimo che risolve il problema:

- **Blocco core** quando il markup e il comportamento esistono già;
- **Block Binding** quando un singolo campo custom deve alimentare un attributo supportato di un
  blocco core;
- **ACF Block** quando il componente ha markup, dati o logica propri;
- **Pattern, template part o partial** quando il valore è composizione e non nuova logica;
- **InnerBlocks** quando il componente deve contenere blocchi scelti o limitati dal progetto.

Per un ACF Block mantieni il contratto visibile: `block.json` dichiara il blocco, il template PHP
renderizza, gli stili sono separati e i campi appartengono al componente. Usa `render.php` per il
markup dinamico e applica sempre l'escaping adatto al contesto (`esc_html`, `esc_attr`, `esc_url`)
anche se il campo è stato validato in ingresso.

I template devono poter rappresentare almeno:

- contenuto completo;
- campo opzionale assente;
- immagine mancante o attachment non più disponibile;
- lista vuota;
- più istanze dello stesso componente nella stessa pagina, salvo un limite documentato dalla
  tecnologia scelta.

Non creare un blocco custom per un solo titolo o pulsante se una Block Binding risolve il caso.
Non infilare componenti propri nel contenuto libero se devono essere riusati in più template.

Prima di proporre funzioni o requisiti dipendenti da versione, consulta
`references/okf-knowledge.md` e, se il progetto ha un bundle OKF, le sue pagine pertinenti; poi la
fonte ufficiale corrente.
