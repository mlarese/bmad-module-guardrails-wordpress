# Finding di sicurezza 771–772

- SHA-256: `0d02bf117c7a10b1e9d3f5a7c9e2b4d6f80123456789abcdef0123456789abcd`
- Secret scan: chiave Stripe live inclusa nello ZIP e ancora attiva presso il provider.
- Test webhook negativo sulla stessa build: richiesta senza firma → HTTP 200.
