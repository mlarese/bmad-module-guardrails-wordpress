#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = ["pytest"]
# ///
"""Test di release_identity.py."""

from __future__ import annotations

import hashlib
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from release_identity import build_parser, freeze  # noqa: E402


COMMIT = "6ed04b2a1c3d5e7f9a0b1c2d3e4f5a6b7c8d9e0f"


def run(*argv: str) -> dict:
    return freeze(build_parser().parse_args(list(argv)))


def artifact(tmp_path: Path, content: bytes = b"tema") -> tuple[str, str]:
    path = tmp_path / "theme.zip"
    path.write_bytes(content)
    return str(path), hashlib.sha256(content).hexdigest()


class TestCongelamento:
    def test_commit_artefatto_e_digest_coerenti(self, tmp_path: Path) -> None:
        path, digest = artifact(tmp_path)
        result = run(
            "--commit", COMMIT, "--artifact", path, "--digest", digest, "--target", "produzione"
        )
        assert result["ok"] is True
        assert result["immutable_verified"] == ["commit", "digest"]

    def test_digest_non_corrispondente_blocca(self, tmp_path: Path) -> None:
        path, _ = artifact(tmp_path)
        result = run("--commit", COMMIT, "--artifact", path, "--digest", "0" * 64, "--target", "p")
        assert any("non corrisponde" in b for b in result["blocking"])

    def test_digest_di_formato_sbagliato_blocca(self) -> None:
        result = run("--commit", COMMIT, "--digest", "e41b90", "--target", "p")
        assert result["digest"]["format_valid"] is False

    def test_artefatto_senza_digest_dichiarato_blocca(self, tmp_path: Path) -> None:
        path, calcolato = artifact(tmp_path)
        result = run("--commit", COMMIT, "--artifact", path, "--target", "p")
        assert any(calcolato in b for b in result["blocking"])

    def test_etichetta_mobile_e_un_avviso_non_un_blocco(self) -> None:
        # A decidere è la forma: `version` non entra fra gli immutabili, quindi
        # `latest` lì è un avviso leggibile, non il criterio.
        result = run("--version", "latest", "--commit", COMMIT, "--target", "p")
        assert any("etichetta mobile" in w for w in result["warnings"])
        assert result["blocking"] == []

    def test_una_frase_con_una_cifra_non_e_uno_snapshot(self) -> None:
        result = run("--content-snapshot", "backup di ieri, 2 copie", "--target", "produzione")
        assert result["immutable_verified"] == []
        assert any("riferimento fisso" in b for b in result["blocking"])

    def test_un_etichetta_mobile_composta_non_passa(self) -> None:
        result = run("--content-snapshot", "latest nightly build 3", "--target", "produzione")
        assert result["ok"] is False

    def test_lo_snapshot_con_prefisso_e_timestamp_passa(self) -> None:
        result = run("--content-snapshot", "content-20260808T180000Z", "--target", "produzione")
        assert result["immutable_verified"] == ["content_snapshot"]

    def test_una_revisione_numerata_passa(self) -> None:
        result = run("--content-snapshot", "r4821", "--target", "produzione")
        assert result["immutable_verified"] == ["content_snapshot"]

    def test_un_digest_senza_artefatto_non_e_verificato(self) -> None:
        result = run("--digest", "e" * 64, "--target", "produzione")
        assert result["immutable_verified"] == []
        assert any("nessun identificatore immutabile" in b for b in result["blocking"])

    def test_il_target_di_produzione_non_e_unetichetta_mobile(self) -> None:
        # `target` dice dove si consegna, non quale revisione: `production` e' il
        # suo nome giusto e non puo' bloccare la delivery.
        result = run("--commit", COMMIT, "--version", "1.4.0", "--target", "production")
        assert result["blocking"] == []
        assert result["ok"] is True

    def test_commit_non_hash_blocca(self) -> None:
        result = run("--commit", "HEAD", "--target", "p")
        assert any("non e' un hash" in b for b in result["blocking"])

    def test_snapshot_dei_contenuti_regge_da_solo(self) -> None:
        result = run("--content-snapshot", "content-20260808T180000Z", "--target", "produzione")
        assert result["immutable_verified"] == ["content_snapshot"]
        assert result["ok"] is True

    def test_uno_snapshot_a_parole_non_e_unidentita(self) -> None:
        result = run("--content-snapshot", "backup di ieri", "--target", "produzione")
        assert any("riferimento fisso" in b for b in result["blocking"])
        assert result["ok"] is False

    def test_senza_identificatori_blocca(self) -> None:
        result = run("--version", "1.0", "--target", "produzione")
        assert any("nessun identificatore immutabile" in b for b in result["blocking"])

    def test_target_mancante_blocca(self) -> None:
        result = run("--commit", COMMIT)
        assert any("target non dichiarato" in b for b in result["blocking"])

    def test_artefatto_illeggibile_blocca(self, tmp_path: Path) -> None:
        result = run("--artifact", str(tmp_path / "assente.zip"), "--target", "p")
        assert any("non leggibile" in b for b in result["blocking"])

    def test_il_digest_viene_normalizzato_in_minuscolo(self, tmp_path: Path) -> None:
        path, digest = artifact(tmp_path)
        result = run("--artifact", path, "--digest", digest.upper(), "--target", "p")
        assert result["release_identity"]["digest"] == digest
        assert result["digest"]["matches"] is True
