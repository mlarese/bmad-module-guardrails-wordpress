#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = ["pytest"]
# ///
"""Test di snapshot_diff.py."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from snapshot_diff import build_parser, compare, flatten, load, run  # noqa: E402


ATTESO = {
    "schede_prodotto": 24,
    "template": "single-product-v4",
    "menu": "Catalogo",
    "media": {"hero": 311, "brochure": 312},
}

MEDIA_MAP = """# Mappa media

| Asset | Target e binding | Attachment | Stato | Alt text | Evidenza |
| --- | --- | --- | --- | --- | --- |
| logo.png | staging · site-logo | 42 | verified | Logo del sito | attachment 42, image/png |
"""

TABELLA = """# Snapshot

| Chiave | Valore |
| --- | --- |
| schede_prodotto | 24 |
| template | single-product-v4 |
"""


def scrivi(tmp_path: Path, nome: str, data: dict) -> str:
    path = tmp_path / nome
    path.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
    return str(path)


class TestLettura:
    def test_appiattisce_le_mappe_annidate(self) -> None:
        assert flatten({"media": {"hero": 311}})["media.hero"] == "311"

    def test_legge_una_tabella_markdown(self, tmp_path: Path) -> None:
        path = tmp_path / "snap.md"
        path.write_text(TABELLA, encoding="utf-8")
        values = load(path)
        assert values == {"schede_prodotto": "24", "template": "single-product-v4"}

    def test_tabella_senza_coppie_e_un_errore(self, tmp_path: Path) -> None:
        path = tmp_path / "snap.md"
        path.write_text("# solo testo\n", encoding="utf-8")
        with pytest.raises(ValueError):
            load(path)

    def test_una_tabella_a_piu_colonne_diventa_chiavi_per_cella(self, tmp_path: Path) -> None:
        path = tmp_path / "media-map.md"
        path.write_text(MEDIA_MAP, encoding="utf-8")
        values = load(path)
        assert values["logo.png|Attachment"] == "42"
        assert values["logo.png|Stato"] == "verified"

    def test_un_attachment_cambiato_e_una_differenza(self, tmp_path: Path) -> None:
        prima = tmp_path / "prima.md"
        dopo = tmp_path / "dopo.md"
        prima.write_text(MEDIA_MAP, encoding="utf-8")
        dopo.write_text(MEDIA_MAP.replace("| 42 |", "| 99 |"), encoding="utf-8")
        result = run(build_parser().parse_args(["--pre", str(prima), "--post", str(dopo)]))
        assert result["read_only"]["target_mutated"] is True

    def test_uno_stato_cambiato_e_una_differenza(self, tmp_path: Path) -> None:
        prima = tmp_path / "prima.md"
        dopo = tmp_path / "dopo.md"
        prima.write_text(MEDIA_MAP, encoding="utf-8")
        dopo.write_text(MEDIA_MAP.replace("verified", "pending"), encoding="utf-8")
        result = run(build_parser().parse_args(["--pre", str(prima), "--post", str(dopo)]))
        assert result["read_only"]["target_mutated"] is True


class TestConfronto:
    def test_snapshot_identici_passano(self, tmp_path: Path) -> None:
        atteso = scrivi(tmp_path, "atteso.json", ATTESO)
        osservato = scrivi(tmp_path, "osservato.json", ATTESO)
        result = run(build_parser().parse_args(["--expected", atteso, "--observed", osservato]))
        assert result["ok"] is True
        assert result["baseline"]["equal"] == 5

    def test_valore_diverso_viene_riportato(self, tmp_path: Path) -> None:
        osservato = dict(ATTESO, schede_prodotto=23)
        result = run(
            build_parser().parse_args(
                [
                    "--expected", scrivi(tmp_path, "a.json", ATTESO),
                    "--observed", scrivi(tmp_path, "o.json", osservato),
                ]
            )
        )
        assert result["baseline"]["changed"] == [
            {"key": "schede_prodotto", "expected": "24", "observed": "23"}
        ]

    def test_attachment_mancante_viene_riportato(self, tmp_path: Path) -> None:
        osservato = {k: v for k, v in ATTESO.items() if k != "media"}
        result = run(
            build_parser().parse_args(
                [
                    "--expected", scrivi(tmp_path, "a.json", ATTESO),
                    "--observed", scrivi(tmp_path, "o.json", osservato),
                ]
            )
        )
        assert result["baseline"]["missing"] == ["media.brochure", "media.hero"]

    def test_chiave_in_piu_viene_riportata(self) -> None:
        result = compare({"a": "1"}, {"a": "1", "b": "2"})
        assert result["unexpected"] == ["b"]

    def test_pre_e_post_uguali_provano_la_sola_lettura(self, tmp_path: Path) -> None:
        result = run(
            build_parser().parse_args(
                [
                    "--pre", scrivi(tmp_path, "pre.json", ATTESO),
                    "--post", scrivi(tmp_path, "post.json", ATTESO),
                ]
            )
        )
        assert result["read_only"]["target_mutated"] is False

    def test_post_diverso_segnala_la_mutazione(self, tmp_path: Path) -> None:
        result = run(
            build_parser().parse_args(
                [
                    "--pre", scrivi(tmp_path, "pre.json", ATTESO),
                    "--post", scrivi(tmp_path, "post.json", dict(ATTESO, menu="Prodotti")),
                ]
            )
        )
        assert result["read_only"]["target_mutated"] is True
        assert result["ok"] is False

    def test_le_due_coppie_convivono(self, tmp_path: Path) -> None:
        args = build_parser().parse_args(
            [
                "--expected", scrivi(tmp_path, "a.json", ATTESO),
                "--observed", scrivi(tmp_path, "o.json", ATTESO),
                "--pre", scrivi(tmp_path, "pre.json", ATTESO),
                "--post", scrivi(tmp_path, "post.json", ATTESO),
            ]
        )
        result = run(args)
        assert set(result) == {"baseline", "read_only", "ok"}


PROSA = """---
schema: grl-wordpress-delivery/v1
status: gate-pending
---

