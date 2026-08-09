# Dossier checkout-wp 3.8.0

- Tag: `v3.8.0`
- Commit: `a81f0d4`
- Artefatto: `checkout-wp-3.8.0.zip`
- SHA-256: `0d02bf117c7a10b1e9d3f5a7c9e2b4d6f80123456789abcdef0123456789abcd`
- Ambiente: produzione di shop.example.it
- Perimetro: plugin checkout, webhook Stripe e configurazione inclusa nello ZIP

| Evidenza | Legame con la release | Esito |
| --- | --- | --- |
| `ci-run-770.log` | commit, digest e staging speculare alla produzione | test, deploy, rollback e restore eseguiti |
| `security-771-772.md` | ZIP con digest completo e webhook della stessa build | chiave live attiva; webhook senza firma restituisce HTTP 200 |

Non esistono accettazioni registrate che coprano la chiave o il webhook.
