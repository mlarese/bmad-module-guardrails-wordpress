#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# ///
"""Test di scan_project.py. Esecuzione: uv run scripts/tests/test_scan_project.py"""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import scan_project  # noqa: E402


class TestBucketDipendenze(unittest.TestCase):
    def test_prefisso_piu_lungo_vince(self):
        # "next-auth" combacia sia con "next" sia con "next-auth": deve vincere il secondo.
        esito = scan_project._bucket_dipendenze(["next", "next-auth"])
        self.assertEqual(esito["web_frontend"], ["next"])
        self.assertEqual(esito["auth_utenti"], ["next-auth"])

    def test_pacchetti_con_scope(self):
        esito = scan_project._bucket_dipendenze(["@anthropic-ai/sdk", "@supabase/supabase-js"])
        self.assertEqual(esito["ai"], ["@anthropic-ai/sdk"])
        self.assertEqual(esito["database"], ["@supabase/supabase-js"])

    def test_confine_di_nome_non_prefisso_nudo(self):
        # "reactivity" non e' "react": il confronto e' a confine di nome.
        self.assertEqual(scan_project._bucket_dipendenze(["reactivity"]), {})

    def test_dipendenza_sconosciuta_esclusa(self):
        self.assertEqual(scan_project._bucket_dipendenze(["lodash", "  "]), {})

    def test_nessun_duplicato(self):
        esito = scan_project._bucket_dipendenze(["stripe", "stripe"])
        self.assertEqual(esito["pagamenti"], ["stripe"])


class TestScansione(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.radice = Path(self._tmp.name)

    def tearDown(self):
        self._tmp.cleanup()

    def test_progetto_vuoto_non_esplode(self):
        esito = scan_project.scansiona(self.radice)
        self.assertTrue(esito["ok"])
        self.assertIsNone(esito["profilo_esistente"])
        self.assertIsNone(esito["readme"])
        self.assertEqual(esito["manifest"], [])

    def test_package_json_e_readme(self):
        (self.radice / "package.json").write_text(
            json.dumps({
                "name": "demo",
                "description": "Un portale",
                "dependencies": {"react": "18", "stripe": "16"},
            }),
            encoding="utf-8",
        )
        (self.radice / "README.md").write_text("# Demo\n\nUn portale.\n", encoding="utf-8")
        esito = scan_project.scansiona(self.radice)
        self.assertEqual(esito["manifest"][0]["nome"], "demo")
        self.assertEqual(esito["manifest"][0]["numero_dipendenze"], 2)
        self.assertIn("pagamenti", esito["dipendenze_segnale"])
        self.assertEqual(esito["readme"]["percorso"], "README.md")
        self.assertIn("Demo", esito["readme"]["estratto"])

    def test_package_json_illeggibile_non_blocca(self):
        (self.radice / "package.json").write_text("{ non json", encoding="utf-8")
        esito = scan_project.scansiona(self.radice)
        self.assertTrue(esito["ok"])
        self.assertEqual(esito["manifest"][0]["errore"], "JSON non leggibile")

    def test_node_modules_ignorato(self):
        modulo = self.radice / "node_modules" / "x"
        modulo.mkdir(parents=True)
        (modulo / "index.js").write_text("x", encoding="utf-8")
        (self.radice / "app.js").write_text("x", encoding="utf-8")
        esito = scan_project.scansiona(self.radice)
        self.assertEqual(esito["estensioni"], {".js": 1})

    def test_profilo_esistente_rilevato(self):
        profilo = self.radice / scan_project.PERCORSO_PROFILO
        profilo.parent.mkdir(parents=True)
        profilo.write_text("# Profilo\n", encoding="utf-8")
        esito = scan_project.scansiona(self.radice)
        self.assertEqual(esito["profilo_esistente"]["percorso"], scan_project.PERCORSO_PROFILO)
        self.assertIn("# Profilo", esito["profilo_esistente"]["contenuto"])

    def test_pyproject_toml(self):
        (self.radice / "pyproject.toml").write_text(
            '[project]\nname = "srv"\ndescription = "API"\ndependencies = ["fastapi>=0.110", "anthropic"]\n',
            encoding="utf-8",
        )
        esito = scan_project.scansiona(self.radice)
        self.assertEqual(esito["manifest"][0]["nome"], "srv")
        self.assertEqual(esito["dipendenze_segnale"]["ai"], ["anthropic"])
        self.assertEqual(esito["dipendenze_segnale"]["web_backend"], ["fastapi"])

    def test_manifest_a_righe_legge_tutte_le_dipendenze(self):
        # Regressione: senza re.MULTILINE veniva letta solo la prima riga.
        (self.radice / scan_project.NOME_REQUISITI_PY).write_text(
            "django==5.0\nopenai>=1.2\nrequests\n", encoding="utf-8"
        )
        esito = scan_project.scansiona(self.radice)
        self.assertEqual(esito["manifest"][0]["numero_dipendenze"], 3)
        self.assertEqual(esito["dipendenze_segnale"]["ai"], ["openai"])
        self.assertEqual(esito["dipendenze_segnale"]["web_backend"], ["django"])

    def test_documenti_di_progetto(self):
        (self.radice / "docs").mkdir()
        (self.radice / "docs" / "prd.md").write_text("x", encoding="utf-8")
        (self.radice / "README.md").write_text("x", encoding="utf-8")
        esito = scan_project.scansiona(self.radice)
        self.assertIn("docs/prd.md", esito["documenti"])
        self.assertIn("README.md", esito["documenti"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
