/* visual-report-creator components.
 *
 * Expands the r-* elements of report.html into their rendered form, draws mermaid diagrams and
 * ECharts charts as SVG, measures every visual, and — when opened by `report.py build` with
 * ?__render=1 — posts the rendered DOM and the measurements back to the build server.
 *
 * The block between REGISTRY-BEGIN and REGISTRY-END is JSON and is the only list of allowed
 * elements and attributes: report.py reads it from here for `check` and `components`.
 */

/* REGISTRY-BEGIN */
const REGISTRY = {
  "inline": ["p", "b", "i", "em", "strong", "a", "ul", "ol", "li", "code", "br"],
  "semantic_classes": ["ok", "warn", "fail", "accent", "muted", "external", "g1", "g2", "g3", "g4", "g5", "g6"],
  "class_diagrams": ["flowchart", "graph", "stateDiagram", "stateDiagram-v2"],
  "row_states": ["ok", "warn", "fail", "accent", "muted"],
  "inline_attrs": {"a": ["href"]},
  "labels": {
    "en": {"appendix": "Appendix", "contents": "Contents",
           "what": "What happened", "meaning": "What it means", "action": "What to do",
           "decision": "Decision", "risk": "Risk", "note": "Note", "question": "Question",
           "ok": "working", "warn": "needs attention", "fail": "failed / hostile",
           "accent": "in focus", "muted": "out of scope", "external": "external"},
    "ru": {"appendix": "Приложение", "contents": "Содержание",
           "what": "Что случилось", "meaning": "Что это значит", "action": "Что делать",
           "decision": "Решение", "risk": "Риск", "note": "Заметка", "question": "Вопрос",
           "ok": "работает", "warn": "требует внимания", "fail": "сбой / угроза",
           "accent": "в фокусе", "muted": "вне рамок", "external": "внешнее"}
  },
  "elements": {
    "r-cover":   {"top": true,  "prose": false, "required": ["title"], "optional": ["subtitle", "date"],
                  "doc": "Title block at the top of the report."},
    "r-summary": {"top": true,  "prose": false, "required": ["title"], "optional": [],
                  "doc": "The answer first: required as the first section after r-cover, with exactly one r-line of each kind (what, meaning, action). Matches outline row 1 (part summary)."},
    "r-line":    {"top": false, "prose": true,  "required": ["kind"], "optional": [], "parent": "r-summary",
                  "doc": "One line of the summary; kind is what | meaning | action; the action line is addressed to the brief's audience."},
    "r-toc":     {"top": true,  "prose": false, "required": [], "optional": [],
                  "doc": "Contents list built from the sections; required right after r-summary at depth standard and detailed."},
    "r-section": {"top": true,  "prose": false, "required": ["title"], "optional": ["part"],
                  "doc": "A titled section; holds layout and content elements. part is main (default) | method | appendix and must match the outline."},
    "r-row":     {"top": false, "prose": false, "required": [], "optional": [],
                  "doc": "Children side by side in equal columns."},
    "r-grid":    {"top": false, "prose": false, "required": ["cols"], "optional": [],
                  "doc": "Children in a grid of `cols` columns (1..MAX_GRID_COLS)."},
    "r-stack":   {"top": false, "prose": false, "required": [], "optional": [],
                  "doc": "Children stacked vertically with even spacing."},
    "r-text":    {"top": false, "prose": true,  "required": [], "optional": [],
                  "doc": "A short block of prose: inline tags only."},
    "r-kpi":     {"top": false, "prose": false, "required": ["value", "label"], "optional": ["delta", "trend"],
                  "doc": "One number with a label; trend is up | down | flat; delta is free text like +5%."},
    "r-callout": {"top": false, "prose": true,  "required": ["kind"], "optional": ["title"],
                  "doc": "Highlighted note; kind is decision | risk | note | question."},
    "r-status":  {"top": false, "prose": false, "required": [], "optional": ["title"],
                  "doc": "A list of r-item status lines."},
    "r-item":    {"top": false, "prose": true,  "required": ["state"], "optional": [], "parent": "r-status",
                  "doc": "One status line inside r-status; state is ok | warn | fail | todo."},
    "r-table":   {"top": false, "prose": false, "required": ["src"], "optional": ["caption", "highlight", "highlight-map", "mono"], "visual": false,
                  "doc": "A table from a CSV file under tables/; the first row is the header. highlight names one column; highlight-map is value:state pairs (offline:fail) colouring whole rows. mono lists columns set in monospace (indicators, hashes, paths, commands)."},
    "r-diagram": {"top": false, "prose": false, "required": ["src"], "optional": ["caption"], "visual": true,
                  "doc": "A mermaid diagram from a .mmd file under diagrams/."},
    "r-chart":   {"top": false, "prose": false, "required": ["src"], "optional": ["caption", "height"], "visual": true,
                  "doc": "An ECharts chart from an option JSON file under charts/; height in px, default 320."}
  },
  "enums": {
    "r-section.part": ["main", "method", "appendix"],
    "r-line.kind": ["what", "meaning", "action"],
    "r-kpi.trend": ["up", "down", "flat"],
    "r-callout.kind": ["decision", "risk", "note", "question"],
    "r-item.state": ["ok", "warn", "fail", "todo"]
  }
};
/* REGISTRY-END */

