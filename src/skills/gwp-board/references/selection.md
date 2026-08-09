# Roster e confini del collegio

Chi entra e su quale segnale. Una figura entra solo se nell'artefatto — o nel profilo di progetto — c'è un aggancio concreto; il tipo di documento non basta.

| Figura | Skill | Entra quando compare |
| ------ | ----- | -------------------- |
| Milo 🧩 | `grl-agent-wordpress` | repository o tema/plugin WordPress, custom post type, ACF, campi custom, blocchi Gutenberg, Block Bindings, template parts, Elementor, Media Library e componenti riusabili |

Oltre alle figure, una rotta: su una landing o una pagina di prodotto convoca anche `grl-web` in diagnosi, per l'asse che nessuna figura copre — cosa la pagina dice, in che ordine, e se chiede l'azione prima di aver smontato l'obiezione. Quando la pagina arriva dal gate di `grl-web`, la lettura non ripete l'asse ma lo **verifica**: si ricostruisce il brief dalla pagina a freddo e si dice dove diverge da quello scritto. Se non diverge, è una riga sola. Conta come rotta, non come figura del collegio.

## Confini

Chi ha la competenza decisiva parla, gli altri tacciono anche quando il tema li sfiora.

| Questione | Parla | Tace |
| --------- | ----- | ---- |

Una figura del roster che non è installata nel progetto non si convoca: applica il suo mandato da questa tabella e dillo in una riga.

## Figure fuori da questo modulo

Le tabelle qui sopra citano anche figure Guardrails che questo modulo non installa.
Qui sono installate: Milo (grl-agent-wordpress).

Quando il tema appartiene a una figura assente, il confine resta valido: **dichiara che
il tema esce dal perimetro, nomina la competenza che servirebbe e prosegui solo su ciò che
resta autorizzato.** Registra `missing_capability` e `handoff_status: pending`; non
improvvisare il parere mancante, non dichiarare completato il passaggio e non superare un
gate che dipende da quella capacità. Il lavoro indipendente può continuare, il gate dipendente
resta `blocked` o `EVIDENZA_INSUFFICIENTE`. Il modulo che la contiene si installa a parte; il
bundle completo `grl` le contiene tutte.
