#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = ["pytest"]
# ///
"""Test di accepted_risks.py."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from accepted_risks import analyze, parse_rows  # noqa: E402


REGISTRO = """# Rischi accettati

- [2026-07-30] [Kai] chiave di test nel tema — ruotata a ogni deploy — ambito: staging-museo, candidato 6ed04b2.
- [2026-08-01] [Vera] log con IP completo — retention 7 giorni — ambito: produzione-museo, fino al 2026-08-05.
- [2026-08-02] [Otto] template duplicato — riscrittura pianificata — ambito: altro-progetto.
riga senza forma
"""


def registro(tmp_path: Path, testo: str = REGISTRO) -> Path:
    path = tmp_path / "accepted-risks.md"
    path.write_text(testo, encoding="utf-8")
    return path


class TestParsing:
    def test_legge_le_quattro_parti_della_riga(self) -> None:
        rows, malformed = parse_rows(REGISTRO)
        assert len(rows) == 3
        assert rows[0]["figure"] == "Kai"
        assert rows[0]["risk"] == "chiave di test nel tema"
        assert "staging-museo" in rows[0]["scope"]
        assert malformed == ["riga senza forma"]

    def test_una_riga_senza_i_tre_segmenti_e_fuori_formato(self) -> None:
        rows, malformed = parse_rows("- [2026-08-01] [Kai] solo il rischio\n")
        assert rows == [] and len(malformed) == 1


class TestFiltro:
    def test_trova_la_riga_che_nomina_il_candidato(self, tmp_path: Path) -> None:
        result = analyze(registro(tmp_path), ["6ed04b2"], "2026-08-09")
        assert result["ok"] is True
        assert [r["figure"] for r in result["rows_matching"]] == ["Kai"]

    def test_trova_la_riga_che_nomina_il_target(self, tmp_path: Path) -> None:
        result = analyze(registro(tmp_path), ["staging-museo"], "2026-08-09")
        assert len(result["rows_matching"]) == 1

    def test_una_riga_scaduta_non_conta_come_accettazione(self, tmp_path: Path) -> None:
        result = analyze(registro(tmp_path), ["produzione-museo"], "2026-08-09")
        assert result["rows_matching"] == []
        assert result["rows_expired"][0]["expires_on"] == "2026-08-05"
        assert result["ok"] is False

    def test_prima_della_scadenza_la_riga_e_viva(self, tmp_path: Path) -> None:
        result = analyze(registro(tmp_path), ["produzione-museo"], "2026-08-04")
        assert len(result["rows_matching"]) == 1
        assert result["rows_expired"] == []

    def test_un_ambito_estraneo_non_copre_il_gate(self, tmp_path: Path) -> None:
        result = analyze(registro(tmp_path), ["produzione-museo", "6ed04b2"], "2026-08-09")
        assert all("altro-progetto" not in r["scope"] for r in result["rows_matching"])

    def test_senza_filtri_restituisce_tutte_le_righe_vive(self, tmp_path: Path) -> None:
        result = analyze(registro(tmp_path), [], "2026-08-09")
        assert len(result["rows_matching"]) == 2

    def test_le_righe_fuori_formato_sono_riportate(self, tmp_path: Path) -> None:
        result = analyze(registro(tmp_path), ["staging-museo"], "2026-08-09")
        assert result["rows_malformed"] == ["riga senza forma"]


class TestScadenzeNonStandard:
    ALTRE_FORME = """# Rischi accettati

- [2026-01-10] [Kai] uno — motivo — ambito: produzione, scade 2025-06-30.
- [2026-01-10] [Vera] due — motivo — ambito: produzione, scadenza: 2025-06-30.
- [2026-01-10] [Otto] tre — motivo — ambito: produzione, expires 2025-06-30.
- [2026-01-10] [Nils] quattro — motivo — ambito: produzione, fino al 31/12/2025.
- [2026-01-10] [Enzo] cinque — motivo — ambito: produzione, ticket 2025-06-30 aperto.
"""

    def test_le_formulazioni_alternative_sono_scadenze(self, tmp_path: Path) -> None:
        result = analyze(registro(tmp_path, self.ALTRE_FORME), ["produzione"], "2026-08-09")
        scadute = {r["figure"] for r in result["rows_expired"]}
        assert scadute == {"Kai", "Vera", "Otto", "Nils"}

    def test_il_formato_italiano_della_data_viene_normalizzato(self, tmp_path: Path) -> None:
        result = analyze(registro(tmp_path, self.ALTRE_FORME), ["produzione"], "2026-08-09")
        nils = next(r for r in result["rows_expired"] if r["figure"] == "Nils")
        assert nils["expires_on"] == "2025-12-31"

    def test_una_data_senza_formula_non_e_una_riga_viva(self, tmp_path: Path) -> None:
        result = analyze(registro(tmp_path, self.ALTRE_FORME), ["produzione"], "2026-08-09")
        assert [r["figure"] for r in result["rows_expiry_unclear"]] == ["Enzo"]
        assert result["rows_matching"] == []
        assert result["ok"] is False


class TestConfrontoSuToken:
    AMBITI = """# Rischi accettati

- [2026-03-01] [Bruno] backup non testato — costo — ambito: preprod, senza scadenza.
- [2026-03-02] [Kai] chiave di test — ruotata — ambito: prod, senza scadenza.
- [2026-03-03] [Otto] template doppio — riscrittura — ambito: candidato a1b2c3d4, produzione.
"""

    def test_preprod_non_risponde_per_prod(self, tmp_path: Path) -> None:
        result = analyze(registro(tmp_path, self.AMBITI), ["prod"], "2026-08-09")
        assert [r["figure"] for r in result["rows_matching"]] == ["Kai"]

    def test_un_commit_lungo_trova_la_forma_breve(self, tmp_path: Path) -> None:
        result = analyze(registro(tmp_path, self.AMBITI), ["a1b2c3d4e5f6"], "2026-08-09")
        assert [r["figure"] for r in result["rows_matching"]] == ["Otto"]
        assert result["rows_matching"][0]["matched_on"] == "a1b2c3d4"

    def test_una_sequenza_di_parole_combacia(self, tmp_path: Path) -> None:
        result = analyze(registro(tmp_path, self.AMBITI), ["candidato a1b2c3d4"], "2026-08-09")
        assert len(result["rows_matching"]) == 1


class TestScadenzaLegataAllaFrase:
    DUE_DATE = """# Rischi accettati

- [2026-01-10] [Kai] token nei log — pilota — ambito: produzione, valida dal 2026-01-15 fino al 2027-06-30.
- [2026-01-10] [Vera] cache — perf — ambito: produzione, release del 2026-05-20, scadenza 2027-12-31.
"""

    def test_prende_la_data_legata_alla_formula(self, tmp_path: Path) -> None:
        result = analyze(registro(tmp_path, self.DUE_DATE), ["produzione"], "2026-08-09")
        assert [r["expires_on"] for r in result["rows_matching"]] == ["2027-06-30", "2027-12-31"]
        assert result["rows_expired"] == []


class TestFileAssente:
    def test_registro_mancante_non_accetta_niente(self, tmp_path: Path) -> None:
        result = analyze(tmp_path / "assente.md", ["x"], "2026-08-09")
        assert result["file_present"] is False
        assert result["ok"] is False

    def test_registro_vuoto_non_accetta_niente(self, tmp_path: Path) -> None:
        result = analyze(registro(tmp_path, ""), ["x"], "2026-08-09")
        assert (result["file_present"], result["rows_total"], result["ok"]) == (True, 0, False)