(function () {
  "use strict";
  const RENDER = new URLSearchParams(location.search).has("__render");
  const errors = [];
  const metrics = [];

  const css = (name) => getComputedStyle(document.documentElement).getPropertyValue(name).trim();
  // UI words in the report's language (<html lang>); a missing language falls back to English.
  const LANG = (document.documentElement.lang || "en").split("-")[0];
  const label = (key) => (REGISTRY.labels[LANG] || REGISTRY.labels.en)[key] || REGISTRY.labels.en[key] || key;
  const make = (tag, cls, text) => {
    const el = document.createElement(tag);
    if (cls) el.className = cls;
    if (text != null) el.textContent = text;
    return el;
  };

  // Data inlined by `build` for the .full.html file; fetched over HTTP otherwise.
  async function load(path) {
    for (const el of document.querySelectorAll('script[type="application/json"][data-path]')) {
      if (el.getAttribute("data-path") === path) return JSON.parse(el.textContent);
    }
    const r = await fetch(path);
    if (!r.ok) throw new Error(`cannot load ${path}: HTTP ${r.status}`);
    return r.text();
  }

  function parseCsv(text) {
    const rows = [];
    let row = [], cell = "", quoted = false;
    for (let i = 0; i < text.length; i++) {
      const c = text[i];
      if (quoted) {
        if (c === '"' && text[i + 1] === '"') { cell += '"'; i++; }
        else if (c === '"') quoted = false;
        else cell += c;
      } else if (c === '"') quoted = true;
      else if (c === ",") { row.push(cell); cell = ""; }
      else if (c === "\n" || c === "\r") {
        if (c === "\r" && text[i + 1] === "\n") i++;
        row.push(cell); rows.push(row); row = []; cell = "";
      } else cell += c;
    }
    if (cell !== "" || row.length) { row.push(cell); rows.push(row); }
    return rows.filter((r) => r.some((x) => x.trim() !== ""));
  }

  function figure(el, body) {
    const caption = el.getAttribute("caption");
    const fig = make("figure", "r-figure");
    fig.appendChild(body);
    if (caption) fig.appendChild(make("figcaption", null, caption));
    el.replaceChildren(fig);
    return fig;
  }

  function idOf(el, i) {
    return el.id || `${el.tagName.toLowerCase()}-${i + 1}`;
  }

  // ------------------------------------------------------------------ simple components

  function renderStatic() {
    document.querySelectorAll("r-cover").forEach((el) => {
      const box = make("div", "r-cover-box");
      box.appendChild(make("h1", null, el.getAttribute("title")));
      if (el.hasAttribute("subtitle")) box.appendChild(make("p", "r-subtitle", el.getAttribute("subtitle")));
      if (el.hasAttribute("date")) box.appendChild(make("p", "r-date", el.getAttribute("date")));
      el.replaceChildren(box);
    });
    document.querySelectorAll("r-summary").forEach((el) => {
      el.dataset.part = "summary";
      el.querySelectorAll("r-line").forEach((line) => {
        line.dataset.kind = line.getAttribute("kind");
        line.prepend(make("span", "r-line-label", label(line.getAttribute("kind"))));
      });
      el.prepend(make("h2", "r-section-title", el.getAttribute("title")));
    });
    let appendixSeen = false;
    document.querySelectorAll("r-section").forEach((el) => {
      const part = el.getAttribute("part") || "main";
      el.dataset.part = part;
      el.prepend(make("h2", "r-section-title", el.getAttribute("title")));
      if (part === "appendix" && !appendixSeen) {
        appendixSeen = true;
        el.before(make("div", "r-appendix-divider", label("appendix")));
      }
    });
    // A title never ends a page alone: it is kept in one unbreakable block with the first thing
    // after it.
    document.querySelectorAll("r-summary > .r-section-title, r-section > .r-section-title").forEach((h) => {
      const next = h.nextElementSibling;
      if (!next) return;
      const keep = make("div", "r-keep");
      h.before(keep);
      keep.append(h, next);
    });
    document.querySelectorAll("r-toc").forEach((el) => {
      const list = make("ol", "r-toc-list");
      // The summary sits right above the contents, so the list starts with the first section.
      document.querySelectorAll("body > r-section").forEach((s, i) => {
        if (!s.id) s.id = `section-${i + 1}`;
        const li = make("li");
        li.dataset.part = s.dataset.part || "main";
        const a = make("a", null, s.getAttribute("title"));
        a.href = `#${s.id}`;
        li.appendChild(a);
        list.appendChild(li);
      });
      el.replaceChildren(make("div", "r-toc-title", label("contents")), list);
    });
    document.querySelectorAll("r-grid").forEach((el) => {
      el.style.setProperty("--cols", el.getAttribute("cols"));
    });
    document.querySelectorAll("r-kpi").forEach((el) => {
      const trend = el.getAttribute("trend") || "";
      el.dataset.trend = trend;
      const box = make("div", "r-kpi-box");
      box.appendChild(make("div", "r-kpi-value", el.getAttribute("value")));
      box.appendChild(make("div", "r-kpi-label", el.getAttribute("label")));
      if (el.hasAttribute("delta")) {
        const arrow = { up: "▲ ", down: "▼ ", flat: "● " }[trend] || "";
        box.appendChild(make("div", "r-kpi-delta", arrow + el.getAttribute("delta")));
      }
      el.replaceChildren(box);
    });
    document.querySelectorAll("r-callout").forEach((el) => {
      el.dataset.kind = el.getAttribute("kind");
      const title = el.getAttribute("title") || label(el.getAttribute("kind"));
      el.prepend(make("div", "r-callout-title", title));
    });
    document.querySelectorAll("r-status").forEach((el) => {
      if (el.hasAttribute("title")) el.prepend(make("div", "r-status-title", el.getAttribute("title")));
    });
    document.querySelectorAll("r-item").forEach((el) => {
      el.dataset.state = el.getAttribute("state");
      const mark = { ok: "✓", warn: "!", fail: "✕", todo: "○" }[el.getAttribute("state")] || "";
      el.prepend(make("span", "r-item-mark", mark));
    });
  }

  async function renderTables() {
    for (const el of document.querySelectorAll("r-table")) {
      try {
        const rows = parseCsv(await load(el.getAttribute("src")));
        const table = make("table");
        // Row highlighting: one column, exact cell values mapped to a row state.
        const col = rows.length ? rows[0].indexOf(el.getAttribute("highlight")) : -1;
        const monoNames = (el.getAttribute("mono") || "").split(",").map((s) => s.trim()).filter(Boolean);
        const mono = new Set(rows.length ? monoNames.map((n) => rows[0].indexOf(n)).filter((i) => i >= 0) : []);
        const map = new Map((el.getAttribute("highlight-map") || "").split(",")
          .map((p) => p.split(":").map((s) => s.trim())).filter((p) => p.length === 2 && p[0]));
        rows.forEach((r, i) => {
          const tr = make("tr");
          r.forEach((c, j) => tr.appendChild(make(i === 0 ? "th" : "td", i > 0 && mono.has(j) ? "mono" : null, c)));
          if (i > 0 && col >= 0 && map.has((r[col] || "").trim())) tr.dataset.state = map.get(r[col].trim());
          (i === 0 ? table.createTHead() : table.tBodies[0] || table.createTBody()).appendChild(tr);
        });
        figure(el, table);
      } catch (e) {
        errors.push({ element: el.id || "r-table", src: el.getAttribute("src"), error: String(e.message || e) });
      }
    }
  }

  // ------------------------------------------------------------------ mermaid

  function mermaidTheme() {
    return {
      darkMode: css("--theme-mode") === "dark",
      background: css("--color-bg"),
      fontFamily: css("--font-sans"),
      fontSize: "16px",
      primaryColor: css("--color-surface"),
      primaryBorderColor: css("--color-accent"),
      primaryTextColor: css("--color-text"),
      secondaryColor: css("--color-surface-2"),
      tertiaryColor: css("--color-bg"),
      lineColor: css("--color-muted"),
      textColor: css("--color-text"),
      clusterBkg: css("--color-surface-2"),
      clusterBorder: css("--color-border"),
      edgeLabelBackground: css("--color-bg"),
    };
  }

  // Semantic classes, defined from the theme and prepended after the diagram's header line, so
  // `A:::fail` means the same colour in every diagram and in both themes.
  function classDefs() {
    const text = css("--color-text");
    const def = (name, fill, stroke, extra = "") =>
      `classDef ${name} fill:${fill},stroke:${stroke},color:${text},stroke-width:2px${extra}`;
    const lines = ["ok", "warn", "fail", "accent", "muted"].map((s) =>
      def(s, css(`--color-${s}-soft`), css(s === "muted" ? "--color-border" : `--color-${s}`)));
    lines.push(def("external", css("--color-bg"), css("--color-muted"), ",stroke-dasharray:6 4"));
    for (let n = 1; n <= 6; n++) {
      const c = css(`--color-series-${n}`);
      lines.push(def(`g${n}`, mix(c, css("--color-bg"), 0.18), c));
    }
    return lines;
  }

  // A blend of two hex colours. classDef values are comma-separated, so color-mix() cannot be
  // used there; a theme colour that is not hex is returned unchanged.
  function mix(fg, bg, amount) {
    const rgb = (h) => {
      const m = /^#([0-9a-f]{3}|[0-9a-f]{6})$/i.exec(h.trim());
      if (!m) return null;
      const s = m[1].length === 3 ? m[1].replace(/./g, "$&$&") : m[1];
      return [0, 2, 4].map((i) => parseInt(s.slice(i, i + 2), 16));
    };
    const a = rgb(fg), b = rgb(bg);
    if (!a || !b) return fg;
    return "#" + a.map((v, i) => Math.round(v * amount + b[i] * (1 - amount)).toString(16).padStart(2, "0")).join("");
  }

  function withClasses(text) {
    const lines = text.split(/\r?\n/);
    const header = lines.findIndex((l) => {
      const t = l.trim();
      return t && !t.startsWith("%%") && t !== "---";
    });
    if (header < 0) return text;
    const kind = lines[header].trim().split(/\s+/)[0];
    if (!REGISTRY.class_diagrams.includes(kind)) return text;
    lines.splice(header + 1, 0, ...classDefs().map((d) => "  " + d));
    return lines.join("\n");
  }

  // A legend of the status classes a diagram uses, in the report's language. Group classes
  // (g1…g6) have no fixed meaning, so they are left to the caption.
  function legendFor(text) {
    const used = new Set();
    for (const line of text.split(/\r?\n/)) {
      if (line.trim().startsWith("%%")) continue;
      for (const m of line.matchAll(/:::([A-Za-z0-9_-]+)/g)) used.add(m[1]);
      const stmt = /^\s*class\s+\S+\s+([A-Za-z0-9_-]+)\s*;?\s*$/.exec(line);
      if (stmt) used.add(stmt[1]);
    }
    const shown = ["accent", "ok", "warn", "fail", "muted", "external"].filter((c) => used.has(c));
    if (!shown.length) return null;
    const box = make("div", "r-legend");
    for (const c of shown) {
      const item = make("span", "r-legend-item");
      const sw = make("span", "r-legend-swatch");
      sw.dataset.cls = c;
      item.append(sw, document.createTextNode(label(c)));
      box.appendChild(item);
    }
    return box;
  }

  // Number of connected parts of a flowchart, or null when mermaid does not expose the graph.
  async function flowchartParts(text) {
    try {
      const diagram = await window.mermaid.mermaidAPI.getDiagramFromText(text);
      const db = diagram && diagram.db;
      if (!db || typeof db.getVertices !== "function" || typeof db.getEdges !== "function") return null;
      const subgraphs = typeof db.getSubGraphs === "function" ? db.getSubGraphs() : [];
      const members = new Map(subgraphs.map((s) => [s.id, s.nodes || []]));
      // An edge to a subgraph connects to every node inside it; sharing a box is not an edge.
      const expand = (id, seen = new Set()) => {
        if (!members.has(id)) return [id];
        if (seen.has(id)) return [];
        seen.add(id);
        return members.get(id).flatMap((n) => expand(n, seen));
      };
      const vertices = db.getVertices();
      const keys = (vertices instanceof Map ? [...vertices.keys()] : Object.keys(vertices))
        .filter((k) => !members.has(k));
      const parent = new Map(keys.map((k) => [k, k]));
      const find = (x) => { while (parent.get(x) !== x) x = parent.get(x); return x; };
      const add = (x) => { if (!parent.has(x)) parent.set(x, x); };
      for (const e of db.getEdges()) {
        for (const a of expand(e.start)) for (const b of expand(e.end)) {
          add(a); add(b); parent.set(find(a), find(b));
        }
      }
      return new Set([...parent.keys()].map(find)).size;
    } catch (e) {
      return null;
    }
  }

  async function renderDiagrams() {
    const els = [...document.querySelectorAll("r-diagram")];
    if (!els.length) return;
    window.mermaid.initialize({ startOnLoad: false, theme: "base", themeVariables: mermaidTheme(),
                                securityLevel: "strict", fontFamily: css("--font-sans") });
    for (const [i, el] of els.entries()) {
      const id = idOf(el, i);
      try {
        const text = await load(el.getAttribute("src"));
        const { svg } = await window.mermaid.render(`${id}-svg`, withClasses(text));
        const box = make("div", "r-visual");
        box.innerHTML = svg;
        const fig = figure(el, box);
        const legend = legendFor(text);
        if (legend) fig.insertBefore(legend, fig.querySelector("figcaption"));
        const type = (text.trim().split(/\s+/)[0] || "").toLowerCase();
        const parts = type === "flowchart" || type === "graph" ? await flowchartParts(text) : null;
        el.dataset.parts = parts == null ? "" : String(parts);
      } catch (e) {
        errors.push({ element: id, src: el.getAttribute("src"), error: String(e.message || e) });
      }
    }
  }

  // ------------------------------------------------------------------ ECharts

  function echartsTheme() {
    const text = css("--color-text"), muted = css("--color-muted"), border = css("--color-border");
    const series = [1, 2, 3, 4, 5, 6].map((n) => css(`--color-series-${n}`)).filter(Boolean);
    const axis = {
      axisLine: { lineStyle: { color: border } },
      axisTick: { lineStyle: { color: border } },
      axisLabel: { color: muted },
      splitLine: { lineStyle: { color: border } },
      nameTextStyle: { color: muted },
    };
    return {
      color: series,
      backgroundColor: "transparent",
      textStyle: { fontFamily: css("--font-sans"), color: text, fontSize: 12 },
      title: { textStyle: { color: text }, subtextStyle: { color: muted } },
      legend: { textStyle: { color: text } },
      categoryAxis: axis, valueAxis: axis, timeAxis: axis, logAxis: axis,
    };
  }

  async function renderCharts() {
    const els = [...document.querySelectorAll("r-chart")];
    if (!els.length) return;
    window.echarts.registerTheme("report", echartsTheme());
    for (const [i, el] of els.entries()) {
      const id = idOf(el, i);
      try {
        const raw = await load(el.getAttribute("src"));
        const option = typeof raw === "string" ? JSON.parse(raw) : raw;
        option.animation = false;
        const box = make("div", "r-visual r-chart-box");
        box.style.height = `${parseInt(el.getAttribute("height") || "320", 10)}px`;
        figure(el, box);
        const chart = window.echarts.init(box, "report", { renderer: "svg", devicePixelRatio: 2 });
        chart.setOption(option);
      } catch (e) {
        errors.push({ element: id, src: el.getAttribute("src"), error: String(e.message || e) });
      }
    }
  }

  // ------------------------------------------------------------------ measurement

  function hasOwnText(node) {
    return [...node.childNodes].some((c) => c.nodeType === 3 && c.textContent.trim() !== "");
  }

  function measure() {
    document.querySelectorAll("r-diagram, r-chart").forEach((el, i) => {
      const svg = el.querySelector("svg");
      const entry = { element: idOf(el, i), tag: el.tagName.toLowerCase(), src: el.getAttribute("src") };
      if (!svg) { metrics.push({ ...entry, measured: false }); return; }
      const rect = svg.getBoundingClientRect();
      const vb = svg.viewBox && svg.viewBox.baseVal;
      const scale = vb && vb.width ? rect.width / vb.width : 1;
      let minFont = null;
      svg.querySelectorAll("text, tspan, foreignObject *").forEach((n) => {
        if (!hasOwnText(n)) return;
        const size = parseFloat(getComputedStyle(n).fontSize);
        if (!isNaN(size) && (minFont === null || size < minFont)) minFont = size;
      });
      const parts = el.dataset.parts;
      metrics.push({
        ...entry,
        measured: minFont !== null,
        width: Math.round(rect.width),
        height: Math.round(rect.height),
        min_text_px: minFont === null ? null : Math.round(minFont * scale * 10) / 10,
        parts: parts === undefined || parts === "" ? null : Number(parts),
      });
    });
  }

  // ------------------------------------------------------------------ main

  async function main() {
    renderStatic();
    await renderTables();
    if (window.mermaid) await renderDiagrams();
    else if (document.querySelector("r-diagram")) errors.push({ element: "r-diagram", error: "mermaid not loaded" });
    if (window.echarts) await renderCharts();
    else if (document.querySelector("r-chart")) errors.push({ element: "r-chart", error: "echarts not loaded" });
    if (document.fonts && document.fonts.ready) await document.fonts.ready;
    await new Promise((r) => requestAnimationFrame(() => requestAnimationFrame(r)));
    measure();
    document.documentElement.dataset.rendered = "true";
    if (RENDER) {
      await fetch("/__done", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ dom: "<!DOCTYPE html>\n" + document.documentElement.outerHTML,
                               text: document.body.innerText, metrics, errors }),
      });
    } else if (errors.length) {
      console.error("visual-report-creator:", errors);
    }
  }

  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", main);
  else main();
})();
