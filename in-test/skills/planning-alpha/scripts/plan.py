#!/usr/bin/env python3
"""Create, inspect and check a plan folder, and every plan nested inside its tasks.

The skill's only executable. Subcommands:

    plan.py new <name> [--root plans] [--in <task-dir>]   scaffold policy.md + research.md
    plan.py plan <plan-dir>                                scaffold plan.md
    plan.py task <plan-dir> <slug> [--row task_NNN]        scaffold tasks/task_NNN_<slug>/task.md
    plan.py split <plan-dir> <task> <slug=REQ,..> ...      one task -> several sibling tasks
    plan.py drop <plan-dir> <task>                         mark a task (or its row) dropped
    plan.py ready <plan-dir>                               what can run now, across the tree
    plan.py handoff <plan-dir> <task>                      print what an executing agent is given
    plan.py accept <plan-dir> [scope]                      scaffold acceptance-<scope>.md
    plan.py status <plan-dir>                              where work continues, as the header
    plan.py sync <plan-dir>                                regenerate the derived blocks
    plan.py check <plan-dir>                               read-only; exit 1 if anything is wrong

A plan is a folder: policy.md, research.md, plan.md, tasks/. Every task is a folder holding
task.md. A task may also hold a plan of its own, `plan-NNN-<slug>/`, which is an ordinary plan:
everything here applies to it unchanged, and the task depends on it.

`status` and `ready` exist so state is computed, not recited. `check` makes the gates
enforceable: a task cannot be `done` without a filled `- Verified:` line, and, when the route
says so, a filled `- Review:` line.

Hand-written state lives only in each task's own folder; `tasks/_index.md` and the counts in
plan.md section 4 are generated from task frontmatter. So two tasks worked on at the same time
never write the same file by hand.

Standard library only. The frontmatter subset understood is what the templates use:
`key: scalar`, `key: [a, b]`, `key: null` and trailing `# comments`.
"""

from __future__ import annotations

import argparse
import datetime as _dt
import re
import sys
from pathlib import Path

# --------------------------------------------------------------------------- constants

STEPS = ["research", "plan", "tasks"]
REVIEWS = ["required", "on-request", "none"]

STATUSES = ["not-started", "in-progress", "blocked", "done", "dropped"]
# A dropped task is finished: the plan decided it is not needed, so a task that depends on it
# may be done while it is dropped.
FINISHED = {"done", "dropped"}
GROUP_ORDER = ["done", "in-progress", "not-started", "blocked", "dropped"]
COUNTS_ORDER = ["done", "in-progress", "not-started", "blocked"]
LABEL = {
    "not-started": "Not Started",
    "in-progress": "In Progress",
    "blocked": "Blocked",
    "done": "Done",
    "dropped": "Dropped",
}

CONFIDENCE = ["High", "Medium", "Low"]

# policy.md is scaffolded before the route is settled; `decided:` holds this until Gate A.
PENDING = "pending"

VERDICTS = ["ACCEPTED", "ACCEPTED WITH CONDITIONS", "NOT ACCEPTED"]
ACCEPT_GLOB = "acceptance-*.md"
ACCEPT_SECTION = "1. Requirements in scope"
ACCEPT_SCOPE_RE = re.compile(r"^(all|task_\d{3}(-task_\d{3})?)$")

# Phrases that point at a conversation the executing agent never had. Kept short and
# unambiguous: a check that fires on innocent prose gets ignored. English only — a task file
# written in another language passes this smoke test unchecked; the readiness row
# "Cold-readable" is the judgement that covers it.
COLD_READ_SMELLS = [
    "as we discussed",
    "as discussed",
    "as agreed",
    "as mentioned earlier",
    "mentioned above",
    "see above",
    "per our conversation",
    "the approach we chose",
    "like last time",
    "same as before",
]

BEGIN = "<!-- BEGIN GENERATED"
END = "<!-- END GENERATED -->"

# Headings and names read by code. Renaming one silently empties a check, so each is named
# once here and its absence is reported loudly.
REQ_SECTION = "5. Decision & Requirements"
TASK_LIST_SECTION = "3. Task List"
CONSTRAINTS_SECTION = "2. Global Constraints"
REVISION_SECTION = "5. Revision Log"
TASK_FILE = "task.md"
ROUTE_REASON = "**Why this route:**"

TASK_DIR_RE = re.compile(r"^task_(\d{3})_[a-z0-9][a-z0-9-]*$")
TASK_ID_RE = re.compile(r"^task_\d{3}$")
NESTED_RE = re.compile(r"^plan-(\d{3})-[a-z0-9][a-z0-9-]*$")
REQ_RE = re.compile(r"\*\*(REQ-[0-9]+)\*\*")
PLACEHOLDER = "{{"  # an unfilled template slot; an approved document carries none
REQ_ID_RE = re.compile(r"^REQ-[0-9]+$")
SLUG_RE = re.compile(r"^[a-z0-9][a-z0-9-]*$")
STRIKE = "~~"  # a struck-through row id in plan.md section 3 marks the row dropped
DEPTH_WARN = 3  # nested plans deeper than this get a warning, never a failure

ASSETS = Path(__file__).resolve().parent.parent / "assets"


# --------------------------------------------------------------------------- parsing


