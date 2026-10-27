#!/usr/bin/env python3
"""Create, build and check a visual report.

    python visual_report.py name <topic>                      print <topic>-<YYYY-MM-DD>-<HHmm>
    python visual_report.py new <report-dir> --type T --depth D [--theme NAME]
                                                              copy the template into a new report
    python visual_report.py status <report-dir>               print the current step, from disk
    python visual_report.py outline-approved <report-dir>     record the user's approve of the outline
    python visual_report.py build <report-dir>                derive, render, write dist, check
    python visual_report.py check <report-dir>                every check, without rendering
    python visual_report.py pdf <report-dir>                  print dist/<name>.min.html to PDF
    python visual_report.py reviewed <report-dir>             record that every page was viewed
    python visual_report.py components                        print the r-* element catalogue

A report is a chain of artifacts: brief.md -> sources/ -> outline (approved) -> claims.md -> src/
-> dist/. The step is the first one that is missing, unfilled, stale or failing its check. An
approved outline is stale when its table changes after the approval.

Rendering runs the system Chrome, Edge or Chromium headless against a local HTTP server; the page
posts its rendered DOM and measurements back. No stdout from the browser and no file:// fetch is
relied on, because neither behaves the same across browsers and platforms.

Exit codes: 0 pass, 1 findings, 2 usage error. Standard library only; every file is UTF-8.
"""

from __future__ import annotations

import argparse
import base64
import csv
import datetime as _dt
import functools
import hashlib
import html.parser
import http.server
import io
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import threading
from pathlib import Path

# --------------------------------------------------------------------------- constants
# Every literal shared with the template, components.js or SKILL.md is named once here.

SKILL_DIR = Path(__file__).resolve().parent.parent
ASSETS = SKILL_DIR / "assets"
TEMPLATE_DIR = ASSETS / "template"
STATIC_ASSETS = ASSETS / "static"
THEME_ASSETS = ASSETS / "themes"
OUTLINE_ASSETS = ASSETS / "outlines"

BRIEF = "brief.md"
CLAIMS = "claims.md"
SOURCES = "sources"
DERIVE = "sources/derive"
SRC = "src"
DIST = "dist"
REPORT_HTML = "report.html"
STATIC = "static"
THEMES = "static/themes"
THEME_CSS = "static/theme.css"
COMPONENTS_JS = "static/components.js"
BUILD_JSON = "build.json"
DATA_DIRS = ("diagrams", "charts", "tables")
NEW_DIRS = (DERIVE, f"{SRC}/diagrams", f"{SRC}/charts", f"{SRC}/tables", DIST)

SOURCES_HEADING = "## Sources"
OUTLINE_HEADING = "## Outline"
OUTLINE_TOKEN = "{{outline-from-type}}"
REGISTRY_BEGIN = "/* REGISTRY-BEGIN */"
REGISTRY_END = "/* REGISTRY-END */"
REGISTRY_ASSIGN = "const REGISTRY ="

BRIEF_FIELDS = ("title", "language", "audience", "type", "depth", "timezone", "theme", "export",
                "variant", "outline", "reviewed")
SCOPES = {"in", "out", "context"}
EXPORTS = {"pdf", "none"}
SUMMARY_PART = "summary"
PARTS = (SUMMARY_PART, "main", "method", "appendix")
DEFAULT_PART = "main"
OUTLINE_COLUMNS = ("n", "part", "title", "visual", "proves", "detail")
TOC_DEPTHS = ("standard", "detailed")  # depths that need an r-toc after the summary
OUTLINE_DRAFT = "draft"
REVIEWED_NONE = "none"
DONE_PATH = "/__done"
RENDER_QUERY = "__render=1"

# Which data file each visual element reads: (folder prefix, suffix).
SRC_RULES = {"r-diagram": ("diagrams/", ".mmd"), "r-chart": ("charts/", ".json"), "r-table": ("tables/", ".csv")}

# Legibility and budget thresholds. Measured at the fixed page width in static/base.css
# (--page-width: 680px). First values; tune them on real reports, then keep them fixed.
MIN_TEXT_PX = 11            # smallest text in a diagram or chart after scaling to the page
MAX_VISUAL_HEIGHT_PX = 700  # taller visuals leave half-empty pages when they move to the next one
MIN_CHART_HEIGHT_PX = 120
MAX_TITLE_WORDS = 12        # a section title is the answer in one line
MAX_KPI_LABEL_WORDS = 6
# Depth chosen by the user: words per prose block (one r-text, r-callout or r-item), and the
# outline parts a report of that depth must have.
DEPTHS = {
    "summary":  {"words": 60,  "required_parts": ()},
    "standard": {"words": 80,  "required_parts": ()},
    "detailed": {"words": 150, "required_parts": ("method", "appendix")},
}
MAX_GRID_COLS = 4
MAX_SERIES = 6
MAX_PIE_SLICES = 7
MAX_CATEGORIES = 12

RENDER_TIMEOUT_S = 120
PROCESS_TIMEOUT_S = 120
WINDOW_SIZE = "1200,1000"
BROWSER_ENV = "REPORT_BROWSER"

WINDOWS_BROWSERS = (
    ("PROGRAMFILES", "Google/Chrome/Application/chrome.exe"),
    ("PROGRAMFILES(X86)", "Google/Chrome/Application/chrome.exe"),
    ("LOCALAPPDATA", "Google/Chrome/Application/chrome.exe"),
    ("PROGRAMFILES", "Microsoft/Edge/Application/msedge.exe"),
    ("PROGRAMFILES(X86)", "Microsoft/Edge/Application/msedge.exe"),
    ("LOCALAPPDATA", "Chromium/Application/chrome.exe"),
)
MAC_BROWSERS = (
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
    "/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge",
    "/Applications/Chromium.app/Contents/MacOS/Chromium",
)
PATH_BROWSERS = ("google-chrome", "google-chrome-stable", "chromium", "chromium-browser",
                 "microsoft-edge", "microsoft-edge-stable", "chrome", "msedge")

FONT_MIME = {".woff2": "font/woff2", ".woff": "font/woff", ".ttf": "font/ttf", ".otf": "font/otf"}

CURLY = re.compile(r"\{\{[^{}]*\}\}")
LINES = re.compile(r"^\d+(-\d+)?(,\d+(-\d+)?)*$")
SCRIPT_BLOCK = re.compile(r"<script\b[^>]*>.*?</script\s*>", re.S | re.I)
SCRIPT_SRC = re.compile(r'<script\b[^>]*\bsrc="([^"]+)"[^>]*>\s*</script\s*>', re.I)
STYLESHEET = re.compile(r'<link\b(?=[^>]*\brel="stylesheet")[^>]*\bhref="([^"]+)"[^>]*>', re.I)
CSS_URL = re.compile(r"""url\((['"]?)(?!data:|https?:|#)([^'")]+)\1\)""")
CLOSE_SCRIPT = re.compile(r"</(script)", re.I)
HEAD_END = re.compile(r"</head\s*>", re.I)

# What the checks do not judge — these need reading, so they are the agent's job, and a guess
# here would be a false alarm that teaches people to ignore the checker:
#   - whether a claim says what its source says, or mixes variants in meaning;
#   - what a diagram should show, or whether the chosen component fits;
#   - the language of the text (only the brief field and <html lang> are compared);
#   - how each page looks;
#   - connectivity of diagrams mermaid does not expose as a graph, and visuals that could not
#     be measured: both are reported as skipped, never as passing.


