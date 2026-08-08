# Media Library WordPress

Ogni immagine, video, PDF o altro asset usato dal sito deve vivere nella Media Library di
WordPress. Il componente deve riferirsi all'attachment, non a un file copiato in una cartella
casuale o a un hotlink.

Flusso obbligatorio:

1. cerca se esiste già un attachment riusabile;
2. se non esiste, importa il file con lo strumento disponibile: Media Library, WP-CLI, REST o
   connettore WordPress autorizzato;
3. verifica l'ID restituito e aggiorna alt text, titolo, caption e descrizione quando il contenuto
   lo richiede;
4. salva l'attachment ID nel campo custom o nel dato del blocco;
5. nel template usa le API native WordPress per generare URL, dimensioni e varianti responsive;
6. controlla che il componente renda anche quando l'attachment è assente o non più pubblico.

Non usare base64, URL esterni temporanei, immagini incluse solo nel repository o placeholder
silenziosi come stato finale. Non dichiarare eseguito un upload senza una risposta verificabile
da WordPress.

Se non esistono credenziali, WP-CLI, REST o un tool collegato, il risultato corretto è:

- codice del componente pronto;
- elenco dei media pendenti con nome e destinazione;
- istruzione precisa per l'import;
- stato esplicito: **non pronto finché la Media Library non è aggiornata**.

Per i dati personali nelle immagini, nei PDF o nei metadati, nomina Vera; per ruoli, permessi e
upload non autorizzati, nomina Kai.
