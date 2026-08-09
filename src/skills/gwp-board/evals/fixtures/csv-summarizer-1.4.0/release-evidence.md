# Dossier csv-summarizer 1.4.0

- Tag: `v1.4.0`
- Commit: `3b1d9e7`
- Artefatto: `dist/csv-summarizer-1.4.0.tgz`
- SHA-256: `41a8c40c2e6f9d7b5a4e3c2f1d0b8a69788776655443322110ffeeddccbbaa99`
- Ambiente: registro npm pubblico
- Perimetro incluso: pacchetto CLI e dipendenze di produzione
- Perimetro escluso: sito documentale e pipeline di sviluppo

Il CLI legge CSV locali e stampa un riepilogo. Non usa rete, database, account o telemetria e non
gestisce dati personali per finalità proprie.

| Evidenza | Legame con la release | Esito |
| --- | --- | --- |
| `ci-run-184.log` | commit `3b1d9e7` e digest completo | unit 86/86; integrazione 12/12; smoke riuscito |
| `security-184.md` | lockfile del commit e digest completo | audit pulito; SBOM MIT/Apache-2.0 |
| `rehearsal-183.log` | stesso digest sul registro npm isolato | pubblicazione, deprecazione e ripristino riusciti |

Ripristino di servizio e dati: non applicabile, perché il candidato non installa un servizio e non
conserva dati. La prova di rollback copre la sola operazione persistente, cioè la pubblicazione.