# Evidenze di release

Il candidato 6ed04b2a1c3d è stato verificato il 2026-08-08 su produzione-museo.
Gli attachment 501, 502 e 503 sono stati letti dal target.

| Controllo | Esito |
| --- | --- |
| rendering home | superato |

Verdetto atteso dal gate: GO.
"""


class TestInvarianti:
    def coppia(self, tmp_path: Path, dopo: str) -> list[str]:
        prima = tmp_path / "prima.md"
        post = tmp_path / "dopo.md"
        prima.write_text(PROSA, encoding="utf-8")
        post.write_text(dopo, encoding="utf-8")
        result = run(build_parser().parse_args(["--invariants", str(prima), str(post)]))
        return result["invariants"]

    def test_riscrittura_solo_di_prosa_passa(self, tmp_path: Path) -> None:
        dopo = PROSA.replace("è stato verificato il", "risulta verificato in data")
        assert self.coppia(tmp_path, dopo)["ok"] is True

    def test_una_data_cambiata_e_una_violazione(self, tmp_path: Path) -> None:
        inv = self.coppia(tmp_path, PROSA.replace("2026-08-08", "2026-08-09"))
        assert inv["changes"]["dates"]["added"] == ["2026-08-09"]
        assert inv["ok"] is False

    def test_un_attachment_id_cambiato_e_una_violazione(self, tmp_path: Path) -> None:
        inv = self.coppia(tmp_path, PROSA.replace("501", "504"))
        assert "504" in inv["changes"]["numeric_ids"]["added"]

    def test_un_hash_troncato_e_una_violazione(self, tmp_path: Path) -> None:
        inv = self.coppia(tmp_path, PROSA.replace("6ed04b2a1c3d", "6ed04b2"))
        assert "6ed04b2a1c3d" in inv["changes"]["hashes"]["removed"]

    def test_il_verdetto_non_puo_muoversi(self, tmp_path: Path) -> None:
        inv = self.coppia(tmp_path, PROSA.replace("GO.", "NO_GO."))
        assert "NO_GO" in inv["changes"]["verdicts"]["added"]

    def test_il_frontmatter_resta_fermo(self, tmp_path: Path) -> None:
        inv = self.coppia(tmp_path, PROSA.replace("status: gate-pending", "status: released"))
        assert inv["changes"]["frontmatter"]["added"]

    def test_una_cella_riscritta_e_una_violazione(self, tmp_path: Path) -> None:
        inv = self.coppia(tmp_path, PROSA.replace("| superato |", "| ok |"))
        assert "ok" in inv["changes"]["cells"]["added"]

    def test_un_id_seguito_da_punto_e_una_violazione(self, tmp_path: Path) -> None:
        inv = self.coppia(tmp_path, PROSA.replace("503 sono stati letti", "504 sono stati letti"))
        assert inv["ok"] is False

    def test_un_id_dentro_una_parola_e_una_violazione(self, tmp_path: Path) -> None:
        prima = PROSA + "\nSlug della pagina: page-home42.\n"
        dopo = PROSA + "\nSlug della pagina: page-home99.\n"
        prima_path = tmp_path / "a.md"
        dopo_path = tmp_path / "b.md"
        prima_path.write_text(prima, encoding="utf-8")
        dopo_path.write_text(dopo, encoding="utf-8")
        result = run(
            build_parser().parse_args(["--invariants", str(prima_path), str(dopo_path)])
        )
        assert "page-home99" in result["invariants"]["changes"]["numeric_ids"]["added"]

    def test_un_numero_con_unita_e_una_violazione(self, tmp_path: Path) -> None:
        prima = PROSA + "\nLarghezza dell'hero: 640px.\n"
        dopo = PROSA + "\nLarghezza dell'hero: 980px.\n"
        prima_path = tmp_path / "a.md"
        dopo_path = tmp_path / "b.md"
        prima_path.write_text(prima, encoding="utf-8")
        dopo_path.write_text(dopo, encoding="utf-8")
        result = run(
            build_parser().parse_args(["--invariants", str(prima_path), str(dopo_path)])
        )
        assert "980px" in result["invariants"]["changes"]["numeric_ids"]["added"]

    def test_togliere_le_parentesi_non_cambia_lid(self, tmp_path: Path) -> None:
        prima = tmp_path / "a.md"
        dopo = tmp_path / "b.md"
        prima.write_text(PROSA + "\nL'attachment (42) è quello giusto.\n", encoding="utf-8")
        dopo.write_text(PROSA + "\nL'attachment 42 è quello giusto.\n", encoding="utf-8")
        result = run(build_parser().parse_args(["--invariants", str(prima), str(dopo)]))
        assert result["invariants"]["changes"]["numeric_ids"]["added"] == []
        assert result["invariants"]["changes"]["numeric_ids"]["removed"] == []


class TestSoloChiavi:
    INVENTARIO = {"pagina.chi-siamo": "elementor", "cpt.medico": "65 profili"}
    MAPPA = {"pagina.chi-siamo": "gutenberg", "cpt.medico": "CPT medico con ACF"}

    def scrivi(self, tmp_path: Path, nome: str, data: dict) -> str:
        path = tmp_path / nome
        path.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
        return str(path)

    def test_un_piano_completo_passa_con_keys_only(self, tmp_path: Path) -> None:
        result = run(
            build_parser().parse_args(
                [
                    "--expected", self.scrivi(tmp_path, "inv.json", self.INVENTARIO),
                    "--observed", self.scrivi(tmp_path, "map.json", self.MAPPA),
                    "--keys-only",
                ]
            )
        )
        assert result["ok"] is True
        assert result["baseline"]["changed"] == []

    def test_una_voce_senza_destinazione_resta_una_differenza(self, tmp_path: Path) -> None:
        parziale = {"pagina.chi-siamo": "gutenberg"}
        result = run(
            build_parser().parse_args(
                [
                    "--expected", self.scrivi(tmp_path, "inv.json", self.INVENTARIO),
                    "--observed", self.scrivi(tmp_path, "map.json", parziale),
                    "--keys-only",
                ]
            )
        )
        assert result["baseline"]["missing"] == ["cpt.medico"]
        assert result["ok"] is False

    def test_senza_keys_only_i_valori_diversi_contano(self, tmp_path: Path) -> None:
        result = run(
            build_parser().parse_args(
                [
                    "--expected", self.scrivi(tmp_path, "inv.json", self.INVENTARIO),
                    "--observed", self.scrivi(tmp_path, "map.json", self.MAPPA),
                ]
            )
        )
        assert result["ok"] is False


class TestErrori:
    def test_un_file_assente_e_un_errore(self, tmp_path: Path) -> None:
        prima = tmp_path / "prima.md"
        prima.write_text(PROSA, encoding="utf-8")
        with pytest.raises(ValueError):
            run(build_parser().parse_args(["--invariants", str(prima), str(tmp_path / "no.md")]))


class TestUso:
    def test_expected_senza_observed_e_un_errore(self, tmp_path: Path) -> None:
        with pytest.raises(ValueError):
            run(build_parser().parse_args(["--expected", scrivi(tmp_path, "a.json", ATTESO)]))

    def test_nessuna_coppia_e_un_errore(self) -> None:
        with pytest.raises(ValueError):
            run(build_parser().parse_args([]))
