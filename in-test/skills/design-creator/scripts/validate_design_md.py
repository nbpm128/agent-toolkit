#!/usr/bin/env python3
"""Validate a DESIGN.md file against the design-creator schema (references/spec.md).

Standard library only -- no PyYAML -- so this runs anywhere Python 3 is present, matching the
convention in skills/planning/scripts/validate_plan.py. Only the frontmatter subset this schema
actually uses is parsed; this is not a general YAML parser.
"""
import argparse
import re
import sys
from collections import Counter

CANONICAL_SECTIONS = [
    "Overview",
    "Colors",
    "Typography",
    "Layout",
    "Elevation & Depth",
    "Shapes",
    "Components",
    "Do's and Don'ts",
]


def split_frontmatter(text):
    lines = text.splitlines()
    dash_indices = [i for i, line in enumerate(lines) if line.strip() == "---"]
    if len(dash_indices) < 2:
        raise ValueError("No frontmatter found (expected two '---' lines)")
    fm_lines = lines[dash_indices[0] + 1 : dash_indices[1]]
    body_lines = lines[dash_indices[1] + 1 :]
    return fm_lines, body_lines


def get_block_lines(fm_lines, key):
    """Lines indented under a top-level `key:` line, until the next 0-indent line or EOF.

    A full-line comment (stripped content starting with `#`) never ends the block, at any
    indentation -- otherwise a 0-indent comment placed between two entries of the same block
    would be misread as the next top-level key and silently truncate everything after it.
    """
    out = []
    in_block = False
    header_re = re.compile(r"^%s:\s*$" % re.escape(key))
    for line in fm_lines:
        if header_re.match(line):
            in_block = True
            continue
        if in_block:
            stripped = line.strip()
            if stripped == "" or stripped.startswith("#"):
                continue
            if re.match(r"^\S", line):
                break
            out.append(line)
    return out


def strip_quotes(value):
    value = value.strip()
    if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
        return value[1:-1]
    return value


def parse_flat_map(block_lines):
    """2-space-indented `key: value` lines -> {key: value}. Deeper-indented lines are ignored.

    This is a minimal, spec-scoped parser, not a real YAML parser: it does not know that a real
    YAML parser treats an unquoted `#` after whitespace as starting a comment. references/spec.md
    requires quoting color values for exactly this reason -- an unquoted `primary: #111111` is
    parsed here as the literal string "#111111", where a real YAML parser would read it as a
    comment and leave the value null.
    """
    result = {}
    for line in block_lines:
        m = re.match(r"^ {2}([\w-]+):\s*(.*)$", line)
        if m:
            result[m.group(1)] = strip_quotes(m.group(2))
    return result


def parse_nested_map(block_lines):
    """2-space `name:` lines each own the 4-space `prop: value` lines that follow them."""
    result = {}
    current = None
    for line in block_lines:
        name_m = re.match(r"^ {2}([\w-]+):\s*$", line)
        if name_m:
            current = name_m.group(1)
            result[current] = {}
            continue
        prop_m = re.match(r"^ {4}([\w-]+):\s*(.*)$", line)
        if prop_m and current is not None:
            result[current][prop_m.group(1)] = strip_quotes(prop_m.group(2))
    return result


def parse_omitted(fm_lines):
    text = "\n".join(fm_lines)
    m = re.search(r"^omitted:\s*\[(.*)\]\s*$", text, re.MULTILINE)
    if not m:
        return []
    return re.findall(r'"([^"]*)"', m.group(1))


def extract_headings(body_lines):
    """[(heading_text, line_no)] for `## ` lines, skipping anything inside a fenced code block."""
    headings = []
    in_code = False
    for i, line in enumerate(body_lines, start=1):
        if line.strip().startswith("```"):
            in_code = not in_code
            continue
        if in_code:
            continue
        m = re.match(r"^## (.+)$", line)
        if m:
            headings.append((m.group(1).rstrip(), i))
    return headings


def check_order(headings):
    """Flag the minimal set of sections that are out of canonical order.

    Reports only the sections NOT in the longest increasing (by canonical index) subsequence of
    the sections actually present, rather than every pairwise inversion -- an all-pairs check
    produces O(n^2) redundant lines for one badly-ordered document (up to 28 lines for 8 fully
    reversed sections), drowning the one real issue in noise.
    """
    seen = set()
    ordered_canonical_present = []
    for name, _ in headings:
        if name in CANONICAL_SECTIONS and name not in seen:
            ordered_canonical_present.append(name)
            seen.add(name)

    n = len(ordered_canonical_present)
    if n < 2:
        return []
    idxs = [CANONICAL_SECTIONS.index(name) for name in ordered_canonical_present]

    lengths = [1] * n
    prev = [-1] * n
    for i in range(n):
        for j in range(i):
            if idxs[j] < idxs[i] and lengths[j] + 1 > lengths[i]:
                lengths[i] = lengths[j] + 1
                prev[i] = j
    best_end = max(range(n), key=lambda i: lengths[i])
    in_lis = set()
    k = best_end
    while k != -1:
        in_lis.add(k)
        k = prev[k]

    out_of_place = [ordered_canonical_present[i] for i in range(n) if i not in in_lis]
    return [
        'ERROR: section order violation: "%s" appears out of canonical order (expected: %s)'
        % (name, ", ".join(CANONICAL_SECTIONS))
        for name in out_of_place
    ]


