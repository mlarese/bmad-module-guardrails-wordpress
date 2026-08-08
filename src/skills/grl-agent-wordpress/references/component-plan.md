# Piano di decomposizione in componenti

Usa questa traccia quando devi trasformare una pagina, un mockup o una richiesta editoriale in
un'implementazione WordPress.

L'output utile non è una lista di widget: è una mappa che collega contenuto e codice.

| Sezione | Specifica minima |
| --- | --- |
| Nome | nome stabile del componente, non il nome della pagina |
| Scopo | quale contenuto o comportamento possiede |
| Campi | chiavi, tipo, obbligatorietà, default, relazione |
| Media | attachment ID, formato, dimensioni, alt/caption |
| Render | blocco core + binding, ACF Block, template part o Elementor isolato |
| Composizione | dove il componente viene inserito e quante volte |
| Fallback | cosa vede l'utente quando un campo è vuoto |
| Verifica | caso pieno, vuoto, media mancante, mobile e contenuto lungo |

Dividi il lavoro in componenti verticali: schema del campo, template/render, stile, dati di
esempio e verifica. Evita di dividere artificialmente un componente che non ha una responsabilità
riusabile.

Una consegna WordPress non è completa se contiene placeholder media, URL esterni temporanei o
campi che l'editor non può aggiornare. Se l'accesso alla Media Library manca, separa chiaramente
il codice pronto dall'operazione media ancora pendente e non segnare il lavoro come finito.
