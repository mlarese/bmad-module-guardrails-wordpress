#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""Pre-pass sul registro dei rischi accettati, filtrato per identita' e target.

Un finding e' accettato solo se una riga del registro condiviso lo copre, e
quella riga ha una forma fissa: `[AAAA-MM-GG] [figura] rischio — motivo —
ambito`. Trovarla e' una ricerca esatta su un file che cresce col progetto;
l'errore che questo script esiste per evitare e' dichiarare accettato un rischio
che nessuno ha accettato.

Se l'ambito copra davvero *questo* finding resta un giudizio: lo script dice
quali righe nominano l'identita' o il target, quali sono scadute e quali non
rispettano il formato.

Uscita: JSON su stdout. Exit 0 = almeno una riga pertinente, 1 = nessuna, 2 = errore.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import unicodedata
from datetime import date
from pathlib import Path

# `[AAAA-MM-GG] [figura] rischio — motivo — ambito`, con il trattino lungo o
# la sequenza `--` come separatore.
ROW = re.compile(
    r"^\s*[-*]?\s*\[(?P<data>\d{4}-\d{2}-\d{2})\]\s*\[(?P<figura>[^\]]+)\]\s*(?P<resto>.+)$"
)
SEPARATOR = re.compile(r"\s+—\s+|\s+--\s+")
# Una data qualsiasi nell'ambito, in una delle due forme che si scrivono.
DATE = r"(?:(\d{4})-(\d{2})-(\d{2})|(\d{2})/(\d{2})/(\d{4}))"
ANY_DATE = re.compile(DATE)
# La scadenza e' la data *legata* alla formula che la introduce. Prendere la
# minima fra quelle presenti scambierebbe «valida dal 2026-01-15 fino al
# 2027-06-30» per una riga scaduta.
EXPIRY = re.compile(
    r"(?:fino a[l]?|scade(?:nza)?|entro(?: il)?|valid[oa] fino a[l]?|expires?)\s*:?\s*" + DATE,
    re.I,
)
HEX = re.compile(r"[0-9a-f]{7,64}")


def fold(text: str) -> str:
    stripped = unicodedata.normalize("NFKD", text)
    ascii_only = stripped.encode("ascii", "ignore").decode("ascii").lower()
    return re.sub(r"[^a-z0-9]+", " ", ascii_only).strip()


def normalize_date(match: re.Match) -> str:
    """Sia `2026-12-31` sia `31/12/2026` diventano confrontabili come stringhe.

    I gruppi della data sono gli ultimi sei del pattern, così la funzione vale
    sia per `ANY_DATE` sia per `EXPIRY`, che la incorpora.
    """
    year, month, day, d, m, y = match.groups()[-6:]
    return f"{year}-{month}-{day}" if year else f"{y}-{m}-{d}"


def matched_on(scope: str, needles: list[str]) -> str | None:
    """Su cosa ha combaciato l'ambito, o None.

    Il confronto è su token interi: `preprod` non deve rispondere per `prod`.
    L'unica eccezione è fra riferimenti esadecimali, dove un commit breve e uno
    lungo nominano la stessa cosa.
    """
    scope_tokens = scope.split()
    for needle in needles:
        if not needle:
            continue
        needle_tokens = needle.split()
        # Sequenza di token: `staging casa verde` dentro l'ambito, non un pezzo
        # di parola.
        for index in range(len(scope_tokens) - len(needle_tokens) + 1):
            if scope_tokens[index:index + len(needle_tokens)] == needle_tokens:
                return needle
        if HEX.fullmatch(needle):
            for token in scope_tokens:
                if HEX.fullmatch(token) and (
                    token.startswith(needle) or needle.startswith(token)
                ):
                    return token
    return None


def parse_rows(text: str) -> tuple[list[dict], list[str]]:
    rows: list[dict] = []
    malformed: list[str] = []
    for line in text.split("\n"):
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        match = ROW.match(line)
        if not match:
            malformed.append(line.strip())
            continue
        parts = SEPARATOR.split(match.group("resto"))
        if len(parts) < 3:
            malformed.append(line.strip())
            continue
        rows.append(
            {
                "date": match.group("data"),
                "figure": match.group("figura").strip(),
                "risk": parts[0].strip(),
                "reason": parts[1].strip(),
                "scope": " — ".join(part.strip() for part in parts[2:]),
                "line": line.strip(),
            }
        )
    return rows, malformed


def analyze(path: Path, needles: list[str], as_of: str) -> dict:
    if not path.is_file():
        return {
            "file": str(path),
            "file_present": False,
            "readable": False,
            "rows_total": 0,
            "rows_matching": [],
            "rows_expired": [],
            "rows_expiry_unclear": [],
            "rows_malformed": [],
            "ok": False,
        }

    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as error:
        return {
            "file": str(path),
            "file_present": True,
            "readable": False,
            "reason": str(error),
            "rows_total": 0,
            "rows_matching": [],
            "rows_expired": [],
            "rows_expiry_unclear": [],
            "rows_malformed": [],
            "ok": False,
        }

    rows, malformed = parse_rows(text)
    folded = [fold(n) for n in needles if n]

    matching, expired, unclear = [], [], []
    for row in rows:
        scope = fold(row["scope"])
        matched = matched_on(scope, folded)
        if folded and not matched:
            continue
        row = {**row, "matched_on": matched}
        deadline_match = EXPIRY.search(row["scope"])
        dates = [normalize_date(match) for match in ANY_DATE.finditer(row["scope"])]
        if not dates:
            matching.append({**row, "expires_on": None})
            continue
        if not deadline_match:
            # C'e' una data ma nessuna formula la lega a una scadenza: chi legge
            # deve guardarla, e intanto la riga non copre nessun finding.
            unclear.append({**row, "dates_found": dates})
            continue
        deadline = normalize_date(deadline_match)
        row = {**row, "expires_on": deadline}
        (expired if deadline < as_of else matching).append(row)

    return {
        "file": str(path),
        "file_present": True,
        "readable": True,
        "as_of": as_of,
        "needles": needles,
        "rows_total": len(rows),
        "rows_matching": matching,
        "rows_expired": expired,
        "rows_expiry_unclear": unclear,
        "rows_malformed": malformed,
        "ok": bool(matching),
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Cerca nel registro dei rischi accettati le righe il cui ambito nomina "
            "l'identita' della release o il target, e separa quelle scadute da quelle "
            "vive e dalle righe fuori formato."
        )
    )
    parser.add_argument(
        "registry",
        help="registro condiviso, di norma {project-root}/_bmad/memory/grl-shared/accepted-risks.md",
    )
    parser.add_argument(
        "--match",
        action="append",
        metavar="VALORE",
        help="identificatore o target che l'ambito deve nominare; ripetibile",
    )
    parser.add_argument(
        "--as-of",
        default=date.today().isoformat(),
        help="data rispetto a cui una scadenza e' passata (default: oggi)",
    )
    parser.add_argument("-o", "--output", help="file di destinazione del JSON (default: stdout)")
    parser.add_argument("--verbose", action="store_true", help="diagnostica su stderr")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        result = analyze(Path(args.registry), args.match or [], args.as_of)
    except OSError as error:
        print(f"errore di filesystem: {error}", file=sys.stderr)
        return 2

    payload = json.dumps(result, ensure_ascii=False, indent=2)
    if args.output:
        Path(args.output).write_text(payload + "\n", encoding="utf-8")
    else:
        print(payload)
    if args.verbose and result["rows_malformed"]:
        for line in result["rows_malformed"]:
            print(f"riga fuori formato: {line}", file=sys.stderr)
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
