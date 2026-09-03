#!/usr/bin/env python3
"""Validate a plan folder, and regenerate the artifacts derived from it.

The task files' frontmatter is the single source of truth for status. `tasks/_index.md` and
`plan.md` section 7's counts are derived from it, so they are generated rather than maintained
by hand -- which removes the whole class of "the index says Done but the task says In Progress"
drift.

    python validate_plan.py <plan-dir> --check    # read-only; exit 1 if anything is wrong
    python validate_plan.py <plan-dir> --sync     # rewrite the generated blocks, then check

Only two regions of markdown are ever written: the whole of `tasks/_index.md` between its
BEGIN/END GENERATED markers, and the counts block in `plan.md`. Prose is never touched, and
nothing outside the markers is parsed for meaning.

Standard library only -- no PyYAML -- so the skill stays portable. The frontmatter subset
supported is what the templates use: `key: scalar`, `key: [a, b]`, `key: null`, and `# comments`.
"""

from __future__ import annotations

import argparse
import datetime as _dt
import re
import sys
from pathlib import Path

STATUSES = ["not-started", "in-progress", "blocked", "delegated", "done", "dropped"]
# Display order in the index, and the order the counts line uses.
GROUP_ORDER = ["done", "in-progress", "not-started", "blocked", "delegated", "dropped"]
LABEL = {
    "not-started": "Not Started",
    "in-progress": "In Progress",
    "blocked": "Blocked",
    "delegated": "Delegated",
    "done": "Done",
    "dropped": "Dropped",
}
COUNTS_ORDER = ["done", "in-progress", "not-started", "blocked", "delegated"]

BEGIN = "<!-- BEGIN GENERATED"
END = "<!-- END GENERATED -->"

PLACEHOLDERS = [
    r"\bTBD\b",
    r"\bTODO\b",
    r"implement later",
    r"fill in details",
    r"similar to task",
    # Template guidance left unreplaced: a `{{placeholder}}` or a `[Sentence-shaped block]` of
    # bracketed instructions. Cheap to spot, expensive to miss -- an artifact shipped with them
    # is one nobody can execute.
    #
    # The templates mark placeholders `{{...}}` rather than `<...>` deliberately: markdown
    # renderers swallow `<Title>` as an unknown HTML tag, so an unfilled angle placeholder shows
    # up as nothing at all -- the one failure mode a placeholder must never have.
    r"\{\{[^}\n]*\}\}",
    r"\[[A-Z][^\]\n]{25,}\]",
]

TASK_FILE_RE = re.compile(r"^task_(\d{3})_[a-z0-9][a-z0-9-]*$")
REQ_RE = re.compile(r"\*\*(REQ-[0-9]+(?:\.[0-9]+)?)\*\*")


def find_placeholder(text: str) -> str | None:
    """The first template placeholder still sitting in a filled artifact, if any."""
    for pattern in PLACEHOLDERS:
        hit = re.search(pattern, text, re.I)
        if hit:
            return hit.group(0).strip()
    return None


# --------------------------------------------------------------------------- parsing


def parse_frontmatter(text: str) -> tuple[dict, str]:
    """Split a document into its frontmatter mapping and its body.

    Returns ({}, text) when the document has no frontmatter, so callers can report that as a
    finding rather than crashing.
    """
    if not text.startswith("---"):
        return {}, text
    end = text.find("\n---", 3)
    if end == -1:
        return {}, text
    raw = text[text.find("\n") + 1 : end]
    body = text[end + 4 :].lstrip("\n")

    data: dict = {}
    for line in raw.split("\n"):
        line = line.split(" #", 1)[0].rstrip() if " #" in line else line.rstrip()
        if not line.strip() or ":" not in line:
            continue
        key, _, value = line.partition(":")
        data[key.strip()] = _coerce(value.strip())
    return data, body


def _coerce(value: str):
    if value in ("", "null", "None", "~"):
        return None
    if value.startswith("[") and value.endswith("]"):
        inner = value[1:-1].strip()
        if not inner:
            return []
        return [v.strip().strip("'\"") for v in inner.split(",") if v.strip()]
    if value.isdigit():
        return int(value)
    return value.strip("'\"")


