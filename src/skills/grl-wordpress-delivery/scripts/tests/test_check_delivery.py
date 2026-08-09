#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = ["pytest"]
# ///
"""Test di check_delivery.py."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from check_delivery import SLUG, check, main, parse_media_table, slugify  # noqa: E402


REPO = Path(__file__).resolve().parents[5]

MEDIA_OK = """# Mappa media

| Asset | Target e binding | Attachment | Stato | Evidenza |
| --- | --- | --- | --- | --- |
| logo.png | staging · site-logo | 42 | verified | attachment 42, image/png, 640×320 |
"""

# Evidenze con il blocco dei path revisionati, il report del gate e l'identità.
# `gate-report.md` va creato accanto, perché il controllo pretende un file vero.
EVIDENZE = """# Evidenze di release

## File revisionati

- content-model.md
- component-plan.md
- release-evidence.md
- delivery.md

Report del gate: gate-report.md
Identità: commit 6ed04b2a1c3d5e7f.
"""

EVIDENZE_VERIFY = """# Evidenze di release

## File revisionati

- release-evidence.md
- delivery.md
"""


def con_evidenze(folder: Path, testo: str = EVIDENZE) -> Path:
    (folder / "release-evidence.md").write_text(testo, encoding="utf-8")
    (folder / "gate-report.md").write_text("# report del gate\n", encoding="utf-8")
    return folder


def delivery(
    tmp_path: Path,
    *,
    slug: str = "wp-demo",
    schema: str = "grl-wordpress-delivery/v1",
    intent: str = "create",
    status: str = "implementing",
    artifacts: str = "{content_model: ready, component_plan: ready, media_map: ready, release_evidence: ready}",
    gates: str = "{substantive_review: pending, prose_review: pending, release: pending}",
    authorized: str = "true",
    scope: str = "staging",
    blockers: str = "[]",
    target: str = "staging",
    identity: str = (
        "{version: 1.0, commit: 6ed04b2a1c3d5e7f, artifact: theme.zip, "
        "digest: null, target: staging, content_snapshot: null}"
    ),
    media: str = MEDIA_OK,
    files: tuple[str, ...] = (
        "content-model.md",
        "component-plan.md",
        "release-evidence.md",
    ),
) -> Path:
    folder = tmp_path / slug
    folder.mkdir(parents=True, exist_ok=True)
    (folder / "delivery.md").write_text(
        "---\n"
        f"schema: {schema}\n"
        f"slug: {slug}\n"
        f"intent: {intent}\n"
        f"status: {status}\n"
        f"target: {target}\n"
        f"release_identity: {identity}\n"
        f"implementation_authorized: {authorized}\n"
        f"authorization_scope: {scope}\n"
        f"artifacts: {artifacts}\n"
        f"gates: {gates}\n"
        f"blockers: {blockers}\n"
        "updated_at: 2026-08-09T10:00:00Z\n"
        "---\n\n- 2026-08-09 — creata.\n",
        encoding="utf-8",
    )
    (folder / "media-map.md").write_text(media, encoding="utf-8")
    for name in files:
        (folder / name).write_text(f"# {name}\n", encoding="utf-8")
    return folder


class TestSchemaEEnum:
    def test_delivery_coerente_passa(self, tmp_path: Path) -> None:
        assert check(delivery(tmp_path), None)["ok"] is True

    def test_schema_sbagliato_viola(self, tmp_path: Path) -> None:
        result = check(delivery(tmp_path, schema="altro/v2"), None)
        assert any("schema" in v for v in result["violations"])

    def test_slug_diverso_dalla_cartella_viola(self, tmp_path: Path) -> None:
        folder = delivery(tmp_path, slug="wp-demo")
        (folder / "delivery.md").write_text(
            (folder / "delivery.md").read_text(encoding="utf-8").replace(
                "slug: wp-demo", "slug: altro-slug"
            ),
            encoding="utf-8",
        )
        result = check(folder, None)
        assert any("non coincide con la cartella" in v for v in result["violations"])

    def test_stato_fuori_enum_viola(self, tmp_path: Path) -> None:
        result = check(delivery(tmp_path, status="quasi-pronto"), None)
        assert any("`status` fuori enum" in v for v in result["violations"])

    def test_gate_fuori_enum_viola(self, tmp_path: Path) -> None:
        result = check(
            delivery(
                tmp_path,
                gates="{substantive_review: ok, prose_review: pending, release: pending}",
            ),
            None,
        )
        assert any("substantive_review" in v for v in result["violations"])

    def test_verdetto_ammesso_come_stato_del_gate_release(self, tmp_path: Path) -> None:
        folder = delivery(
            tmp_path,
            status="release-approved",
            gates="{substantive_review: passed, prose_review: passed, release: GO_CON_CONDIZIONI}",
        )
        con_evidenze(folder)
        assert check(folder, None)["ok"] is True

    def test_file_mancante_viene_elencato(self, tmp_path: Path) -> None:
        result = check(delivery(tmp_path, files=("content-model.md",)), None)
        assert "component-plan.md" in result["missing_files"]

    def test_senza_delivery_md_si_ferma(self, tmp_path: Path) -> None:
        folder = tmp_path / "vuota"
        folder.mkdir()
        result = check(folder, None)
        assert result["ok"] is False
        assert result["frontmatter"] is None

    def test_autorizzazione_senza_ambito_viola(self, tmp_path: Path) -> None:
        result = check(delivery(tmp_path, authorized="true", scope=""), None)
        assert any("authorization_scope" in v for v in result["violations"])

    def test_blocked_senza_blocker_viola(self, tmp_path: Path) -> None:
        result = check(delivery(tmp_path, status="blocked"), None)
        assert any("senza nessun blocker" in v for v in result["violations"])

    def test_target_vuoto_viola(self, tmp_path: Path) -> None:
        result = check(delivery(tmp_path, target=""), None)
        assert any("`target` vuoto" in v for v in result["violations"])

    def test_slug_non_normalizzato_viola(self, tmp_path: Path) -> None:
        result = check(delivery(tmp_path, slug="Studio Arco"), None)
        assert any("non e' normalizzato" in v for v in result["violations"])

    def test_uno_slug_con_versione_puntata_e_ammesso(self, tmp_path: Path) -> None:
        result = check(delivery(tmp_path, slug="museo-civico-1.0"), None)
        assert not any("normalizzato" in v for v in result["violations"])


class TestCoerenza:
    def test_gate_avviato_con_artefatto_pendente_viola(self, tmp_path: Path) -> None:
        result = check(
            delivery(
                tmp_path,
                artifacts="{content_model: ready, component_plan: pending, media_map: ready, release_evidence: ready}",
                gates="{substantive_review: passed, prose_review: pending, release: pending}",
            ),
            None,
        )
        assert any("gate avviati con artefatti aperti" in v for v in result["violations"])

    def test_release_approved_senza_review_viola(self, tmp_path: Path) -> None:
        result = check(
            delivery(
                tmp_path,
                status="release-approved",
                gates="{substantive_review: pending, prose_review: pending, release: pending}",
            ),
            None,
        )
        messages = " ".join(result["violations"])
        assert "review sostanziale" in messages and "verdetto favorevole" in messages

    def test_released_con_media_pendente_viola(self, tmp_path: Path) -> None:
        media = MEDIA_OK + "| hero.webp | staging · home.hero |  | pending | import non eseguito |\n"
        result = check(
            delivery(
                tmp_path,
                status="released",
                gates="{substantive_review: passed, prose_review: passed, release: GO}",
                media=media,
            ),
            None,
        )
        assert any("media ancora pendenti" in v for v in result["violations"])

    def test_release_approved_senza_identita_immutabile_viola(self, tmp_path: Path) -> None:
        result = check(
            delivery(
                tmp_path,
                status="release-approved",
                gates="{substantive_review: passed, prose_review: passed, release: GO}",
                identity="{version: 1.0, commit: null, artifact: null, digest: null, target: staging, content_snapshot: null}",
            ),
            None,
        )
        assert any("identificatore immutabile" in v for v in result["violations"])

    def test_tabella_media_illeggibile_blocca_la_promozione(self, tmp_path: Path) -> None:
        result = check(
            delivery(
                tmp_path,
                status="release-approved",
                gates="{substantive_review: passed, prose_review: passed, release: GO}",
                media="| A | B |\n| - | - |\n| x | y |\n",
            ),
            None,
        )
        assert any("tabella dei media non leggibile" in v for v in result["violations"])

    def test_no_go_non_promuove(self, tmp_path: Path) -> None:
        result = check(
            delivery(
                tmp_path,
                status="release-approved",
                gates="{substantive_review: passed, prose_review: passed, release: NO_GO}",
            ),
            None,
        )
        assert any("verdetto favorevole" in v for v in result["violations"])


class TestTransizioni:
    def test_transizione_ammessa(self, tmp_path: Path) -> None:
        result = check(delivery(tmp_path, status="implementing"), "verification-pending")
        assert result["transition"]["allowed"] is True
        assert result["ok"] is True

    def test_salto_non_ammesso(self, tmp_path: Path) -> None:
        result = check(delivery(tmp_path, status="planning"), "released")
        assert result["transition"]["allowed"] is False
        assert any("non ammessa" in v for v in result["violations"])

    def test_released_e_terminale(self, tmp_path: Path) -> None:
        result = check(
            delivery(
                tmp_path,
                status="released",
                gates="{substantive_review: passed, prose_review: passed, release: GO}",
            ),
            "implementing",
        )
        assert result["transition"]["allowed"] is False

    def test_stato_inesistente_viola(self, tmp_path: Path) -> None:
        result = check(delivery(tmp_path), "quasi-fatto")
        assert any("stato inesistente" in v for v in result["violations"])


class TestMedia:
    def test_verified_senza_attachment_id_viola(self, tmp_path: Path) -> None:
        media = MEDIA_OK.replace("| 42 |", "|  |")
        result = check(delivery(tmp_path, media=media), None)
        assert any("attachment ID numerico" in v for v in result["violations"])

    def test_url_non_e_un_attachment_id(self, tmp_path: Path) -> None:
        media = MEDIA_OK.replace("| 42 |", "| https://sito/wp-content/logo.png |")
        result = check(delivery(tmp_path, media=media), None)
        assert any("attachment ID numerico" in v for v in result["violations"])

    def test_verified_senza_evidenza_viola(self, tmp_path: Path) -> None:
        media = MEDIA_OK.replace("| attachment 42, image/png, 640×320 |", "|  |")
        result = check(delivery(tmp_path, media=media), None)
        assert any("senza evidenza" in v for v in result["violations"])

    def test_attachment_duplicato_viola(self, tmp_path: Path) -> None:
        media = MEDIA_OK + "| hero.webp | staging · home.hero | 42 | verified | attachment 42 |\n"
        result = check(delivery(tmp_path, media=media), None)
        assert any("usato da" in v for v in result["violations"])

    def test_stato_media_fuori_enum_viola(self, tmp_path: Path) -> None:
        media = MEDIA_OK.replace("| verified |", "| caricato |")
        result = check(delivery(tmp_path, media=media), None)
        assert any("fuori da" in v for v in result["violations"])

    def test_tabella_senza_colonne_attese_viola(self, tmp_path: Path) -> None:
        result = check(delivery(tmp_path, media="| A | B |\n| - | - |\n| x | y |\n"), None)
        assert any("colonne attese" in v for v in result["violations"])

    def test_il_riepilogo_conta_gli_stati(self, tmp_path: Path) -> None:
        media = MEDIA_OK + "| hero.webp | staging · home.hero |  | pending | import assente |\n"
        result = check(delivery(tmp_path, media=media), None)
        assert result["media"]["by_state"] == {"pending": 1, "verified": 1, "blocked": 0}
        assert result["media"]["all_verified"] is False

    def test_parsing_ignora_la_riga_separatrice(self) -> None:
        rows, problems = parse_media_table(MEDIA_OK)
        assert problems == []
        assert len(rows) == 1 and rows[0]["asset"] == "logo.png"


class TestSlugify:
    def test_normalizza_nome_libero(self) -> None:
        assert slugify("Studio Arco — Sito 2026") == "studio-arco-sito-2026"

    def test_lo_slug_prodotto_supera_sempre_il_validatore(self) -> None:
        nomi = [
            "Dott. Rossi",
            "Sito Rev. 2",
            "Studio Arco S.r.l. Milano",
            "ACME S.p.A. – sito 2026",
            "Sito v. 1 . 2",
            "Museo Civico 1.0",
            "Città di Verona",
        ]
        for nome in nomi:
            slug = slugify(nome)
            assert slug and SLUG.fullmatch(slug), f"{nome} → {slug!r}"

    def test_il_punto_di_punteggiatura_diventa_trattino(self) -> None:
        assert slugify("Dott. Rossi") == "dott-rossi"

    def test_conserva_la_versione_puntata(self) -> None:
        assert slugify("Museo Civico 1.0") == "museo-civico-1.0"

    def test_toglie_gli_accenti(self) -> None:
        assert slugify("Città di Verona") == "citta-di-verona"

    def test_lo_stesso_nome_da_sempre_lo_stesso_slug(self) -> None:
        assert slugify("  Studio  Arco  ") == slugify("Studio Arco")

    def test_un_nome_senza_lettere_non_produce_slug(self, capsys) -> None:
        assert main(["--slugify", "—«»—"]) == 1

    def test_la_modalita_slugify_non_richiede_la_cartella(self, capsys) -> None:
        assert main(["--slugify", "Studio Arco"]) == 0
        assert '"slug": "studio-arco"' in capsys.readouterr().out


class TestIdentitaAttesaDeiMedia:
    ATTESI = {"logo.png": {"mime": "image/png", "dimensions": "640×320"}}

    def test_identita_registrata_passa(self, tmp_path: Path) -> None:
        result = check(delivery(tmp_path), None, self.ATTESI)
        assert result["violations"] == []
        assert result["media"]["expected_checked"] == 1

    def test_un_campo_non_registrato_viola(self, tmp_path: Path) -> None:
        result = check(delivery(tmp_path), None, {"logo.png": {"mime": "image/webp"}})
        assert any("mime atteso (image/webp)" in v for v in result["violations"])

    def test_un_attachment_che_e_solo_un_prefisso_viola(self, tmp_path: Path) -> None:
        # 42 non deve valere per 4207: il confronto è sulla cella, non sulla riga.
        media = MEDIA_OK.replace("| 42 |", "| 4207 |").replace("attachment 42,", "attachment 4207,")
        result = check(delivery(tmp_path, media=media), None, {"logo.png": {"attachment": "42"}})
        assert any("attachment atteso 42, registrato 4207" in v for v in result["violations"])

    def test_dimensioni_che_sono_una_sottostringa_violano(self, tmp_path: Path) -> None:
        media = MEDIA_OK.replace("640×320", "1640×3200")
        result = check(
            delivery(tmp_path, media=media), None, {"logo.png": {"dimensions": "640×320"}}
        )
        assert any("dimensions atteso (640×320)" in v for v in result["violations"])

    def test_il_target_non_puo_valere_come_mime(self, tmp_path: Path) -> None:
        result = check(delivery(tmp_path), None, {"logo.png": {"mime": "staging"}})
        assert any("mime atteso (staging)" in v for v in result["violations"])

    def test_senza_identita_registrata_il_campo_e_non_verificabile(self, tmp_path: Path) -> None:
        media = MEDIA_OK.replace("| attachment 42, image/png, 640×320 |", "|  |")
        result = check(
            delivery(tmp_path, media=media), None, {"logo.png": {"mime": "image/png"}}
        )
        assert any("non verificabile" in v for v in result["violations"])

    def test_un_asset_atteso_e_assente_viola(self, tmp_path: Path) -> None:
        result = check(delivery(tmp_path), None, {"hero.webp": {"mime": "image/webp"}})
        assert any("assente dalla mappa" in v for v in result["violations"])

    def test_senza_attesi_il_controllo_non_scatta(self, tmp_path: Path) -> None:
        result = check(delivery(tmp_path), None, None)
        assert "expected_checked" not in result["media"]

    def test_guarda_anche_le_colonne_oltre_le_cinque_obbligatorie(self, tmp_path: Path) -> None:
        # `Identità` è la colonna dove MIME e dimensioni vengono di norma registrati:
        # scartarla farebbe fallire il confronto su una mappa corretta.
        media = (
            "# Mappa media\n\n"
            "| Asset | Target e binding | Attachment | Identità | Stato | Evidenza |\n"
            "| --- | --- | --- | --- | --- | --- |\n"
            "| logo.png | staging · site-logo | 42 | image/png · 640×320 | verified | GET media/42 |\n"
        )
        result = check(delivery(tmp_path, media=media), None, self.ATTESI)
        assert result["violations"] == []


class TestIdentitaDellaRelease:
    GATES_OK = "{substantive_review: passed, prose_review: passed, release: GO}"

    def promossa(self, tmp_path: Path, identity: str) -> Path:
        folder = delivery(
            tmp_path, status="release-approved", gates=self.GATES_OK, identity=identity
        )
        return con_evidenze(folder)

    def test_un_digest_senza_artefatto_non_promuove(self, tmp_path: Path) -> None:
        result = check(
            self.promossa(
                tmp_path,
                "{version: 1.0, commit: null, artifact: null, digest: "
                + "e" * 64
                + ", target: staging, content_snapshot: null}",
            ),
            None,
        )
        assert any("identificatore immutabile verificato" in v for v in result["violations"])

    def test_uno_snapshot_a_parole_non_promuove(self, tmp_path: Path) -> None:
        result = check(
            self.promossa(
                tmp_path,
                "{version: 1.0, commit: null, artifact: null, digest: null, "
                "target: staging, content_snapshot: backup di ieri 2 copie}",
            ),
            None,
        )
        assert any("identificatore immutabile verificato" in v for v in result["violations"])

    def test_un_digest_con_artefatto_corrispondente_promuove(self, tmp_path: Path) -> None:
        import hashlib

        contenuto = b"tema"
        digest = hashlib.sha256(contenuto).hexdigest()
        folder = self.promossa(
            tmp_path,
            "{version: 1.0, commit: null, artifact: theme.zip, digest: "
            + digest
            + ", target: staging, content_snapshot: null}",
        )
        (folder / "theme.zip").write_bytes(contenuto)
        con_evidenze(folder, EVIDENZE.replace("commit 6ed04b2a1c3d5e7f", f"digest {digest}"))
        assert check(folder, None)["violations"] == []

    def test_un_target_congelato_altrove_viola(self, tmp_path: Path) -> None:
        result = check(
            delivery(
                tmp_path,
                identity="{version: 1.0, commit: 6ed04b2a1c3d5e7f, artifact: null, "
                "digest: null, target: produzione, content_snapshot: null}",
            ),
            None,
        )
        assert any("congelato per un altro ambiente" in v for v in result["violations"])


class TestEvidenzeDeiGate:
    def test_prose_review_passata_senza_i_path_viola(self, tmp_path: Path) -> None:
        folder = delivery(
            tmp_path,
            gates="{substantive_review: passed, prose_review: passed, release: pending}",
        )
        (folder / "release-evidence.md").write_text("# Evidenze\n\nTutto fatto.\n", encoding="utf-8")
        result = check(folder, None)
        assert any("blocco «File revisionati»" in v for v in result["violations"])

    def test_un_verdetto_senza_identita_citata_viola(self, tmp_path: Path) -> None:
        folder = delivery(
            tmp_path,
            status="gate-pending",
            gates="{substantive_review: passed, prose_review: passed, release: GO}",
        )
        con_evidenze(folder, EVIDENZE.replace("commit 6ed04b2a1c3d5e7f", "commit ignoto"))
        result = check(folder, None)
        assert any("non nomina l'identità" in v for v in result["violations"])

    def test_evidenze_complete_passano(self, tmp_path: Path) -> None:
        folder = delivery(
            tmp_path,
            status="gate-pending",
            gates="{substantive_review: passed, prose_review: passed, release: GO}",
        )
        con_evidenze(folder)
        assert check(folder, None)["violations"] == []


class TestVerifyEInizializzazione:
    def test_verify_non_deve_pianificare_componenti(self, tmp_path: Path) -> None:
        result = check(
            delivery(
                tmp_path,
                intent="verify",
                artifacts="{content_model: not-applicable, component_plan: not-applicable, "
                "media_map: ready, release_evidence: ready}",
            ),
            None,
        )
        assert result["violations"] == []

    def test_not_applicable_non_vale_per_create(self, tmp_path: Path) -> None:
        result = check(
            delivery(
                tmp_path,
                artifacts="{content_model: not-applicable, component_plan: ready, "
                "media_map: ready, release_evidence: ready}",
            ),
            None,
        )
        assert any("vale solo per `intent: verify`" in v for v in result["violations"])

    def test_not_applicable_non_blocca_i_gate(self, tmp_path: Path) -> None:
        folder = delivery(
            tmp_path,
            intent="verify",
            artifacts="{content_model: not-applicable, component_plan: not-applicable, "
            "media_map: ready, release_evidence: ready}",
            gates="{substantive_review: passed, prose_review: pending, release: pending}",
        )
        result = check(folder, None)
        assert not any("gate avviati con artefatti aperti" in v for v in result["violations"])

    def test_in_inizializzazione_i_file_mancanti_non_sono_violazioni(self, tmp_path: Path) -> None:
        folder = delivery(tmp_path, files=())
        result = check(folder, None, initializing=True)
        assert "content-model.md" in result["missing_files"]
        assert not any("file della delivery mancante" in v for v in result["violations"])


class TestValoriConVirgole:
    def test_un_ambito_con_due_ambienti_resta_intero(self, tmp_path: Path) -> None:
        result = check(delivery(tmp_path, scope='"staging, produzione"', target="staging"), None)
        assert result["violations"] == []

    def test_i_blocker_a_blocchi_reggono_le_virgole(self, tmp_path: Path) -> None:
        folder = delivery(tmp_path, status="blocked")
        testo = (folder / "delivery.md").read_text(encoding="utf-8").replace(
            "blockers: []",
            "blockers:\n  - manca la baseline approvata, senza cui la verifica non prova nulla",
        )
        (folder / "delivery.md").write_text(testo, encoding="utf-8")
        result = check(folder, None)
        assert result["frontmatter"]["blockers"] == [
            "manca la baseline approvata, senza cui la verifica non prova nulla"
        ]
        assert result["blocking_state"] is True

    def test_una_delivery_bloccata_e_dichiarata_tale(self, tmp_path: Path) -> None:
        folder = delivery(tmp_path, status="blocked", target="", blockers="[target non risolvibile]")
        result = check(folder, None)
        assert result["blocking_state"] is True
        assert any("`target` vuoto" in v for v in result["violations"])


class TestPromozione:
    """I requisiti terminali si valutano su dove si sta andando, non su dove si è."""

    def test_la_promozione_non_passa_con_i_gate_pendenti(self, tmp_path: Path) -> None:
        result = check(delivery(tmp_path, status="gate-pending"), "release-approved")
        assert result["ok"] is False
        messages = " ".join(result["violations"])
        assert "review sostanziale" in messages and "verdetto favorevole" in messages

    def test_la_promozione_non_passa_senza_identita(self, tmp_path: Path) -> None:
        result = check(
            delivery(
                tmp_path,
                status="gate-pending",
                gates="{substantive_review: passed, prose_review: passed, release: GO}",
                identity="{version: 1.0, commit: null, artifact: null, digest: null, "
                "target: staging, content_snapshot: null}",
            ),
            "release-approved",
        )
        assert any("identificatore immutabile" in v for v in result["violations"])

    def test_la_promozione_non_passa_con_un_media_pendente(self, tmp_path: Path) -> None:
        media = MEDIA_OK + "| hero.webp | staging · home |  | pending | import assente |\n"
        folder = delivery(
            tmp_path,
            status="gate-pending",
            gates="{substantive_review: passed, prose_review: passed, release: GO}",
            media=media,
        )
        con_evidenze(folder)
        result = check(folder, "release-approved")
        assert any("media ancora pendenti" in v for v in result["violations"])

    def test_una_promozione_legittima_passa(self, tmp_path: Path) -> None:
        folder = delivery(
            tmp_path,
            status="gate-pending",
            gates="{substantive_review: passed, prose_review: passed, release: GO}",
        )
        con_evidenze(folder)
        assert check(folder, "release-approved")["ok"] is True


class TestAutorizzazione:
    def test_implementing_senza_autorizzazione_viola(self, tmp_path: Path) -> None:
        result = check(delivery(tmp_path, authorized="false", scope=""), None)
        assert any("il silenzio non è consenso" in v for v in result["violations"])

    def test_la_transizione_a_implementing_pretende_lautorizzazione(self, tmp_path: Path) -> None:
        result = check(
            delivery(tmp_path, status="planning", authorized="false", scope=""),
            "implementing",
        )
        assert any("il silenzio non è consenso" in v for v in result["violations"])

    def test_unautorizzazione_per_un_altro_target_non_vale(self, tmp_path: Path) -> None:
        result = check(
            delivery(tmp_path, target="produzione", scope="staging-casa-verde"), None
        )
        assert any("non nomina il target" in v for v in result["violations"])

    def test_lo_scope_che_nomina_il_target_passa(self, tmp_path: Path) -> None:
        result = check(
            delivery(tmp_path, target="produzione", scope="produzione e staging"), None
        )
        assert not any("non nomina il target" in v for v in result["violations"])


class TestVerifyCompleto:
    def verify_delivery(self, tmp_path: Path, **kwargs) -> Path:
        folder = delivery(
            tmp_path,
            intent="verify",
            status="verification-pending",
            artifacts="{content_model: not-applicable, component_plan: not-applicable, "
            "media_map: ready, release_evidence: ready}",
            files=("release-evidence.md",),
            **kwargs,
        )
        return folder

    def test_verify_senza_i_due_file_del_piano_e_coerente(self, tmp_path: Path) -> None:
        folder = self.verify_delivery(tmp_path)
        result = check(folder, None)
        assert result["missing_files"] == []
        assert result["violations"] == []

    def test_la_prose_review_di_verify_copre_due_file(self, tmp_path: Path) -> None:
        folder = self.verify_delivery(
            tmp_path,
            gates="{substantive_review: passed, prose_review: passed, release: pending}",
        )
        (folder / "release-evidence.md").write_text(EVIDENZE_VERIFY, encoding="utf-8")
        assert check(folder, None)["violations"] == []


class TestFrontmatterABlocchi:
    def test_le_mappe_indentate_vengono_lette(self, tmp_path: Path) -> None:
        folder = tmp_path / "wp-demo"
        folder.mkdir()
        (folder / "delivery.md").write_text(
            "---\n"
            "schema: grl-wordpress-delivery/v1\n"
            "slug: wp-demo\n"
            "intent: create\n"
            "status: implementing\n"
            "target: staging\n"
            "implementation_authorized: true\n"
            "authorization_scope: staging\n"
            "artifacts:\n"
            "  content_model: ready\n"
            "  component_plan: ready\n"
            "  media_map: ready\n"
            "  release_evidence: ready\n"
            "gates:\n"
            "  substantive_review: pending\n"
            "  prose_review: pending\n"
            "  release: pending\n"
            "blockers: []\n"
            "---\n\n- 2026-08-09 — creata.\n",
            encoding="utf-8",
        )
        (folder / "media-map.md").write_text(MEDIA_OK, encoding="utf-8")
        for name in ("content-model.md", "component-plan.md", "release-evidence.md"):
            (folder / name).write_text(f"# {name}\n", encoding="utf-8")
        result = check(folder, None)
        assert result["frontmatter"]["artifacts"]["content_model"] == "ready"
        assert result["violations"] == []


class TestFixtureDelModulo:
    def test_wp_casa_verde_e_coerente(self) -> None:
        folder = REPO / "src/skills/grl-wordpress-delivery/evals/fixtures/wp-casa-verde"
        result = check(folder, None)
        assert result["violations"] == []
        assert result["media"]["by_state"]["pending"] == 1

    def test_museo_civico_e_finalizzabile(self) -> None:
        folder = REPO / "src/skills/grl-wordpress-delivery/evals/fixtures/museo-civico-1.0"
        result = check(folder, None)
        assert result["violations"] == []
        assert result["media"]["all_verified"] is True
