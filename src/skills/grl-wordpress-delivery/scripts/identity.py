#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# ///
"""Che cosa vale come identita' immutabile di una release. Una definizione sola.

Importato da `release_identity.py`, che congela il candidato, e da
`check_delivery.py`, che verifica la promozione: due copie divergenti farebbero
passare alla promozione un'identita' che il congelamento rifiuta.

Il criterio e' la forma, non la parola: un valore vale come identificatore solo
se corrisponde per intero a un formato dichiarato. Cosi' `latest nightly build 3`
non ha scampatoie che una lista di parole vietate lascerebbe aperte.
"""

from __future__ import annotations

import hashlib
import re
from pathlib import Path

SHA256 = re.compile(r"[0-9a-f]{64}")
COMMIT_HASH = re.compile(r"[0-9a-f]{7,40}")
# Timestamp compatto o ISO, hash, revisione numerica: eventualmente preceduti da
# un'etichetta (`content-`, `snap_`). Sempre per intero, mai in mezzo alla prosa.
SNAPSHOT_REF = re.compile(
    r"(?:[A-Za-z][\w.-]*[-_])?"
    r"(?:\d{8}T\d{6}Z|\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z?|[0-9a-f]{7,64}|r\d+)"
)

# Restano solo per un avviso leggibile: non decidono piu' se un valore identifica.
MUTABLE_LABELS = {
    "latest", "current", "stable", "head", "main", "master", "trunk", "edge",
    "nightly", "rolling", "dev", "develop", "prod", "production", "release",
}


def is_commit(value: str) -> bool:
    return bool(COMMIT_HASH.fullmatch(value.strip().lower()))


def is_digest(value: str) -> bool:
    return bool(SHA256.fullmatch(value.strip().lower()))


def is_snapshot_ref(value: str) -> bool:
    return bool(SNAPSHOT_REF.fullmatch(value.strip()))


def sha256_of(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def digest_matches(artifact: str | None, declared: str | None, base: Path | None = None) -> bool | None:
    """True/False se l'artefatto e' leggibile, None se non lo e'.

    None non e' un successo: un digest che nessuno ha ricalcolato resta
    dichiarato, mai verificato.
    """
    if not artifact or not declared or not is_digest(declared):
        return None
    path = Path(artifact)
    if not path.is_absolute() and base is not None:
        path = base / artifact
    if not path.is_file():
        return None
    return sha256_of(path) == declared.strip().lower()


def immutable(
    commit: str | None,
    digest: str | None,
    content_snapshot: str | None,
    digest_verified: bool | None,
) -> list[str]:
    """Gli identificatori che reggono davvero, nell'ordine in cui si preferiscono.

    Il digest entra solo se qualcuno l'ha ricalcolato sull'artefatto: una stringa
    di 64 esadecimali non prova niente da sola.
    """
    found: list[str] = []
    if commit and is_commit(commit):
        found.append("commit")
    if digest and is_digest(digest) and digest_verified:
        found.append("digest")
    if content_snapshot and is_snapshot_ref(content_snapshot):
        found.append("content_snapshot")
    return found
