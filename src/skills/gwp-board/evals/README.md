# Eval di gwp-board

`cases.json` copre i quattro verdetti del release gate, l'identità immutabile della release,
le evidenze, la selezione mirata, il consenso sui rischi e la sequenza review sostanziale → review di prosa.
I dossier sotto `fixtures/` rendono verificabili i tre gate con release identificata.

`triggers.json` separa collegio e decisione di rilascio da test, deploy, code review e delivery
WordPress. Passare i due file esplicitamente a `bmad-eval-runner` nei modi `quality` e `trigger`.
