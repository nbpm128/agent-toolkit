#!/usr/bin/env python3
"""Scaffold and validate a skill built from a design file.

    python skill.py new   <skill-dir>   create <name>-workspace/skill-design.md beside the skill
    python skill.py check <skill-dir>   validate the structure of the skill and its design
    python skill.py status <skill-dir>  print the current step, computed from what is on disk

The design lives outside the skill, in a sibling `<name>-workspace/` directory, because it is a
temporary artifact. While the design is `draft`, the skill's SKILL.md must not be written (new
skill) or changed (existing skill, compared against the sha256 recorded by `new`).

Exit codes: 0 pass, 1 findings, 2 usage error. Standard library only; every file is UTF-8.
"""

from __future__ import annotations

import argparse
import datetime as _dt
import hashlib
import json
import re
import sys
from pathlib import Path

# Literals shared with assets/skill-design.template.md. Renaming one there without renaming it
# here must fail loudly, so each is named once.
SKILL_FILE = "SKILL.md"
DESIGN_FILE = "skill-design.md"
WORKSPACE_SUFFIX = "-workspace"
TEMPLATE = Path(__file__).resolve().parent.parent / "assets" / "skill-design.template.md"
REFERENCES_DIR = "references"
EVALS_FILE = Path("evals") / "evals.json"

DESIGN_TYPE = "skill-design"
STATUS_DRAFT, STATUS_APPROVED = "draft", "approved"
STATUSES = {STATUS_DRAFT, STATUS_APPROVED}
MODE_NEW, MODE_EXISTING = "new", "existing"
MODES = {MODE_NEW, MODE_EXISTING}
NO_BASELINE = "none"

# Frontmatter rules of the skill spec, the same ones skill-creator's quick_validate.py applies.
ALLOWED_KEYS = {"name", "description", "license", "allowed-tools", "metadata", "compatibility"}
NAME_MAX, DESCRIPTION_MAX, COMPATIBILITY_MAX = 64, 1024, 500

KEBAB = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")
SHA256_HEX = re.compile(r"^[0-9a-f]{64}$")
CURLY = re.compile(r"\{\{[^{}]*\}\}")
INLINE_CODE = re.compile(r"`[^`]*`")
REF_MENTION = re.compile(r"references/[^\s`'\")\]|,;]+")


class Nested:
    """Marker for a key whose value is an indented block (e.g. `metadata:`). Not validated."""

    def __repr__(self) -> str:
        return "<nested>"


# --------------------------------------------------------------------------- parsing


def parse_frontmatter(text: str) -> tuple[dict, str]:
    """Split a document into a flat frontmatter mapping and its body.

    Handles `key: value`, quoted values, trailing ` # comment` on unquoted values, block
    scalars (`>` folds with spaces, `|` keeps newlines) and nested blocks (kept as Nested).
    Returns ({}, text) when there is no frontmatter, so the caller reports it as a finding.
    """
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return {}, text
    try:
        end = next(i for i in range(1, len(lines)) if lines[i].strip() == "---")
    except StopIteration:
        return {}, text

    raw, body = lines[1:end], "\n".join(lines[end + 1 :])
    data: dict = {}
    i = 0
    while i < len(raw):
        line = raw[i]
        i += 1
        if not line.strip() or line.lstrip().startswith("#") or line[:1].isspace() or ":" not in line:
            continue
        key, _, value = line.partition(":")
        key, value = key.strip(), value.strip()

        block: list[str] = []
        while i < len(raw) and (not raw[i].strip() or raw[i][:1].isspace()):
            block.append(raw[i])
            i += 1
        while block and not block[-1].strip():
            block.pop()

        if value[:1] in (">", "|"):
            parts = [b.strip() for b in block]
            data[key] = (" " if value[0] == ">" else "\n").join(p for p in parts if p or value[0] == "|")
        elif not value and block:
            data[key] = Nested()
        else:
            data[key] = _scalar(value)
    return data, body


def _scalar(value: str) -> str:
    if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
        return value[1:-1]
    hash_at = value.find(" #")
    if hash_at != -1:
        value = value[:hash_at]
    return value.strip()


