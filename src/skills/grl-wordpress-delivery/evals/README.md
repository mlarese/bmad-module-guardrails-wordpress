# Eval di grl-wordpress-delivery

`cases.json` esercita `create`, `resume`, `migrate` e `verify`, la regola degli attachment ID,
la registrazione dell'alt text per le immagini verificate, la sola lettura in verifica e la
sequenza review sostanziale → review di prosa → release gate finale.

`triggers.json` distingue la delivery end-to-end dalla consulenza WordPress, dalla critica visiva,
dalle operations e dal release gate già isolato. Usare i file nei modi `quality` e `trigger`.