def purpose_line(body: str) -> str:
    """The blockquote line right under the H1 -- the deliverable, as shown in the index."""
    lines = []
    seen_h1 = False
    for line in body.split("\n"):
        if line.startswith("# "):
            seen_h1 = True
            continue
        if not seen_h1:
            continue
        if line.startswith(">"):
            lines.append(line.lstrip("> ").strip())
        elif lines:
            break
        elif line.strip():
            break
    return " ".join(lines).strip()


def section(body: str, heading: str) -> str:
    """The text under a `## heading`, up to the next `## `."""
    pattern = re.compile(
        r"^##\s+" + re.escape(heading) + r"\s*$(.*?)(?=^##\s|\Z)",
        re.M | re.S,
    )
    match = pattern.search(body)
    return match.group(1) if match else ""


def strip_generated(body: str) -> str:
    """Drop generated regions -- their contents are the script's own, not the author's."""
    out, cursor = [], 0
    while True:
        start = body.find(BEGIN, cursor)
        if start == -1:
            out.append(body[cursor:])
            return "".join(out)
        out.append(body[cursor:start])
        stop = body.find(END, start)
        if stop == -1:
            return "".join(out)
        cursor = stop + len(END)


def strip_progress_log(body: str) -> str:
    """Everything before `## Progress Log`.

    The log quotes real command output, which legitimately contains angle brackets and
    bracketed text -- scanning it for placeholders would produce false positives.
    """
    marker = body.find("## Progress Log")
    return body if marker == -1 else body[:marker]


# --------------------------------------------------------------------------- model


class Task:
    def __init__(self, path: Path):
        self.path = path
        self.name = path.stem
        text = path.read_text(encoding="utf-8")
        self.meta, self.body = parse_frontmatter(text)
        self.status = self.meta.get("status")
        self.milestone = self.meta.get("milestone")
        self.satisfies = _as_list(self.meta.get("satisfies"))
        self.depends_on = _as_list(self.meta.get("depends_on"))
        self.sub_plan = self.meta.get("sub_plan")
        self.deliverable = purpose_line(self.body)
        self.instructions = section(self.body, "Instructions")
        self.acceptance = section(self.body, "Acceptance / Verification")


