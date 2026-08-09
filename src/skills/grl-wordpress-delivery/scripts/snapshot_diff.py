#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""Confronta lo snapshot atteso di una delivery con quello osservato sul target.

`verify` e' in sola lettura: legge il target, lo confronta con una baseline
approvata e riporta le differenze senza correggerle. Il confronto e' esatto —
chiavi mancanti, chiavi in piu', valori diversi — e ripetendolo sugli stessi due
file da' sempre lo stesso esito.

Cosa comporti una differenza in WordPress resta di Milo. E se lo snapshot post
diverge dal pre, la verifica ha mutato il target e va invalidata: e' l'unica
conclusione che lo script si permette.

Con `--invariants` fa lo stesso lavoro sui file di prosa della delivery: dopo la
review di prosa cio' che il testo *dice* deve essere identico, e la parte che si
puo' confrontare esattamente — frontmatter, codice, celle, URL, date, hash, id e
verdetti — e' un diff fra due multiinsiemi.

Formati accettati: JSON piatto oppure tabella markdown (`| Chiave | Valore |`, o
piu' colonne, che diventano una chiave per cella).

Uscita: JSON su stdout. Exit 0 = coincidono, 1 = differenze, 2 = errore.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter
from pathlib import Path

SEPARATOR = re.compile(r"^[-: |]+$")
HEADER_KEYS = ("chiave", "campo", "key", "voce")

FRONTMATTER = re.compile(r"\A---\r?\n(.*?)\r?\n---\r?\n", re.DOTALL)
FENCED = re.compile(r"(?:```|~~~)[^\n]*\n(.*?)(?:```|~~~)", re.DOTALL)
INLINE_CODE = re.compile(r"`([^`\n]+)`")
URL = re.compile(r"\b(?:https?://|www\.)[^\s<>()\[\]\"']+")
ISO_DATE = re.compile(r"\b\d{4}-\d{2}-\d{2}(?:T[\d:]{5,8}Z?)?\b")
# Hash e commit: cifre e lettere insieme, mai una parola.
HASH = re.compile(r"(?<![0-9a-zA-Z])(?=[0-9a-f]*\d)(?=[0-9a-f]*[a-f])[0-9a-f]{7,64}(?![0-9a-zA-Z])")
# Ogni token che contiene una cifra, delimitato dai soli spazi: `attachment 42.`,
# `page-home42` e `640px` sono id quanto un `42` isolato, e un delimitatore più
# stretto li lascerebbe cambiare senza che il confronto se ne accorga. Meglio
# qualche token in più da spiegare che un attachment ID mutato in silenzio.
TOKEN_WITH_DIGIT = re.compile(r"\S*\d\S*")
# Simmetrica: `(42` e `42` sono lo stesso id, e togliere le parentesi durante la
# revisione non deve risultare un identificatore cambiato.
SURROUNDING_PUNCTUATION = "\"'«»()[]{}*_`.,;:!?"
VERDICT = re.compile(
    r"(?<![A-Z_])(GO_CON_CONDIZIONI|EVIDENZA_INSUFFICIENTE|NO_GO|GO)(?![A-Z_])"
)

INVARIANT_LABELS = {
    "frontmatter": "frontmatter",
    "code": "blocchi e frammenti di codice",
    "cells": "celle di tabella",
    "urls": "URL",
    "dates": "date",
    "hashes": "hash e commit",
    "numeric_ids": "id, numeri e codici",
    "verdicts": "verdetti",
}


def parse_table(text: str) -> dict[str, str]:
    """Coppie chiave/valore di una tabella markdown.

    A due colonne la prima cella e' la chiave. Con piu' colonne ogni cella
    diventa una chiave propria, `riga.colonna`: su `media-map.md` attachment ID
    e stato stanno nella terza e nella quarta colonna, e tenere solo le prime due
    li lascerebbe cambiare senza che il confronto se ne accorga.
    """
    rows: list[list[str]] = []
    for line in text.split("\n"):
        line = line.strip()
        if not line.startswith("|") or SEPARATOR.match(line):
            continue
        cells = [cell.strip() for cell in line.strip("|").split("|")]
        if len(cells) < 2 or not cells[0]:
            continue
        rows.append(cells)
    if not rows:
        return {}

    header = rows[0]
    body = rows[1:] if len(header) > 2 or header[0].lower() in HEADER_KEYS else rows

    values: dict[str, str] = {}
    for cells in body:
        if len(header) <= 2:
            values[cells[0]] = cells[1]
            continue
        for index, cell in enumerate(cells[1:], start=1):
            column = header[index] if index < len(header) else f"colonna-{index}"
            # Separatore `|` e non `.`: `logo.png.Stato` sarebbe illeggibile.
            values[f"{cells[0]}|{column}"] = cell
    return values


def flatten(data: object, prefix: str = "") -> dict[str, str]:
    """Un JSON annidato diventa chiavi puntate: il confronto resta piatto."""
    flat: dict[str, str] = {}
    if isinstance(data, dict):
        for key, value in data.items():
            flat.update(flatten(value, f"{prefix}.{key}" if prefix else str(key)))
    elif isinstance(data, list):
        for index, value in enumerate(data):
            flat.update(flatten(value, f"{prefix}[{index}]"))
    else:
        flat[prefix] = "" if data is None else str(data)
    return flat


def load(path: Path) -> dict[str, str]:
    text = path.read_text(encoding="utf-8")
    if path.suffix.lower() == ".json" or text.lstrip().startswith(("{", "[")):
        return flatten(json.loads(text))
    values = parse_table(text)
    if not values:
        raise ValueError(f"{path}: nessuna coppia chiave/valore leggibile")
    return values


def compare(
    expected: dict[str, str], observed: dict[str, str], keys_only: bool = False
) -> dict:
    """Differenze fra due mappe.

    Con `keys_only` conta solo la copertura: inventario e mappa di una
    migrazione hanno le stesse chiavi e valori diversi per costruzione — l'uno
    descrive l'origine, l'altra la destinazione — e confrontarne i valori
    dichiarerebbe rotto ogni piano corretto.
    """
    missing = sorted(set(expected) - set(observed))
    unexpected = sorted(set(observed) - set(expected))
    changed = [
        {"key": key, "expected": expected[key], "observed": observed[key]}
        for key in sorted(set(expected) & set(observed))
        if expected[key] != observed[key]
    ]
    equal = len(set(expected) & set(observed)) - len(changed)
    return {
        "missing": missing,
        "unexpected": unexpected,
        "changed": [] if keys_only else changed,
        "equal": equal,
        "keys_only": keys_only,
        "ok": not (missing or unexpected or (changed and not keys_only)),
    }


def extract_invariants(text: str) -> dict[str, Counter]:
    """Cio' che la review di prosa non puo' toccare, per categoria."""
    frontmatter = FRONTMATTER.match(text)
    cells: list[str] = []
    for line in text.split("\n"):
        line = line.strip()
        if line.startswith("|") and not SEPARATOR.match(line):
            cells.extend(cell.strip() for cell in line.strip("|").split("|") if cell.strip())
    return {
        "frontmatter": Counter([frontmatter.group(1).strip()] if frontmatter else []),
        "code": Counter(
            [block.strip() for block in FENCED.findall(text)]
            + [snippet.strip() for snippet in INLINE_CODE.findall(text)]
        ),
        "cells": Counter(cells),
        "urls": Counter(URL.findall(text)),
        "dates": Counter(ISO_DATE.findall(text)),
        "hashes": Counter(HASH.findall(text)),
        "numeric_ids": Counter(
            token.strip(SURROUNDING_PUNCTUATION)
            for token in TOKEN_WITH_DIGIT.findall(text)
            if token.strip(SURROUNDING_PUNCTUATION)
        ),
        "verdicts": Counter(VERDICT.findall(text)),
    }


def compare_invariants(before: str, after: str) -> dict:
    left, right = extract_invariants(before), extract_invariants(after)
    changes: dict[str, dict] = {}
    violations: list[str] = []
    for key, label in INVARIANT_LABELS.items():
        removed, added = left[key] - right[key], right[key] - left[key]
        changes[key] = {"removed": sorted(removed.elements()), "added": sorted(added.elements())}
        if removed or added:
            violations.append(
                f"{label}: {sum(removed.values())} rimossi, {sum(added.values())} aggiunti"
            )
    return {"changes": changes, "violations": violations, "ok": not violations}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Confronta due snapshot di una delivery (JSON piatto o tabella markdown) e "
            "riporta chiavi mancanti, chiavi in piu' e valori diversi. Con --pre e --post "
            "verifica che la lettura non abbia mutato il target; con --invariants verifica "
            "che la review di prosa non abbia toccato frontmatter, codice, celle, URL, "
            "date, hash, id e verdetti."
        )
    )
    parser.add_argument("--expected", help="snapshot atteso approvato")
    parser.add_argument("--observed", help="snapshot osservato sul target")
    parser.add_argument("--pre", help="snapshot del target prima della verifica")
    parser.add_argument("--post", help="snapshot del target dopo la verifica")
    parser.add_argument(
        "--keys-only",
        action="store_true",
        help="con --expected/--observed confronta solo la copertura delle chiavi, non i valori",
    )
    parser.add_argument(
        "--invariants",
        nargs=2,
        metavar=("PRIMA", "DOPO"),
        help="i due file di prosa da confrontare: prima e dopo la review",
    )
    parser.add_argument("-o", "--output", help="file di destinazione del JSON (default: stdout)")
    parser.add_argument("--verbose", action="store_true", help="diagnostica su stderr")
    return parser


