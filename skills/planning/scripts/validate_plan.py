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
`plan.md` section 6's "Delivered by" column is never touched either -- it is checked for drift
against task frontmatter (`--check` catches a stale value) but stays hand-maintained, since its
neighboring "Accepted" column is evidence-driven and would be at risk of being clobbered by an
automatic rewrite.

Standard library only -- no PyYAML -- so the skill stays portable. The frontmatter subset
supported is what the templates use: `key: scalar`, `key: [a, b]`, `key: null`, and `# comments`.

Regex is used only as an exact-format parser -- task filename numbering, REQ-id extraction,
section-body isolation by heading. It is never used to judge whether prose content (Instructions,
Acceptance wording) is finished or well-formed; that judgment is a human/reviewer responsibility.
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

TASK_FILE_RE = re.compile(r"^task_(\d{3})_[a-z0-9][a-z0-9-]*$")
REQ_RE = re.compile(r"\*\*(REQ-[0-9]+(?:\.[0-9]+)?)\*\*")
REQ_ID_RE = re.compile(r"^REQ-[0-9]+(?:\.[0-9]+)?$")


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


def extract_block(text: str) -> str | None:
    """The payload currently sitting between a document's BEGIN/END GENERATED markers.

    None when the markers are absent, so a caller can tell "out of sync" apart from "not
    generated at all".
    """
    start = text.find(BEGIN)
    if start == -1:
        return None
    open_end = text.find("-->", start)
    if open_end == -1:
        return None
    stop = text.find(END, open_end)
    if stop == -1:
        return None
    return text[open_end + 3 : stop]


def _drift_comparable(payload: str) -> str:
    """Strip the one line expected to change every day regardless of real content."""
    lines = [ln for ln in payload.split("\n") if not ln.startswith("**Updated:**")]
    return "\n".join(lines).strip("\n")


def parse_req_table(table_body: str) -> dict[str, list[str]]:
    """Parse a `| REQ | Delivered by | Accepted |` markdown table into {req: [task names]}.

    Header and separator rows are skipped because their first cell never matches `REQ-NNN`.
    """
    result: dict[str, list[str]] = {}
    for line in table_body.split("\n"):
        line = line.strip()
        if not line.startswith("|"):
            continue
        cells = [c.strip() for c in line.strip("|").split("|")]
        if len(cells) < 2 or not REQ_ID_RE.match(cells[0]):
            continue
        result[cells[0]] = [d.strip() for d in cells[1].split(",") if d.strip()]
    return result


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


# --------------------------------------------------------------------------- PlanIndex


