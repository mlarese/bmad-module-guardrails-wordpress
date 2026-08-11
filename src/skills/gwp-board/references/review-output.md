# Consegna della revisione ordinaria

Produci un solo riepilogo schematico in conversazione, destinato all'utente che deve decidere cosa cambiare prima di continuare il lavoro:

1. **Esaminato** — artefatto, severità applicata e stato del profilo.
2. **Convocate ed escluse** — figura e aggancio concreto, oppure motivo dell'esclusione. L'elenco copre **tutte le figure del roster installate nel progetto**: una figura che non compare né fra le convocate né fra le escluse è stata dimenticata, non valutata, e nessuno se ne accorge leggendo il riepilogo.
3. **Per figura** — massimo cinque punti ordinati per costo di non intervenire; ciascuno contiene problema, conseguenza nel contesto esaminato e mossa minima. Per codice/spec etichetta ogni punto `Standards` o `Spec` e cita la versione osservata. Una figura senza rilievi occupa una riga.
4. **Conflitti** — richieste incompatibili e costo di ciascuna scelta, senza arbitrare.
5. **Da registrare** — decisioni prese e rischi che l'utente vuole accettare.

L'unica scrittura è in append in `{project-root}/_bmad/memory/grl-shared/`. Mostra sempre le righe e chiedi conferma esplicita prima di scrivere:

- `decisions.md`: `[AAAA-MM-GG] [figura] decisione — vincolo che l'ha imposta`;
- `accepted-risks.md`: `[AAAA-MM-GG] [figura] rischio — motivo dell'accettazione — ambito di validità`.

Non registrare mai un rischio di tua iniziativa: quella riga zittisce segnalazioni future. Crea un file solo quando contiene almeno una riga confermata.
