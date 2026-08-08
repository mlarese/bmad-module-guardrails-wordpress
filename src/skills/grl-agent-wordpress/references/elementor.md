# Confine Elementor

Elementor è una scelta di presentazione, non il modello dati. I dati propri del componente
restano nei campi custom; Elementor li legge con Dynamic Tags quando il widget e il tipo di campo
lo supportano.

Usalo quando il vantaggio concreto è l'iterazione visuale da parte di chi non scrive codice, in
particolare su landing page a vita breve. Prima di sceglierlo esplicita:

- quale template o area è confinata a Elementor;
- quali asset e widget aggiunge;
- cosa resta funzionante se il builder viene rimosso;
- chi manterrà il layout quando il contenuto cambia;
- come vengono gestiti campi vuoti, media mancanti e responsive.

Non mescolare Elementor nei template condivisi del tema Gutenberg senza una ragione verificabile:
la dipendenza può trascinare CSS, JavaScript, contenitori e markup del builder su pagine che non ne
hanno bisogno.

Il Repeater ACF non è supportato nativamente da Elementor Pro. Per liste ripetibili usa un
componente Gutenberg/ACF o un'estensione esplicita, non uno shortcode improvvisato dentro un
widget HTML senza escaping e contratto di dati.

Quando il criterio è vita lunga, contenuto strutturato o prestazioni prevedibili, parti da
Gutenberg + campi custom. Quando il criterio è iterazione visuale rapida su una landing isolata,
Elementor può essere appropriato. La decisione deve lasciare chiaro il costo di uscita.