def check_duplicates(headings):
    counts = Counter(name for name, _ in headings)
    return [
        'ERROR: duplicate section heading: "%s" appears more than once' % name
        for name, count in counts.items()
        if count > 1
    ]


TOKEN_REF_RE = re.compile(r"\{(colors|typography|rounded|spacing)\.([\w-]+)\}")


def check_token_refs(components, colors, typography_names, rounded, spacing):
    section_maps = {"colors": colors, "rounded": rounded, "spacing": spacing}
    errors = []
    for comp_name, props in components.items():
        for prop_name, value in props.items():
            for m in TOKEN_REF_RE.finditer(value):
                section, token = m.group(1), m.group(2)
                defined = token in typography_names if section == "typography" else token in section_maps[section]
                if not defined:
                    errors.append(
                        "ERROR: undefined token reference: {%s.%s} used in components.%s.%s but "
                        '"%s" is not defined under %s' % (section, token, comp_name, prop_name, token, section)
                    )
    return errors


def check_primary_color(colors):
    if "primary" not in colors:
        return ["ERROR: missing required token: colors.primary is not defined"]
    return []


HEX6_RE = re.compile(r"^#([0-9a-fA-F]{6})$")
HEX3_RE = re.compile(r"^#([0-9a-fA-F]{3})$")
RGB_RE = re.compile(r"^rgba?\(\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*(?:,\s*([\d.]+)\s*)?\)$")
TOKEN_REF_SINGLE_RE = re.compile(r"^\{colors\.([\w-]+)\}$")


def resolve_color(value, colors, _depth=0):
    """Resolve a literal color or a {colors.X} reference to an (r, g, b) tuple, or None if it
    can't be resolved to a single opaque color (undefined token, translucent, unrecognized)."""
    if _depth > 5:
        return None
    v = strip_quotes(value)
    ref_m = TOKEN_REF_SINGLE_RE.match(v)
    if ref_m:
        token = ref_m.group(1)
        if token not in colors:
            return None
        return resolve_color(colors[token], colors, _depth + 1)
    m = HEX6_RE.match(v)
    if m:
        h = m.group(1)
        return tuple(int(h[i : i + 2], 16) for i in (0, 2, 4))
    m = HEX3_RE.match(v)
    if m:
        h = m.group(1)
        return tuple(int(c * 2, 16) for c in h)
    m = RGB_RE.match(v)
    if m:
        r, g, b = int(m.group(1)), int(m.group(2)), int(m.group(3))
        alpha = m.group(4)
        if alpha is not None and float(alpha) < 1.0:
            return None
        return (r, g, b)
    return None


def relative_luminance(rgb):
    def channel(c):
        c = c / 255.0
        return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4

    r, g, b = rgb
    return 0.2126 * channel(r) + 0.7152 * channel(g) + 0.0722 * channel(b)


def contrast_ratio(rgb1, rgb2):
    l1, l2 = relative_luminance(rgb1), relative_luminance(rgb2)
    lighter, darker = max(l1, l2), min(l1, l2)
    return (lighter + 0.05) / (darker + 0.05)


def check_contrast(components, colors):
    errors = []
    for comp_name, props in components.items():
        if "backgroundColor" not in props or "textColor" not in props:
            continue
        bg = resolve_color(props["backgroundColor"], colors)
        fg = resolve_color(props["textColor"], colors)
        if bg is None or fg is None:
            continue
        ratio = contrast_ratio(bg, fg)
        if ratio < 4.5:
            errors.append(
                "ERROR: insufficient contrast: components.%s textColor/backgroundColor pair has "
                "contrast ratio %.2f:1, below the 4.5:1 WCAG AA minimum" % (comp_name, ratio)
            )
    return errors


def check_omitted_sections(headings, omitted):
    present = {name for name, _ in headings}
    return [
        'ERROR: section "%s" is missing from the body and not declared in frontmatter omitted:' % name
        for name in CANONICAL_SECTIONS
        if name not in present and name not in omitted
    ]


def validate(path):
    with open(path, "r", encoding="utf-8") as f:
        text = f.read()
    fm_lines, body_lines = split_frontmatter(text)

    colors = parse_flat_map(get_block_lines(fm_lines, "colors"))
    rounded = parse_flat_map(get_block_lines(fm_lines, "rounded"))
    spacing = parse_flat_map(get_block_lines(fm_lines, "spacing"))
    typography_names = set(parse_flat_map(get_block_lines(fm_lines, "typography")).keys())
    components = parse_nested_map(get_block_lines(fm_lines, "components"))
    omitted = parse_omitted(fm_lines)
    headings = extract_headings(body_lines)

    errors = []
    errors += check_order(headings)
    errors += check_duplicates(headings)
    errors += check_token_refs(components, colors, typography_names, rounded, spacing)
    errors += check_primary_color(colors)
    errors += check_contrast(components, colors)
    errors += check_omitted_sections(headings, omitted)
    return errors


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("path", help="Path to the DESIGN.md file to validate")
    args = parser.parse_args()

    errors = validate(args.path)
    if not errors:
        print("OK: %s is a valid DESIGN.md" % args.path)
        return 0
    for error in errors:
        print(error)
    print("FAILED: %d issue(s) found" % len(errors))
    return 1


if __name__ == "__main__":
    sys.exit(main())
