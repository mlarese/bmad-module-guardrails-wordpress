# Dossier backoffice 2.2.0

- Tag: `v2.2.0`
- Commit: `77b12ae`
- Immagine: `registry.example/backoffice@sha256:0912b4f8e6c0a2d1f3b5e7a9c8d6f4b20123456789abcdef0123456789abcdef`
- Ambiente: produzione interna
- Perimetro: solo team amministrativo; accesso pubblico escluso

| Evidenza | Legame con la release | Esito |
| --- | --- | --- |
| `ci-run-551.log` | commit e digest completo | 208/208 test; DAST e dependency scan puliti |
| `drill-552.md` | stesso digest su staging speculare alla produzione interna | deploy, rollback, restore e smoke riusciti |

Difetto non bloccante osservato: l'export CSV usa intestazioni inglesi nella UI italiana. Issue
`BO-91`, responsabile Luca, scadenza 2026-08-12, condizione limitata al perimetro interno indicato.
Non esiste ancora una conferma esplicita per registrarlo in `accepted-risks.md`.
