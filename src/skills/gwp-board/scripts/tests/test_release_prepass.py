#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = ["pytest"]
# ///
"""Test di release_prepass.py."""

from __future__ import annotations

import hashlib
import subprocess
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from release_prepass import build_parser, analyze, slugify  # noqa: E402


COMMIT = "3b1d9e7a0c4f5b6d7e8f9a0b1c2d3e4f5a6b7c8d"


def run(tmp_path: Path, *argv: str) -> dict:
    args = build_parser().parse_args(
        ["--output-folder", str(tmp_path / "out"), *argv]
    )
    return analyze(args)


def artifact(tmp_path: Path, content: bytes = b"pacchetto") -> tuple[Path, str]:
    path = tmp_path / "bundle.tgz"
    path.write_bytes(content)
    return path, hashlib.sha256(content).hexdigest()


class TestSlugify:
    def test_normalizza_accenti_e_separatori(self) -> None:
        assert slugify("Città", "npm pubblico") == "citta-npm-pubblico"

    def test_scarta_le_parti_vuote(self) -> None:
        assert slugify("", "prod", "") == "prod"

    def test_tronca_senza_lasciare_trattini_finali(self) -> None:
        assert not slugify("x" * 59 + " coda").endswith("-")


class TestIdentita:
    def test_commit_e_digest_coerenti_non_bloccano(self, tmp_path: Path) -> None:
        path, digest = artifact(tmp_path)
        result = run(
            tmp_path,
            "--artifact", str(path),
            "--digest", digest,
            "--id", f"commit={COMMIT}",
            "--environment", "npm pubblico",
            "--scope", "pacchetto CLI",
        )
        assert result["ok"] is True
        assert result["identity"]["well_formed"] == ["commit", "digest"]
        # Il commit non e' stato risolto in nessun repository: ben formato non
        # significa esistente, e il gate deve poterlo distinguere.
        assert result["identity"]["verified"] == ["digest"]
        assert any("nessuno l'ha risolto" in w for w in result["warnings"])
        assert result["identity"]["digest"]["matches"] is True

    def test_digest_che_non_corrisponde_blocca(self, tmp_path: Path) -> None:
        path, _ = artifact(tmp_path)
        result = run(
            tmp_path,
            "--artifact", str(path),
            "--digest", "0" * 64,
            "--id", f"commit={COMMIT}",
            "--environment", "prod",
            "--scope", "api",
        )
        assert result["ok"] is False
        assert any("non corrisponde" in b for b in result["blocking"])

    def test_digest_di_formato_sbagliato_blocca(self, tmp_path: Path) -> None:
        result = run(
            tmp_path,
            "--digest", "abc123",
            "--environment", "prod",
            "--scope", "api",
        )
        assert result["identity"]["digest"]["format_valid"] is False
        assert any("64 cifre" in b for b in result["blocking"])

    def test_etichetta_mobile_blocca(self, tmp_path: Path) -> None:
        result = run(
            tmp_path,
            "--id", "tag=latest",
            "--id", f"commit={COMMIT}",
            "--environment", "prod",
            "--scope", "api",
        )
        assert result["identity"]["mutable_labels"] == ["tag"]
        assert any("etichetta mobile" in b for b in result["blocking"])

    def test_commit_non_hash_non_e_immutabile(self, tmp_path: Path) -> None:
        result = run(
            tmp_path, "--id", "commit=HEAD", "--environment", "prod", "--scope", "api"
        )
        assert result["identity"]["well_formed"] == []
        assert any("non e' un hash" in b for b in result["blocking"])

    def test_senza_identificatori_blocca(self, tmp_path: Path) -> None:
        result = run(tmp_path, "--environment", "prod", "--scope", "api")
        assert any("nessun identificatore immutabile" in b for b in result["blocking"])

    def test_identificatore_malformato_e_un_errore(self, tmp_path: Path) -> None:
        with pytest.raises(ValueError):
            run(tmp_path, "--id", "solocommit")

    def test_artefatto_mancante_blocca(self, tmp_path: Path) -> None:
        result = run(
            tmp_path,
            "--artifact", str(tmp_path / "assente.tgz"),
            "--environment", "prod",
            "--scope", "api",
        )
        assert any("non leggibile" in b for b in result["blocking"])


class TestAmbienteEPerimetro:
    def test_ambiente_mancante_blocca(self, tmp_path: Path) -> None:
        result = run(tmp_path, "--id", f"commit={COMMIT}", "--scope", "api")
        assert any("ambiente non dichiarato" in b for b in result["blocking"])

    def test_perimetro_mancante_blocca(self, tmp_path: Path) -> None:
        result = run(tmp_path, "--id", f"commit={COMMIT}", "--environment", "prod")
        assert any("perimetro non dichiarato" in b for b in result["blocking"])


