#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""Pre-pass del release gate: identita' della release e destinazione del report.

Il gate deve legare il verdetto a una release identificata e scrivere il report
dove nessun gate precedente venga sovrascritto. Sono due lavori deterministici:
un digest o corrisponde al file o no, uno slug derivato dagli stessi input e'
sempre lo stesso, una cartella e' scrivibile o non lo e'.

Lo script constata; il verdetto resta del modello. Un `blocking` non e' un NO_GO:
dice che quella prova non regge, e il gate decide se cio' comporta
EVIDENZA_INSUFFICIENTE o altro.

Uscita: JSON su stdout. Exit 0 = nessun blocco, 1 = almeno un blocco, 2 = errore.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
import tempfile
import unicodedata
from datetime import datetime, timezone
from pathlib import Path

# Un'etichetta che domani punta a un altro contenuto non identifica una release:
# il gate varrebbe per qualcosa che non esiste piu'.
MUTABLE_LABELS = {
    "latest",
    "current",
    "stable",
    "head",
    "main",
    "master",
    "trunk",
    "edge",
    "nightly",
    "rolling",
    "dev",
    "develop",
    "prod",
    "production",
    "release",
}

SHA256 = re.compile(r"^[0-9a-f]{64}$")
# Un commit e' immutabile solo se e' un hash: `HEAD` o un nome di branch no.
COMMIT_HASH = re.compile(r"^[0-9a-f]{7,40}$")
SLUG_STRIP = re.compile(r"[^a-z0-9]+")

UNIDENTIFIED_SLUG = "release-non-identificata"
SLUG_MAX = 60


def slugify(*parts: str) -> str:
    """Slug sicuro per un nome di file, stabile a parita' di input."""
    joined = "-".join(p for p in parts if p)
    normalized = unicodedata.normalize("NFKD", joined)
    ascii_only = normalized.encode("ascii", "ignore").decode("ascii").lower()
    slug = SLUG_STRIP.sub("-", ascii_only).strip("-")
    return slug[:SLUG_MAX].strip("-")


