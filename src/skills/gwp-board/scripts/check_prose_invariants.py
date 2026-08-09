#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""Post-check della revisione di prosa: cosa doveva restare identico e' restato.

La revisione di prosa puo' cambiare come una cosa e' detta, non cosa dice. La
distinzione ha una parte esatta — frontmatter, codice, URL, identificatori,
date, numeri, righe di memoria, verdetti — e confrontarla e' un diff fra due
multiinsiemi: stesso input, stesso esito.

Il giudizio editoriale resta del revisore. Lo script dice se qualcosa che doveva
restare fermo si e' mosso.

Uscita: JSON su stdout. Exit 0 = invarianti rispettate, 1 = violate, 2 = errore.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter
from pathlib import Path

FRONTMATTER = re.compile(r"\A---\r?\n(.*?)\r?\n---\r?\n", re.DOTALL)
FENCED = re.compile(r"(?:```|~~~)[^\n]*\n(.*?)(?:```|~~~)", re.DOTALL)
INLINE_CODE = re.compile(r"`([^`\n]+)`")
URL = re.compile(r"\b(?:https?://|www\.)[^\s<>()\[\]\"']+")
# Hash lunghi, digest e commit abbreviati: cifre e lettere insieme, mai una parola.
HEXID = re.compile(r"(?<![0-9a-zA-Z])(?=[0-9a-f]*\d)(?=[0-9a-f]*[a-f])[0-9a-f]{7,64}(?![0-9a-zA-Z])")
SEMVER = re.compile(r"(?<![\w.])v?\d+\.\d+(?:\.\d+)?(?:[-+][0-9A-Za-z.-]+)?(?![\w.])")
DATE = re.compile(r"\b(?:\d{4}-\d{2}-\d{2}|\d{2}/\d{2}/\d{4})\b")
NUMBER = re.compile(r"(?<![\w.])\d+(?:[.,]\d+)*(?![\w.])")
# Le righe di memoria condivisa hanno una forma fissa e non sono prosa.
MEMORY_LINE = re.compile(r"^\s*[-*]?\s*\[\d{4}-\d{2}-\d{2}\]\s*\[[^\]]+\].*$", re.MULTILINE)
VERDICT = re.compile(
    r"(?<![A-Z_])(GO_CON_CONDIZIONI|EVIDENZA_INSUFFICIENTE|NO_GO|GO)(?![A-Z_])"
)

LABELS = {
    "frontmatter": "frontmatter",
    "code": "blocchi e frammenti di codice",
    "urls": "URL",
    "identifiers": "identificatori",
    "dates": "date",
    "numbers": "numeri e formule",
    "memory_lines": "righe di memoria",
    "verdicts": "verdetti",
}


def extract(text: str) -> dict[str, Counter]:
    frontmatter = FRONTMATTER.match(text)
    fenced = [block.strip() for block in FENCED.findall(text)]
    inline = [snippet.strip() for snippet in INLINE_CODE.findall(text)]
    identifiers = HEXID.findall(text) + SEMVER.findall(text)
    return {
        "frontmatter": Counter([frontmatter.group(1).strip()] if frontmatter else []),
        "code": Counter(fenced + inline),
        "urls": Counter(URL.findall(text)),
        "identifiers": Counter(identifiers),
        "dates": Counter(DATE.findall(text)),
        "numbers": Counter(NUMBER.findall(text)),
        "memory_lines": Counter(line.strip() for line in MEMORY_LINE.findall(text)),
        "verdicts": Counter(VERDICT.findall(text)),
    }


def compare(before: str, after: str) -> dict:
    left, right = extract(before), extract(after)
    changes: dict[str, dict] = {}
    violations: list[str] = []

    for key in LABELS:
        removed = left[key] - right[key]
        added = right[key] - left[key]
        changes[key] = {
            "removed": sorted(removed.elements()),
            "added": sorted(added.elements()),
        }
        if removed or added:
            violations.append(
                f"{LABELS[key]}: {sum(removed.values())} rimossi, {sum(added.values())} aggiunti"
            )

    return {
        "changes": changes,
        "violations": violations,
        "ok": not violations,
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Confronta il testo prima e dopo la revisione di prosa e riporta ogni "
            "differenza in frontmatter, codice, URL, identificatori, date, numeri, "
            "righe di memoria e verdetti: cio' che la revisione non puo' toccare."
        )
    )
    parser.add_argument("before", help="testo prima della revisione di prosa")
    parser.add_argument("after", help="testo dopo la revisione di prosa")
    parser.add_argument("-o", "--output", help="file di destinazione del JSON (default: stdout)")
    parser.add_argument("--verbose", action="store_true", help="diagnostica su stderr")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    before, after = Path(args.before), Path(args.after)
    for path in (before, after):
        if not path.is_file():
            print(f"errore: file non leggibile: {path}", file=sys.stderr)
            return 2
    try:
        result = compare(
            before.read_text(encoding="utf-8"), after.read_text(encoding="utf-8")
        )
    except OSError as error:
        print(f"errore di filesystem: {error}", file=sys.stderr)
        return 2

    result = {"before": str(before), "after": str(after), **result}
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
