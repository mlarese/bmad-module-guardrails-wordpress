#!/usr/bin/env python3
"""Test del merger dei gruppi tematici di bmad-party-mode."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import tomllib
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts" / "merge-party-groups.py"
SOURCE = ROOT / "assets" / "party-groups.toml"


class MergePartyGroupsTests(unittest.TestCase):
    def run_script(self, project: Path, source: Path = SOURCE, *extra: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, str(SCRIPT), "--project-root", str(project), "--source", str(source), *extra],
            check=False,
            capture_output=True,
            text=True,
        )

    def test_merges_groups_and_preserves_user_content(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            project = Path(directory)
            target = project / "_bmad" / "custom" / "bmad-party-mode.toml"
            target.parent.mkdir(parents=True)
            target.write_text(
                "[workflow]\ndefault_party = \"my-room\"\n\n"
                "[[workflow.party_groups]]\n"
                "id = \"my-room\"\nname = \"My Room\"\n"
                "scene = \"room\"\nmembers = [\"bmad-agent-pm\"]\n\n"
                "# >>> grl:party-groups — generato da gwp-setup, non modificare a mano >>>\n"
                "[[workflow.party_groups]]\nid = \"grl-old\"\nname = \"Old\"\n"
                "scene = \"old\"\nmembers = [\"grl-agent-security\"]\n"
                "# <<< grl:party-groups <<<\n",
                encoding="utf-8",
            )

            result = self.run_script(project)

            self.assertEqual(result.returncode, 0, result.stderr)
            parsed = tomllib.loads(target.read_text(encoding="utf-8"))
            self.assertEqual(parsed["workflow"]["default_party"], "my-room")
            ids = {group["id"] for group in parsed["workflow"]["party_groups"]}
            self.assertIn("my-room", ids)
            self.assertIn("grl-governance", ids)
            self.assertNotIn("grl-old", ids)

    def test_dry_run_does_not_write(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            project = Path(directory)
            (project / "_bmad").mkdir()
            result = self.run_script(project, SOURCE, "--dry-run")
            self.assertEqual(result.returncode, 0, result.stderr)
            payload = json.loads(result.stdout)
            self.assertTrue(payload["dry_run"])
            self.assertFalse((project / "_bmad" / "custom" / "bmad-party-mode.toml").exists())

    def test_invalid_source_fails_without_writing(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            project = Path(directory)
            (project / "_bmad").mkdir()
            invalid = project / "invalid.toml"
            invalid.write_text("[workflow]\nparty_mode = \"session\"\n", encoding="utf-8")

            result = self.run_script(project, invalid)

            self.assertEqual(result.returncode, 1)
            self.assertFalse((project / "_bmad" / "custom" / "bmad-party-mode.toml").exists())


if __name__ == "__main__":
    unittest.main()