# --------------------------------------------------------------------------- small helpers


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def sha256_of(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def dist_paths(report: Path) -> dict[str, Path]:
    name = report.resolve().name
    d = report / DIST
    return {"min": d / f"{name}.min.html", "full": d / f"{name}.full.html",
            "pdf": d / f"{name}.pdf", "build": d / BUILD_JSON}


def placeholders(text: str) -> list[str]:
    return [" ".join(m.split())[:60] for m in CURLY.findall(text)]


class UsageError(Exception):
    """A loud failure: missing template literal, missing browser, broken registry."""


# --------------------------------------------------------------------------- parsing


def parse_frontmatter(text: str) -> tuple[dict, str]:
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return {}, text
    try:
        end = next(i for i in range(1, len(lines)) if lines[i].strip() == "---")
    except StopIteration:
        return {}, text
    data = {}
    for line in lines[1:end]:
        if ":" in line and not line.lstrip().startswith("#"):
            key, _, value = line.partition(":")
            data[key.strip()] = value.strip()
    return data, "\n".join(lines[end + 1:])


def table_rows(text: str) -> list[list[str]]:
    """Body rows of every markdown table in text: header and separator rows dropped."""
    rows, header_seen = [], False
    for line in text.splitlines():
        s = line.strip()
        if not s.startswith("|"):
            header_seen = False
            continue
        cells = [c.strip() for c in s.strip("|").split("|")]
        if all(re.fullmatch(r":?-{3,}:?", c) for c in cells if c):
            continue
        if not header_seen:
            header_seen = True
            continue
        rows.append(cells)
    return rows


def brief_section(body: str, heading: str) -> str | None:
    """Text under a `## ` heading up to the next one, or None when the heading is missing."""
    if heading not in body:
        return None
    return re.split(r"(?m)^## ", body.split(heading, 1)[1], maxsplit=1)[0]


def outline_table(report: Path) -> str | None:
    """The Outline table lines, normalized; what an approval is a hash of."""
    _fields, body = parse_frontmatter(read(report / BRIEF))
    section = brief_section(body, OUTLINE_HEADING)
    if section is None:
        return None
    return "\n".join(line.strip() for line in section.splitlines() if line.strip().startswith("|"))


def parse_outline(report: Path) -> tuple[list[dict], list[str]]:
    path = report / BRIEF
    _fields, body = parse_frontmatter(read(path))
    section = brief_section(body, OUTLINE_HEADING)
    if section is None:
        return [], [f"{path}: no '{OUTLINE_HEADING}' heading"]
    rows, findings = [], []
    for cells in table_rows(section):
        if len(cells) < len(OUTLINE_COLUMNS):
            findings.append(f"{path}: outline row needs {' | '.join(OUTLINE_COLUMNS)}: {' | '.join(cells)}")
            continue
        rows.append(dict(zip(OUTLINE_COLUMNS, cells)))
    return rows, findings


def parse_brief(report: Path) -> tuple[dict, list[dict], list[str]]:
    """(fields, sources, findings). A missing Sources heading is a finding, not an empty list."""
    path = report / BRIEF
    text = read(path)
    fields, body = parse_frontmatter(text)
    findings = []
    if not fields:
        return {}, [], [f"{path}: no frontmatter"]
    section = brief_section(body, SOURCES_HEADING)
    if section is None:
        findings.append(f"{path}: no '{SOURCES_HEADING}' heading")
        return fields, [], findings
    sources = []
    for cells in table_rows(section):
        if len(cells) < 3:
            findings.append(f"{path}: sources row needs id | path | scope: {' | '.join(cells)}")
            continue
        sources.append({"id": cells[0], "path": cells[1], "scope": cells[2]})
    return fields, sources, findings


def parse_claims(report: Path) -> tuple[list[dict], list[str]]:
    path = report / CLAIMS
    claims, findings = [], []
    for cells in table_rows(read(path)):
        if len(cells) < 4:
            findings.append(f"{path}: claims row needs id | claim | source | lines: {' | '.join(cells)}")
            continue
        claims.append({"id": cells[0], "claim": cells[1], "source": cells[2], "lines": cells[3]})
    return claims, findings


def load_registry(report: Path | None = None) -> dict:
    js = (report / SRC / COMPONENTS_JS) if report else (STATIC_ASSETS / "components.js")
    text = read(js)
    if REGISTRY_BEGIN not in text or REGISTRY_END not in text:
        raise UsageError(f"{js}: registry markers missing; components.js and visual_report.py are out of step")
    block = text.split(REGISTRY_BEGIN, 1)[1].split(REGISTRY_END, 1)[0].strip()
    if not block.startswith(REGISTRY_ASSIGN):
        raise UsageError(f"{js}: registry block does not start with '{REGISTRY_ASSIGN}'")
    block = block[len(REGISTRY_ASSIGN):].strip().rstrip(";")
    try:
        return json.loads(block)
    except json.JSONDecodeError as e:
        raise UsageError(f"{js}: registry is not valid JSON: {e}") from e


# --------------------------------------------------------------------------- checks


def check_brief(report: Path) -> tuple[dict, list[dict], list[str]]:
    path = report / BRIEF
    if not path.is_file():
        return {}, [], [f"{path} is missing; run new"]
    fields, sources, findings = parse_brief(report)
    # The outline has its own step; its placeholders are reported by check_outline.
    text = read(path)
    if OUTLINE_HEADING in text:
        text = text.split(OUTLINE_HEADING, 1)[0]
    for ph in placeholders(text):
        findings.append(f"{path}: placeholder left: {ph}")
    for key in BRIEF_FIELDS:
        if not fields.get(key):
            findings.append(f"{path}: field '{key}' is empty")
    if fields.get("export") and fields["export"] not in EXPORTS:
        findings.append(f"{path}: export is {fields['export']!r}, expected one of {sorted(EXPORTS)}")
    if fields.get("depth") and fields["depth"] not in DEPTHS:
        findings.append(f"{path}: depth is {fields['depth']!r}, expected one of {list(DEPTHS)}")
    if fields.get("type") and fields["type"] not in report_types():
        findings.append(f"{path}: type is {fields['type']!r}, expected one of {report_types()}")
    theme = fields.get("theme")
    if theme and not (report / SRC / THEMES / f"{theme}.css").is_file():
        findings.append(f"{path}: theme {theme!r} has no file {SRC}/{THEMES}/{theme}.css")
    if not sources:
        findings.append(f"{path}: no sources")
    seen = set()
    for s in sources:
        if s["id"] in seen:
            findings.append(f"{path}: duplicate source id {s['id']!r}")
        seen.add(s["id"])
        if s["scope"] not in SCOPES:
            findings.append(f"{path}: source {s['id']} scope is {s['scope']!r}, expected one of {sorted(SCOPES)}")
    return fields, sources, findings


def report_types() -> list[str]:
    return sorted(p.stem for p in OUTLINE_ASSETS.glob("*.md"))


def depth_of(fields: dict) -> dict:
    return DEPTHS.get(fields.get("depth", ""), DEPTHS["standard"])


def check_outline(report: Path, fields: dict) -> tuple[list[dict], list[str], bool]:
    """(rows, findings about the table itself, approved?). Approval is reported by the caller."""
    rows, findings = parse_outline(report)
    _f, body = parse_frontmatter(read(report / BRIEF))
    section = brief_section(body, OUTLINE_HEADING) or ""
    for ph in placeholders(section):
        findings.append(f"{BRIEF} outline: placeholder left: {ph}")
    if not rows and not findings:
        findings.append(f"{BRIEF} outline: no rows")
    for i, r in enumerate(rows):
        where = f"{BRIEF} outline row {r['n']}"
        if r["part"] not in PARTS:
            findings.append(f"{where}: part {r['part']!r}, expected one of {list(PARTS)}")
        if (i == 0) != (r["part"] == SUMMARY_PART):
            findings.append(f"{where}: the summary is row 1 and only row 1 (part {SUMMARY_PART!r})")
        if not r["proves"].strip("{} "):
            findings.append(f"{where}: 'proves' is empty; say what the visual proves about the title")
        if len(r["title"].split()) > MAX_TITLE_WORDS:
            findings.append(f"{where}: title has {len(r['title'].split())} words, max {MAX_TITLE_WORDS}")
    parts = {r["part"] for r in rows}
    for need in depth_of(fields)["required_parts"]:
        if need not in parts:
            findings.append(f"{BRIEF} outline: depth {fields.get('depth')} needs a {need!r} row")
    titles = [r["title"] for r in rows]
    for t in sorted({t for t in titles if titles.count(t) > 1}):
        findings.append(f"{BRIEF} outline: duplicate title {t!r}")
    table = outline_table(report)
    approved = bool(table) and fields.get("outline") == hashlib.sha256(table.encode("utf-8")).hexdigest()
    return rows, findings, approved


def source_file(report: Path, source: dict) -> Path:
    p = Path(source["path"])
    return p if p.is_absolute() else report / p


def check_sources(report: Path, sources: list[dict]) -> list[str]:
    findings = []
    for s in sources:
        if CURLY.search(s["path"]):
            continue  # already reported as a placeholder
        if not source_file(report, s).is_file():
            findings.append(f"{BRIEF}: source {s['id']} path {s['path']!r} does not exist "
                            f"(save chat-only data under {SOURCES}/ first)")
    return findings


def check_claims(report: Path, sources: list[dict]) -> list[str]:
    path = report / CLAIMS
    if not path.is_file():
        return [f"{path} is missing"]
    claims, findings = parse_claims(report)
    for ph in placeholders(read(path)):
        findings.append(f"{path}: placeholder left: {ph}")
    if not claims:
        findings.append(f"{path}: no claims")
    by_id = {s["id"]: s for s in sources}
    seen = set()
    for c in claims:
        where = f"{path}: claim {c['id']}"
        if c["id"] in seen:
            findings.append(f"{where}: duplicate id")
        seen.add(c["id"])
        src = by_id.get(c["source"])
        if src is None:
            if not CURLY.search(c["source"]):
                findings.append(f"{where}: source {c['source']!r} is not in {BRIEF}")
            continue
        if src["scope"] == "out":
            findings.append(f"{where}: cites {c['source']}, which is scope 'out' (another variant)")
        if CURLY.search(c["lines"]):
            continue
        if not LINES.match(c["lines"].replace(" ", "")):
            findings.append(f"{where}: lines {c['lines']!r} is not like 12, 12-14 or 12-14,30")
            continue
        f = source_file(report, src)
        if not f.is_file():
            continue  # reported by check_sources
        count = len(f.read_text(encoding="utf-8", errors="replace").splitlines())
        for part in c["lines"].replace(" ", "").split(","):
            lo, _, hi = part.partition("-")
            if not (1 <= int(lo) <= int(hi or lo) <= count):
                findings.append(f"{where}: lines {part} outside {src['path']} (1-{count})")
    return findings


VOID = {"br", "meta", "link", "img", "hr", "input", "wbr"}
HEAD_TAGS = {"meta", "title", "link", "script"}


class SrcParser(html.parser.HTMLParser):
    """Checks src/report.html against the registry. Fixed format only: tag and attribute names."""

    def __init__(self, registry: dict):
        super().__init__(convert_charrefs=True)
        self.reg = registry
        self.elements = registry["elements"]
        self.inline = set(registry["inline"])
        self.inline_attrs = registry.get("inline_attrs", {})
        self.enums = registry.get("enums", {})
        self.stack: list[str] = []
        self.findings: list[str] = []
        self.ids: set[str] = set()
        self.srcs: list[tuple[str, str]] = []
        self.lang = None
        self.prose: list[dict] = []  # {"tag", "id", "words"}
        self.sections: list[dict] = []  # {"title", "part", "line"}
        self.highlights: list[dict] = []  # {"src", "column", "map", "mono", "line"}
        self.top: list[str] = []  # top-level element tags in order
        self.summary_lines: list[str] = []  # r-line kinds in order
        self.in_script = False

    def where(self) -> str:
        return f"line {self.getpos()[0]}"

    def flag(self, msg: str) -> None:
        self.findings.append(f"{SRC}/{REPORT_HTML} {self.where()}: {msg}")

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        parent = self.stack[-1] if self.stack else None
        if tag == "html":
            self.lang = a.get("lang")
        elif tag in ("head", "body"):
            pass
        elif "head" in self.stack:
            self.head_tag(tag, a)
        elif tag in self.elements:
            self.component(tag, a, parent)
        elif tag in self.inline:
            if not any(self.elements.get(t, {}).get("prose") for t in self.stack):
                self.flag(f"<{tag}> outside a prose element (r-text, r-callout, r-item)")
            allowed = set(self.inline_attrs.get(tag, []))
            for k in a:
                if k not in allowed:
                    self.flag(f"<{tag}> attribute {k!r} is not allowed")
        else:
            self.flag(f"<{tag}> is not allowed; use an r-* element (see `visual_report.py components`)")
        if tag not in VOID:
            self.stack.append(tag)

    def handle_startendtag(self, tag, attrs):
        self.handle_starttag(tag, attrs)
        if tag not in VOID and self.stack and self.stack[-1] == tag:
            self.stack.pop()

    def head_tag(self, tag, a):
        if tag not in HEAD_TAGS:
            self.flag(f"<{tag}> is not allowed in <head>")
        elif tag == "script":
            if not a.get("src", "").startswith(f"{STATIC}/"):
                self.flag("inline <script> or a script outside static/ is not allowed")
            self.in_script = True
        elif tag == "link" and not (a.get("rel") == "stylesheet" and a.get("href", "").startswith(f"{STATIC}/")):
            self.flag("only stylesheets from static/ may be linked")

    def component(self, tag, a, parent):
        spec = self.elements[tag]
        if spec.get("top") and parent != "body":
            self.flag(f"<{tag}> belongs directly in <body>")
        if not spec.get("top") and parent == "body":
            self.flag(f"<{tag}> must be inside an r-section")
        if spec.get("parent") and parent != spec["parent"]:
            self.flag(f"<{tag}> must be directly inside <{spec['parent']}>")
        allowed = set(spec["required"]) | set(spec["optional"]) | {"id"}
        for k in a:
            if k not in allowed:
                self.flag(f"<{tag}> attribute {k!r} is not allowed")
        for k in spec["required"]:
            if not a.get(k):
                self.flag(f"<{tag}> needs attribute {k!r}")
        for key, values in self.enums.items():
            t, _, attr = key.partition(".")
            if t == tag and a.get(attr) and a[attr] not in values:
                self.flag(f"<{tag}> {attr}={a[attr]!r}, expected one of {values}")
        if "id" in a:
            if a["id"] in self.ids:
                self.flag(f"duplicate id {a['id']!r}")
            self.ids.add(a["id"])
        if tag == "r-grid" and a.get("cols"):
            if not a["cols"].isdigit() or not 1 <= int(a["cols"]) <= MAX_GRID_COLS:
                self.flag(f"<r-grid> cols={a['cols']!r}, expected 1..{MAX_GRID_COLS}")
        if tag == "r-chart" and a.get("height"):
            h = a["height"]
            if not h.isdigit() or not MIN_CHART_HEIGHT_PX <= int(h) <= MAX_VISUAL_HEIGHT_PX:
                self.flag(f"<r-chart> height={h!r}, expected {MIN_CHART_HEIGHT_PX}..{MAX_VISUAL_HEIGHT_PX}")
        if tag in SRC_RULES and a.get("src") and not CURLY.search(a["src"]):
            prefix, suffix = SRC_RULES[tag]
            if not (a["src"].startswith(prefix) and a["src"].endswith(suffix)):
                self.flag(f"<{tag}> src={a['src']!r}, expected {prefix}*{suffix}")
            self.srcs.append((tag, a["src"]))
        if spec.get("prose"):
            self.prose.append({"tag": tag, "id": a.get("id", ""), "line": self.getpos()[0],
                               "words": 0, "depth": len(self.stack)})
        if parent == "body":
            self.top.append(tag)
        if tag in ("r-section", "r-summary"):
            part = SUMMARY_PART if tag == "r-summary" else a.get("part", DEFAULT_PART)
            self.sections.append({"title": a.get("title", ""), "part": part, "line": self.getpos()[0]})
            words = len(a.get("title", "").split())
            if words > MAX_TITLE_WORDS:
                self.flag(f"<{tag}> title has {words} words, max {MAX_TITLE_WORDS}; state the answer in one line")
        if tag == "r-line":
            self.summary_lines.append(a.get("kind", ""))
        if tag == "r-kpi" and len(a.get("label", "").split()) > MAX_KPI_LABEL_WORDS:
            self.flag(f"<r-kpi> label has {len(a['label'].split())} words, max {MAX_KPI_LABEL_WORDS}")
        if tag == "r-table" and ("highlight" in a or "highlight-map" in a or "mono" in a):
            self.highlights.append({"src": a.get("src", ""), "column": a.get("highlight"),
                                    "map": a.get("highlight-map"), "mono": a.get("mono"),
                                    "line": self.getpos()[0]})

    def handle_endtag(self, tag):
        if tag == "script":
            self.in_script = False
        if tag in VOID:
            return
        if tag in self.stack:
            while self.stack and self.stack.pop() != tag:
                pass

    def handle_data(self, data):
        if self.in_script:
            if data.strip():
                self.flag("inline <script> content is not allowed")
            return
        if not data.strip() or "head" in self.stack or not self.stack:
            return
        owner = None
        for i, t in enumerate(self.stack):
            if self.elements.get(t, {}).get("prose"):
                owner = next((p for p in reversed(self.prose) if p["depth"] == i), None)
                break
        if owner is None:
            if self.stack[-1] not in ("title",):
                self.flag(f"text outside a prose element: {' '.join(data.split())[:40]!r}")
            return
        owner["words"] += len(data.split())


def check_src(report: Path, fields: dict) -> tuple[list[str], list[tuple[str, str]]]:
    path = report / SRC / REPORT_HTML
    if not path.is_file():
        return [f"{path} is missing"], []
    text = read(path)
    findings = [f"{path}: placeholder left: {ph}" for ph in placeholders(text)]
    p = SrcParser(load_registry(report))
    p.feed(text)
    p.close()
    findings += p.findings
    if fields.get("language") and p.lang != fields["language"]:
        findings.append(f"{path}: <html lang={p.lang!r}> differs from brief language {fields['language']!r}")
    limit = depth_of(fields)["words"]
    for block in p.prose:
        if block["words"] > limit:
            name = block["id"] or f"{block['tag']} at line {block['line']}"
            findings.append(f"{path}: {name} has {block['words']} words, max {limit} at depth "
                            f"{fields.get('depth')}; cut it or turn it into a table, list or visual")
    findings += check_order(fields, p.top, p.summary_lines, p.reg)
    findings += match_outline(report, p.sections)
    findings += check_highlights(report, p.highlights, p.reg)
    findings += check_diagram_classes(report, p.reg)
    findings += check_label_classes(report, p.reg)
    return findings, p.srcs


def check_order(fields: dict, top: list[str], lines: list[str], registry: dict) -> list[str]:
    """The answer first: r-cover, then r-summary with what / meaning / action, then r-toc when
    the depth needs one, then the sections."""
    path, findings = f"{SRC}/{REPORT_HTML}", []
    body = [t for t in top if t != "r-cover"]
    if not body or body[0] != "r-summary":
        findings.append(f"{path}: the first section must be <r-summary> (the answer first)")
    if top.count("r-summary") > 1:
        findings.append(f"{path}: only one <r-summary>")
    kinds = registry.get("enums", {}).get("r-line.kind", [])
    if sorted(lines) != sorted(kinds):
        findings.append(f"{path}: <r-summary> needs exactly one r-line of each kind {kinds}, has {lines}")
    needs_toc = fields.get("depth") in TOC_DEPTHS
    if needs_toc and (len(body) < 2 or body[1] != "r-toc"):
        findings.append(f"{path}: depth {fields.get('depth')} needs <r-toc> right after <r-summary>")
    if top.count("r-toc") > 1:
        findings.append(f"{path}: only one <r-toc>")
    return findings


def check_highlights(report: Path, highlights: list[dict], registry: dict) -> list[str]:
    """highlight names a CSV header; highlight-map is value:state pairs with known states."""
    states = set(registry.get("row_states", []))
    path, findings = f"{SRC}/{REPORT_HTML}", []
    for h in highlights:
        where = f"{path} line {h['line']}: <r-table src={h['src']!r}>"
        f = report / SRC / h["src"]
        header = [c.strip() for c in next(csv.reader(io.StringIO(read(f))), [])] if f.is_file() else None
        for col in [c.strip() for c in (h.get("mono") or "").split(",") if c.strip()]:
            if header is not None and col not in header:
                findings.append(f"{where}: mono column {col!r} is not a header of {h['src']}")
        if h["column"] is None and h["map"] is None:
            continue
        if not h["column"] or not h["map"]:
            findings.append(f"{where}: highlight and highlight-map go together")
            continue
        for pair in h["map"].split(","):
            value, sep, state = (x.strip() for x in pair.partition(":"))
            if not sep or not value:
                findings.append(f"{where}: highlight-map entry {pair.strip()!r} is not value:state")
            elif state not in states:
                findings.append(f"{where}: highlight-map state {state!r}, expected one of {sorted(states)}")
        if header is not None and h["column"] not in header:
            findings.append(f"{where}: highlight column {h['column']!r} is not a header of {h['src']}")
    return findings


MMD_CLASS_USE = re.compile(r":::([A-Za-z0-9_-]+)")
MMD_CLASS_STMT = re.compile(r"^\s*class\s+\S+\s+([A-Za-z0-9_-]+)\s*;?\s*$")
MMD_CLASSDEF = re.compile(r"^\s*classDef\s")


def check_diagram_classes(report: Path, registry: dict) -> list[str]:
    """Classes in flowchart and state diagrams must be the semantic set the theme defines.

    Other diagram types are skipped: in a classDiagram `class Name` declares a class, so the
    same syntax means something else there.
    """
    known = set(registry.get("semantic_classes", []))
    kinds = set(registry.get("class_diagrams", []))
    findings = []
    for f in sorted((report / SRC / "diagrams").glob("*.mmd")):
        lines = read(f).splitlines()
        head = next((l.strip() for l in lines if l.strip() and not l.strip().startswith("%%") and l.strip() != "---"), "")
        if (head.split() or [""])[0] not in kinds:
            continue
        for n, line in enumerate(lines, 1):
            if line.strip().startswith("%%"):
                continue
            where = f"{SRC}/diagrams/{f.name}:{n}"
            if MMD_CLASSDEF.match(line):
                findings.append(f"{where}: own classDef is not allowed; use a semantic class ({', '.join(sorted(known))})")
                continue
            used = MMD_CLASS_USE.findall(line)
            m = MMD_CLASS_STMT.match(line)
            if m:
                used.append(m.group(1))
            for name in used:
                if name not in known:
                    findings.append(f"{where}: class {name!r} is unknown; use one of {', '.join(sorted(known))}")
    return findings


# A node defined with a label: ID["label"], ID[label], ID(label), ID((label)), ID{label}, … with an
# optional :::class. Labels that themselves contain brackets do not match and are skipped.
MMD_NODE = re.compile(
    r"(?<![\w-])([A-Za-z_][\w-]*)\s*"
    r"(?:\[\[|\[\(|\(\(\(|\(\(|\(\[|\[/|\[\\|\[|\(|\{\{|\{|>)"
    r"\s*\"?([^\"\[\]\(\)\{\}]+?)\"?\s*"
    r"(?:\]\]|\)\]|\)\)\)|\)\)|\]\)|/\]|\\\]|\]|\)|\}\}|\})"
    r"(?::::([A-Za-z0-9_-]+))?")
MMD_CLASS_ASSIGN = re.compile(r"^\s*class\s+([\w,-]+)\s+([A-Za-z0-9_-]+)\s*;?\s*$")


def check_label_classes(report: Path, registry: dict) -> list[str]:
    """One entity, one colour: a node label written the same way in several flowcharts must
    carry the same class (or none) in all of them. Labels are compared as written, with <br/>
    and extra spaces removed; state diagrams and other types are skipped."""
    seen: dict[str, dict[str, list[str]]] = {}  # label -> class -> [file, ...]
    for f in sorted((report / SRC / "diagrams").glob("*.mmd")):
        lines = read(f).splitlines()
        head = next((l.strip() for l in lines if l.strip() and not l.strip().startswith("%%") and l.strip() != "---"), "")
        if (head.split() or [""])[0] not in ("flowchart", "graph"):
            continue
        labels, classes = {}, {}
        for line in lines:
            if line.strip().startswith("%%"):
                continue
            m = MMD_CLASS_ASSIGN.match(line)
            if m:
                for node in m.group(1).split(","):
                    classes[node] = m.group(2)
                continue
            for node, label, cls in MMD_NODE.findall(line):
                labels.setdefault(node, " ".join(re.sub(r"<br\s*/?>", " ", label).split()))
                if cls:
                    classes[node] = cls
        for node, label in labels.items():
            if label:
                seen.setdefault(label, {}).setdefault(classes.get(node, "none"), []).append(f.name)
    findings = []
    for label, by_class in sorted(seen.items()):
        if len(by_class) > 1:
            parts = "; ".join(f"{c} in {', '.join(sorted(set(fs)))}" for c, fs in sorted(by_class.items()))
            findings.append(f"{SRC}/diagrams: {label!r} has different classes ({parts}); one entity, one colour")
    return findings


def match_outline(report: Path, sections: list[dict]) -> list[str]:
    """src sections must be the approved outline rows: same order, title and part."""
    rows, _findings = parse_outline(report)
    if not rows:
        return []  # reported by check_outline
    path = f"{SRC}/{REPORT_HTML}"
    findings = []
    for i in range(max(len(rows), len(sections))):
        row = rows[i] if i < len(rows) else None
        sec = sections[i] if i < len(sections) else None
        if row is None:
            findings.append(f"{path} line {sec['line']}: section {sec['title']!r} is not in the outline; "
                            "add it to the outline and get it approved, or remove it")
        elif sec is None:
            findings.append(f"{path}: outline row {row['n']} {row['title']!r} has no r-section")
        elif (sec["title"], sec["part"]) != (row["title"], row["part"]):
            findings.append(f"{path} line {sec['line']}: section {i + 1} is {sec['title']!r} ({sec['part']}), "
                            f"outline row {row['n']} is {row['title']!r} ({row['part']})")
    return findings


def check_data(report: Path, srcs: list[tuple[str, str]]) -> list[str]:
    findings, used = [], {s for _, s in srcs}
    for tag, s in srcs:
        derived = s.startswith("charts/") and (report / DERIVE / f"{Path(s).stem}.py").is_file()
        if not (report / SRC / s).is_file() and not derived:
            findings.append(f"<{tag}> src={s!r}: {SRC}/{s} does not exist")
    for d in DATA_DIRS:
        for f in sorted((report / SRC / d).glob("*")):
            rel = f"{d}/{f.name}"
            if f.is_file() and rel not in used:
                findings.append(f"{SRC}/{rel} is not used by any element; use it or delete it")
    return findings


def _as_list(x) -> list:
    return x if isinstance(x, list) else [x] if isinstance(x, dict) else []


def check_charts(report: Path) -> list[str]:
    findings = []
    for f in sorted((report / SRC / "charts").glob("*.json")):
        where = f"{SRC}/charts/{f.name}"
        try:
            option = json.loads(read(f))
        except json.JSONDecodeError as e:
            findings.append(f"{where}: not valid JSON: {e}")
            continue
        if not isinstance(option, dict):
            findings.append(f"{where}: top level must be an ECharts option object")
            continue
        series = _as_list(option.get("series"))
        if len(series) > MAX_SERIES:
            findings.append(f"{where}: {len(series)} series, max {MAX_SERIES}")
        for s in series:
            if isinstance(s, dict) and s.get("type") == "pie" and len(_as_list_data(s)) > MAX_PIE_SLICES:
                findings.append(f"{where}: pie with {len(_as_list_data(s))} slices, max {MAX_PIE_SLICES}; "
                                "group the small ones into 'Other'")
        for axis_key in ("xAxis", "yAxis"):
            for axis in _as_list(option.get(axis_key)):
                if isinstance(axis, dict) and axis.get("type", "category") == "category":
                    data = axis.get("data")
                    if isinstance(data, list) and len(data) > MAX_CATEGORIES:
                        findings.append(f"{where}: {axis_key} has {len(data)} categories, max {MAX_CATEGORIES}")
    return findings


def _as_list_data(series: dict) -> list:
    d = series.get("data")
    return d if isinstance(d, list) else []


def check_dist(report: Path, sources: list[dict]) -> tuple[list[str], list[str]]:
    """(findings, notes) about dist: freshness, render errors, legibility, leaked paths."""
    paths = dist_paths(report)
    if not paths["min"].is_file() or not paths["build"].is_file():
        return [f"{DIST}/ has no build; run build"], []
    findings, notes = [], []
    newest = newest_input(report)
    if newest and newest[0] > paths["min"].stat().st_mtime:
        findings.append(f"{paths['min'].name} is older than {newest[1]}; run build")
    build = json.loads(read(paths["build"]))
    for e in build.get("errors", []):
        findings.append(f"render error in {e.get('element')} ({e.get('src', '')}): {e.get('error')}")
    if "full" not in build:
        findings.append(f"{BUILD_JSON} has no full.html render check (built by an older script); run build")
    findings += build.get("full", [])
    for m in build.get("metrics", []):
        name = f"{m['element']} ({m.get('src')})"
        if not m.get("measured"):
            notes.append(f"{name}: could not be measured; legibility skipped")
            continue
        if m["min_text_px"] is not None and m["min_text_px"] < MIN_TEXT_PX:
            findings.append(f"{name}: smallest text is {m['min_text_px']}px at page width, min {MIN_TEXT_PX}px; "
                            "fewer nodes per row or split it (references/legibility.md)")
        if m["height"] > MAX_VISUAL_HEIGHT_PX:
            findings.append(f"{name}: {m['height']}px tall, max {MAX_VISUAL_HEIGHT_PX}px; "
                            "fewer nodes per column or split it (references/legibility.md)")
        if m["tag"] == "r-diagram":
            if m.get("parts") is None:
                notes.append(f"{name}: connectivity not checked (not a flowchart, or graph not exposed)")
            elif m["parts"] > 1:
                findings.append(f"{name}: {m['parts']} disconnected parts; join them into one flow "
                                "(references/legibility.md)")
    needles = {f"{SOURCES}/"}
    for s in sources:
        if not CURLY.search(s["path"]):
            needles |= {s["path"], s["path"].replace("/", "\\")}
    for key in ("min", "full"):
        if not paths[key].is_file():
            findings.append(f"{paths[key].name} is missing; run build")
            continue
        text = read(paths[key])
        # Inlined libraries are not report content; data blocks are.
        text = SCRIPT_BLOCK.sub(lambda m: m.group(0) if "data-path" in m.group(0)[:200] else "", text)
        for n in sorted(needles):
            if n and n in text:
                findings.append(f"{paths[key].name} contains the source path {n!r}; dist must not refer to src")
    return findings, notes


def newest_input(report: Path) -> tuple[float, str] | None:
    """Newest file that build reads, excluding what build itself writes."""
    best = None
    theme_css = (report / SRC / THEME_CSS).resolve()
    charts = (report / SRC / "charts").resolve()
    for base in (report / SRC, report / DERIVE):
        if not base.is_dir():
            continue
        for f in base.rglob("*"):
            if not f.is_file() or f.resolve() == theme_css:
                continue
            if f.parent.resolve() == charts and (report / DERIVE / f"{f.stem}.py").is_file():
                continue  # written by build from its derivation
            t = f.stat().st_mtime
            if best is None or t > best[0]:
                best = (t, f.relative_to(report).as_posix())
    return best


def collect(report: Path, with_dist: bool = True) -> tuple[list[str], list[str]]:
    """Every finding and note, in chain order. Shared by check, build and status."""
    fields, sources, findings = check_brief(report)
    if not fields and not (report / BRIEF).is_file():
        return findings, []
    findings += check_sources(report, sources)
    _rows, outline_findings, approved = check_outline(report, fields)
    findings += outline_findings
    if not approved:
        findings.append(f"{BRIEF} outline is not approved (or changed after approval); "
                        "show it to the user, and run outline-approved only after their explicit approve")
    findings += check_claims(report, sources)
    src_findings, srcs = check_src(report, fields)
    findings += src_findings + check_data(report, srcs) + check_charts(report)
    notes = []
    lang = (fields.get("language") or "").split("-")[0]
    if lang and (report / SRC / COMPONENTS_JS).is_file() and lang not in load_registry(report).get("labels", {}):
        notes.append(f"no UI labels for language {lang!r} in {COMPONENTS_JS}; English labels are used "
                     "(Appendix, Contents, legend); add a labels entry for it")
    if with_dist:
        dist_findings, notes = check_dist(report, sources)
        findings += dist_findings
    return findings, notes


# --------------------------------------------------------------------------- browser


def find_browser() -> str:
    env = os.environ.get(BROWSER_ENV)
    if env:
        if Path(env).is_file():
            return env
        raise UsageError(f"{BROWSER_ENV}={env!r} does not exist")
    candidates = []
    if sys.platform == "win32":
        for var, rel in WINDOWS_BROWSERS:
            base = os.environ.get(var)
            if base:
                candidates.append(str(Path(base) / rel))
    elif sys.platform == "darwin":
        candidates += MAC_BROWSERS
    for c in candidates:
        if Path(c).is_file():
            return c
    for name in PATH_BROWSERS:
        found = shutil.which(name)
        if found:
            return found
    raise UsageError(f"no Chrome, Edge or Chromium found; install one or set {BROWSER_ENV} to its path")


def browser_args(browser: str, profile: str) -> list[str]:
    args = [browser, "--headless", "--disable-gpu", "--no-first-run", "--no-default-browser-check",
            "--hide-scrollbars", f"--window-size={WINDOW_SIZE}", f"--user-data-dir={profile}"]
    if sys.platform.startswith("linux") and hasattr(os, "geteuid") and os.geteuid() == 0:
        args.append("--no-sandbox")  # Chromium refuses to start as root with its sandbox on
    return args


def stop(proc: subprocess.Popen) -> None:
    if proc.poll() is None:
        proc.terminate()
        try:
            proc.wait(10)
        except subprocess.TimeoutExpired:
            proc.kill()


# --------------------------------------------------------------------------- build


def run_derivations(report: Path) -> None:
    for script in sorted((report / DERIVE).glob("*.py")):
        r = subprocess.run([sys.executable, "-I", str(script)], cwd=report, capture_output=True,
                           text=True, encoding="utf-8", timeout=PROCESS_TIMEOUT_S)
        if r.returncode != 0:
            raise UsageError(f"{DERIVE}/{script.name} failed:\n{r.stderr.strip()}")
        try:
            data = json.loads(r.stdout)
        except json.JSONDecodeError as e:
            raise UsageError(f"{DERIVE}/{script.name} must print one JSON ECharts option: {e}") from e
        write(report / SRC / "charts" / f"{script.stem}.json", json.dumps(data, indent=2, ensure_ascii=False))


def apply_theme(report: Path, theme: str) -> None:
    src = report / SRC / THEMES / f"{theme}.css"
    if not src.is_file():
        raise UsageError(f"theme {theme!r}: {src} does not exist")
    shutil.copyfile(src, report / SRC / THEME_CSS)


def render(directory: Path, page: str, browser: str) -> dict:
    """Open directory/page headless through a local server; return what the page posts back."""
    got: dict = {}
    done = threading.Event()

    class Handler(http.server.SimpleHTTPRequestHandler):
        def log_message(self, *args):
            pass

        def do_POST(self):
            if self.path != DONE_PATH:
                self.send_response(404)
                self.end_headers()
                return
            n = int(self.headers.get("Content-Length", "0"))
            got.update(json.loads(self.rfile.read(n).decode("utf-8")))
            self.send_response(204)
            self.end_headers()
            done.set()

    server = http.server.ThreadingHTTPServer(("127.0.0.1", 0),
                                             functools.partial(Handler, directory=str(directory)))
    threading.Thread(target=server.serve_forever, daemon=True).start()
    profile = tempfile.mkdtemp(prefix="visual-report-")
    url = f"http://127.0.0.1:{server.server_address[1]}/{page}?{RENDER_QUERY}"
    proc = subprocess.Popen(browser_args(browser, profile) + [url],
                            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    try:
        if not done.wait(RENDER_TIMEOUT_S):
            raise UsageError(f"{page} did not report back within {RENDER_TIMEOUT_S}s; "
                             "open it through a local server and read the console")
    finally:
        stop(proc)
        server.shutdown()
        shutil.rmtree(profile, ignore_errors=True)
    return got


def inline_css(css_path: Path) -> str:
    """The stylesheet with local url(...) fonts and images turned into data URIs."""
    text = read(css_path)

    def repl(m):
        target = (css_path.parent / m.group(2)).resolve()
        if not target.is_file():
            return m.group(0)
        mime = FONT_MIME.get(target.suffix.lower(), "application/octet-stream")
        return f"url(data:{mime};base64,{base64.b64encode(target.read_bytes()).decode('ascii')})"

    return CSS_URL.sub(repl, text)


def safe_in_script(text: str) -> str:
    """Text that cannot close the <script> element it is inlined into."""
    return CLOSE_SCRIPT.sub(r"<\\/\1", text)


def inline_styles(html_text: str, base: Path) -> str:
    def repl(m):
        path = base / m.group(1)
        if not path.is_file():
            raise UsageError(f"stylesheet {m.group(1)} not found under {base}")
        return f"<style>\n{inline_css(path)}\n</style>"

    return STYLESHEET.sub(repl, html_text)


def write_min(report: Path, dom: str) -> None:
    text = SCRIPT_BLOCK.sub("", dom)
    text = inline_styles(text, report / SRC)
    write(dist_paths(report)["min"], text)


def write_full(report: Path, srcs: list[tuple[str, str]]) -> None:
    base = report / SRC
    text = inline_styles(read(base / REPORT_HTML), base)
    blocks = []
    for _, s in sorted(set(srcs)):
        f = base / s
        if not f.is_file():
            continue
        raw = read(f)
        value = json.loads(raw) if f.suffix == ".json" else raw
        payload = json.dumps(value, ensure_ascii=False).replace("</", "<\\/")  # "<\/" is valid JSON
        blocks.append(f'<script type="application/json" data-path="{s}">{payload}</script>')
    data = "\n".join(blocks)

    def repl(m):
        path = base / m.group(1)
        if not path.is_file():
            raise UsageError(f"script {m.group(1)} not found under {base}")
        return f"<script>\n{safe_in_script(read(path))}\n</script>"

    # Data goes in before the libraries are inlined: mermaid's own code contains "</head>", and a
    # data block inserted there cut the library in two and printed its tail as page text.
    text, n = HEAD_END.subn(lambda m: f"{data}\n{m.group(0)}", text, count=1)
    if n != 1:
        raise UsageError(f"{SRC}/{REPORT_HTML} has no </head>")
    text = SCRIPT_SRC.sub(repl, text)
    write(dist_paths(report)["full"], text)


def full_check(src_result: dict, full_result: dict) -> list[str]:
    """Findings from rendering the .full.html: it must match the src render."""
    name = "full.html"
    if "dom" not in full_result:
        return [f"{name} reported back without a DOM"]
    findings = [f"{name}: render error in {e.get('element')}: {e.get('error')}" for e in full_result.get("errors", [])]
    n_src, n_full = len(src_result.get("metrics", [])), len(full_result.get("metrics", []))
    if n_src != n_full:
        findings.append(f"{name} draws {n_full} visual(s), src draws {n_src}")
    a, b = src_result.get("text", ""), full_result.get("text", "")
    if a != b:
        i = next((k for k in range(min(len(a), len(b))) if a[k] != b[k]), min(len(a), len(b)))
        findings.append(f"{name} page text differs from src at char {i}: {b[i:i + 60]!r} "
                        f"(lengths {len(b)} vs {len(a)})")
    return findings


def cmd_build(args) -> int:
    report = Path(args.report)
    fields, sources, brief_findings = check_brief(report)
    if not fields:
        return report_findings(brief_findings)
    browser = find_browser()
    run_derivations(report)
    apply_theme(report, fields.get("theme", ""))
    _src_findings, srcs = check_src(report, fields)
    result = render(report / SRC, REPORT_HTML, browser)
    if "dom" not in result:
        raise UsageError("the page reported back without a DOM")
    write_min(report, result["dom"])
    write_full(report, srcs)
    # The full file is a different document (everything inlined), so it is rendered on its own
    # and must draw the same visuals with no errors and no stray text.
    full = dist_paths(report)["full"]
    full_result = render(full.parent, full.name, browser)
    write(dist_paths(report)["build"], json.dumps({
        "built": _dt.datetime.now().isoformat(timespec="seconds"),
        "browser": browser,
        "metrics": result.get("metrics", []),
        "errors": result.get("errors", []),
        "full": full_check(result, full_result),
    }, indent=2, ensure_ascii=False))
    for key in ("min", "full"):
        p = dist_paths(report)[key]
        print(f"wrote {p} ({p.stat().st_size // 1024} KB)")
    findings, notes = collect(report)
    return report_findings(findings, notes)


# --------------------------------------------------------------------------- other commands


def report_findings(findings: list[str], notes: list[str] = ()) -> int:
    for n in notes:
        print(f"NOTE: {n}")
    for f in findings:
        print(f"ERROR: {f}")
    if findings:
        return 1
    print("OK")
    return 0


def cmd_new(args) -> int:
    report = Path(args.report)
    if report.exists() and any(report.iterdir()):
        print(f"ERROR: {report} exists and is not empty")
        return 1
    theme, rtype, depth = args.theme, args.type, args.depth
    if not (THEME_ASSETS / f"{theme}.css").is_file():
        names = sorted(p.stem for p in THEME_ASSETS.glob("*.css"))
        print(f"ERROR: theme {theme!r} not found; available: {', '.join(names)}")
        return 1
    if rtype not in report_types():
        print(f"ERROR: type {rtype!r} not found; available: {', '.join(report_types())}")
        return 1
    if depth not in DEPTHS:
        print(f"ERROR: depth {depth!r}; expected one of {', '.join(DEPTHS)}")
        return 1
    shutil.copytree(TEMPLATE_DIR, report, dirs_exist_ok=True)
    for d in NEW_DIRS:
        (report / d).mkdir(parents=True, exist_ok=True)
    shutil.copytree(STATIC_ASSETS, report / SRC / STATIC, dirs_exist_ok=True)
    shutil.copytree(THEME_ASSETS, report / SRC / THEMES, dirs_exist_ok=True)
    brief = report / BRIEF
    text = read(brief)
    for key, value in (("theme", theme), ("type", rtype), ("depth", depth)):
        text, n = re.subn(rf"(?m)^{key}:.*$", f"{key}: {value}", text)
        if n != 1:
            raise UsageError(f"{brief}: no '{key}:' line; template and visual_report.py are out of step")
    if OUTLINE_TOKEN not in text:
        raise UsageError(f"{brief}: no {OUTLINE_TOKEN}; template and visual_report.py are out of step")
    text = text.replace(OUTLINE_TOKEN, read(OUTLINE_ASSETS / f"{rtype}.md").strip())
    write(brief, text)
    print(f"created {report} (type: {rtype}, depth: {depth}, theme: {theme})")
    return 0


def cmd_name(args) -> int:
    slug = re.sub(r"[^a-z0-9]+", "-", args.topic.lower()).strip("-") or "report"
    print(f"{slug}-{_dt.datetime.now().strftime('%Y-%m-%d-%H%M')}")
    return 0


def cmd_outline_approved(args) -> int:
    """Run only after the user's explicit approve of the outline shown in the chat."""
    report = Path(args.report)
    fields, _sources, _f = check_brief(report)
    _rows, findings, _approved = check_outline(report, fields)
    if findings:
        return report_findings(findings + ["the outline is not ready to approve"])
    table = outline_table(report)
    brief = report / BRIEF
    sha = hashlib.sha256(table.encode("utf-8")).hexdigest()
    text, n = re.subn(r"(?m)^outline:.*$", f"outline: {sha}", read(brief))
    if n != 1:
        raise UsageError(f"{brief}: no 'outline:' line")
    write(brief, text)
    print("outline: approved")
    return 0


def compute_step(report: Path) -> tuple[str, str]:
    """(step, what to do). This is the only place the per-step instructions are written; SKILL.md
    keeps only the two steps that need judgement (the outline gate and the review)."""
    if not (report / BRIEF).is_file():
        return "start", (f"ask the first round (SKILL.md), then run new {report} --type T --depth D "
                         "[--theme NAME]")
    fields, sources, f = check_brief(report)
    if f:
        return "brief", f"fill {BRIEF} from the first-round answers: {len(f)} finding(s); run check"
    f = check_sources(report, sources)
    if f:
        return "sources", (f"save chat-only data verbatim under {SOURCES}/, list every source with its "
                           f"scope, and read every source in full: {len(f)} finding(s)")
    _rows, f, approved = check_outline(report, fields)
    if f:
        return "outline", (f"fill the outline in {BRIEF} from the type's skeleton: row 1 is the summary, "
                           f"each title answers its question, proves says what the visual shows: "
                           f"{len(f)} finding(s)")
    if not approved:
        return "outline", ("show the outline in the chat with approve / amend (SKILL.md, the outline gate); "
                           "run outline-approved only after the user's explicit approve")
    f = check_claims(report, sources)
    if f:
        return "claims", (f"write every statement the report will make in {CLAIMS}, with its source "
                          f"and lines: {len(f)} finding(s)")
    src_f, srcs = check_src(report, fields)
    f = src_f + check_data(report, srcs) + check_charts(report)
    if f:
        return "src", (f"compose {SRC}/{REPORT_HTML}: r-summary for outline row 1, r-toc at depth "
                       f"{' / '.join(TOC_DEPTHS)}, then one r-section per row with the same title and "
                       f"part, in order; one data file per visual; numbers from data come from "
                       f"{DERIVE}/ (read references/components.md first): {len(f)} finding(s); run check")
    paths = dist_paths(report)
    newest = newest_input(report)
    if not paths["min"].is_file() or not paths["build"].is_file() or (
            newest and newest[0] > paths["min"].stat().st_mtime):
        return "build", "run build"
    f, _notes = check_dist(report, sources)
    if f:
        return "fix", (f"fix what check reports: {len(f)} finding(s); for a flagged visual change "
                       "its structure (references/legibility.md); run check")
    if fields.get("export") == "pdf" and (
            not paths["pdf"].is_file() or paths["pdf"].stat().st_mtime < paths["min"].stat().st_mtime):
        return "pdf", "run pdf"
    if fields.get("reviewed") != sha256_of(paths["min"]):
        target = paths["pdf"].name if fields.get("export") == "pdf" else paths["min"].name
        return "review", (f"view every page of {target} and open {paths['full'].name} once "
                          "(SKILL.md, the review), then run reviewed")
    return "done", f"hand over the paths in {DIST}/ with a line on what the report covers"


def cmd_status(args) -> int:
    report = Path(args.report)
    step, todo = compute_step(report)
    print(f"report: {report.resolve().name}")
    print(f"step: {step} — {todo}")
    return 0


def cmd_check(args) -> int:
    report = Path(args.report)
    findings, notes = collect(report)
    return report_findings(findings, notes)


def cmd_pdf(args) -> int:
    report = Path(args.report)
    paths = dist_paths(report)
    if not paths["min"].is_file():
        print(f"ERROR: {paths['min']} is missing; run build")
        return 1
    browser = find_browser()
    profile = tempfile.mkdtemp(prefix="visual-report-")
    out = paths["pdf"].resolve()
    out.unlink(missing_ok=True)
    try:
        subprocess.run(browser_args(browser, profile) + [f"--print-to-pdf={out}", "--no-pdf-header-footer",
                                                         paths["min"].resolve().as_uri()],
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=PROCESS_TIMEOUT_S)
    finally:
        shutil.rmtree(profile, ignore_errors=True)
    if not out.is_file() or out.stat().st_size == 0:
        print(f"ERROR: {browser} did not write {out}")
        return 1
    print(f"wrote {out} ({out.stat().st_size // 1024} KB)")
    return 0


def cmd_reviewed(args) -> int:
    report = Path(args.report)
    paths = dist_paths(report)
    if not paths["min"].is_file():
        print(f"ERROR: {paths['min']} is missing; run build")
        return 1
    brief = report / BRIEF
    text, n = re.subn(r"(?m)^reviewed:.*$", f"reviewed: {sha256_of(paths['min'])}", read(brief))
    if n != 1:
        raise UsageError(f"{brief}: no 'reviewed:' line")
    write(brief, text)
    print(f"reviewed: {paths['min'].name}")
    return 0


def cmd_components(_args) -> int:
    reg = load_registry()
    print("| element | required | optional | notes |")
    print("|---|---|---|---|")
    for tag, spec in reg["elements"].items():
        flags = []
        if spec.get("top"):
            flags.append("top level")
        if spec.get("prose"):
            limits = " / ".join(f"{k} {v['words']}" for k, v in DEPTHS.items())
            flags.append(f"prose; words per block by depth: {limits}")
        if spec.get("parent"):
            flags.append(f"inside {spec['parent']}")
        enums = [f"{k.split('.')[1]}: {' | '.join(v)}" for k, v in reg.get("enums", {}).items()
                 if k.startswith(tag + ".")]
        notes = "; ".join(flags + enums + [spec.get("doc", "")])
        print(f"| `{tag}` | {', '.join(spec['required']) or '—'} | {', '.join(spec['optional']) or '—'} | {notes} |")
    print(f"\nInline tags inside prose elements: {', '.join(reg['inline'])}")
    return 0


# --------------------------------------------------------------------------- main


def main(argv: list[str] | None = None) -> int:
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = parser.add_subparsers(dest="command", required=True)
    p = sub.add_parser("name", help="print a dated folder name for a topic")
    p.add_argument("topic")
    p.set_defaults(func=cmd_name)
    p = sub.add_parser("new", help="copy the template into a new report folder")
    p.add_argument("report")
    p.add_argument("--type", required=True, help="a file name in assets/outlines/ without .md")
    p.add_argument("--depth", required=True, choices=list(DEPTHS))
    p.add_argument("--theme", default="light")
    p.set_defaults(func=cmd_new)
    for name, func, help_ in (("status", cmd_status, "print the current step"),
                              ("outline-approved", cmd_outline_approved,
                               "record the user's explicit approve of the outline"),
                              ("build", cmd_build, "derive, render and write dist, then check"),
                              ("check", cmd_check, "run every check without rendering"),
                              ("pdf", cmd_pdf, "print the min.html to PDF"),
                              ("reviewed", cmd_reviewed, "record that every page was viewed")):
        p = sub.add_parser(name, help=help_)
        p.add_argument("report")
        p.set_defaults(func=func)
    p = sub.add_parser("components", help="print the r-* element catalogue")
    p.set_defaults(func=cmd_components)
    args = parser.parse_args(argv)
    try:
        return args.func(args)
    except UsageError as e:
        print(f"ERROR: {e}")
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