def _as_list(value) -> list[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    return [v.strip() for v in str(value).split(",") if v.strip()]


def resolver(tasks: list[Task]) -> dict[str, str]:
    """Map every way a task may be referenced to its full stem.

    Task files are named `task_007_add-token-refresh`, but `depends_on` is authored as the short
    `task_007` -- the templates use that form because the slug may change while the number does
    not. Both spellings resolve here.
    """
    table: dict[str, str] = {}
    for t in tasks:
        table[t.name] = t.name
        prefix = t.name.split("_")[:2]
        if len(prefix) == 2:
            table["_".join(prefix)] = t.name
    return table


def load_tasks(tasks_dir: Path) -> list[Task]:
    if not tasks_dir.is_dir():
        return []
    files = sorted(p for p in tasks_dir.glob("task_*.md") if p.is_file())
    return [Task(p) for p in files]


# --------------------------------------------------------------------------- checks


def check(plan_dir: Path, tasks: list[Task]) -> list[str]:
    problems: list[str] = []
    add = problems.append

    research = plan_dir / "research.md"
    plan_md = plan_dir / "plan.md"
    tasks_dir = plan_dir / "tasks"

    # --- research: approved, and the REQ set it defines
    reqs: list[str] = []
    if not research.exists():
        add("research.md is missing -- Phase 2 may not run without approved research.")
    else:
        meta, body = parse_frontmatter(research.read_text(encoding="utf-8"))
        if not meta:
            add("research.md has no frontmatter (expected type/plan/status/confidence/date).")
        elif meta.get("status") not in ("draft", "approved"):
            add(f"research.md status is {meta.get('status')!r}; expected draft or approved.")
        elif meta.get("status") == "draft" and tasks:
            add("research.md is still draft, but tasks already exist -- the Phase 1 gate was skipped.")
        reqs = REQ_RE.findall(section(body, "5. Decision & Requirements"))
        if not reqs and tasks:
            add("research.md section 5 declares no REQ-NNN ids, so nothing can be traced.")
        hit = find_placeholder(body)
        if hit:
            add(f"research.md: template placeholder left unfilled ({hit!r})")

    if not plan_md.exists():
        add("plan.md is missing.")
    else:
        _, plan_body = parse_frontmatter(plan_md.read_text(encoding="utf-8"))
        hit = find_placeholder(strip_generated(plan_body))
        if hit:
            add(f"plan.md: template placeholder left unfilled ({hit!r})")
        if BEGIN not in plan_body:
            add("plan.md: section 7 has no BEGIN/END GENERATED markers -- counts cannot be synced")
    if not tasks:
        add(f"no task files found in {tasks_dir}")
        return problems

    names = resolver(tasks)

    # --- per-task shape
    for t in tasks:
        where = t.path.name
        if not TASK_FILE_RE.match(t.name):
            add(f"{where}: filename must be task_NNN_<kebab-slug>.md")
        if not t.meta:
            add(f"{where}: no frontmatter -- status cannot be read")
            continue
        if t.status not in STATUSES:
            add(f"{where}: status {t.status!r} is not one of {'/'.join(STATUSES)}")
        if not t.deliverable:
            add(f"{where}: no `> deliverable` line under the H1 -- the index has nothing to show")
        if not t.satisfies:
            add(f"{where}: satisfies is empty -- a task tracing to no REQ is scope creep")
        for req in t.satisfies:
            if reqs and req not in reqs:
                add(f"{where}: satisfies {req}, which research.md section 5 does not define")
        for dep in t.depends_on:
            if dep not in names:
                add(f"{where}: depends_on {dep}, which does not exist")
        if not t.acceptance.strip():
            add(f"{where}: Acceptance / Verification is empty")
        elif "`" not in t.acceptance:
            add(f"{where}: Acceptance / Verification names no command or observable in backticks")
        hit = find_placeholder(strip_progress_log(t.body))
        if hit:
            add(f"{where}: template placeholder left unfilled ({hit!r})")

        # --- delegation is symmetric: the status and the folder must agree
        folder = t.path.with_suffix("")
        if t.status == "delegated":
            if not t.sub_plan:
                add(f"{where}: status is delegated but sub_plan is null")
            if not folder.is_dir():
                add(f"{where}: status is delegated but {folder.name}/ does not exist")
            elif (folder / "tasks").is_dir():
                for nested in (folder / "tasks").glob("task_*"):
                    if nested.is_dir():
                        add(f"{where}: sub-plan nests another sub-plan ({nested.name}) -- depth is capped at one")
        elif folder.is_dir():
            add(f"{where}: a sub-plan folder exists but the task's status is {t.status!r}, not delegated")

    # --- dependency graph
    graph = {t.name: [names[d] for d in t.depends_on if d in names] for t in tasks}
    for cycle in find_cycles(graph):
        add("dependency cycle: " + " -> ".join(cycle))

    by_name = {t.name: t for t in tasks}
    for t in tasks:
        if t.status != "done":
            continue
        for dep in t.depends_on:
            other = by_name.get(names.get(dep, dep))
            if other and other.status != "done":
                add(f"{t.path.name}: is done, but its dependency {dep} is {other.status!r}")

    # --- requirement coverage
    covered = {req for t in tasks for req in t.satisfies}
    for req in reqs:
        if req not in covered:
            add(f"{req} is defined in research.md but no task satisfies it")

    return problems


def find_cycles(graph: dict[str, list[str]]) -> list[list[str]]:
    """Every cycle reachable in the dependency graph, reported once each."""
    cycles: list[list[str]] = []
    seen_signatures: set[frozenset] = set()
    state: dict[str, int] = {}
    stack: list[str] = []

    def walk(node: str) -> None:
        state[node] = 1
        stack.append(node)
        for nxt in graph.get(node, []):
            if state.get(nxt) == 1:
                cycle = stack[stack.index(nxt) :] + [nxt]
                signature = frozenset(cycle)
                if signature not in seen_signatures:
                    seen_signatures.add(signature)
                    cycles.append(cycle)
            elif state.get(nxt, 0) == 0:
                walk(nxt)
        stack.pop()
        state[node] = 2

    for node in graph:
        if state.get(node, 0) == 0:
            walk(node)
    return cycles


# --------------------------------------------------------------------------- generation


def counts_line(tasks: list[Task]) -> str:
    tally = {s: 0 for s in STATUSES}
    for t in tasks:
        if t.status in tally:
            tally[t.status] += 1
    parts = [f"{tally[s]} {LABEL[s]}" for s in COUNTS_ORDER]
    if tally["dropped"]:
        parts.append(f"{tally['dropped']} Dropped")
    return "**Counts:** " + " / ".join(parts)


def render_index(plan_dir: Path, tasks: list[Task]) -> str:
    today = _dt.date.today().isoformat()
    out = [counts_line(tasks), f"**Updated:** {today}", ""]
    for status in GROUP_ORDER:
        group = [t for t in tasks if t.status == status]
        out.append(f"## {LABEL[status]}")
        if not group:
            out += ["_(none)_", ""]
            continue
        out += ["| Task | Deliverable | M | Depends on |", "|---|---|---|---|"]
        for t in group:
            deps = ", ".join(t.depends_on) if t.depends_on else "—"
            milestone = t.milestone or "—"
            deliverable = (t.deliverable or "—").replace("|", "\\|")
            out.append(f"| {t.name} | {deliverable} | {milestone} | {deps} |")
        out.append("")
    return "\n".join(out).rstrip() + "\n"


def replace_block(text: str, payload: str) -> str | None:
    """Swap what sits between the BEGIN/END markers. None when the markers are absent."""
    start = text.find(BEGIN)
    if start == -1:
        return None
    open_end = text.find("-->", start)
    if open_end == -1:
        return None
    stop = text.find(END, open_end)
    if stop == -1:
        return None
    return text[: open_end + 3] + "\n" + payload + text[stop:]


def sync(plan_dir: Path, tasks: list[Task]) -> list[str]:
    notes: list[str] = []
    index_path = plan_dir / "tasks" / "_index.md"
    plan_path = plan_dir / "plan.md"
    plan_name = plan_dir.name

    payload = render_index(plan_dir, tasks)
    if index_path.exists():
        text = index_path.read_text(encoding="utf-8")
        updated = replace_block(text, payload)
        if updated is None:
            notes.append(f"{index_path.name}: no BEGIN/END GENERATED markers -- rewrote the file")
            updated = new_index(plan_name, payload)
    else:
        updated = new_index(plan_name, payload)
        notes.append(f"{index_path.name}: created")
    index_path.parent.mkdir(parents=True, exist_ok=True)
    index_path.write_text(updated, encoding="utf-8", newline="\n")

    if plan_path.exists():
        text = plan_path.read_text(encoding="utf-8")
        updated = replace_block(text, counts_line(tasks) + "\n")
        if updated is None:
            notes.append("plan.md: no BEGIN/END GENERATED markers in section 7 -- counts not written")
        else:
            plan_path.write_text(updated, encoding="utf-8", newline="\n")
    return notes


def new_index(plan_name: str, payload: str) -> str:
    return (
        "---\n"
        "type: task-index\n"
        f"plan: {plan_name}\n"
        "---\n\n"
        f"# Task Index — {plan_name}\n\n"
        "> Generated from the task files. Do not edit by hand — set `status:` in a task's\n"
        "> frontmatter, then run `python scripts/validate_plan.py <plan-dir> --sync`.\n\n"
        f"{BEGIN} -->\n{payload}{END}\n"
    )


# --------------------------------------------------------------------------- cli


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("plan_dir", type=Path, help="plans/plan-<name>/")
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--check", action="store_true", help="read-only (default)")
    mode.add_argument("--sync", action="store_true", help="regenerate the derived blocks, then check")
    args = parser.parse_args(argv)

    plan_dir: Path = args.plan_dir
    if not plan_dir.is_dir():
        print(f"not a directory: {plan_dir}", file=sys.stderr)
        return 2

    tasks = load_tasks(plan_dir / "tasks")

    if args.sync:
        for note in sync(plan_dir, tasks):
            print(f"sync: {note}")
        print(f"sync: {len(tasks)} task(s) -> tasks/_index.md, plan.md section 7")

    problems = check(plan_dir, tasks)
    if problems:
        print(f"\n{len(problems)} problem(s) in {plan_dir}:")
        for p in problems:
            print(f"  - {p}")
        return 1

    print(f"OK: {plan_dir} is consistent ({len(tasks)} task(s)) -- {counts_line(tasks)[12:]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
