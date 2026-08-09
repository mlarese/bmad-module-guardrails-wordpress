#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""Post-check del report del release gate: schema, sezioni e verdetto unico.

Il report e' letto da chi autorizza il rilascio senza vedere questa
conversazione. Che porti i campi obbligatori, che le sezioni ci siano tutte e
che il verdetto sia uno solo fra quattro sono controlli con esito identico a
parita' di file: qui, non nel prompt.

Se il verdetto sia giusto lo decide il collegio. Lo script dice se il report e'
leggibile come verdetto.

Uscita: JSON su stdout. Exit 0 = conforme, 1 = violazioni, 2 = errore.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import unicodedata
from pathlib import Path

VERDICTS = ("GO_CON_CONDIZIONI", "EVIDENZA_INSUFFICIENTE", "NO_GO", "GO")
GATE_SCHEMA = "gwp-board/release-gate/v1"

REQUIRED_SECTIONS = (
    "identita e validita",
    "convocate ed escluse",
    "decisioni e rischi applicabili",
    "evidenze e lacune",
    "rilievi e blocchi",
    "condizioni",
    "verdetto e motivazione",
)

FRONTMATTER = re.compile(r"\A---\r?\n(.*?)\r?\n---\r?\n", re.DOTALL)
INLINE_MAP = re.compile(r"^\{(.*)\}$")
FENCE = re.compile(r"^\s*(```|~~~)")
ISO_DATE = re.compile(r"\b\d{4}-\d{2}-\d{2}\b")
# La riga che dichiara il verdetto ha una forma sola, cosi' il testo intorno puo'
# argomentare senza che una citazione sembri un secondo verdetto.
VERDICT_LINE = re.compile(
    r"^\s*\**\s*Verdetto\s*:?\**\s*:?\s*\**\s*(" + "|".join(VERDICTS) + r")\**",
    re.MULTILINE,
)
# Il timestamp del gate: `20260809T120000Z` oppure una data ISO.
GATE_DATE = re.compile(r"(\d{4})-?(\d{2})-?(\d{2})")


def fold(text: str) -> str:
    """Confronto dei titoli senza accenti e senza maiuscole."""
    stripped = unicodedata.normalize("NFKD", text)
    ascii_only = stripped.encode("ascii", "ignore").decode("ascii").lower()
    return re.sub(r"[^a-z0-9]+", " ", ascii_only).strip()


def parse_scalar(raw: str) -> object:
    value = raw.strip()
    if value in ("", "null", "~"):
        return None
    if value.startswith(('"', "'")) and value[-1:] == value[:1] and len(value) >= 2:
        return value[1:-1]
    if value in ("true", "false"):
        return value == "true"
    inline = INLINE_MAP.match(value)
    if inline:
        mapping: dict[str, object] = {}
        for chunk in split_top_level(inline.group(1)):
            if ":" not in chunk:
                continue
            key, item = chunk.split(":", 1)
            mapping[key.strip()] = parse_scalar(item)
        return mapping
    return value


def split_top_level(text: str) -> list[str]:
    """Divide su virgole non annidate, cosi' `{a: {b: 1, c: 2}}` resta intero."""
    parts, depth, current = [], 0, []
    for char in text:
        if char in "{[":
            depth += 1
        elif char in "}]":
            depth -= 1
        if char == "," and depth == 0:
            parts.append("".join(current))
            current = []
            continue
        current.append(char)
    if current:
        parts.append("".join(current))
    return [p.strip() for p in parts if p.strip()]


def parse_frontmatter(text: str) -> dict[str, object] | None:
    match = FRONTMATTER.match(text)
    if not match:
        return None
    data: dict[str, object] = {}
    for line in match.group(1).split("\n"):
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        if ":" not in line:
            continue
        key, raw = line.split(":", 1)
        if key.startswith((" ", "\t")):
            continue
        data[key.strip()] = parse_scalar(raw)
    return data


def split_sections(text: str) -> dict[str, str]:
    """Corpo diviso per heading di secondo livello, ignorando i blocchi di codice."""
    body = FRONTMATTER.sub("", text, count=1)
    sections: dict[str, str] = {}
    current, buffer, in_fence = None, [], False
    for line in body.split("\n"):
        if FENCE.match(line):
            in_fence = not in_fence
        if not in_fence and line.startswith("## "):
            if current is not None:
                sections[current] = "\n".join(buffer).strip()
            current, buffer = fold(line[3:]), []
            continue
        buffer.append(line)
    if current is not None:
        sections[current] = "\n".join(buffer).strip()
    return sections


