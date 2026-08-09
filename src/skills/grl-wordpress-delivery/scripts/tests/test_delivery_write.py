#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = ["pytest"]
# ///
"""Test di delivery_write.py."""

from __future__ import annotations

import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from delivery_write import LOCK_NAME, acquire, main, release, write  # noqa: E402


def invecchia(folder: Path, secondi: int) -> None:
    lock = folder / LOCK_NAME
    payload = json.loads(lock.read_text(encoding="utf-8"))
    passato = datetime.now(timezone.utc) - timedelta(seconds=secondi)
    payload["acquired_at"] = passato.strftime("%Y-%m-%dT%H:%M:%SZ")
    lock.write_text(json.dumps(payload), encoding="utf-8")


class TestLock:
    def test_acquisisce_e_scrive_pid_e_timestamp(self, tmp_path: Path) -> None:
        result, code = acquire(tmp_path / "wp-demo", 3600, False)
        assert (code, result["acquired"]) == (0, True)
        payload = json.loads((tmp_path / "wp-demo" / LOCK_NAME).read_text(encoding="utf-8"))
        assert payload["pid"] > 0 and payload["acquired_at"].endswith("Z")

    def test_la_seconda_acquisizione_fallisce(self, tmp_path: Path) -> None:
        acquire(tmp_path / "wp-demo", 3600, False)
        result, code = acquire(tmp_path / "wp-demo", 3600, False)
        assert (code, result["acquired"]) == (1, False)
        assert "un'altra esecuzione" in result["reason"]

    def test_un_lock_recente_non_e_orfano(self, tmp_path: Path) -> None:
        acquire(tmp_path / "wp-demo", 3600, False)
        result, _ = acquire(tmp_path / "wp-demo", 3600, True)
        assert result["stale"] is False
        assert result["acquired"] is False

    def test_un_lock_vecchio_e_orfano_e_va_dichiarato(self, tmp_path: Path) -> None:
        folder = tmp_path / "wp-demo"
        acquire(folder, 3600, False)
        invecchia(folder, 7200)
        result, code = acquire(folder, 3600, False)
        assert result["stale"] is True and code == 1
        assert "--force-stale" in result["reason"]

    def test_force_stale_rileva_il_lock_orfano(self, tmp_path: Path) -> None:
        folder = tmp_path / "wp-demo"
        acquire(folder, 3600, False)
        invecchia(folder, 7200)
        result, code = acquire(folder, 3600, True)
        assert (code, result["acquired"], result["took_over_stale"]) == (0, True, True)

    def test_release_toglie_il_lock(self, tmp_path: Path) -> None:
        acquire(tmp_path / "wp-demo", 3600, False)
        result, code = release(tmp_path / "wp-demo")
        assert (code, result["released"]) == (0, True)
        assert not (tmp_path / "wp-demo" / LOCK_NAME).exists()

    def test_release_senza_lock_non_e_un_errore(self, tmp_path: Path) -> None:
        result, code = release(tmp_path)
        assert (code, result["released"]) == (0, False)


class TestScrittura:
    def test_sostituisce_il_file_sotto_lock(self, tmp_path: Path) -> None:
        folder = tmp_path / "wp-demo"
        acquire(folder, 3600, False)
        destinazione = folder / "delivery.md"
        destinazione.write_text("vecchio\n", encoding="utf-8")
        temporaneo = folder / ".delivery.md.tmp"
        temporaneo.write_text("nuovo\n", encoding="utf-8")
        result, code = write(destinazione, temporaneo)
        assert (code, result["written"]) == (0, True)
        assert destinazione.read_text(encoding="utf-8") == "nuovo\n"
        assert not temporaneo.exists()

    def test_senza_lock_rifiuta_di_scrivere(self, tmp_path: Path) -> None:
        destinazione = tmp_path / "delivery.md"
        temporaneo = tmp_path / "tmp.md"
        temporaneo.write_text("nuovo\n", encoding="utf-8")
        result, code = write(destinazione, temporaneo)
        assert (code, result["written"]) == (1, False)
        assert not destinazione.exists()

    def test_temporaneo_assente_e_un_errore(self, tmp_path: Path) -> None:
        acquire(tmp_path, 3600, False)
        result, code = write(tmp_path / "delivery.md", tmp_path / "assente.tmp")
        assert code == 2 and result["written"] is False


class TestCli:
    def test_write_senza_from_e_un_errore(self, tmp_path: Path) -> None:
        assert main(["--write", str(tmp_path / "x.md")]) == 2

    def test_acquire_restituisce_zero_e_poi_uno(self, tmp_path: Path) -> None:
        folder = str(tmp_path / "wp-demo")
        assert main(["--acquire", folder]) == 0
        assert main(["--acquire", folder]) == 1
