# Guardrails WordPress (`gwp`)

Presidio dell'architettura WordPress a componenti: Gutenberg, Elementor confinato dove serve, ACF e campi custom, template e Media Library, senza contenuti strutturati dentro pagine monolitiche.

Modulo BMad. È una porzione del bundle [Guardrails](https://github.com/mlarese/bmad-module-guardrails):
stesse figure, stesso comportamento, solo l'area wordpress.

> **Generato.** Questo repository è prodotto da `tools/build_modules.py` nel
> repository [bmad-module-guardrails](https://github.com/mlarese/bmad-module-guardrails).
> Le modifiche si fanno lì e poi si rigenera: qui vengono sovrascritte.

## Figure

| Figura | Ruolo | Skill | Cosa presidia |
| ------ | ----- | ----- | ------------- |
| 🧩 Milo | WordPress Component Architect | `grl-agent-wordpress` | Progetta e implementa WordPress a componenti con Gutenberg, Elementor, ACF, campi custom, template e Media Library, senza lasciare contenuti strutturati dentro pagine monolitiche… |

## Skill e workflow

| Skill | Comando | Cosa fa |
| ----- | ------- | ------- |
| `gwp-setup` | Installa Guardrails WordPress | Registra Guardrails, le figure, le stanze tematiche di party mode e le voci di help. Non crea la memoria condivisa. |
| `gwp-profile` | Profila il progetto | Raccoglie in pochi minuti gli otto campi che danno contesto a tutte le figure, criticità inclusa. |
| `gwp-profile` | Aggiorna il profilo | Riallinea il profilo quando il progetto cambia, e dice se il cambiamento invalida rischi già accettati. |
| `gwp-board` | Convoca il collegio | Fa leggere lo stesso artefatto alle sole figure pertinenti e restituisce un riepilogo unico, conflitti compresi. |
| `gwp-board` | Rischi già accettati | Mostra, raggruppato per figura, quello che il progetto ha consapevolmente scelto di accettare. |

## Installazione

```
bmad install gwp
```

Poi, come primo passo, `gwp-profile`: raccoglie il profilo di progetto — settore,
dati trattati, mercato, stack, criticità — e da lì ogni figura deriva quanto essere
severa. Senza profilo il default resta `normal` e le figure partono senza contesto.

## Memoria condivisa

Il profilo vive in `{project-root}/_bmad/memory/grl-shared/project-profile.md`, insieme
a `decisions.md` e `accepted-risks.md`. Il percorso è lo stesso per tutti i moduli
Guardrails: installandone due, il profilo resta uno solo e si compila una volta.

## Convivenza con il bundle

Questo modulo installa skill con **lo stesso nome** del bundle `grl` — `grl-agent-wordpress`
sta identica in entrambi. Bundle e moduli tematici non vanno installati insieme nello
stesso progetto: si sceglie il bundle completo, oppure i moduli delle aree che servono.

## Licenza

MIT.