def check(path: Path) -> dict:
    text = path.read_text(encoding="utf-8")
    violations: list[str] = []

    frontmatter = parse_frontmatter(text)
    if frontmatter is None:
        return {
            "path": str(path),
            "frontmatter_present": False,
            "verdict": None,
            "missing_sections": list(REQUIRED_SECTIONS),
            "violations": ["il report non ha frontmatter: schema e verdetto non sono leggibili"],
            "ok": False,
        }

    if frontmatter.get("gate") != GATE_SCHEMA:
        violations.append(f"campo `gate` assente o diverso da `{GATE_SCHEMA}`")

    verdict = frontmatter.get("verdict")
    if verdict not in VERDICTS:
        violations.append(
            f"`verdict` deve essere uno fra {', '.join(VERDICTS)}; trovato: {verdict!r}"
        )

    for field in ("environment", "scope", "gate_started_at_utc"):
        if not frontmatter.get(field):
            violations.append(f"campo `{field}` mancante o vuoto")

    identity = frontmatter.get("release_identity")
    if not isinstance(identity, dict):
        identity = {}
        violations.append("`release_identity` mancante o non e' una mappa")
    identity_values = {k: v for k, v in identity.items() if v}

    sections = split_sections(text)
    missing = [name for name in REQUIRED_SECTIONS if name not in sections]
    for name in missing:
        violations.append(f"sezione mancante: `{name}`")
    if not missing:
        present = [name for name in sections if name in REQUIRED_SECTIONS]
        if present != list(REQUIRED_SECTIONS):
            violations.append(
                "le sezioni obbligatorie non seguono l'ordine previsto: " + " → ".join(present)
            )

    # Il verdetto sta su una riga a schema fisso: la motivazione resta libera di
    # spiegare perche' non e' un NO_GO senza che quella citazione diventi un
    # secondo verdetto.
    verdict_section = sections.get("verdetto e motivazione", "")
    declared_line = VERDICT_LINE.search(verdict_section)
    if not declared_line:
        violations.append(
            "la sezione del verdetto non apre con una riga `**Verdetto:** <VALORE>`"
        )
    elif verdict in VERDICTS and declared_line.group(1) != verdict:
        violations.append(
            f"il verdetto della sezione ({declared_line.group(1)}) "
            f"non coincide con il frontmatter ({verdict})"
        )

    if verdict in ("GO", "GO_CON_CONDIZIONI") and not identity_values:
        violations.append(f"{verdict} senza nessun identificatore di release valorizzato")

    deadlines: list[str] = []
    if verdict == "GO_CON_CONDIZIONI":
        conditions = sections.get("condizioni", "")
        deadlines = ISO_DATE.findall(conditions)
        gate_day = GATE_DATE.match(str(frontmatter.get("gate_started_at_utc") or ""))
        if not conditions:
            violations.append("GO_CON_CONDIZIONI senza condizioni")
        elif not deadlines:
            violations.append("le condizioni non portano una scadenza in formato AAAA-MM-GG")
        elif gate_day:
            # «scadenza futura» e' un confronto, non un'impressione: una condizione
            # gia' scaduta all'apertura del gate non e' un'azione, e' un blocco.
            start = "-".join(gate_day.groups())
            if not any(deadline > start for deadline in deadlines):
                violations.append(
                    f"nessuna scadenza e' successiva all'apertura del gate ({start}): "
                    + ", ".join(sorted(set(deadlines)))
                )

    if verdict == "NO_GO" and not sections.get("rilievi e blocchi"):
        violations.append("NO_GO senza blocchi elencati")

    if verdict == "EVIDENZA_INSUFFICIENTE" and not sections.get("evidenze e lacune"):
        violations.append("EVIDENZA_INSUFFICIENTE senza lacune elencate")

    return {
        "path": str(path),
        "frontmatter_present": True,
        "verdict": verdict if verdict in VERDICTS else None,
        "release_identity": identity_values,
        "sections_found": list(sections),
        "missing_sections": missing,
        "condition_deadlines": sorted(set(deadlines)),
        "violations": violations,
        "ok": not violations,
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Verifica il report del release gate: frontmatter `gwp-board/release-gate/v1`, "
            "sezioni obbligatorie, verdetto unico fra GO, GO_CON_CONDIZIONI, NO_GO ed "
            "EVIDENZA_INSUFFICIENTE, e le prove che ciascun verdetto richiede."
        )
    )
    parser.add_argument("report", help="file markdown del report del gate")
    parser.add_argument("-o", "--output", help="file di destinazione del JSON (default: stdout)")
    parser.add_argument("--verbose", action="store_true", help="diagnostica su stderr")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    path = Path(args.report)
    if not path.is_file():
        print(f"errore: report non leggibile: {path}", file=sys.stderr)
        return 2
    try:
        result = check(path)
    except OSError as error:
        print(f"errore di filesystem: {error}", file=sys.stderr)
        return 2

    payload = json.dumps(result, ensure_ascii=False, indent=2)
    if args.output:
        Path(args.output).write_text(payload + "\n", encoding="utf-8")
    else:
        print(payload)
    if args.verbose:
        for line in result["violations"]:
            print(f"violazione: {line}", file=sys.stderr)
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