def run(args: argparse.Namespace) -> dict:
    result: dict = {}
    if bool(args.expected) != bool(args.observed):
        raise ValueError("--expected e --observed vanno usati insieme")
    if bool(args.pre) != bool(args.post):
        raise ValueError("--pre e --post vanno usati insieme")
    if not args.expected and not args.pre and not args.invariants:
        raise ValueError(
            "serve almeno una coppia: --expected/--observed, --pre/--post oppure --invariants"
        )

    if args.expected:
        result["baseline"] = compare(
            load(Path(args.expected)), load(Path(args.observed)), args.keys_only
        )
    if args.pre:
        mutation = compare(load(Path(args.pre)), load(Path(args.post)))
        mutation["target_mutated"] = not mutation["ok"]
        result["read_only"] = mutation
    if args.invariants:
        before, after = (Path(p) for p in args.invariants)
        for path in (before, after):
            if not path.is_file():
                raise ValueError(f"file non leggibile: {path}")
        result["invariants"] = compare_invariants(
            before.read_text(encoding="utf-8"), after.read_text(encoding="utf-8")
        )

    result["ok"] = all(
        section.get("ok", True) for key, section in result.items() if isinstance(section, dict)
    )
    return result


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        result = run(args)
    except (ValueError, json.JSONDecodeError) as error:
        print(f"errore: {error}", file=sys.stderr)
        return 2
    except OSError as error:
        print(f"errore di filesystem: {error}", file=sys.stderr)
        return 2

    payload = json.dumps(result, ensure_ascii=False, indent=2)
    if args.output:
        Path(args.output).write_text(payload + "\n", encoding="utf-8")
    else:
        print(payload)
    if args.verbose and not result["ok"]:
        print("differenze rilevate", file=sys.stderr)
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
