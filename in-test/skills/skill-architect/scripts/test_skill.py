#!/usr/bin/env python3
"""Acceptance tests for skill.py. Run: python scripts/test_skill.py -v"""

from __future__ import annotations

import hashlib
import re
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SKILL_PY = Path(__file__).resolve().parent / "skill.py"

GOOD_SKILL_MD = """---
name: {name}
description: Does one thing. Use when the user asks for that thing.
---

# {name}

Body text. Read `references/guide.md` before the first run.
"""


GOOD_EVALS = """[
  {"name": "case-one", "prompt": "Do the thing.", "expect": ["does the thing"]},
  {"name": "case-two", "prompt": "Again.", "context": "after case one", "expect": ["does it again"]}
]
"""


def run(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(SKILL_PY), *args],
        capture_output=True,
        text=True,
        encoding="utf-8",
    )


def write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def make_skill(root: Path, name: str = "demo-skill", body: str | None = None) -> Path:
    skill = root / name
    write(skill / "SKILL.md", body if body is not None else GOOD_SKILL_MD.format(name=name))
    write(skill / "references" / "guide.md", "guide\n")
    return skill


def set_status(design: Path, status: str) -> None:
    text = design.read_text(encoding="utf-8").replace("status: draft", f"status: {status}", 1)
    design.write_text(text, encoding="utf-8")


def fill_placeholders(design: Path) -> None:
    """Replace every placeholder form the template uses with real-looking text."""
    text = re.sub(r"\{\{[^{}]*\}\}", "filled", design.read_text(encoding="utf-8"))
    out = []
    for part in re.split(r"(\n\s*\n)", text):
        s = part.strip()
        out.append("Filled section text." if s.startswith("[") and s.endswith("]") else part)
    design.write_text("".join(out), encoding="utf-8")


class SkillPyTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def design_of(self, name: str = "demo-skill") -> Path:
        return self.root / f"{name}-workspace" / "skill-design.md"

    # 1
    def test_new_fresh(self) -> None:
        r = run("new", str(self.root / "demo-skill"))
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        design = self.design_of()
        text = design.read_text(encoding="utf-8")
        self.assertIn("mode: new", text)
        self.assertIn("status: draft", text)
        self.assertIn("skill: demo-skill", text)
        self.assertNotIn("{{name}}", text)
        self.assertNotIn("{{YYYY-MM-DD}}", text)
        self.assertFalse((self.root / "demo-skill").exists(), "skill folder must not be created")

    # 2
    def test_new_existing(self) -> None:
        skill = make_skill(self.root)
        r = run("new", str(skill))
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        text = self.design_of().read_text(encoding="utf-8")
        digest = hashlib.sha256((skill / "SKILL.md").read_bytes()).hexdigest()
        self.assertIn("mode: existing", text)
        self.assertIn(f"baseline: {digest}", text)

    # 3
    def test_new_refuses_overwrite(self) -> None:
        run("new", str(self.root / "demo-skill"))
        design = self.design_of()
        design.write_text(design.read_text(encoding="utf-8") + "\nmy notes\n", encoding="utf-8")
        r = run("new", str(self.root / "demo-skill"))
        self.assertEqual(r.returncode, 1)
        self.assertIn("already exists", r.stdout)
        self.assertIn("my notes", design.read_text(encoding="utf-8"))

    # 4
    def test_check_draft_passes(self) -> None:
        run("new", str(self.root / "demo-skill"))
        r = run("check", str(self.root / "demo-skill"))
        self.assertEqual(r.returncode, 0, r.stdout)
        self.assertIn("OK:", r.stdout)
        self.assertIn("design: draft", r.stdout)

    # 5
    def test_gate_new(self) -> None:
        run("new", str(self.root / "demo-skill"))
        make_skill(self.root)
        r = run("check", str(self.root / "demo-skill"))
        self.assertEqual(r.returncode, 1)
        self.assertIn("exists while skill-design.md is draft", r.stdout)

    # 6
    def test_gate_existing(self) -> None:
        skill = make_skill(self.root)
        run("new", str(skill))
        r = run("check", str(skill))
        self.assertEqual(r.returncode, 0, r.stdout)
        with (skill / "SKILL.md").open("a", encoding="utf-8") as f:
            f.write("\nA sneaky edit.\n")
        r = run("check", str(skill))
        self.assertEqual(r.returncode, 1)
        self.assertIn("changed while skill-design.md is draft", r.stdout)

    # 7
    def test_approved_placeholder(self) -> None:
        run("new", str(self.root / "demo-skill"))
        design = self.design_of()
        set_status(design, "approved")
        r = run("check", str(self.root / "demo-skill"))
        self.assertEqual(r.returncode, 1)
        self.assertIn("approved but placeholder left", r.stdout)
        # Filled in completely, the same approved design passes (with a skill present).
        fill_placeholders(design)
        set_status(design, "approved")
        text = design.read_text(encoding="utf-8")
        self.assertIn("status: approved", text)
        make_skill(self.root)
        r = run("check", str(self.root / "demo-skill"))
        self.assertEqual(r.returncode, 0, r.stdout)

    # 8
    def test_frontmatter_all_errors(self) -> None:
        bad = (
            "---\n"
            "name: other-name\n"
            "colour: blue\n"
            f"description: <b>{'x' * 1100}</b>\n"
            "---\n\nBody mentions `references/guide.md`.\n"
        )
        skill = make_skill(self.root, body=bad)
        r = run("check", str(skill))
        self.assertEqual(r.returncode, 1)
        self.assertIn("unknown frontmatter key(s): colour", r.stdout)
        self.assertIn("does not match folder", r.stdout)
        self.assertIn("max 1024", r.stdout)
        self.assertIn("contains < or >", r.stdout)

    # 9
    def test_references(self) -> None:
        body = GOOD_SKILL_MD.format(name="demo-skill").replace(
            "Read `references/guide.md` before the first run.",
            "Read `references/missing.md` first. Pattern: `references/<topic>.md`.",
        )
        skill = make_skill(self.root, body=body)
        r = run("check", str(skill))
        self.assertEqual(r.returncode, 1)
        self.assertIn("references/guide.md is never mentioned", r.stdout)
        self.assertIn("mentions references/missing.md, which does not exist", r.stdout)
        self.assertNotIn("<topic>", r.stdout)

    # 11 (no false positives): a placeholder named inside code is prose about placeholders
    def test_placeholder_in_code_is_skipped(self) -> None:
        body = GOOD_SKILL_MD.format(name="demo-skill").replace(
            "Body text.", "Fill every `{{placeholder}}` in the template.\n\n```\n{{also skipped}}\n```"
        )
        skill = make_skill(self.root, body=body)
        r = run("check", str(skill))
        self.assertEqual(r.returncode, 0, r.stdout)
        body = body.replace("Fill every", "Fill {{this one}} and every")
        write(skill / "SKILL.md", body)
        r = run("check", str(skill))
        self.assertEqual(r.returncode, 1)
        self.assertIn("placeholder left: {{this one}}", r.stdout)

    def step_of(self, skill: Path) -> str:
        r = run("status", str(skill))
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        line = next(l for l in r.stdout.splitlines() if l.startswith("step: "))
        return line.split()[1]

    # task 004, criterion 1
    def test_status_steps(self) -> None:
        skill = self.root / "demo-skill"
        self.assertEqual(self.step_of(skill), "start")
        run("new", str(skill))
        self.assertEqual(self.step_of(skill), "design")
        design = self.design_of()
        fill_placeholders(design)
        self.assertEqual(self.step_of(skill), "approval")
        set_status(design, "approved")
        self.assertEqual(self.step_of(skill), "write")
        make_skill(self.root)
        self.assertEqual(self.step_of(skill), "evals")
        write(skill / "evals" / "evals.json", GOOD_EVALS)
        good = (skill / "SKILL.md").read_text(encoding="utf-8")
        write(skill / "SKILL.md", good.replace("name: demo-skill", "name: Wrong Name"))
        self.assertEqual(self.step_of(skill), "fix")
        write(skill / "SKILL.md", good)
        self.assertEqual(self.step_of(skill), "done")

    # task 004, criterion 2
    def test_status_existing(self) -> None:
        skill = make_skill(self.root)
        self.assertEqual(self.step_of(skill), "start")
        run("new", str(skill))
        self.assertEqual(self.step_of(skill), "design")
        design = self.design_of()
        text = design.read_text(encoding="utf-8")
        baseline = next(l for l in text.splitlines() if l.startswith("baseline:"))
        fill_placeholders(design)
        # fill_placeholders must not touch the recorded baseline
        text = design.read_text(encoding="utf-8")
        self.assertIn(baseline, text)
        set_status(design, "approved")
        self.assertEqual(self.step_of(skill), "write")

    # task 005, criterion 1
    def test_evals_validation(self) -> None:
        skill = make_skill(self.root)
        evals = skill / "evals" / "evals.json"
        write(evals, GOOD_EVALS)
        r = run("check", str(skill))
        self.assertEqual(r.returncode, 0, r.stdout)
        bad = {
            "{not json": "not valid JSON",
            "[]": "no cases",
            '[{"name": "a", "prompt": "p", "expect": []}]': "expect must be a non-empty list",
            '[{"name": "a", "prompt": "p", "expect": ["x"]}, {"name": "a", "prompt": "q", "expect": ["y"]}]': "duplicate name 'a'",
        }
        for text, message in bad.items():
            with self.subTest(message=message):
                write(evals, text)
                r = run("check", str(skill))
                self.assertEqual(r.returncode, 1, r.stdout)
                self.assertIn(message, r.stdout)

    # 10
    def test_utf8(self) -> None:
        body = GOOD_SKILL_MD.format(name="demo-skill").replace(
            "Body text.", "Текст на русском → со стрелкой и «кавычками»."
        )
        skill = make_skill(self.root, body=body)
        r = run("new", str(skill))
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        r = run("check", str(skill))
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertNotIn("Traceback", r.stderr)


if __name__ == "__main__":
    unittest.main()