def sha256_of(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def directory_writable(directory: Path) -> tuple[bool, str | None]:
    """Prova a creare la cartella e a scriverci: la sola esistenza non basta."""
    try:
        directory.mkdir(parents=True, exist_ok=True)
    except OSError as error:
        return False, f"cartella non creabile: {error}"
    try:
        handle, name = tempfile.mkstemp(dir=directory, prefix=".gate-probe-")
        os.close(handle)
        os.unlink(name)
    except OSError as error:
        return False, f"cartella non scrivibile: {error}"
    return True, None


def resolve_in_repo(repo: Path, revision: str) -> str | None:
    """Commit a cui un tag o una revisione punta davvero, se il repo e' leggibile."""
    result = subprocess.run(
        ["git", "rev-parse", "--verify", f"{revision}^{{commit}}"],
        cwd=repo,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        return None
    return result.stdout.strip() or None


def parse_identifiers(pairs: list[str]) -> dict[str, str]:
    identifiers: dict[str, str] = {}
    for pair in pairs:
        if "=" not in pair:
            raise ValueError(f"identificatore senza `=`: {pair}")
        key, value = pair.split("=", 1)
        key, value = key.strip(), value.strip()
        if not key:
            raise ValueError(f"identificatore senza chiave: {pair}")
        if value:
            identifiers[key] = value
    return identifiers


def analyze(args: argparse.Namespace) -> dict:
    blocking: list[str] = []
    identifiers = parse_identifiers(args.id or [])

    mutable = sorted(
        key for key, value in identifiers.items() if value.lower() in MUTABLE_LABELS
    )
    for key in mutable:
        blocking.append(
            f"`{key}={identifiers[key]}` e' un'etichetta mobile: non identifica la release"
        )

    artifact: dict = {"path": None, "exists": False, "sha256": None, "size_bytes": None}
    if args.artifact:
        path = Path(args.artifact)
        artifact["path"] = str(path)
        if path.is_file():
            artifact["exists"] = True
            artifact["sha256"] = sha256_of(path)
            artifact["size_bytes"] = path.stat().st_size
        else:
            blocking.append(f"artefatto non leggibile: {path}")

    digest: dict = {"declared": args.digest, "format_valid": None, "matches": None}
    if args.digest:
        declared = args.digest.strip().lower()
        digest["declared"] = declared
        digest["format_valid"] = bool(SHA256.match(declared))
        if not digest["format_valid"]:
            blocking.append(
                "il digest dichiarato non ha 64 cifre esadecimali: non e' uno SHA-256"
            )
        if artifact["sha256"]:
            digest["matches"] = digest["format_valid"] and declared == artifact["sha256"]
            if not digest["matches"]:
                blocking.append(
                    "il digest dichiarato non corrisponde a quello calcolato sull'artefatto"
                )

    # Due livelli distinti: la forma di una stringa e l'esistenza di cio' che
    # nomina. Un hash inventato e' ben formato e non identifica niente, quindi
    # `verified` accoglie solo cio' che qualcuno ha davvero risolto o calcolato.
    commit = identifiers.get("commit", "")
    well_formed: list[str] = []
    verified: list[str] = []
    warnings: list[str] = []
    if COMMIT_HASH.match(commit.lower()):
        well_formed.append("commit")
    if digest["format_valid"]:
        well_formed.append("digest")
    if digest.get("matches"):
        verified.append("digest")
    if commit and not COMMIT_HASH.match(commit.lower()):
        blocking.append(f"`commit={commit}` non e' un hash: non e' immutabile")

    consistency: list[dict] = []
    if args.repo:
        repo = Path(args.repo)
        if not (repo / ".git").exists():
            blocking.append(f"repository non leggibile: {repo}")
        else:
            resolved_commit = (
                resolve_in_repo(repo, commit) if COMMIT_HASH.match(commit.lower()) else None
            )
            for key in ("tag", "revision", "branch"):
                value = identifiers.get(key)
                if not value:
                    continue
                target = resolve_in_repo(repo, value)
                entry = {"identifier": key, "value": value, "resolved_commit": target}
                if target is None:
                    entry["consistent"] = None
                    blocking.append(f"`{key}={value}` non risolve a un commit del repository")
                elif resolved_commit:
                    entry["consistent"] = target == resolved_commit
                    if not entry["consistent"]:
                        blocking.append(
                            f"`{key}={value}` punta a {target[:12]}, non al commit dichiarato"
                        )
                else:
                    entry["consistent"] = None
                consistency.append(entry)
            if resolved_commit:
                verified.append("commit")

    if "commit" in well_formed and "commit" not in verified:
        warnings.append(
            "il commit e' ben formato ma nessuno l'ha risolto in un repository: "
            "passa `--repo` o dichiaralo fra le lacune del report"
        )

    if not well_formed:
        blocking.append(
            "nessun identificatore immutabile: servono un commit hash "
            "o un artefatto con digest"
        )

    started_at = args.started_at or datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    identity_part = ""
    if "commit" in well_formed:
        identity_part = commit.lower()[:12]
    elif artifact.get("sha256"):
        identity_part = str(artifact["sha256"])[:12]
    base = slugify(identity_part, args.environment or "", args.scope or "")
    release_slug = base or UNIDENTIFIED_SLUG

    output_folder = Path(args.output_folder)
    directory = output_folder / "release-gates"
    writable, reason = directory_writable(directory)
    if not writable:
        blocking.append(reason or "cartella del report non utilizzabile")
    report_path = directory / f"{release_slug}-{started_at}.md"

    if not args.environment:
        blocking.append("ambiente non dichiarato")
    if not args.scope:
        blocking.append("perimetro non dichiarato")

    return {
        "identity": {
            "declared": identifiers,
            "mutable_labels": mutable,
            "well_formed": well_formed,
            "verified": verified,
            "artifact": artifact,
            "digest": digest,
            "consistency": consistency,
        },
        "report": {
            "release_slug": release_slug,
            "gate_started_at_utc": started_at,
            "path": str(report_path),
            "directory_writable": writable,
            "already_exists": report_path.exists(),
        },
        "environment": args.environment or None,
        "scope": args.scope or None,
        "warnings": warnings,
        "blocking": blocking,
        "ok": not blocking,
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Pre-pass del release gate: verifica identita', digest e coerenza degli "
            "identificatori, e prepara slug, timestamp e destinazione del report."
        )
    )
    parser.add_argument(
        "--output-folder",
        required=True,
        help="cartella di output del progetto; il report va in <output-folder>/release-gates",
    )
    parser.add_argument("--artifact", help="file dell'artefatto su cui calcolare lo SHA-256")
    parser.add_argument("--digest", help="digest SHA-256 dichiarato per l'artefatto")
    parser.add_argument(
        "--id",
        action="append",
        metavar="CHIAVE=VALORE",
        help="identificatore dichiarato (commit=, tag=, version=, build=); ripetibile",
    )
    parser.add_argument("--environment", help="ambiente unico del gate")
    parser.add_argument("--scope", help="perimetro incluso del gate")
    parser.add_argument("--repo", help="repository git su cui risolvere tag e revisioni")
    parser.add_argument(
        "--started-at",
        help="timestamp UTC ordinabile del gate (default: ora corrente, formato 20260809T143000Z)",
    )
    parser.add_argument("-o", "--output", help="file di destinazione del JSON (default: stdout)")
    parser.add_argument("--verbose", action="store_true", help="diagnostica su stderr")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        result = analyze(args)
    except ValueError as error:
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
    if args.verbose:
        for line in result["blocking"]:
            print(f"blocco: {line}", file=sys.stderr)
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
