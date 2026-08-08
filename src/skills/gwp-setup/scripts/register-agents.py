#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# ///
"""Registra le figure Guardrails nel roster degli agenti installati (config TOML).

Perché serve
------------
`resolve_party.py` di bmad-party-mode costruisce la stanza di default dalla tabella
`[agents.*]` del config centrale, letta da `resolve_config.py` sui quattro layer TOML
(`_bmad/config.toml`, `config.user.toml`, `custom/config.toml`, `custom/config.user.toml`)
e senza alcun filtro per `module` o per `team`: chi è registrato come agente entra nella
stanza. I due layer `_bmad/config.toml` e `_bmad/config.user.toml` sono rigenerati
dall'installer a ogni installazione — scriverci sarebbe effimero. Questo script scrive
quindi in `_bmad/custom/config.toml`, il layer di team che l'installer non tocca mai e
che vince sul config base.

Cosa scrive
-----------
- `_bmad/custom/config.toml` → una tabella `[agents.<nome-skill>]` per ogni figura, con
  `module`, `team`, `name`, `title`, `icon`, `description`. La fonte di verità sono i
  blocchi `[agent]` dei `customize.toml` delle skill installate; `--module-yaml` serve
  solo come ripiego quando le skill non si trovano su disco.
La scrittura è anti-zombie: le tabelle precedenti dello stesso modulo vengono
rimosse prima di riscrivere, perché in TOML una tabella dichiarata due volte è un errore
di parsing. Il risultato viene riparsato con `tomllib` prima di toccare il disco: se non
è TOML valido, non si scrive nulla.

Codici di uscita: 0 = successo, 1 = errore d'uso o di validazione, 2 = errore d'ambiente.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import tomllib
from pathlib import Path

sys.dont_write_bytecode = True

MODULE_CODE = "grl"
AGENT_FIELDS = ("module", "team", "name", "title", "icon", "description")

BEGIN = f"# >>> {MODULE_CODE}:agents — generato da {MODULE_CODE}-setup, non modificare a mano >>>"
END = f"# <<< {MODULE_CODE}:agents <<<"


def toml_string(value: str) -> str:
    """Serializza una stringa come TOML basic string su una riga."""
    escaped = (
        str(value)
        .replace("\\", "\\\\")
        .replace('"', '\\"')
        .replace("\n", "\\n")
        .replace("\r", "\\r")
        .replace("\t", "\\t")
    )
    return f'"{escaped}"'


def read_agents_from_skills(skills_dir: Path) -> tuple[dict[str, dict], list[str]]:
    """Legge il blocco [agent] dai customize.toml delle skill `{module}-agent-*`.

    La chiave del roster è il nome della cartella della skill (es. `grl-agent-privacy`),
    coerente con come l'installer registra gli agenti BMM (`bmad-agent-analyst`).
    """
    agents: dict[str, dict] = {}
    warnings: list[str] = []
    if not skills_dir.is_dir():
        return agents, [f"cartella delle skill non trovata: {skills_dir}"]

    for skill_dir in sorted(skills_dir.glob(f"{MODULE_CODE}-agent-*")):
        customize = skill_dir / "customize.toml"
        if not customize.is_file():
            warnings.append(f"{skill_dir.name}: customize.toml assente, saltata")
            continue
        try:
            with customize.open("rb") as stream:
                block = tomllib.load(stream).get("agent", {})
        except tomllib.TOMLDecodeError as error:
            warnings.append(f"{skill_dir.name}: customize.toml illeggibile ({error}), saltata")
            continue
        missing = [f for f in AGENT_FIELDS if not str(block.get(f, "")).strip()]
        if missing:
            warnings.append(f"{skill_dir.name}: campi [agent] mancanti {missing}, saltata")
            continue
        agents[skill_dir.name] = {f: block[f] for f in AGENT_FIELDS}
    return agents, warnings


def read_agents_from_module_yaml(module_yaml: Path) -> tuple[dict[str, dict], list[str]]:
    """Ripiego: ricava il roster dal blocco `agents:` di module.yaml.

    Parsing minimale a righe, per non introdurre una dipendenza da pyyaml in uno
    script che deve poter girare ovunque giri BMad.
    """
    agents: dict[str, dict] = {}
    warnings: list[str] = []

    def roster_key(code: str) -> str:
        prefix = f"{MODULE_CODE}-agent-"
        return code if code.startswith(prefix) else f"{prefix}{code}"

    if not module_yaml.is_file():
        return agents, [f"module.yaml non trovato: {module_yaml}"]

    entry: dict[str, str] = {}
    in_agents = False
    for raw in module_yaml.read_text(encoding="utf-8").splitlines():
        if not raw.strip() or raw.lstrip().startswith("#"):
            continue
        if re.match(r"^agents:\s*$", raw):
            in_agents = True
            continue
        if in_agents and not raw.startswith((" ", "\t", "-")):
            break  # tornati al livello superiore: il blocco agents è finito
        if not in_agents:
            continue
        stripped = raw.strip()
        if stripped.startswith("- "):
            if entry.get("code"):
                agents[roster_key(entry["code"])] = entry
            entry = {}
            stripped = stripped[2:].strip()
        key, _, value = stripped.partition(":")
        if not value:
            continue
        entry[key.strip()] = value.strip().strip('"').strip("'")
    if entry.get("code"):
        agents[roster_key(entry["code"])] = entry

    for skill_name, data in list(agents.items()):
        missing = [f for f in AGENT_FIELDS if not str(data.get(f, "")).strip()]
        if missing:
            warnings.append(f"{skill_name}: campi mancanti in module.yaml {missing}, saltata")
            del agents[skill_name]
        else:
            agents[skill_name] = {f: data[f] for f in AGENT_FIELDS}
    return agents, warnings


def strip_marked_block(text: str) -> str:
    """Rimuove il blocco fra i marker, se presente."""
    pattern = re.compile(
        re.escape(BEGIN) + r".*?" + re.escape(END) + r"\n?", re.DOTALL
    )
    return pattern.sub("", text)


def strip_tables(text: str, matches) -> str:
    """Rimuove le tabelle TOML il cui header soddisfa `matches(header)`.

    Una tabella va dall'header alla prossima riga che apre una tabella, o a fine file.
    I commenti che la precedono restano dove sono: non si presume che appartengano a noi.
    """
    out: list[str] = []
    skipping = False
    for line in text.splitlines(keepends=True):
        stripped = line.strip()
        if stripped.startswith("[") and "]" in stripped:
            header = stripped[1 : stripped.index("]")].strip()
            skipping = matches(header)
        if not skipping:
            out.append(line)
    return "".join(out)


def render_agents_block(agents: dict[str, dict]) -> str:
    lines = [BEGIN]
    for skill_name in sorted(agents):
        data = agents[skill_name]
        lines.append("")
        lines.append(f"[agents.{skill_name}]")
        for field in AGENT_FIELDS:
            lines.append(f"{field} = {toml_string(data[field])}")
    lines.append("")
    lines.append(END)
    return "\n".join(lines) + "\n"


def write_validated(path: Path, text: str, dry_run: bool) -> None:
    """Riparsa il risultato e lo scrive solo se è TOML valido."""
    try:
        tomllib.loads(text)
    except tomllib.TOMLDecodeError as error:
        raise SystemExit(
            json.dumps(
                {
                    "status": "error",
                    "error": f"il risultato per {path} non è TOML valido: {error}. Nessuna scrittura eseguita.",
                },
                indent=2,
                ensure_ascii=False,
            )
        )
    if dry_run:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Registra le figure Guardrails nel roster degli agenti installati."
    )
    parser.add_argument(
        "--project-root", required=True,
        help="Radice del progetto che contiene _bmad/ (percorso reale, non {project-root}).",
    )
    parser.add_argument(
        "--skills-dir",
        help="Cartella delle skill installate. Default: {project-root}/.claude/skills",
    )
    parser.add_argument(
        "--module-yaml",
        help="module.yaml da cui ricavare il roster se le skill non si trovano su disco.",
    )
    parser.add_argument(
        "--dry-run", action="store_true",
        help="Mostra cosa verrebbe scritto senza toccare il disco.",
    )
    args = parser.parse_args()

    if "{project-root}" in args.project_root:
        print(json.dumps({
            "status": "error",
            "error": "token '{project-root}' non risolto in --project-root: passa il percorso reale del progetto.",
        }, indent=2, ensure_ascii=False))
        return 1

    project_root = Path(args.project_root).resolve()
    bmad_dir = project_root / "_bmad"
    if not bmad_dir.is_dir():
        print(json.dumps({
            "status": "error",
            "error": f"_bmad/ non trovato in {project_root}: il progetto non ha un'installazione BMad.",
        }, indent=2, ensure_ascii=False))
        return 2

    if not (bmad_dir / "config.toml").is_file():
        print(json.dumps({
            "status": "error",
            "error": (
                f"{bmad_dir / 'config.toml'} non trovato. Questo script registra il roster nel "
                "config TOML a quattro layer. Su un'installazione BMad più vecchia (config.yaml) "
                "le figure vanno registrate con il meccanismo di quella versione."
            ),
        }, indent=2, ensure_ascii=False))
        return 2

    skills_dir = Path(args.skills_dir) if args.skills_dir else project_root / ".claude" / "skills"
    agents, warnings = read_agents_from_skills(skills_dir)
    source = "customize.toml delle skill installate"

    if not agents and args.module_yaml:
        agents, fallback_warnings = read_agents_from_module_yaml(Path(args.module_yaml))
        warnings += fallback_warnings
        source = "module.yaml (ripiego: skill non trovate su disco)"

    if not agents:
        print(json.dumps({
            "status": "error",
            "error": f"nessuna figura {MODULE_CODE} trovata da registrare.",
            "warnings": warnings,
        }, indent=2, ensure_ascii=False))
        return 1

    # --- Roster → _bmad/custom/config.toml (layer di team, mai toccato dall'installer)
    custom_config = bmad_dir / "custom" / "config.toml"
    text = custom_config.read_text(encoding="utf-8") if custom_config.is_file() else ""
    text = strip_marked_block(text)
    text = strip_tables(text, lambda h: h.startswith(f"agents.{MODULE_CODE}-agent-"))
    if text and not text.endswith("\n"):
        text += "\n"
    if text.strip():
        text += "\n"
    text += render_agents_block(agents)
    write_validated(custom_config, text, args.dry_run)

    print(json.dumps({
        "status": "success",
        "dry_run": args.dry_run,
        "source": source,
        "agents_registered": sorted(agents),
        "agents_count": len(agents),
        "roster_file": str(custom_config),
        "warnings": warnings,
    }, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