def find_placeholders(body: str) -> list[str]:
    """Unfilled template placeholders: any `{{...}}`, and any paragraph that is wholly
    `[ ... ]` with no `](` inside (so a markdown link or checkbox never counts).
    Fenced code blocks and inline code spans are skipped: text in code *talks about*
    placeholders (`fill every {{placeholder}}`) rather than being one.
    """
    kept, fenced = [], False
    for line in body.splitlines():
        if line.lstrip().startswith("```"):
            fenced = not fenced
            continue
        kept.append("" if fenced else INLINE_CODE.sub("", line))
    text = "\n".join(kept)

    found = CURLY.findall(text)
    for para in re.split(r"\n\s*\n", text):
        p = para.strip()
        if p.startswith("[") and p.endswith("]") and "](" not in p:
            found.append(_short(p))
    return found


def _short(text: str, limit: int = 60) -> str:
    one = " ".join(text.split())
    return one if len(one) <= limit else one[: limit - 3] + "..."


def sha256_of(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def paths_for(skill_dir: Path) -> tuple[str, Path, Path]:
    name = skill_dir.resolve().name
    workspace = skill_dir.resolve().parent / f"{name}{WORKSPACE_SUFFIX}"
    return name, workspace, workspace / DESIGN_FILE


# --------------------------------------------------------------------------- new


def cmd_new(args: argparse.Namespace) -> int:
    skill_dir = Path(args.skill_dir)
    name, workspace, design = paths_for(skill_dir)
    if design.exists():
        print(f"ERROR: {design} already exists; edit it instead of starting over")
        return 1
    if not TEMPLATE.is_file():
        print(f"ERROR: template missing: {TEMPLATE}")
        return 1

    skill_md = skill_dir / SKILL_FILE
    if skill_md.is_file():
        mode, baseline = MODE_EXISTING, sha256_of(skill_md)
    else:
        mode, baseline = MODE_NEW, NO_BASELINE

    text = TEMPLATE.read_text(encoding="utf-8")
    for key, value in {
        "name": name,
        "mode": mode,
        "baseline": baseline,
        "YYYY-MM-DD": _dt.date.today().isoformat(),
    }.items():
        token = "{{" + key + "}}"
        if token not in text:
            # The template and this script disagree on a literal: fail rather than write a
            # design that silently misses a field.
            print(f"ERROR: template has no {token}; template and skill.py are out of step")
            return 1
        text = text.replace(token, value)

    workspace.mkdir(parents=True, exist_ok=True)
    design.write_text(text, encoding="utf-8")
    print(f"created {design} (mode: {mode})")
    return 0


# --------------------------------------------------------------------------- check
#
# What check does not judge — these need reading, so they are the agent's job, and a guess
# here would be a false alarm that teaches people to ignore the checker:
#   - prose quality of SKILL.md or the design;
#   - whether the Model section actually generates the rules;
#   - how many principles or prohibitions there are;
#   - whether the description triggers well;
#   - the contents of scripts/ and assets/;
#   - `references/` mentions containing `<`, `{` or `*` (skipped as patterns, not guessed at);
#   - evals contents: whether cases are good, traced to real failures, or check behaviour
#     rather than wording (only their shape is checked).


def check_design(design: Path, name: str, skill_md: Path) -> tuple[list[str], str]:
    findings: list[str] = []
    meta, body = parse_frontmatter(design.read_text(encoding="utf-8"))
    if not meta:
        return [f"{design}: no frontmatter"], "unreadable"

    status, mode = meta.get("status"), meta.get("mode")
    if meta.get("type") != DESIGN_TYPE:
        findings.append(f"{design}: type is {meta.get('type')!r}, expected {DESIGN_TYPE!r}")
    if meta.get("skill") != name:
        findings.append(f"{design}: skill is {meta.get('skill')!r}, expected {name!r} (the folder name)")
    if status not in STATUSES:
        findings.append(f"{design}: status is {status!r}, expected one of {sorted(STATUSES)}")
    if mode not in MODES:
        findings.append(f"{design}: mode is {mode!r}, expected one of {sorted(MODES)}")

    baseline = meta.get("baseline")
    if mode == MODE_EXISTING and not (isinstance(baseline, str) and SHA256_HEX.match(baseline)):
        findings.append(f"{design}: mode is existing but baseline is not a sha256 hex digest")

    if status == STATUS_APPROVED:
        for ph in find_placeholders(body):
            findings.append(f"{design}: approved but placeholder left: {ph}")

    if status == STATUS_DRAFT:
        if mode == MODE_NEW and skill_md.exists():
            findings.append(f"{skill_md} exists while {DESIGN_FILE} is draft; approve the design first")
        if mode == MODE_EXISTING and isinstance(baseline, str) and SHA256_HEX.match(baseline):
            if not skill_md.is_file():
                findings.append(f"{skill_md} is gone while {DESIGN_FILE} is draft")
            elif sha256_of(skill_md) != baseline:
                findings.append(f"{skill_md} changed while {DESIGN_FILE} is draft; approve the design first")
    return findings, str(status)


def check_skill_md(skill_dir: Path, name: str) -> list[str]:
    skill_md = skill_dir / SKILL_FILE
    text = skill_md.read_text(encoding="utf-8")
    meta, body = parse_frontmatter(text)
    if not meta:
        return [f"{skill_md}: no frontmatter"]

    findings: list[str] = []
    unknown = sorted(set(meta) - ALLOWED_KEYS)
    if unknown:
        findings.append(f"{skill_md}: unknown frontmatter key(s): {', '.join(unknown)}")

    fm_name = meta.get("name")
    if not isinstance(fm_name, str) or not fm_name:
        findings.append(f"{skill_md}: name is missing or not a string")
    else:
        if not KEBAB.match(fm_name):
            findings.append(f"{skill_md}: name {fm_name!r} is not kebab-case")
        if len(fm_name) > NAME_MAX:
            findings.append(f"{skill_md}: name is {len(fm_name)} chars, max {NAME_MAX}")
        if fm_name != name:
            findings.append(f"{skill_md}: name {fm_name!r} does not match folder {name!r}")

    desc = meta.get("description")
    if not isinstance(desc, str) or not desc:
        findings.append(f"{skill_md}: description is missing or not a string")
    else:
        if len(desc) > DESCRIPTION_MAX:
            findings.append(f"{skill_md}: description is {len(desc)} chars, max {DESCRIPTION_MAX}")
        if "<" in desc or ">" in desc:
            findings.append(f"{skill_md}: description contains < or >")

    compat = meta.get("compatibility")
    if isinstance(compat, str) and len(compat) > COMPATIBILITY_MAX:
        findings.append(f"{skill_md}: compatibility is {len(compat)} chars, max {COMPATIBILITY_MAX}")

    for ph in find_placeholders(body):
        findings.append(f"{skill_md}: placeholder left: {ph}")

    refs_dir = skill_dir / REFERENCES_DIR
    if refs_dir.is_dir():
        for f in sorted(p for p in refs_dir.rglob("*") if p.is_file()):
            rel = f.relative_to(skill_dir).as_posix()
            if rel not in text:
                findings.append(f"{skill_md}: {rel} is never mentioned, so nothing triggers reading it")
    for mention in sorted(set(REF_MENTION.findall(text))):
        mention = mention.rstrip(".:")
        if any(c in mention for c in "<{*"):
            continue
        if not (skill_dir / mention).exists():
            findings.append(f"{skill_md}: mentions {mention}, which does not exist")
    return findings


def check_evals(skill_dir: Path) -> list[str]:
    """Shape of evals/evals.json: a non-empty list of {name, prompt, context?, expect[]}."""
    path = skill_dir / EVALS_FILE
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        return [f"{path}: not valid JSON: {e}"]
    if not isinstance(data, list):
        return [f"{path}: top level must be a list of cases"]
    if not data:
        return [f"{path}: no cases"]

    findings: list[str] = []
    seen: set[str] = set()
    for i, case in enumerate(data):
        where = f"{path}: case {i}"
        if not isinstance(case, dict):
            findings.append(f"{where}: not an object")
            continue
        for key in ("name", "prompt"):
            value = case.get(key)
            if not isinstance(value, str) or not value.strip():
                findings.append(f"{where}: {key} is missing or blank")
        if "context" in case and not isinstance(case["context"], str):
            findings.append(f"{where}: context must be a string")
        expect = case.get("expect")
        if not isinstance(expect, list) or not expect:
            findings.append(f"{where}: expect must be a non-empty list")
        elif any(not isinstance(e, str) or not e.strip() for e in expect):
            findings.append(f"{where}: expect holds a blank or non-string item")
        name = case.get("name")
        if isinstance(name, str) and name.strip():
            if name in seen:
                findings.append(f"{where}: duplicate name {name!r}")
            seen.add(name)
    return findings


def collect_findings(skill_dir: Path) -> tuple[list[str], str]:
    """Every finding `check` reports, and the design status. Shared with `status`."""
    name, _workspace, design = paths_for(skill_dir)
    skill_md = skill_dir / SKILL_FILE

    findings: list[str] = []
    status = "absent"
    if not skill_md.is_file() and not design.is_file():
        findings.append(f"nothing to check: neither {skill_md} nor {design} exists")
    if design.is_file():
        design_findings, status = check_design(design, name, skill_md)
        findings += design_findings
    if skill_md.is_file():
        findings += check_skill_md(skill_dir, name)
    if (skill_dir / EVALS_FILE).is_file():
        findings += check_evals(skill_dir)
    return findings, status


def cmd_check(args: argparse.Namespace) -> int:
    skill_dir = Path(args.skill_dir)
    findings, status = collect_findings(skill_dir)
    for f in findings:
        print(f"ERROR: {f}")
    if findings:
        return 1
    print(f"OK: {skill_dir} (design: {status})")
    return 0


# --------------------------------------------------------------------------- status
#
# The step is the first artifact that is missing or not ready. Computed here so the agent
# asks instead of reasoning it out, and gets the same answer in every session.

STEP_START = "start"
STEP_DESIGN = "design"
STEP_APPROVAL = "approval"
STEP_WRITE = "write"
STEP_EVALS = "evals"
STEP_FIX = "fix"
STEP_DONE = "done"


def compute_step(skill_dir: Path) -> tuple[str, str, str]:
    """Return (design line, step, what to do)."""
    _name, _workspace, design = paths_for(skill_dir)
    skill_md = skill_dir / SKILL_FILE

    if not design.is_file():
        todo = f"run skill.py new {skill_dir}"
        if skill_md.is_file():
            todo += " (existing skill: audit mode)"
        return "absent", STEP_START, todo

    meta, body = parse_frontmatter(design.read_text(encoding="utf-8"))
    status, mode = meta.get("status"), meta.get("mode")
    design_line = f"{status} ({mode})"

    if status == STATUS_DRAFT:
        left = find_placeholders(body)
        if left:
            return design_line, STEP_DESIGN, f"fill the design: {len(left)} placeholder(s) left"
        return design_line, STEP_APPROVAL, "offer the design for approval"

    if status == STATUS_APPROVED:
        unwritten = (mode == MODE_NEW and not skill_md.is_file()) or (
            mode == MODE_EXISTING and skill_md.is_file() and sha256_of(skill_md) == meta.get("baseline")
        )
        if unwritten:
            return design_line, STEP_WRITE, "write the skill files from the design"
        if skill_md.is_file() and not (skill_dir / EVALS_FILE).is_file():
            return design_line, STEP_EVALS, f"seed {EVALS_FILE.as_posix()} from design section 7"

    findings, _status = collect_findings(skill_dir)
    if findings:
        return design_line, STEP_FIX, f"{len(findings)} finding(s); run skill.py check {skill_dir}"
    return design_line, STEP_DONE, "nothing left; the workspace can be deleted"


def cmd_status(args: argparse.Namespace) -> int:
    skill_dir = Path(args.skill_dir)
    name, _workspace, _design = paths_for(skill_dir)
    design_line, step, todo = compute_step(skill_dir)
    print(f"skill: {name}")
    print(f"design: {design_line}")
    print(f"step: {step} — {todo}")
    return 0


# --------------------------------------------------------------------------- main


def main(argv: list[str] | None = None) -> int:
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8")

    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = parser.add_subparsers(dest="command", required=True)
    p_new = sub.add_parser("new", help="create the design file in the sibling workspace")
    p_new.add_argument("skill_dir")
    p_new.set_defaults(func=cmd_new)
    p_check = sub.add_parser("check", help="validate the skill and its design")
    p_check.add_argument("skill_dir")
    p_check.set_defaults(func=cmd_check)
    p_status = sub.add_parser("status", help="print the current step, computed from disk")
    p_status.add_argument("skill_dir")
    p_status.set_defaults(func=cmd_status)

    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