class TestReport:
    def test_slug_deriva_dal_commit_dallambiente_e_dal_perimetro(self, tmp_path: Path) -> None:
        result = run(
            tmp_path,
            "--id", f"commit={COMMIT}",
            "--environment", "npm pubblico",
            "--scope", "CLI",
            "--started-at", "20260809T120000Z",
        )
        assert result["report"]["release_slug"] == "3b1d9e7a0c4f-npm-pubblico-cli"
        assert result["report"]["path"].endswith(
            "release-gates/3b1d9e7a0c4f-npm-pubblico-cli-20260809T120000Z.md"
        )

    def test_senza_identita_usa_lo_slug_dedicato(self, tmp_path: Path) -> None:
        result = run(tmp_path, "--started-at", "20260809T120000Z")
        assert result["report"]["release_slug"] == "release-non-identificata"

    def test_lo_stesso_input_produce_lo_stesso_slug(self, tmp_path: Path) -> None:
        argv = ("--id", f"commit={COMMIT}", "--environment", "prod", "--scope", "api")
        primo = run(tmp_path, *argv, "--started-at", "20260809T120000Z")
        secondo = run(tmp_path, *argv, "--started-at", "20260809T120000Z")
        assert primo["report"] == secondo["report"]

    def test_la_cartella_del_report_viene_creata_e_verificata(self, tmp_path: Path) -> None:
        result = run(tmp_path, "--id", f"commit={COMMIT}", "--environment", "p", "--scope", "s")
        assert result["report"]["directory_writable"] is True
        assert (tmp_path / "out" / "release-gates").is_dir()

    def test_cartella_non_scrivibile_blocca(self, tmp_path: Path) -> None:
        occupato = tmp_path / "out"
        occupato.write_text("non sono una cartella", encoding="utf-8")
        result = run(tmp_path, "--id", f"commit={COMMIT}", "--environment", "p", "--scope", "s")
        assert result["report"]["directory_writable"] is False
        assert any("non creabile" in b or "non scrivibile" in b for b in result["blocking"])

    def test_timestamp_di_default_e_utc_ordinabile(self, tmp_path: Path) -> None:
        result = run(tmp_path, "--id", f"commit={COMMIT}", "--environment", "p", "--scope", "s")
        started = result["report"]["gate_started_at_utc"]
        assert started.endswith("Z") and "T" in started and len(started) == 16


class TestCoerenzaRepo:
    @staticmethod
    def _repo(tmp_path: Path) -> tuple[Path, str]:
        repo = tmp_path / "repo"
        repo.mkdir()
        env = {
            "GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@e",
            "GIT_COMMITTER_NAME": "t", "GIT_COMMITTER_EMAIL": "t@e",
            "PATH": "/usr/bin:/bin:/usr/local/bin",
        }
        subprocess.run(["git", "init", "-q"], cwd=repo, check=True, env=env)
        (repo / "f.txt").write_text("x", encoding="utf-8")
        subprocess.run(["git", "add", "f.txt"], cwd=repo, check=True, env=env)
        subprocess.run(["git", "commit", "-qm", "uno"], cwd=repo, check=True, env=env)
        subprocess.run(["git", "tag", "v1.0.0"], cwd=repo, check=True, env=env)
        head = subprocess.run(
            ["git", "rev-parse", "HEAD"], cwd=repo, capture_output=True, text=True, env=env
        ).stdout.strip()
        return repo, head

    def test_tag_coerente_col_commit(self, tmp_path: Path) -> None:
        repo, head = self._repo(tmp_path)
        result = run(
            tmp_path,
            "--repo", str(repo),
            "--id", f"commit={head}",
            "--id", "tag=v1.0.0",
            "--environment", "prod",
            "--scope", "app",
        )
        assert result["identity"]["consistency"][0]["consistent"] is True
        assert result["identity"]["verified"] == ["commit"]
        assert result["warnings"] == []
        assert result["ok"] is True

    def test_tag_inesistente_blocca(self, tmp_path: Path) -> None:
        repo, head = self._repo(tmp_path)
        result = run(
            tmp_path,
            "--repo", str(repo),
            "--id", f"commit={head}",
            "--id", "tag=v9.9.9",
            "--environment", "prod",
            "--scope", "app",
        )
        assert any("non risolve a un commit" in b for b in result["blocking"])

    def test_repo_senza_git_blocca(self, tmp_path: Path) -> None:
        result = run(
            tmp_path,
            "--repo", str(tmp_path),
            "--id", f"commit={COMMIT}",
            "--environment", "prod",
            "--scope", "app",
        )
        assert any("repository non leggibile" in b for b in result["blocking"])
