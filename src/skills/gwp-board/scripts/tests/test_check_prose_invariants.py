#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = ["pytest"]
# ///
"""Test di check_prose_invariants.py."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from check_prose_invariants import compare, extract  # noqa: E402


BASE = """---
gate: gwp-board/release-gate/v1
verdict: GO
---

# Gate di rilascio

La release v1.4.0 al commit 3b1d9e7a0c4f è stata verificata il 2026-08-09.
Il log sta su https://ci.example.org/run/184 e copre 24 test.

```bash
sha256sum bundle.tgz
```

- [2026-08-09] [Kai] chiave ruotata — evidenza: report 771 — ambito: solo produzione.

Verdetto: GO.
"""


def coppia(tmp_path: Path, dopo: str, prima: str = BASE) -> dict:
    (tmp_path / "prima.md").write_text(prima, encoding="utf-8")
    (tmp_path / "dopo.md").write_text(dopo, encoding="utf-8")
    return compare(prima, dopo)


class TestEstrazione:
    def test_riconosce_le_categorie(self) -> None:
        found = extract(BASE)
        assert "3b1d9e7a0c4f" in found["identifiers"]
        assert "v1.4.0" in found["identifiers"]
        assert "2026-08-09" in found["dates"]
        assert "https://ci.example.org/run/184" in found["urls"]
        assert found["verdicts"]["GO"] == 2
        assert sum(found["memory_lines"].values()) == 1

    def test_una_parola_esadecimale_senza_cifre_non_e_un_identificatore(self) -> None:
        assert extract("la faccenda decaf resta aperta")["identifiers"] == {}


class TestConfronto:
    def test_riscrittura_solo_di_prosa_passa(self, tmp_path: Path) -> None:
        dopo = BASE.replace(
            "è stata verificata il", "risulta verificata in data"
        ).replace("Il log sta su", "Il log è disponibile all'indirizzo")
        assert coppia(tmp_path, dopo)["ok"] is True

    def test_data_cambiata_viola(self, tmp_path: Path) -> None:
        result = coppia(tmp_path, BASE.replace("2026-08-09] [Kai]", "2026-08-10] [Kai]"))
        assert result["ok"] is False
        assert result["changes"]["dates"]["added"] == ["2026-08-10"]

    def test_identificatore_troncato_viola(self, tmp_path: Path) -> None:
        result = coppia(tmp_path, BASE.replace("3b1d9e7a0c4f", "3b1d9e7"))
        assert "3b1d9e7a0c4f" in result["changes"]["identifiers"]["removed"]

    def test_verdetto_cambiato_viola(self, tmp_path: Path) -> None:
        result = coppia(tmp_path, BASE.replace("Verdetto: GO.", "Verdetto: NO_GO."))
        assert "NO_GO" in result["changes"]["verdicts"]["added"]

    def test_url_riscritto_viola(self, tmp_path: Path) -> None:
        result = coppia(tmp_path, BASE.replace("/run/184", "/run/185"))
        assert result["changes"]["urls"]["added"]

    def test_frontmatter_toccato_viola(self, tmp_path: Path) -> None:
        result = coppia(tmp_path, BASE.replace("verdict: GO", "verdict: NO_GO"))
        assert result["changes"]["frontmatter"]["added"]

    def test_codice_riformattato_viola(self, tmp_path: Path) -> None:
        result = coppia(tmp_path, BASE.replace("sha256sum bundle.tgz", "sha256sum  bundle.tgz"))
        assert result["changes"]["code"]["added"]

    def test_numero_cambiato_viola(self, tmp_path: Path) -> None:
        result = coppia(tmp_path, BASE.replace("copre 24 test", "copre 25 test"))
        assert "25" in result["changes"]["numbers"]["added"]

    def test_riga_di_memoria_riscritta_viola(self, tmp_path: Path) -> None:
        result = coppia(tmp_path, BASE.replace("chiave ruotata", "chiave sostituita"))
        assert result["changes"]["memory_lines"]["added"]

    def test_testo_identico_non_riporta_nulla(self, tmp_path: Path) -> None:
        result = coppia(tmp_path, BASE)
        assert result["violations"] == []
