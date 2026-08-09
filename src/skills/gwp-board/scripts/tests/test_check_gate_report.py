#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = ["pytest"]
# ///
"""Test di check_gate_report.py."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from check_gate_report import check, parse_frontmatter, split_sections  # noqa: E402


SEZIONI = """
## Identità e validità

Release v1.4.0, commit 3b1d9e7.

## Convocate ed escluse

Otto sul packaging; privacy esclusa: nessun dato personale.

## Decisioni e rischi applicabili

Nessun rischio accettato pertinente.

## Evidenze e lacune

CI run 184 verde, log allegato.

## Rilievi e blocchi

{blocchi}

## Condizioni

{condizioni}

## Verdetto e motivazione

**Verdetto:** {verdetto}

Le prove decisive sono complete.
"""


def report(
    tmp_path: Path,
    verdict: str = "GO",
    *,
    gate: str = "gwp-board/release-gate/v1",
    identity: str = "{commit: 3b1d9e7, tag: v1.4.0}",
    environment: str = "npm pubblico",
    scope: str = "pacchetto CLI",
    started: str = "20260809T120000Z",
    corpo: str | None = None,
    blocchi: str = "Nessun blocco.",
    condizioni: str = "Nessuna condizione.",
    verdetto_sezione: str | None = None,
) -> Path:
    body = corpo if corpo is not None else SEZIONI.format(
        blocchi=blocchi,
        condizioni=condizioni,
        verdetto=verdetto_sezione if verdetto_sezione is not None else verdict,
    )
    path = tmp_path / "gate.md"
    path.write_text(
        "---\n"
        f"gate: {gate}\n"
        f"verdict: {verdict}\n"
        f"release_identity: {identity}\n"
        f"environment: {environment}\n"
        f"scope: {scope}\n"
        f"gate_started_at_utc: {started}\n"
        "---\n" + body,
        encoding="utf-8",
    )
    return path


class TestParsing:
    def test_legge_le_mappe_inline(self) -> None:
        data = parse_frontmatter("---\nrelease_identity: {commit: abc, tag: v1}\n---\n")
        assert data["release_identity"] == {"commit": "abc", "tag": "v1"}

    def test_null_diventa_none(self) -> None:
        assert parse_frontmatter("---\nverdict: null\n---\n")["verdict"] is None

    def test_senza_frontmatter_restituisce_none(self) -> None:
        assert parse_frontmatter("# titolo\n") is None

    def test_i_titoli_si_confrontano_senza_accenti(self, tmp_path: Path) -> None:
        sezioni = split_sections("---\na: b\n---\n## Identità e validità\ntesto\n")
        assert "identita e validita" in sezioni

    def test_un_heading_dentro_un_blocco_di_codice_non_apre_una_sezione(self) -> None:
        sezioni = split_sections("## Vera\n```\n## Finta\n```\ntesto\n")
        assert list(sezioni) == ["vera"]


class TestVerdetto:
    def test_report_conforme_passa(self, tmp_path: Path) -> None:
        result = check(report(tmp_path))
        assert result["ok"] is True
        assert result["verdict"] == "GO"

    def test_verdetto_fuori_enum_viola(self, tmp_path: Path) -> None:
        result = check(report(tmp_path, "FORSE"))
        assert result["ok"] is False
        assert any("verdict" in v for v in result["violations"])

    def test_la_motivazione_puo_citare_un_verdetto_scartato(self, tmp_path: Path) -> None:
        corpo = SEZIONI.format(
            blocchi="Nessun blocco.",
            condizioni="Nessuna condizione.",
            verdetto="GO\n\nNon è un NO_GO perché nessun blocco è provato.",
        )
        assert check(report(tmp_path, "GO", corpo=corpo))["ok"] is True

    def test_sezione_che_contraddice_il_frontmatter_viola(self, tmp_path: Path) -> None:
        result = check(report(tmp_path, "GO", verdetto_sezione="NO_GO"))
        assert any("non coincide" in v for v in result["violations"])

    def test_sezione_senza_riga_di_verdetto_viola(self, tmp_path: Path) -> None:
        corpo = SEZIONI.replace("**Verdetto:** {verdetto}", "Direi {verdetto}").format(
            blocchi="Nessun blocco.", condizioni="Nessuna condizione.", verdetto="GO"
        )
        result = check(report(tmp_path, "GO", corpo=corpo))
        assert any("riga `**Verdetto:**" in v for v in result["violations"])

    def test_sezioni_fuori_ordine_violano(self, tmp_path: Path) -> None:
        corpo = SEZIONI.format(
            blocchi="Nessun blocco.", condizioni="Nessuna condizione.", verdetto="GO"
        )
        pezzi = corpo.split("## Condizioni")
        invertito = pezzi[0].replace(
            "## Rilievi e blocchi\n\nNessun blocco.\n",
            "",
        ) + "## Condizioni" + pezzi[1].replace(
            "## Verdetto e motivazione",
            "## Rilievi e blocchi\n\nNessun blocco.\n\n## Verdetto e motivazione",
        )
        result = check(report(tmp_path, "GO", corpo=invertito))
        assert any("ordine previsto" in v for v in result["violations"])

    def test_nominare_altri_verdetti_fuori_dalla_sezione_e_lecito(self, tmp_path: Path) -> None:
        corpo = SEZIONI.format(
            blocchi="Nessun blocco: non concede GO né GO_CON_CONDIZIONI altrove.",
            condizioni="Nessuna condizione.",
            verdetto="GO",
        )
        assert check(report(tmp_path, "GO", corpo=corpo))["ok"] is True

    def test_no_goal_non_e_un_verdetto(self, tmp_path: Path) -> None:
        result = check(report(tmp_path, "GO", verdetto_sezione="GO: nessun NO_GOAL residuo"))
        assert result["ok"] is True


class TestProvePerVerdetto:
    def test_go_senza_identita_viola(self, tmp_path: Path) -> None:
        result = check(report(tmp_path, "GO", identity="{commit: null, tag: null}"))
        assert any("identificatore" in v for v in result["violations"])

    def test_condizionato_senza_scadenza_viola(self, tmp_path: Path) -> None:
        result = check(
            report(tmp_path, "GO_CON_CONDIZIONI", condizioni="Luca sistemerà BO-91.")
        )
        assert any("scadenza" in v for v in result["violations"])

    def test_condizionato_con_scadenza_passa(self, tmp_path: Path) -> None:
        result = check(
            report(
                tmp_path,
                "GO_CON_CONDIZIONI",
                condizioni="BO-91 — Luca — entro 2026-08-12.",
            )
        )
        assert result["ok"] is True
        assert result["condition_deadlines"] == ["2026-08-12"]

    def test_scadenza_gia_passata_viola(self, tmp_path: Path) -> None:
        result = check(
            report(
                tmp_path,
                "GO_CON_CONDIZIONI",
                condizioni="BO-91 — Luca — entro 2025-01-10.",
                started="20260809T120000Z",
            )
        )
        assert any("successiva all'apertura del gate" in v for v in result["violations"])

    def test_no_go_senza_blocchi_viola(self, tmp_path: Path) -> None:
        result = check(report(tmp_path, "NO_GO", blocchi=""))
        assert any("senza blocchi" in v for v in result["violations"])

    def test_evidenza_insufficiente_senza_identita_passa(self, tmp_path: Path) -> None:
        result = check(
            report(tmp_path, "EVIDENZA_INSUFFICIENTE", identity="{commit: null}")
        )
        assert result["ok"] is True


class TestSchema:
    def test_frontmatter_assente_e_una_violazione_unica(self, tmp_path: Path) -> None:
        path = tmp_path / "gate.md"
        path.write_text("# Gate\n\nGO\n", encoding="utf-8")
        result = check(path)
        assert result["frontmatter_present"] is False
        assert result["missing_sections"]

    def test_gate_sbagliato_viola(self, tmp_path: Path) -> None:
        result = check(report(tmp_path, gate="altro/v1"))
        assert any("`gate`" in v for v in result["violations"])

    def test_ambiente_vuoto_viola(self, tmp_path: Path) -> None:
        result = check(report(tmp_path, environment=""))
        assert any("environment" in v for v in result["violations"])

    def test_sezione_mancante_viene_elencata(self, tmp_path: Path) -> None:
        result = check(report(tmp_path, corpo="## Verdetto e motivazione\n\nGO\n"))
        assert "condizioni" in result["missing_sections"]
        assert "identita e validita" in result["missing_sections"]
