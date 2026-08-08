# Modello contenuti e campi custom

L'output è un modello editoriale che un altro sviluppatore può implementare e un editor può
usare senza conoscere il markup.

Parti dal contenuto, non dalla pagina:

- quali entità esistono: post type, tassonomie, utenti o opzioni;
- quali dati sono nativi di WordPress e quali appartengono al componente;
- quali campi sono obbligatori, ripetibili, relazionali o con fallback;
- quali dati devono essere interrogabili con `WP_Query` e quali servono solo al render;
- quali componenti riusano lo stesso contratto.

Per i dati propri del componente usa sempre un field group e un nome stabile. Non salvare markup
HTML nei campi e non usare un Repeater come sostituto di una relazione o di un post type.

Per immagini e file, preferisci il formato di ritorno **Attachment ID**: il template può usare
`wp_get_attachment_image()` e le API native per `srcset`, dimensioni e lazy loading. Se la query
deve filtrare o ordinare molti valori di campo, segnala il costo di `meta_query` su `wp_postmeta`
prima di proporre una soluzione.

Quando il progetto lo permette, abilita Local JSON o un meccanismo equivalente per versionare la
definizione dei campi. Distingui sempre schema dei campi, contenuto inserito dall'editor e codice
del componente.

Il contratto minimo da restituire è:

| Elemento | Domanda |
| --- | --- |
| Entità | Quale contenuto possiede questi dati? |
| Field group | Quali campi esistono e quali sono obbligatori? |
| Componente | Quale markup e comportamento produce? |
| Template | Dove viene composto e con quali fallback? |
| Media | Quale attachment ID e quali metadati servono? |
| Verifica | Come si controlla il caso pieno, vuoto e ripetuto? |
