#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""Lock esclusivo e scrittura atomica sulla cartella di una delivery.

Due esecuzioni sullo stesso slug non devono sovrapporsi, e un file di stato non
deve mai restare scritto a meta'. Entrambe le garanzie richiedono primitive che
solo il sistema operativo puo' dare: `O_EXCL` crea il lock o fallisce, mai
tutt'e due; `os.replace` sostituisce il file o non lo tocca. Una sequenza di
comandi di shell che controlla e poi crea lascia passare due esecuzioni.

Un lock piu' vecchio della soglia e' orfano di un run interrotto: lo script lo
riporta, e sta a chi lo legge decidere se rilevarlo con `--force-stale`.

Uscita: JSON su stdout. Exit 0 = fatto, 1 = lock occupato o rifiuto, 2 = errore.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

LOCK_NAME = ".lock"
STALE_AFTER_SECONDS = 3600


def now_utc() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def read_lock(lock: Path) -> dict:
    try:
        return json.loads(lock.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}


def lock_age_seconds(payload: dict) -> float | None:
    stamp = payload.get("acquired_at")
    if not stamp:
        return None
    try:
        acquired = datetime.strptime(stamp, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
    except ValueError:
        return None
    return (datetime.now(timezone.utc) - acquired).total_seconds()


def acquire(folder: Path, stale_after: int, force_stale: bool) -> tuple[dict, int]:
    folder.mkdir(parents=True, exist_ok=True)
    lock = folder / LOCK_NAME
    payload = json.dumps({"pid": os.getpid(), "acquired_at": now_utc()}, ensure_ascii=False)

    try:
        handle = os.open(lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o644)
    except FileExistsError:
        existing = read_lock(lock)
        age = lock_age_seconds(existing)
        stale = age is not None and age > stale_after
        if not (stale and force_stale):
            return (
                {
                    "action": "acquire",
                    "lock": str(lock),
                    "acquired": False,
                    "held_by": existing,
                    "age_seconds": age,
                    "stale": stale,
                    "reason": (
                        "lock orfano: rileva con --force-stale e registralo nella cronologia"
                        if stale
                        else "un'altra esecuzione sta scrivendo su questo slug"
                    ),
                },
                1,
            )
        lock.write_text(payload, encoding="utf-8")
        return (
            {
                "action": "acquire",
                "lock": str(lock),
                "acquired": True,
                "took_over_stale": True,
                "previous": existing,
                "age_seconds": age,
            },
            0,
        )

    with os.fdopen(handle, "w", encoding="utf-8") as stream:
        stream.write(payload)
    return {"action": "acquire", "lock": str(lock), "acquired": True, "took_over_stale": False}, 0


def write(destination: Path, source: Path) -> tuple[dict, int]:
    if not source.is_file():
        return {"action": "write", "written": False, "reason": f"temporaneo assente: {source}"}, 2
    lock = destination.parent / LOCK_NAME
    if not lock.exists():
        return (
            {
                "action": "write",
                "written": False,
                "reason": f"nessun lock su {destination.parent}: acquisiscilo prima di scrivere",
            },
            1,
        )
    destination.parent.mkdir(parents=True, exist_ok=True)
    os.replace(source, destination)
    return {
        "action": "write",
        "written": True,
        "destination": str(destination),
        "bytes": destination.stat().st_size,
    }, 0


def release(folder: Path) -> tuple[dict, int]:
    lock = folder / LOCK_NAME
    if not lock.exists():
        return {"action": "release", "lock": str(lock), "released": False}, 0
    lock.unlink()
    return {"action": "release", "lock": str(lock), "released": True}, 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Lock esclusivo per slug e scrittura atomica dei file di una delivery. "
            "--acquire crea il lock o fallisce; --write sostituisce il file con un "
            "rename atomico; --release lo toglie."
        )
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--acquire", metavar="CARTELLA", help="acquisisce il lock della delivery")
    group.add_argument("--write", metavar="DESTINAZIONE", help="file da sostituire atomicamente")
    group.add_argument("--release", metavar="CARTELLA", help="rilascia il lock della delivery")
    parser.add_argument("--from", dest="source", help="file temporaneo da spostare, con --write")
    parser.add_argument(
        "--stale-after",
        type=int,
        default=STALE_AFTER_SECONDS,
        help=f"secondi oltre i quali un lock e' orfano (default: {STALE_AFTER_SECONDS})",
    )
    parser.add_argument(
        "--force-stale",
        action="store_true",
        help="rileva un lock orfano invece di fermarsi; va registrato nella cronologia",
    )
    parser.add_argument("-o", "--output", help="file di destinazione del JSON (default: stdout)")
    parser.add_argument("--verbose", action="store_true", help="diagnostica su stderr")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        if args.acquire:
            result, code = acquire(Path(args.acquire), args.stale_after, args.force_stale)
        elif args.write:
            if not args.source:
                print("errore: --write richiede --from <temporaneo>", file=sys.stderr)
                return 2
            result, code = write(Path(args.write), Path(args.source))
        else:
            result, code = release(Path(args.release))
    except OSError as error:
        print(f"errore di filesystem: {error}", file=sys.stderr)
        return 2

    payload = json.dumps(result, ensure_ascii=False, indent=2)
    if args.output:
        Path(args.output).write_text(payload + "\n", encoding="utf-8")
    else:
        print(payload)
    if args.verbose and result.get("reason"):
        print(result["reason"], file=sys.stderr)
    return code


if __name__ == "__main__":
    sys.exit(main())