def parse_frontmatter(text: str) -> tuple[dict, str]:
    """Split a document into its frontmatter mapping and its body.

    Returns ({}, text) when there is no frontmatter, so a caller reports that as a finding
    instead of crashing on it.
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
        line = _strip_comment(line)
        if not line.strip() or ":" not in line:
            continue
        key, _, value = line.partition(":")
        data[key.strip()] = _coerce(value.strip())
    return data, body


def _strip_comment(line: str) -> str:
    """Drop a trailing ` # comment`, which the templates use to list a field's allowed values.

    A quoted value keeps its `#`, because there it is data: cutting at it would truncate the
    value silently instead of reporting anything.
    """
    key, sep, value = line.partition(":")
    if not sep or value.strip()[:1] in ("'", '"'):
        return line.rstrip()
    return (key + sep + value.split(" #", 1)[0]).rstrip()


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


def _as_list(value) -> list[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    return [v.strip() for v in str(value).split(",") if v.strip()]


def _filled(text: str) -> bool:
    """WHEN a log value says something: not empty, not a bare label, not a template slot.

    `[hint]` and `{{slot}}` are what the templates ship, and `Run:` alone is a label with
    nothing after it. Each would let an empty entry open the gate it is meant to hold.
    """
    text = text.strip()
    if not text or text.startswith("[") or PLACEHOLDER in text:
        return False
    return not re.fullmatch(r"[\w-]+:", text)


def placeholder_lines(body: str) -> list[int]:
    """1-based line numbers of the body that still hold a `{{slot}}`."""
    return [i for i, ln in enumerate(body.split("\n"), 1) if PLACEHOLDER in ln]


def purpose_line(body: str) -> str:
    """The blockquote right under the H1 — the deliverable, as the index shows it."""
    lines: list[str] = []
    seen_h1 = False
    for line in body.split("\n"):
        if line.startswith("# "):
            seen_h1 = True
            continue
        if not seen_h1:
            continue
        if line.startswith(">"):
            lines.append(line.lstrip("> ").strip())
        elif lines or line.strip():
            break
    return " ".join(lines).strip()


def section(body: str, heading: str) -> str:
    """The text under a `## heading`, up to the next `## `."""
    pattern = re.compile(r"^##\s+" + re.escape(heading) + r"\s*$(.*?)(?=^##\s|\Z)", re.M | re.S)
    match = pattern.search(body)
    return match.group(1) if match else ""


def table_rows(body: str) -> list[list[str]]:
    """Every markdown table row under a section, as lists of stripped cells.

    Header and separator rows come back too; callers discard them by testing the first cell,
    which is cheaper than trying to detect a header reliably.
    """
    rows: list[list[str]] = []
    for line in body.split("\n"):
        line = line.strip()
        if not line.startswith("|"):
            continue
        rows.append([c.strip() for c in line.strip("|").split("|")])
    return rows


def extract_block(text: str) -> str | None:
    """What currently sits between the BEGIN/END GENERATED markers, or None if absent."""
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


def replace_block(text: str, payload: str) -> str | None:
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


def find_cycles(graph: dict[str, list[str]]) -> list[list[str]]:
    """Every cycle reachable in the dependency graph, reported once each."""
    cycles: list[list[str]] = []
    seen: set[frozenset] = set()
    state: dict[str, int] = {}
    stack: list[str] = []

    def walk(node: str) -> None:
        state[node] = 1
        stack.append(node)
        for nxt in graph.get(node, []):
            if state.get(nxt) == 1:
                cycle = stack[stack.index(nxt) :] + [nxt]
                if frozenset(cycle) not in seen:
                    seen.add(frozenset(cycle))
                    cycles.append(cycle)
            elif state.get(nxt, 0) == 0:
                walk(nxt)
        stack.pop()
        state[node] = 2

    for node in graph:
        if state.get(node, 0) == 0:
            walk(node)
    return cycles


def set_field(text: str, key: str, value: str) -> str:
    """Replace `key:` in a document's frontmatter, keeping its trailing `# comment`.

    Raises when the key is absent: a silent no-op would leave the file claiming the old value.
    """
    end = text.find("\n---", 3)
    if not text.startswith("---") or end == -1:
        raise ValueError(f"no frontmatter to set {key!r} in")
    head, rest = text[:end], text[end:]
    pattern = re.compile(rf"^({re.escape(key)}:)([^\n#]*)(\s+#[^\n]*)?$", re.M)
    if not pattern.search(head):
        raise ValueError(f"frontmatter has no {key!r} field")
    head = pattern.sub(lambda m: f"{m.group(1)} {value}" + (m.group(3) or ""), head, count=1)
    return head + rest


def append_revision(path: Path, change: str, why: str) -> bool:
    """Add a row to the Revision Log table of plan.md. False when the section is missing."""
    lines = path.read_text(encoding="utf-8").split("\n")
    try:
        start = next(i for i, ln in enumerate(lines) if re.match(r"^##\s+" + re.escape(REVISION_SECTION) + r"\s*$", ln))
    except StopIteration:
        return False
    stop = next((i for i in range(start + 1, len(lines)) if lines[i].startswith("## ")), len(lines))
    last = max((i for i in range(start, stop) if lines[i].strip().startswith("|")), default=None)
    if last is None:
        return False
    lines.insert(last + 1, f"| {_dt.date.today().isoformat()} | {change} | {why} |")
    _write(path, "\n".join(lines))
    return True


# --------------------------------------------------------------------------- model


class Task:
    """One task folder: `tasks/task_NNN_<slug>/task.md`, and any plan nested beside it."""

    def __init__(self, folder: Path):
        self.dir = folder
        self.path = folder / TASK_FILE
        self.name = folder.name
        m = TASK_DIR_RE.match(self.name)
        self.number = int(m.group(1)) if m else None
        self.short = f"task_{m.group(1)}" if m else self.name
        text = self.path.read_text(encoding="utf-8") if self.path.is_file() else ""
        self.meta, self.body = parse_frontmatter(text)
        self.status = self.meta.get("status")
        self.satisfies = _as_list(self.meta.get("satisfies"))
        self.depends_on = _as_list(self.meta.get("depends_on"))
        self.task_deps = [d for d in self.depends_on if not d.startswith("plan-")]
        self.plan_deps = [d for d in self.depends_on if d.startswith("plan-")]
        self.deliverable = purpose_line(self.body)
        self.acceptance = section(self.body, "Acceptance / Verification")
        self.progress = section(self.body, "Progress Log")
        self.files = self._files()
        self.nested = sorted(d for d in folder.iterdir() if d.is_dir() and d.name.startswith("plan-"))

    def _files(self) -> list[tuple[str, str]]:
        """(action, repo-relative path) for every readable row of the Files table.

        A cell that is not plainly a path is skipped rather than guessed at: a placeholder, a
        prose phrase, an absolute path or a URL.
        """
        out: list[tuple[str, str]] = []
        for row in table_rows(section(self.body, "Files")):
            if len(row) < 2:
                continue
            action = row[0].strip("* ").lower()
            if action not in ("create", "modify", "delete", "touch"):
                continue
            cell = row[1].strip().strip("`").split("#", 1)[0].strip()
            cell = cell.split(":", 1)[0].strip()  # drop `:38-52` and `:build_parser()`
            if not cell or PLACEHOLDER in cell or " " in cell or cell.startswith(("/", "~", "http")):
                continue
            if "/" not in cell and "." not in cell:
                continue
            out.append((action, cell))
        return out

    def file_set(self) -> set[str]:
        return {Path(rel).as_posix().lower() for _, rel in self.files}

    def leans_on_the_conversation(self) -> list[str]:
        """A smoke test: phrases pointing at a conversation the reader never had."""
        lowered = self.body.lower()
        return [p for p in COLD_READ_SMELLS if p in lowered]

    def has_filled_line(self, prefix: str) -> bool:
        """WHEN the Progress Log carries a `- <prefix>:` entry that actually says something.

        Text must follow on the same line or on a line indented under it; the bare label does
        not open the gate.
        """
        needle = f"- {prefix}:"
        lines = self.progress.split("\n")
        for i, line in enumerate(lines):
            stripped = line.strip()
            if not stripped.startswith(needle):
                continue
            if _filled(stripped[len(needle):]):
                return True
            indent = len(line) - len(line.lstrip())
            for nxt in lines[i + 1 :]:
                if not nxt.strip() or len(nxt) - len(nxt.lstrip()) <= indent:
                    break
                if _filled(nxt.strip().lstrip("-").strip()):
                    return True
        return False


class Row:
    """One row of plan.md section 3. The task folder may not exist yet."""

    def __init__(self, cells: list[str]):
        raw = cells[0].strip()
        self.dropped = raw.startswith(STRIKE)
        self.id = raw.strip("~ ").strip()
        self.title = cells[1].strip()
        self.satisfies = [c.strip() for c in cells[2].split(",") if REQ_ID_RE.match(c.strip())]
        self.depends_on = [c.strip() for c in cells[3].split(",") if TASK_ID_RE.match(c.strip())]


def load_tasks(tasks_dir: Path) -> list[Task]:
    if not tasks_dir.is_dir():
        return []
    return [Task(p) for p in sorted(tasks_dir.iterdir()) if p.is_dir() and p.name.startswith("task_")]


def parse_rows(plan_body: str) -> list[Row]:
    out: list[Row] = []
    for cells in table_rows(section(plan_body, TASK_LIST_SECTION)):
        if len(cells) < 4 or any(PLACEHOLDER in c for c in cells):
            continue
        row = Row(cells)
        if TASK_ID_RE.match(row.id):
            out.append(row)
    return out


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


def render_index(tasks: list[Task]) -> str:
    out = [counts_line(tasks), f"**Updated:** {_dt.date.today().isoformat()}", ""]
    for status in GROUP_ORDER:
        group = [t for t in tasks if t.status == status]
        out.append(f"## {LABEL[status]}")
        if not group:
            out += ["_(none)_", ""]
            continue
        out += ["| Task | Deliverable | Satisfies | Depends on |", "|---|---|---|---|"]
        for t in group:
            deps = ", ".join(t.depends_on) if t.depends_on else "—"
            sat = ", ".join(t.satisfies) if t.satisfies else "—"
            deliverable = (t.deliverable or "—").replace("|", "\\|")
            out.append(f"| {t.name} | {deliverable} | {sat} | {deps} |")
        out.append("")
    return "\n".join(out).rstrip() + "\n"


def new_index(plan_name: str, payload: str) -> str:
    return (
        "---\n"
        "type: task-index\n"
        f"plan: {plan_name}\n"
        "---\n\n"
        f"# Task Index — {plan_name}\n\n"
        "> Generated from the task files. Never edited by hand — set `status:` in a task's\n"
        "> frontmatter, then run `plan.py sync`.\n\n"
        f"{BEGIN} -->\n{payload}{END}\n"
    )


def _drift_comparable(payload: str) -> str:
    """Drop the one line that changes every day regardless of content."""
    return "\n".join(ln for ln in payload.split("\n") if not ln.startswith("**Updated:**")).strip("\n")


# --------------------------------------------------------------------------- the plan


class Plan:
    """One plan folder: its route, its artifacts, its tasks, and the plans nested in them."""

    def __init__(self, plan_dir: Path):
        self.dir = plan_dir
        self.name = plan_dir.name
        # Depth is read from the path, so a plan checked on its own still knows how deep it is.
        self.depth = sum(1 for part in plan_dir.resolve().parts if NESTED_RE.match(part))

        self.policy_path = plan_dir / "policy.md"
        self.policy_meta, self.policy_body = self._read(self.policy_path)
        self.steps = _as_list(self.policy_meta.get("steps")) or list(STEPS)
        self.review = self.policy_meta.get("review") or "required"

        self.research_path = plan_dir / "research.md"
        self.research_meta, self.research_body = self._read(self.research_path)
        self.req_section = section(self.research_body, REQ_SECTION)
        # A line still holding a `{{slot}}` is the template's example, not a requirement.
        self.reqs = [req for ln in self.req_section.split("\n") if PLACEHOLDER not in ln for req in REQ_RE.findall(ln)]

        self.plan_path = plan_dir / "plan.md"
        self.plan_meta, self.plan_body = self._read(self.plan_path)
        self.rows = parse_rows(self.plan_body) if self.plan_path.exists() else []

        self.tasks = load_tasks(plan_dir / "tasks")
        self.by_short = {t.short: t for t in self.tasks}

    @staticmethod
    def _read(path: Path) -> tuple[dict, str]:
        if not path.exists():
            return {}, ""
        return parse_frontmatter(path.read_text(encoding="utf-8"))

    # --- lookups

    @property
    def research_approved(self) -> bool:
        return self.research_meta.get("status") == "approved"

    @property
    def plan_approved(self) -> bool:
        return self.plan_meta.get("status") == "approved"

    def task(self, ref: str) -> Task | None:
        return self.by_short.get(ref) or next((t for t in self.tasks if t.name == ref), None)

    def row(self, ref: str) -> Row | None:
        short = "_".join(ref.split("_")[:2])
        return next((r for r in self.rows if r.id == short), None)

    def unwritten(self) -> list[Row]:
        return [r for r in self.rows if not r.dropped and r.id not in self.by_short]

    def ordered(self, tasks: list[Task]) -> list[Task]:
        """Tasks in the order of plan.md section 3, then any task with no row."""
        rank = {r.id: i for i, r in enumerate(self.rows)}
        return sorted(tasks, key=lambda t: (rank.get(t.short, len(rank)), t.name))

    def used_numbers(self) -> set[int]:
        nums = {t.number for t in self.tasks if t.number is not None}
        return nums | {int(r.id[5:]) for r in self.rows}

    def listed_satisfies(self) -> set[str]:
        return {req for r in self.rows if not r.dropped for req in r.satisfies}

    def nested_plan(self, task: Task, ref: str) -> Plan | None:
        path = task.dir / ref
        return Plan(path) if path.is_dir() else None

    def dep_state(self, task: Task, dep: str) -> str | None:
        """None when the dependency is finished, otherwise what it is waiting on."""
        if dep.startswith("plan-"):
            sub = self.nested_plan(task, dep)
            if sub is None:
                return f"{dep} (missing)"
            step, _ = sub.where()
            return None if step == "done" else f"{dep} ({step})"
        other = self.task(dep)
        if other is None:
            row = self.row(dep)
            return None if row and row.dropped else f"{dep} (not written)"
        return None if other.status in FINISHED else f"{dep} ({other.status})"

    def blockers(self, task: Task) -> list[str]:
        return [s for d in task.depends_on if (s := self.dep_state(task, d))]

    # --- where work continues

    def _where(self) -> tuple[str, str, tuple[Task, Plan] | None]:
        if not self.policy_path.exists():
            return "research", "no policy.md: research starts and the route is proposed at Gate A", None
        if not self.research_path.exists():
            return "research", "research.md does not exist yet", None
        if not self.research_approved:
            return "research", "research.md is draft: finish it, disclose, and put Gate A to the user", None
        if "plan" in self.steps and not self.plan_path.exists():
            return "plan", "research is approved and the route asks for plan.md, which does not exist yet", None
        if "plan" in self.steps and not self.plan_approved:
            return "plan", "plan.md is draft: finish the task list and put the gate to the user", None
        if "tasks" not in self.steps:
            return "done", "the route ends here and every step it names is complete", None

        unfinished = self.ordered([t for t in self.tasks if t.status not in FINISHED])
        unwritten = self.unwritten()
        if not unfinished and not unwritten:
            if not self.tasks:
                return "tasks", "no task is written yet: elaborate the first one", None
            return "done", "every task is finished — `accept` is available and is not required", None
        for t in unfinished:
            if t.status == "in-progress":
                return "tasks", f"{t.short} is in progress", None
        for t in unfinished:
            if t.status == "not-started" and not self.blockers(t):
                return "tasks", f"{t.short} is written and ready to run (see `plan.py ready` for all)", None
        for t in unfinished:
            if t.status != "not-started" or any(self.dep_state(t, d) for d in t.task_deps):
                continue
            for d in t.plan_deps:
                if self.dep_state(t, d):
                    sub = self.nested_plan(t, d)
                    if sub is not None:
                        return "nested", f"{t.short} waits on its plan {d}", (t, sub)
        if unwritten:
            return "tasks", f"{unwritten[0].id} is not written yet: elaborate it", None
        waiting = ", ".join(f"{t.short} on {', '.join(self.blockers(t)) or t.status}" for t in unfinished)
        return "tasks", f"nothing can run: {waiting}", None

    def where(self) -> tuple[str, str]:
        step, why, _ = self._where()
        return ("tasks" if step == "nested" else step), why

    def locate(self, trail: list[str] | None = None) -> tuple[list[str], Plan, str, str]:
        """Walk down to the deepest place work continues: (path, plan, step, why)."""
        trail = (trail or []) + [self.name]
        step, why, nested = self._where()
        if nested is not None:
            task, sub = nested
            return sub.locate(trail + [task.short])
        return trail, self, step, why

    def header(self, trail: list[str], step: str, why: str) -> list[str]:
        """The two header lines, ready to copy into a message."""
        first = f"Plan: {' › '.join(trail)} · {step} · {why}"
        if step == "research":
            second = (
                f"Research: {self.research_path.as_posix()} · {self.research_meta.get('status', 'missing')}"
                f" · confidence {self.research_meta.get('confidence', '—')}"
            )
        elif step == "plan":
            second = f"Plan: {self.plan_path.as_posix()} · {self.plan_meta.get('status', 'missing')} · {len(self.rows)} row(s)"
        else:
            total = len([r for r in self.rows if not r.dropped]) or len([t for t in self.tasks if t.status != "dropped"])
            done = len([t for t in self.tasks if t.status == "done"])
            source = self.plan_path if "plan" in self.steps else self.research_path
            second = f"{source.stem.capitalize()}: {source.as_posix()} · approved · {done} of {total} task(s) done"
        return [first, second]

    # --- checks

    def check(self) -> tuple[list[str], list[str]]:
        """(problems, warnings) for this plan and every plan nested in its tasks."""
        problems: list[str] = []
        warnings: list[str] = []
        problems += self._check_policy()
        problems += self._check_research()
        problems += self._check_route_drift()
        problems += self._check_plan()
        if self.tasks or (self.dir / "tasks").is_dir():
            problems += self._check_tasks()
        if self.tasks:
            problems += self._check_generated()
        problems += self._check_coverage()
        problems += self._check_acceptance()
        if self.depth == DEPTH_WARN + 1:
            warnings.append(f"{self.dir.as_posix()}: plans are nested {self.depth} deep — past {DEPTH_WARN}")
        for t in self.tasks:
            for sub_dir in t.nested:
                sub_problems, sub_warnings = Plan(sub_dir).check()
                rel = f"tasks/{t.name}/{sub_dir.name}"
                problems += [f"{rel}/{p}" for p in sub_problems]
                warnings += sub_warnings
        return problems, warnings

    def _check_policy(self) -> list[str]:
        out: list[str] = []
        if not self.policy_path.exists():
            return ["policy.md is missing — the route was never settled with the user"]
        if not self.policy_meta:
            return ["policy.md has no frontmatter (expected type/plan/decided/steps/review)"]
        steps = _as_list(self.policy_meta.get("steps"))
        if not steps:
            out.append("policy.md: steps is empty — a route has at least [research]")
        else:
            unknown = [s for s in steps if s not in STEPS]
            if unknown:
                out.append(f"policy.md: steps has unknown value(s) {', '.join(unknown)}; allowed: {', '.join(STEPS)}")
            elif steps[0] != "research":
                out.append(f"policy.md: steps starts with {steps[0]!r} — every route starts with research")
            elif steps != [s for s in STEPS if s in steps]:
                # A subsequence, not a prefix: `plan` and `tasks` are each optional; only the
                # order is fixed, because a task list cannot precede the plan that holds it.
                out.append(f"policy.md: steps is {steps}; the order is fixed as {STEPS}, though later steps may be left out")
        if self.policy_meta.get("review") not in REVIEWS:
            out.append(f"policy.md: review is {self.policy_meta.get('review')!r}; expected one of {', '.join(REVIEWS)}")
        decided = self.policy_meta.get("decided")
        if self.research_approved and (decided is None or str(decided) == PENDING):
            out.append("policy.md: research.md is approved but `decided:` is still pending — Gate A records the route by date")
        default = self.steps == STEPS and self.review == "required"
        if not default and not self._route_reason():
            out.append("policy.md: the route is weaker than the default but `**Why this route:**` is empty")
        return out

    def _route_reason(self) -> str:
        at = self.policy_body.find(ROUTE_REASON)
        if at == -1:
            return ""
        line = self.policy_body[at + len(ROUTE_REASON) :].split("\n", 1)[0].strip()
        return "" if line.startswith("[") else line

    def _check_research(self) -> list[str]:
        out: list[str] = []
        if not self.research_path.exists():
            return ["research.md is missing — every route starts with research"]
        if not self.research_meta:
            return ["research.md has no frontmatter (expected type/plan/status/confidence/brief/updated)"]
        if self.research_meta.get("status") not in ("draft", "approved"):
            out.append(f"research.md: status is {self.research_meta.get('status')!r}; expected draft or approved")
        if self.research_meta.get("confidence") not in CONFIDENCE:
            out.append(f"research.md: confidence is {self.research_meta.get('confidence')!r}; expected one of {', '.join(CONFIDENCE)}")
        if self.research_approved and self.research_meta.get("confidence") == "Low":
            out.append("research.md is approved with confidence Low — Low means research is not finished")
        if self.research_approved and (left := placeholder_lines(self.research_body)):
            out.append(f"research.md is approved but still holds `{{{{...}}}}` on body line(s) {', '.join(map(str, left[:8]))}")
        brief = self.research_meta.get("brief")
        if brief not in (None, "none") and not (self.dir / str(brief)).is_file():
            out.append(f"research.md: brief is {brief!r}, which does not exist")
        if NESTED_RE.match(self.name) and brief in (None, "none"):
            out.append("research.md: this plan lives in a task folder but has no `brief: ../task.md`")
        if not self.research_approved and (self.plan_path.exists() or self.tasks):
            out.append("research.md is still draft, but plan.md or task folders already exist — Gate A was skipped")
        if (self.plan_path.exists() or self.tasks) and not self.req_section.strip():
            out.append(f"research.md has no section {REQ_SECTION!r} — the heading was renamed, so coverage is silently empty")
        elif (self.plan_path.exists() or self.tasks) and not self.reqs:
            out.append(f"research.md section {REQ_SECTION!r} declares no **REQ-NNN** id, so nothing can be traced")
        return out

    def _check_route_drift(self) -> list[str]:
        out: list[str] = []
        if not self.policy_path.exists():
            return out
        if self.plan_path.exists() and "plan" not in self.steps:
            out.append("plan.md exists but the route does not include the `plan` step — the route was widened silently")
        if self.tasks and "tasks" not in self.steps:
            out.append("task folders exist but the route does not include the `tasks` step — the route was widened silently")
        return out

    def _check_plan(self) -> list[str]:
        out: list[str] = []
        if "plan" in self.steps and self.tasks and not self.plan_approved:
            out.append("task folders exist but plan.md is missing or still draft — no task was authorised")
        if "plan" not in self.steps or not self.plan_path.exists():
            return out
        if self.plan_approved and (left := placeholder_lines(self.plan_body)):
            out.append(f"plan.md is approved but still holds `{{{{...}}}}` on body line(s) {', '.join(map(str, left[:8]))}")
        if not self.plan_meta:
            out.append("plan.md has no frontmatter (expected type/plan/status/updated)")
        elif self.plan_meta.get("status") not in ("draft", "approved"):
            out.append(f"plan.md: status is {self.plan_meta.get('status')!r}; expected draft or approved")
        if BEGIN not in self.plan_body:
            out.append("plan.md: section 4 has no BEGIN/END GENERATED markers — counts cannot be synced")
        if not section(self.plan_body, TASK_LIST_SECTION).strip():
            out.append(f"plan.md has no section {TASK_LIST_SECTION!r} — the heading was renamed, so the task list cannot be read")
        ids = [r.id for r in self.rows]
        for dup in sorted({i for i in ids if ids.count(i) > 1}):
            out.append(f"plan.md: {dup} is listed more than once")
        for r in self.rows:
            for req in r.satisfies:
                if self.reqs and req not in self.reqs:
                    out.append(f"plan.md: {r.id} satisfies {req}, which research.md does not define")
        return out

    def _check_tasks(self) -> list[str]:
        out: list[str] = []
        add = out.append
        tasks_dir = self.dir / "tasks"
        for stray in sorted(tasks_dir.glob("task_*.md")):
            add(f"tasks/{stray.name}: a task is a folder `task_NNN_<slug>/task.md`, not a file")

        for t in self.tasks:
            where = f"tasks/{t.name}"
            if not TASK_DIR_RE.match(t.name):
                add(f"{where}: folder name must be task_NNN_<kebab-slug>")
            if not t.path.is_file():
                add(f"{where}: no {TASK_FILE} — the folder holds no task")
                continue
            if not t.meta:
                add(f"{where}/{TASK_FILE}: no frontmatter — status cannot be read")
                continue
            if t.status not in STATUSES:
                add(f"{where}: status {t.status!r} is not one of {'/'.join(STATUSES)}")
            if not t.deliverable:
                add(f"{where}: no `> deliverable` line under the H1 — the index has nothing to show")
            if not t.satisfies and t.status != "dropped":
                add(f"{where}: satisfies is empty — a task tracing to no REQ is scope creep")
            for req in t.satisfies:
                if self.reqs and req not in self.reqs:
                    add(f"{where}: satisfies {req}, which research.md section 5 does not define")
            for dep in t.task_deps:
                if self.task(dep) is None and self.row(dep) is None:
                    add(f"{where}: depends_on {dep}, which is neither a task nor a row")
            for dep in t.plan_deps:
                if not (t.dir / dep).is_dir():
                    add(f"{where}: depends_on {dep}, which is not a folder inside this task")
            for sub in t.nested:
                m = NESTED_RE.match(sub.name)
                if not m or int(m.group(1)) != t.number:
                    add(f"{where}/{sub.name}: a plan inside task_{t.number:03d} is named plan-{t.number:03d}-<slug>")
                if sub.name not in t.plan_deps:
                    add(f"{where}: holds {sub.name} but does not depend on it")
            if not t.acceptance.strip() and t.status != "dropped":
                add(f"{where}: Acceptance / Verification is empty — nothing states what would prove this task")

            row = self.row(t.short)
            if row is None and "plan" in self.steps and self.plan_path.exists():
                add(f"{where}: has no row in plan.md section 3 — the task list is the approved artifact")
            if row is not None:
                if set(row.satisfies) != set(t.satisfies):
                    add(f"{where}: satisfies {t.satisfies} but its row in plan.md says {row.satisfies}")
                if set(row.depends_on) != set(t.task_deps):
                    add(f"{where}: depends_on {t.task_deps} but its row in plan.md says {row.depends_on}")
                if row.dropped and t.status != "dropped":
                    add(f"{where}: its row is struck as dropped but status is {t.status!r}")

            if t.status != "dropped":
                if not t.files:
                    add(f"{where}: the Files table names no readable path — a cold reader cannot tell what to open")
                for action, rel in t.files:
                    exists = Path(rel).exists()
                    if action in ("modify", "delete") and not exists:
                        add(f"{where}: Files says {action} {rel}, which does not exist")
                    elif action == "create" and exists and t.status == "not-started":
                        add(f"{where}: Files says create {rel}, which already exists")
                for phrase in t.leans_on_the_conversation():
                    add(f'{where}: the body says "{phrase}" — it points at a conversation the executing agent has not had')

            if t.status == "done":
                if not t.has_filled_line("Verified"):
                    add(f"{where}: status is done but the Progress Log has no filled `- Verified:` entry")
                if self.review == "required" and not t.has_filled_line("Review"):
                    add(f"{where}: status is done but the Progress Log has no filled `- Review:` entry (review: required)")
                for state in self.blockers(t):
                    add(f"{where}: is done, but its dependency {state} is not finished")

        graph = {t.short: [d for d in t.task_deps] for t in self.tasks}
        for r in self.rows:
            graph.setdefault(r.id, list(r.depends_on))
        for cycle in find_cycles(graph):
            add("dependency cycle: " + " -> ".join(cycle))
        return out

    def _check_coverage(self) -> list[str]:
        """WHEN a requirement exists that no task and no listed row carries."""
        if "tasks" not in self.steps or not self.reqs:
            return []
        if not self.tasks and not self.plan_path.exists():
            return []
        covered = {req for t in self.tasks if t.status != "dropped" for req in t.satisfies}
        covered |= self.listed_satisfies()
        return [f"{req} is defined in research.md but no task carries it" for req in self.reqs if req not in covered]

    def acceptances(self) -> list[Path]:
        return sorted(self.dir.glob(ACCEPT_GLOB))

    def _check_acceptance(self) -> list[str]:
        """WHEN a verdict claims more than its own table shows. NOT ACCEPTED claims nothing."""
        out: list[str] = []
        for path in self.acceptances():
            meta, body = parse_frontmatter(path.read_text(encoding="utf-8"))
            verdict = meta.get("verdict")
            if verdict not in VERDICTS:
                out.append(f"{path.name}: verdict is {verdict!r}; expected one of {', '.join(VERDICTS)}")
                continue
            if verdict == "NOT ACCEPTED":
                continue
            if left := placeholder_lines(body):
                out.append(f"{path.name}: verdict is {verdict} but `{{{{...}}}}` remain on body line(s) {', '.join(map(str, left[:8]))}")
            scope = section(body, ACCEPT_SECTION)
            if not scope.strip():
                out.append(f"{path.name}: no section {ACCEPT_SECTION!r} — the heading was renamed, so no row can be read")
                continue
            rows = [r for r in table_rows(scope) if r[0] not in ("REQ", "") and not r[0].startswith("---")]
            if not rows:
                out.append(f"{path.name}: verdict is {verdict} but the scope table has no requirement rows")
            elif verdict == "ACCEPTED":
                failing = [r[0] for r in rows if r[-1].strip("* ").upper() != "PASS"]
                if failing:
                    out.append(f"{path.name}: verdict is ACCEPTED but {', '.join(failing)} is not PASS")
        return out

    def _check_generated(self) -> list[str]:
        out: list[str] = []
        index_path = self.dir / "tasks" / "_index.md"
        fresh = _drift_comparable(render_index(self.tasks))
        if not index_path.exists():
            out.append("tasks/_index.md is missing — run `plan.py sync`")
        else:
            current = extract_block(index_path.read_text(encoding="utf-8"))
            if current is None:
                out.append("tasks/_index.md: no BEGIN/END GENERATED markers — cannot verify sync")
            elif _drift_comparable(current) != fresh:
                out.append("tasks/_index.md is out of sync with task frontmatter — run `plan.py sync`")
        if self.plan_path.exists():
            current = extract_block(self.plan_path.read_text(encoding="utf-8"))
            if current is not None and current.strip("\n") != counts_line(self.tasks):
                out.append("plan.md section 4 counts are out of sync with task frontmatter — run `plan.py sync`")
        return out

    # --- generation

    def sync(self) -> list[str]:
        notes: list[str] = []
        index_path = self.dir / "tasks" / "_index.md"
        payload = render_index(self.tasks)
        if index_path.exists():
            updated = replace_block(index_path.read_text(encoding="utf-8"), payload)
            if updated is None:
                notes.append("tasks/_index.md: no BEGIN/END GENERATED markers — rewrote the file")
                updated = new_index(self.name, payload)
        else:
            updated = new_index(self.name, payload)
            notes.append("tasks/_index.md: created")
        index_path.parent.mkdir(parents=True, exist_ok=True)
        _write(index_path, updated)
        if self.plan_path.exists():
            updated = replace_block(self.plan_path.read_text(encoding="utf-8"), counts_line(self.tasks) + "\n")
            if updated is None:
                notes.append("plan.md: no BEGIN/END GENERATED markers in section 4 — counts not written")
            else:
                _write(self.plan_path, updated)
        return notes


# --------------------------------------------------------------------------- scaffolding


def _write(path: Path, text: str) -> None:
    path.write_text(text, encoding="utf-8", newline="\n")


def _fill(template: str, **values: str) -> str:
    text = (ASSETS / template).read_text(encoding="utf-8")
    text = text.replace("{{YYYY-MM-DD}}", _dt.date.today().isoformat())
    for key, value in values.items():
        text = text.replace("{{" + key + "}}", value)
    return text


def _titlecase(slug: str) -> str:
    return slug.replace("-", " ").capitalize()


def _fail(message: str) -> int:
    print(message, file=sys.stderr)
    return 2


def _task_text(number: int, slug: str, satisfies: list[str], depends_on: list[str]) -> str:
    return _fill(
        "task.template.md",
        NNN=f"{number:03d}",
        Title=_titlecase(slug),
        satisfies=", ".join(satisfies),
        depends_on=", ".join(depends_on),
    )


def _row_line(task_id: str, title: str, satisfies: list[str], depends_on: list[str]) -> str:
    return f"| {task_id} | {title} | {', '.join(satisfies) or '—'} | {', '.join(depends_on) or '—'} |"


def _rewrite_rows(plan_path: Path, edit) -> None:
    """Apply `edit(cells) -> list[str] | None` to every task row of section 3.

    `edit` returns replacement lines, or None to keep the line as it is.
    """
    lines = plan_path.read_text(encoding="utf-8").split("\n")
    out: list[str] = []
    inside = False
    for line in lines:
        if line.startswith("## "):
            inside = bool(re.match(r"^##\s+" + re.escape(TASK_LIST_SECTION) + r"\s*$", line))
        if inside and line.strip().startswith("|"):
            cells = [c.strip() for c in line.strip().strip("|").split("|")]
            if len(cells) >= 4 and TASK_ID_RE.match(cells[0].strip("~ ")):
                replacement = edit(cells)
                if replacement is not None:
                    out.extend(replacement)
                    continue
        out.append(line)
    _write(plan_path, "\n".join(out))


def cmd_new(args) -> int:
    if not SLUG_RE.match(args.name):
        return _fail(f"plan name must be kebab-case: {args.name!r}")
    brief = "none"
    task_dir = None
    if args.in_task:
        task_dir = Path(args.in_task)
        m = TASK_DIR_RE.match(task_dir.name)
        if not m or not (task_dir / TASK_FILE).is_file():
            return _fail(f"--in needs a task folder task_NNN_<slug>/ holding {TASK_FILE}: {task_dir}")
        if any(d.is_dir() and d.name.startswith("plan-") for d in task_dir.iterdir()):
            return _fail(f"{task_dir} already holds a plan")
        plan_dir = task_dir / f"plan-{m.group(1)}-{args.name}"
        brief = f"../{TASK_FILE}"
    else:
        plan_dir = Path(args.root) / f"plan-{args.name}"
    for existing in ("policy.md", "research.md", "plan.md"):
        if (plan_dir / existing).exists():
            return _fail(f"refusing to overwrite: {plan_dir / existing} already exists")
    plan_dir.mkdir(parents=True, exist_ok=True)
    title = args.title or _titlecase(args.name)
    _write(plan_dir / "policy.md", _fill("policy.template.md", **{"plan-name": plan_dir.name}))
    _write(plan_dir / "research.md", _fill("research.template.md", **{"plan-name": plan_dir.name, "Title": title, "brief": brief}))
    print(f"created {plan_dir.as_posix()}/policy.md   (route proposed: [research, plan, tasks], review required; decided: pending)")
    print(f"created {plan_dir.as_posix()}/research.md (status: draft, brief: {brief})")
    if task_dir is not None:
        task_md = task_dir / TASK_FILE
        meta, _ = parse_frontmatter(task_md.read_text(encoding="utf-8"))
        deps = _as_list(meta.get("depends_on")) + [plan_dir.name]
        _write(task_md, set_field(task_md.read_text(encoding="utf-8"), "depends_on", f"[{', '.join(deps)}]"))
        print(f"updated {task_md.as_posix()}: depends_on {deps}")
        parent = task_dir.parent.parent
        if (parent / "policy.md").exists():
            Plan(parent).sync()
    return 0


def cmd_plan(args) -> int:
    plan = Plan(args.plan_dir)
    if plan.plan_path.exists():
        return _fail(f"refusing to overwrite: {plan.plan_path} already exists")
    if "plan" not in plan.steps:
        return _fail(f"the route in policy.md is {plan.steps} — it does not include the `plan` step")
    if not plan.research_approved:
        return _fail("research.md is not approved — Gate A comes before plan.md")
    title = args.title or _titlecase(plan.name.removeprefix("plan-"))
    _write(plan.plan_path, _fill("plan.template.md", **{"plan-name": plan.name, "Title": title}))
    print(f"created {plan.plan_path.as_posix()} (status: draft)")
    return 0


def _task_gate(plan: Plan) -> str | None:
    if "tasks" not in plan.steps:
        return f"the route in policy.md is {plan.steps} — it does not include the `tasks` step"
    if not plan.research_approved:
        return "research.md is not approved — Gate A comes before any task"
    if "plan" in plan.steps and not plan.plan_approved:
        return "plan.md is missing or still draft — the task list is approved before any task folder"
    return None


def cmd_task(args) -> int:
    plan = Plan(args.plan_dir)
    if not SLUG_RE.match(args.slug):
        return _fail(f"slug must be kebab-case: {args.slug!r}")
    if (reason := _task_gate(plan)) is not None:
        return _fail(reason)

    if "plan" in plan.steps:
        # The approved task list is the source: number, REQs and dependencies come from its row,
        # so the folder cannot drift from what the user approved.
        if not args.row:
            return _fail("--row task_NNN is required: the task comes from a row of plan.md section 3")
        row = plan.row(args.row)
        if row is None:
            return _fail(f"plan.md section 3 has no row {args.row}")
        if row.dropped:
            return _fail(f"{row.id} is struck as dropped in plan.md")
        if plan.task(row.id) is not None:
            return _fail(f"{row.id} is already written: {plan.task(row.id).name}")
        if args.satisfies and set(args.satisfies) != set(row.satisfies):
            return _fail(f"--satisfies {args.satisfies} differs from the row's {row.satisfies}")
        number, satisfies, depends = int(row.id[5:]), row.satisfies, row.depends_on
    else:
        if not args.satisfies:
            return _fail("--satisfies REQ-NNN is required: a task traces to the requirements it delivers")
        used = plan.used_numbers()
        number = max(used) + 1 if used else 1
        satisfies, depends = args.satisfies, args.depends_on or []
    unknown = [r for r in satisfies if plan.reqs and r not in plan.reqs]
    if unknown:
        return _fail(f"research.md does not define {', '.join(unknown)}")
    if not satisfies:
        return _fail("the task would satisfy no REQ")

    folder = plan.dir / "tasks" / f"task_{number:03d}_{args.slug}"
    folder.mkdir(parents=True, exist_ok=True)
    _write(folder / TASK_FILE, _task_text(number, args.slug, satisfies, depends))
    print(f"created {(folder / TASK_FILE).as_posix()}")
    for note in Plan(args.plan_dir).sync():
        print(f"sync: {note}")
    return 0


def cmd_split(args) -> int:
    plan = Plan(args.plan_dir)
    if (reason := _task_gate(plan)) is not None:
        return _fail(reason)
    parts: list[tuple[str, list[str]]] = []
    for spec in args.parts:
        slug, sep, reqs = spec.partition("=")
        ids = [r.strip() for r in reqs.split(",") if r.strip()]
        if not sep or not SLUG_RE.match(slug) or not ids or not all(REQ_ID_RE.match(r) for r in ids):
            return _fail(f"each part is <kebab-slug>=REQ-NNN[,REQ-NNN]: {spec!r}")
        parts.append((slug, ids))
    if len(parts) < 2:
        return _fail("a split has at least two parts")

    short = "_".join(args.task.split("_")[:2])
    row, task = plan.row(short), plan.task(short)
    if row is None and task is None:
        return _fail(f"no task or row {args.task}")
    if task is not None and task.status in FINISHED:
        return _fail(f"{task.name} is {task.status} — a finished task is not split")
    if task is not None and task.nested:
        return _fail(f"{task.name} holds its own plan — split inside that plan instead")
    original = set(row.satisfies if row else task.satisfies)
    for slug, ids in parts:
        if not set(ids) <= original:
            return _fail(f"part {slug} claims {sorted(set(ids) - original)}, which {short} does not carry")
    covered = {r for _, ids in parts for r in ids}
    if covered != original:
        return _fail(f"the parts leave {sorted(original - covered)} uncovered; together they must carry {sorted(original)}")

    depends = row.depends_on if row else task.task_deps
    used = plan.used_numbers()
    numbers = [int(short[5:])]
    nxt = max(used) + 1
    for _ in parts[1:]:
        numbers.append(nxt)
        nxt += 1
    new_ids = [f"task_{n:03d}" for n in numbers]

    if row is not None:
        def edit(cells: list[str]) -> list[str] | None:
            rid = cells[0].strip("~ ")
            if rid == short:
                return [_row_line(i, _titlecase(s), ids, depends) for i, (s, ids) in zip(new_ids, parts)]
            deps = [d.strip() for d in cells[3].split(",") if TASK_ID_RE.match(d.strip())]
            if short in deps:
                deps = [x for d in deps for x in (new_ids if d == short else [d])]
                return ["| " + " | ".join(cells[:3] + [", ".join(deps)] + cells[4:]) + " |"]
            return None

        _rewrite_rows(plan.plan_path, edit)
        if not append_revision(plan.plan_path, f"Split {short} into {', '.join(new_ids)}", "user's choice of split"):
            print(f"note: plan.md has no {REVISION_SECTION!r} table — log the split by hand", file=sys.stderr)

    if task is not None:
        first = plan.dir / "tasks" / f"{new_ids[0]}_{parts[0][0]}"
        if first != task.dir:
            task.dir.rename(first)
        text = (first / TASK_FILE).read_text(encoding="utf-8")
        text = set_field(text, "satisfies", f"[{', '.join(parts[0][1])}]")
        text = set_field(text, "status", "not-started")
        _write(first / TASK_FILE, text)
        print(f"kept    {(first / TASK_FILE).as_posix()} (status: not-started — re-elaborate it for its part)")
        for (slug, ids), number in zip(parts[1:], numbers[1:]):
            folder = plan.dir / "tasks" / f"task_{number:03d}_{slug}"
            folder.mkdir(parents=True, exist_ok=True)
            _write(folder / TASK_FILE, _task_text(number, slug, ids, depends))
            print(f"created {(folder / TASK_FILE).as_posix()}")
    for other in plan.tasks:
        if other.short != short and short in other.task_deps:
            deps = [x for d in other.depends_on for x in (new_ids if d == short else [d])]
            _write(other.path, set_field(other.path.read_text(encoding="utf-8"), "depends_on", f"[{', '.join(deps)}]"))
            print(f"rewired {other.name}: depends_on {deps}")
    print(f"split {short} -> {', '.join(new_ids)}")
    for note in Plan(args.plan_dir).sync():
        print(f"sync: {note}")
    return 0


def cmd_drop(args) -> int:
    plan = Plan(args.plan_dir)
    short = "_".join(args.task.split("_")[:2])
    row, task = plan.row(short), plan.task(short)
    if row is None and task is None:
        return _fail(f"no task or row {args.task}")
    if task is not None:
        if task.status == "done":
            return _fail(f"{task.name} is done — a finished task is not dropped")
        _write(task.path, set_field(task.path.read_text(encoding="utf-8"), "status", "dropped"))
        print(f"dropped {task.name}")
    if row is not None and not row.dropped:
        _rewrite_rows(
            plan.plan_path,
            lambda cells: ["| " + " | ".join([f"{STRIKE}{short}{STRIKE}"] + cells[1:]) + " |"]
            if cells[0].strip("~ ") == short
            else None,
        )
        append_revision(plan.plan_path, f"Dropped {short}", "user's decision")
        print(f"struck  {short} in plan.md section 3")
    for note in Plan(args.plan_dir).sync():
        print(f"sync: {note}")
    left = Plan(args.plan_dir)._check_coverage()
    for line in left:
        print(f"uncovered: {line}")
    return 0


def _collect_ready(plan: Plan, trail: list[str], out: dict) -> None:
    for t in plan.ordered([t for t in plan.tasks if t.status not in FINISHED]):
        label = " › ".join(trail + [t.name])
        if t.status == "in-progress":
            out["running"].append((label, t))
        elif t.status == "not-started":
            blocking = plan.blockers(t)
            (out["waiting"] if blocking else out["ready"]).append((label, t, blocking) if blocking else (label, t))
        else:
            out["waiting"].append((label, t, [t.status]))
        for sub_dir in t.nested:
            sub = Plan(sub_dir)
            step, why = sub.where()
            if step in ("research", "plan"):
                out["gates"].append((" › ".join(trail + [t.short, sub.name]), step, why))
            _collect_ready(sub, trail + [t.short, sub.name], out)
    for r in plan.unwritten():
        out["unwritten"].append(" › ".join(trail + [r.id]) + f"  {r.title}")


def _groups(ready: list[tuple[str, Task]]) -> list[list[tuple[str, Task]]]:
    """Ready tasks joined when their Files tables share a path. A task with no readable Files
    stands alone: overlap cannot be ruled out, so it is not grouped with anything by guess."""
    groups: list[list[tuple[str, Task]]] = []
    files: list[set[str]] = []
    for item in ready:
        fs = item[1].file_set()
        hits = [i for i, g in enumerate(files) if fs and g and fs & g]
        merged = [item]
        merged_files = set(fs)
        for i in reversed(hits):
            merged = groups.pop(i) + merged
            merged_files |= files.pop(i)
        groups.append(merged)
        files.append(merged_files)
    return groups


def cmd_ready(args) -> int:
    plan = Plan(args.plan_dir)
    if (reason := _task_gate(plan)) is not None:
        print(f"no task can run yet: {reason}")
        return 0
    out: dict = {"running": [], "ready": [], "waiting": [], "unwritten": [], "gates": []}
    _collect_ready(plan, [plan.name], out)

    if out["running"]:
        print("in progress:")
        for label, _ in out["running"]:
            print(f"  {label}")
    print("ready to run (written, dependencies finished):")
    if not out["ready"]:
        print("  None.")
    groups = _groups(out["ready"])
    for g in groups:
        for label, t in g:
            fs = ", ".join(sorted(t.file_set())) or "no readable Files — overlap unknown"
            print(f"  {label}    files: {fs}")
        if len(g) > 1:
            shared = set.intersection(*(t.file_set() for _, t in g)) or {p for _, t in g for p in t.file_set()}
            print(f"  → share files ({', '.join(sorted(shared))}): one at a time")
    known = [g for g in groups if all(t.file_set() for _, t in g)]
    unknown = [label for g in groups for label, t in g if not t.file_set()]
    if len(known) > 1:
        print(f"  → {len(known)} groups with no shared files: any order, or together")
    if unknown:
        print(f"  → overlap unknown for {', '.join(unknown)}: fill its Files table before running it beside another")
    print("waiting:")
    if not out["waiting"]:
        print("  None.")
    for label, _, blocking in out["waiting"]:
        print(f"  {label}    on {', '.join(blocking)}")
    if out["gates"]:
        print("plans waiting on a gate:")
        for label, step, why in out["gates"]:
            print(f"  {label}    {step}: {why}")
    print("not written yet:")
    if not out["unwritten"]:
        print("  None.")
    for line in out["unwritten"]:
        print(f"  {line}")
    return 0


def cmd_accept(args) -> int:
    plan = Plan(args.plan_dir)
    if not ACCEPT_SCOPE_RE.match(args.scope):
        return _fail(f"scope must be `all`, `task_001` or `task_001-task_003`: {args.scope!r}")
    path = plan.dir / f"acceptance-{args.scope}.md"
    if path.exists():
        return _fail(f"refusing to overwrite: {path} already exists")
    scope = "whole plan" if args.scope == "all" else args.scope
    _write(path, _fill("acceptance.template.md", **{"plan-name": plan.name, "scope": scope}))
    print(f"created {path.as_posix()} (verdict: NOT ACCEPTED)")
    return 0


def cmd_status(args) -> int:
    root = Plan(args.plan_dir)
    trail, plan, step, why = root.locate()
    for line in plan.header(trail, step, why):
        print(line)
    print()
    print(f"plan    : {plan.dir.as_posix()}")
    print(f"route   : steps {plan.steps}, review {plan.review}")
    print(f"research: {plan.research_meta.get('status', 'missing')}, confidence {plan.research_meta.get('confidence', '—')}")
    if "plan" in plan.steps:
        print(f"plan.md : {plan.plan_meta.get('status', 'missing')}, {len(plan.rows)} row(s), {len(plan.unwritten())} not written")
    if plan.tasks:
        print(f"tasks   : {counts_line(plan.tasks)[12:]}")
        for t in plan.tasks:
            if t.status in ("blocked", "in-progress"):
                last = [ln for ln in t.progress.split("\n") if ln.strip().startswith("-")]
                note = last[-1].strip()[2:] if last else "no Progress Log entry"
                print(f"          {t.name}: {t.status} — {note}")
    for path in plan.acceptances():
        verdict = parse_frontmatter(path.read_text(encoding="utf-8"))[0].get("verdict")
        print(f"accept  : {path.name} — {verdict}")
    print(f"step    : {step}")
    print(f"          {why}")
    return 0


def cmd_handoff(args) -> int:
    """Print exactly what an agent carrying out this task is given, and nothing else."""
    plan = Plan(args.plan_dir)
    task = plan.task("_".join(args.task.split("_")[:2])) or plan.task(args.task)
    if task is None or not task.path.is_file():
        known = ", ".join(t.name for t in plan.tasks) or "(none)"
        return _fail(f"no written task {args.task}. Known: {known}")
    constraints = section(plan.plan_body, CONSTRAINTS_SECTION).strip()
    print(f"# Handoff — {task.name}\n")
    print(
        "You are carrying out one task. Everything you need is below; there is no earlier\n"
        "conversation to recover. Before changing anything, list what you would have to invent\n"
        "to finish this — if that list is not empty, report it and stop.\n"
    )
    if constraints:
        print(f"## Constraints inherited from the plan\n\n{constraints}\n")
    print("---\n")
    print(task.path.read_text(encoding="utf-8").rstrip())
    return 0


def cmd_sync(args) -> int:
    plan = Plan(args.plan_dir)
    for note in plan.sync():
        print(f"sync: {note}")
    print(f"sync: {len(plan.tasks)} task(s) -> tasks/_index.md" + (", plan.md section 4" if plan.plan_path.exists() else ""))
    return 0


def cmd_check(args) -> int:
    plan = Plan(args.plan_dir)
    problems, warnings = plan.check()
    for w in warnings:
        print(f"warning: {w}")
    if problems:
        print(f"\n{len(problems)} problem(s) in {plan.dir.as_posix()}:")
        for p in problems:
            print(f"  - {p}")
        return 1
    tail = f" — {counts_line(plan.tasks)[12:]}" if plan.tasks else ""
    print(f"OK: {plan.dir.as_posix()} is consistent ({len(plan.tasks)} task(s)){tail}")
    return 0


# --------------------------------------------------------------------------- cli


def main(argv: list[str] | None = None) -> int:
    # Messages carry `—` and `›`; a console on a legacy code page would mangle them.
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    sub = parser.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("new", help="scaffold policy.md + research.md for a new plan")
    p.add_argument("name", help="kebab-case plan name, 2-4 words")
    p.add_argument("--root", default="plans", help="where top-level plan folders live (default: plans)")
    p.add_argument("--in", dest="in_task", metavar="TASK_DIR", help="create the plan inside this task folder")
    p.add_argument("--title", help="human title for the H1 (default: from the name)")
    p.set_defaults(func=cmd_new)

    p = sub.add_parser("plan", help="scaffold plan.md")
    p.add_argument("plan_dir", type=Path)
    p.add_argument("--title")
    p.set_defaults(func=cmd_plan)

    p = sub.add_parser("task", help="scaffold tasks/task_NNN_<slug>/task.md, then sync")
    p.add_argument("plan_dir", type=Path)
    p.add_argument("slug", help="kebab-case, 2-4 words")
    p.add_argument("--row", metavar="TASK", help="the plan.md row this task writes, e.g. task_003 (required when the route has `plan`)")
    p.add_argument("--satisfies", nargs="+", metavar="REQ", help="REQ ids (required when the route has no `plan`)")
    p.add_argument("--depends-on", nargs="+", metavar="TASK", help="short task ids, when the route has no `plan`")
    p.set_defaults(func=cmd_task)

    p = sub.add_parser("split", help="replace one task with several sibling tasks")
    p.add_argument("plan_dir", type=Path)
    p.add_argument("task", help="task_003 or the full folder name")
    p.add_argument("parts", nargs="+", help="slug=REQ-001[,REQ-002] per part, two or more")
    p.set_defaults(func=cmd_split)

    p = sub.add_parser("drop", help="mark a task dropped: its status, and its row struck in plan.md")
    p.add_argument("plan_dir", type=Path)
    p.add_argument("task")
    p.set_defaults(func=cmd_drop)

    p = sub.add_parser("ready", help="what can run now, across this plan and every nested plan")
    p.add_argument("plan_dir", type=Path)
    p.set_defaults(func=cmd_ready)

    p = sub.add_parser("accept", help="scaffold acceptance-<scope>.md for an accept verdict")
    p.add_argument("plan_dir", type=Path)
    p.add_argument("scope", nargs="?", default="all", help="all (default), task_001 or task_001-task_003")
    p.set_defaults(func=cmd_accept)

    p = sub.add_parser("status", help="where work continues, as the two header lines")
    p.add_argument("plan_dir", type=Path)
    p.set_defaults(func=cmd_status)

    p = sub.add_parser("handoff", help="print exactly what an agent carrying out this task is given")
    p.add_argument("plan_dir", type=Path)
    p.add_argument("task", help="task_003 or the full folder name")
    p.set_defaults(func=cmd_handoff)

    p = sub.add_parser("sync", help="regenerate tasks/_index.md and plan.md section 4")
    p.add_argument("plan_dir", type=Path)
    p.set_defaults(func=cmd_sync)

    p = sub.add_parser("check", help="read-only; exit 1 if anything is wrong, across the whole tree")
    p.add_argument("plan_dir", type=Path)
    p.set_defaults(func=cmd_check)

    args = parser.parse_args(argv)
    if args.cmd != "new" and not args.plan_dir.is_dir():
        return _fail(f"not a directory: {args.plan_dir}")
    try:
        return args.func(args)
    except ValueError as exc:
        return _fail(str(exc))


if __name__ == "__main__":
    raise SystemExit(main())
