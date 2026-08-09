# Revisione editoriale finale

Invoca `bmad-review lenses=prose` con la lingua dell'output, la guida di stile del progetto e `reader_type=humans`; per contenuti multilingue revisiona ogni lingua separatamente. Nella revisione ordinaria, se la skill non è disponibile, esegui manualmente lo stesso controllo. Il release gate non ammette questo fallback e segue il proprio contratto.

Applica soltanto correzioni di chiarezza, grammatica, coesione, tono e terminologia. Non cambiare fatti, conclusioni, severità, fonti, citazioni, riferimenti normativi o clinici, decisioni o testo dell'utente. Lascia invariati codice, comandi, dati strutturati, frontmatter, URL, identificatori, date, formule e righe di memoria; in HTML e Markdown revisiona solo la prosa leggibile. Consegna il testo corretto, non i risultati della review.

Quando il testo revisionato è un file, conserva una copia prima della revisione e confronta le due versioni:

```
uv run scripts/check_prose_invariants.py <prima>.md <dopo>.md
```

Lo script elenca ogni differenza nelle categorie che devono restare ferme. Annulla quelle differenze prima di consegnare: se una di esse era necessaria, il cambiamento è sostanziale e non appartiene a questa revisione.
