#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""Congela e verifica l'identita' del candidato di release.

Il gate vale per una release e non per un'altra, quindi l'identita' va congelata
prima dei controlli. Cosa sia congelabile e' esatto: un digest o corrisponde al
file o no, `latest` non identifica niente, uno SHA-256 ha 64 cifre esadecimali.

Se il candidato sia semanticamente lo stesso della volta prima resta un giudizio
di Milo e del modello; qui si constata l'identita' dichiarata.

Uscita: JSON su stdout. Exit 0 = identita' congelabile, 1 = no, 2 = errore.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from identity import (  # noqa: E402
    MUTABLE_LABELS,
    immutable,
    is_commit,
    is_digest,
    is_snapshot_ref,
    sha256_of,
)

FIELDS = ("version", "commit", "artifact", "digest", "target", "content_snapshot")


def freeze(args: argparse.Namespace) -> dict:
    blocking: list[str] = []
    identity = {field: getattr(args, field) or None for field in FIELDS}

    # Un valore vale come identita' per la sua forma, non per la sua parola:
    # l'etichetta mobile qui e' solo un avviso leggibile. `target` non entra
    # affatto, perche' dice *dove* si consegna e `production` e' il suo nome
    # giusto.
    warnings: list[str] = []
    for field in ("version", "commit", "content_snapshot"):
        value = identity[field]
        if value and value.lower() in MUTABLE_LABELS:
            warnings.append(f"`{field}={value}` e' un'etichetta mobile e non identifica la release")

    computed = None
    if identity["artifact"]:
        path = Path(identity["artifact"])
        if path.is_file():
            computed = sha256_of(path)
        else:
            blocking.append(f"artefatto non leggibile: {path}")

    digest_state = {"declared": identity["digest"], "format_valid": None, "computed": computed,
                    "matches": None}
    if identity["digest"]:
        declared = identity["digest"].strip().lower()
        identity["digest"] = declared
        digest_state["declared"] = declared
        digest_state["format_valid"] = is_digest(declared)
        if not digest_state["format_valid"]:
            blocking.append("il digest dichiarato non ha 64 cifre esadecimali: non e' uno SHA-256")
        if computed:
            digest_state["matches"] = digest_state["format_valid"] and declared == computed
            if not digest_state["matches"]:
                blocking.append("il digest dichiarato non corrisponde all'artefatto")
    elif computed:
        blocking.append(f"artefatto senza digest dichiarato; calcolato: {computed}")

    commit = identity["commit"] or ""
    if commit and is_commit(commit) and commit.strip().isdigit():
        warnings.append(
            f"`commit={commit}` e' tutto decimale: sembra un numero di revisione, non un hash"
        )
    if commit and not is_commit(commit):
        blocking.append(f"`commit={commit}` non e' un hash: non e' immutabile")
    snapshot = identity["content_snapshot"]
    if snapshot and not is_snapshot_ref(snapshot):
        blocking.append(
            f"`content_snapshot={snapshot}` non e' un riferimento fisso: serve per intero "
            "un timestamp, un hash o una revisione `r<numero>`"
        )

    verified = immutable(commit, identity["digest"], snapshot, digest_state.get("matches"))
    if not verified:
        blocking.append(
            "nessun identificatore immutabile: servono un commit hash, un artefatto con "
            "digest corrispondente o uno snapshot dei contenuti"
        )
    if not identity["target"]:
        blocking.append("target non dichiarato")

    return {
        "release_identity": identity,
        "digest": digest_state,
        "immutable_verified": verified,
        "warnings": warnings,
        "blocking": blocking,
        "ok": not blocking,
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Congela l'identita' del candidato: verifica formato e corrispondenza dello "
            "SHA-256, rifiuta le etichette mobili e dice quali identificatori sono "
            "davvero immutabili."
        )
    )
    parser.add_argument("--version", help="versione o tag del candidato")
    parser.add_argument("--commit", help="commit immutabile")
    parser.add_argument("--artifact", help="file dell'artefatto su cui calcolare lo SHA-256")
    parser.add_argument("--digest", help="digest SHA-256 dichiarato")
    parser.add_argument("--target", help="target della delivery")
    parser.add_argument(
        "--content-snapshot",
        help="revisione o snapshot dei contenuti, quando non sono versionati nel codice",
    )
    parser.add_argument("-o", "--output", help="file di destinazione del JSON (default: stdout)")
    parser.add_argument("--verbose", action="store_true", help="diagnostica su stderr")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        result = freeze(args)
    except OSError as error:
        print(f"errore di filesystem: {error}", file=sys.stderr)
        return 2

    payload = json.dumps(result, ensure_ascii=False, indent=2)
    if args.output:
        Path(args.output).write_text(payload + "\n", encoding="utf-8")
    else:
        print(payload)
    if args.verbose:
        for line in result["blocking"]:
            print(f"blocco: {line}", file=sys.stderr)
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