class PlanIndex:
    """Owns parsing a plan folder, its deterministic structural checks, and keeping
    `tasks/_index.md` / `plan.md` section 7 in sync with task frontmatter.

    No method here judges prose *content* (is this Instructions line finished, is this Acceptance
    criterion well-worded) -- only exact, deterministic facts: does a referenced task/REQ exist,
    is the dependency graph acyclic, is a section empty, does a generated block match what it
    should generate. That boundary is deliberate (see the module docstring).
    """

    def __init__(self, plan_dir: Path):
        self.plan_dir = plan_dir
        self.tasks = load_tasks(plan_dir / "tasks")
        self.research_path = plan_dir / "research.md"
        if self.research_path.exists():
            self.research_meta, self.research_body = parse_frontmatter(
                self.research_path.read_text(encoding="utf-8")
            )
        else:
            self.research_meta, self.research_body = {}, ""
        self.research_reqs = REQ_RE.findall(section(self.research_body, "5. Decision & Requirements"))

    # --- checks

    def check(self) -> list[str]:
        problems: list[str] = []
        add = problems.append

        plan_md = self.plan_dir / "plan.md"

        if not self.research_path.exists():
            add("research.md is missing -- Phase 2 may not run without approved research.")
        else:
            meta = self.research_meta
            if not meta:
                add("research.md has no frontmatter (expected type/plan/status/confidence/date).")
            elif meta.get("status") not in ("draft", "approved"):
                add(f"research.md status is {meta.get('status')!r}; expected draft or approved.")
            elif meta.get("status") == "draft" and self.tasks:
                add("research.md is still draft, but tasks already exist -- the Phase 1 gate was skipped.")
            if not self.research_reqs and self.tasks:
                add("research.md section 5 declares no REQ-NNN ids, so nothing can be traced.")

        if not plan_md.exists():
            add("plan.md is missing.")
        else:
            _, plan_body = parse_frontmatter(plan_md.read_text(encoding="utf-8"))
            if BEGIN not in plan_body:
                add("plan.md: section 7 has no BEGIN/END GENERATED markers -- counts cannot be synced")

        if not self.tasks:
            add(f"no task files found in {self.plan_dir / 'tasks'}")
            return problems

        problems.extend(self._check_tasks())
        problems.extend(self._check_index_drift())
        problems.extend(self._check_req008_drift())
        return problems

    def _check_tasks(self) -> list[str]:
        problems: list[str] = []
        add = problems.append
        tasks = self.tasks
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
                if self.research_reqs and req not in self.research_reqs:
                    add(f"{where}: satisfies {req}, which research.md section 5 does not define")
            for dep in t.depends_on:
                if dep not in names:
                    add(f"{where}: depends_on {dep}, which does not exist")
            if not t.acceptance.strip():
                add(f"{where}: Acceptance / Verification is empty")

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
        for req in self.research_reqs:
            if req not in covered:
                add(f"{req} is defined in research.md but no task satisfies it")

        return problems

    def _check_index_drift(self) -> list[str]:
        """WHEN the generated blocks don't match what current task frontmatter produces."""
        problems: list[str] = []
        index_path = self.plan_dir / "tasks" / "_index.md"
        fresh_index = _drift_comparable(render_index(self.plan_dir, self.tasks))
        if not index_path.exists():
            problems.append("tasks/_index.md is missing -- out of sync, run --sync")
        else:
            current = extract_block(index_path.read_text(encoding="utf-8"))
            if current is None:
                problems.append("tasks/_index.md: no BEGIN/END GENERATED markers -- cannot verify sync")
            elif _drift_comparable(current) != fresh_index:
                problems.append("tasks/_index.md is out of sync with task frontmatter -- run --sync")

        plan_path = self.plan_dir / "plan.md"
        if plan_path.exists():
            fresh_counts = counts_line(self.tasks)
            current = extract_block(plan_path.read_text(encoding="utf-8"))
            if current is not None and current.strip("\n") != fresh_counts:
                problems.append("plan.md section 7 counts are out of sync with task frontmatter -- run --sync")
        return problems

    def _check_req008_drift(self) -> list[str]:
        """WHEN plan.md section 6's "Delivered by" column no longer matches `satisfies`.

        Never writes section 6 -- its "Accepted" column is evidence-driven (Phase 5) and sits in
        the same row, so this only reports the mismatch.
        """
        problems: list[str] = []
        plan_path = self.plan_dir / "plan.md"
        if not plan_path.exists():
            return problems
        _, plan_body = parse_frontmatter(plan_path.read_text(encoding="utf-8"))
        table = parse_req_table(section(plan_body, "6. Requirements Traceability"))
        names = resolver(self.tasks)

        fresh: dict[str, list[str]] = {}
        for t in self.tasks:
            for req in t.satisfies:
                fresh.setdefault(req, []).append(t.name)

        for req, fresh_names in fresh.items():
            fresh_sorted = sorted(set(fresh_names))
            table_raw = table.get(req, [])
            # Table rows use either short (`task_001`) or full form -- resolve both to the full
            # stem before comparing, the same way `depends_on` edges already are. Both sides go
            # through a set first so a duplicate REQ in one task's own `satisfies` can't produce
            # a spurious mismatch against a table that lists the task once.
            table_resolved = sorted({names.get(n, n) for n in table_raw})
            if table_resolved != fresh_sorted:
                table_repr = ", ".join(table_raw) if table_raw else "(missing from table)"
                problems.append(
                    f"plan.md section 6: {req} 'Delivered by' lists {table_repr}, but task "
                    f"frontmatter says {', '.join(fresh_sorted)}"
                )
        return problems

    # --- generation

    def sync(self) -> list[str]:
        notes: list[str] = []
        index_path = self.plan_dir / "tasks" / "_index.md"
        plan_path = self.plan_dir / "plan.md"
        plan_name = self.plan_dir.name

        payload = render_index(self.plan_dir, self.tasks)
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
            updated = replace_block(text, counts_line(self.tasks) + "\n")
            if updated is None:
                notes.append("plan.md: no BEGIN/END GENERATED markers in section 7 -- counts not written")
            else:
                plan_path.write_text(updated, encoding="utf-8", newline="\n")
        return notes


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

    idx = PlanIndex(plan_dir)

    if args.sync:
        for note in idx.sync():
            print(f"sync: {note}")
        print(f"sync: {len(idx.tasks)} task(s) -> tasks/_index.md, plan.md section 7")

    problems = idx.check()
    if problems:
        print(f"\n{len(problems)} problem(s) in {plan_dir}:")
        for p in problems:
            print(f"  - {p}")
        return 1

    print(f"OK: {plan_dir} is consistent ({len(idx.tasks)} task(s)) -- {counts_line(idx.tasks)[12:]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
