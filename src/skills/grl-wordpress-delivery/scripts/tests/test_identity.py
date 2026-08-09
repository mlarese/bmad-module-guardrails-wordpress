#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = ["pytest"]
# ///
"""Test di identity.py, il modulo che decide che cosa vale come identità."""

from __future__ import annotations

import hashlib
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from identity import (  # noqa: E402
    digest_matches,
    immutable,
    is_commit,
    is_digest,
    is_snapshot_ref,
)


COMMIT = "6ed04b2a1c3d5e7f9a0b1c2d3e4f5a6b7c8d9e0f"


class TestForme:
    def test_un_hash_di_sette_cifre_e_un_commit(self) -> None:
        assert is_commit("6ed04b2") and is_commit(COMMIT)

    def test_head_non_e_un_commit(self) -> None:
        assert not is_commit("HEAD") and not is_commit("main")

    def test_un_digest_ha_sessantaquattro_cifre(self) -> None:
        assert is_digest("e" * 64) and not is_digest("e" * 63)

    def test_uno_snapshot_e_un_timestamp_un_hash_o_una_revisione(self) -> None:
        assert is_snapshot_ref("20260808T180000Z")
        assert is_snapshot_ref("content-20260808T180000Z")
        assert is_snapshot_ref("2026-08-08T18:00:00Z")
        assert is_snapshot_ref("6ed04b2a1c3d")
        assert is_snapshot_ref("r4821")

    def test_una_frase_con_una_cifra_non_e_uno_snapshot(self) -> None:
        # Il difetto che questo modulo esiste per chiudere: `search` accettava
        # qualunque numero in mezzo alla prosa.
        assert not is_snapshot_ref("backup di ieri, 2 copie")
        assert not is_snapshot_ref("latest nightly build 3")
        assert not is_snapshot_ref("snapshot del 9 agosto")

    def test_un_numero_nudo_non_e_uno_snapshot(self) -> None:
        assert not is_snapshot_ref("3")


class TestDigest:
    def test_corrisponde_al_file(self, tmp_path: Path) -> None:
        artefatto = tmp_path / "theme.zip"
        artefatto.write_bytes(b"tema")
        digest = hashlib.sha256(b"tema").hexdigest()
        assert digest_matches(str(artefatto), digest) is True

    def test_non_corrisponde(self, tmp_path: Path) -> None:
        artefatto = tmp_path / "theme.zip"
        artefatto.write_bytes(b"tema")
        assert digest_matches(str(artefatto), "0" * 64) is False

    def test_artefatto_irraggiungibile_non_e_un_successo(self, tmp_path: Path) -> None:
        assert digest_matches(str(tmp_path / "assente.zip"), "0" * 64) is None

    def test_path_relativo_alla_cartella_della_delivery(self, tmp_path: Path) -> None:
        (tmp_path / "theme.zip").write_bytes(b"tema")
        digest = hashlib.sha256(b"tema").hexdigest()
        assert digest_matches("theme.zip", digest, tmp_path) is True


class TestImmutabili:
    def test_il_commit_regge_da_solo(self) -> None:
        assert immutable(COMMIT, None, None, None) == ["commit"]

    def test_il_digest_regge_solo_se_verificato(self) -> None:
        assert immutable(None, "e" * 64, None, None) == []
        assert immutable(None, "e" * 64, None, True) == ["digest"]

    def test_un_digest_smentito_non_regge(self) -> None:
        assert immutable(None, "e" * 64, None, False) == []

    def test_lo_snapshot_regge_se_e_un_riferimento_fisso(self) -> None:
        assert immutable(None, None, "content-20260808T180000Z", None) == ["content_snapshot"]
        assert immutable(None, None, "backup di ieri 2 copie", None) == []

    def test_senza_niente_non_c_e_identita(self) -> None:
        assert immutable(None, None, None, None) == []
