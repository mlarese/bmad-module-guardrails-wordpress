# Guardrails WordPress (`gwp`) — istruzioni di progetto

## Questo repository è generato

Il contenuto è prodotto da `tools/build_modules.py` nel repository
[bmad-module-guardrails](https://github.com/mlarese/bmad-module-guardrails), che resta
la fonte unica delle skill.

**Non modificare le skill qui.** Una modifica fatta in questo repository viene persa
alla prima rigenerazione. Il percorso corretto è: modifica in `src/skills/` della
fonte, poi `python3 tools/build_modules.py --module gwp`, poi commit qui.

## Cosa cambia rispetto al bundle

- il roster contiene solo le figure di quest'area
- le due skill del core sono rinominate: `gwp-profile`, `gwp-board`
- la memoria condivisa resta `_bmad/memory/grl-shared/`, uguale per tutti i moduli

## Niente pull request

Il lavoro finisce con i commit e, se richiesto, con il push del branch.
