# Worked Example

> Worked fragments showing the density the templates ask for. Read one when what you are about to write feels thin and you want something to compare against. Both examples here (a CLI tool that exports CSV or JSON, and an S3 boundary check) are fictitious, invented for this file, and not part of any project.

The running example throughout: adding a `--format` option so the CLI's `export` command writes CSV or JSON instead of CSV only.

## 1. An interview round

`Plan: cli-export · Phase 2 Planning · Task 1 of 3`

Complexity: simple — one clear unknown, the rest is settled by the existing writer.

Reply per question (`1B`); a skipped question takes its ★; "proceed" takes every ★.

**My current assumptions**

`ASM-004` (verified): the `export` command writes CSV only, through `write_csv()` (evidence: `cli/export.py:40`).

**Q1 — Where the `--format` value is validated**
The flag needs a fixed set of accepted values before `export` runs.

- A validate inside `export()` itself, alongside the existing CSV logic — keeps validation next to its one caller, but a second command that takes `--format` later would repeat the check
- B ★ validate in the shared CLI argument parser, with `choices=["csv", "json"]` — one place for every command that takes the flag, and an unknown value is rejected before any command runs
- C do not validate; let an unknown value fall through to a `KeyError` from the writer lookup — no new code, but the error message means nothing to the user

Reply: `1A`, `1B` or `1C`.

The user replied `1B`, which fixed the question: `--format` gets `choices=["csv", "json"]` in the shared parser, so `export()` itself never has to reject a value.

## 2. A filled-in task

```markdown
---
status: not-started
milestone: M1
satisfies: [REQ-002]
assumptions: [ASM-004]
depends_on: []
sub_plan: null
updated: 2026-09-22
---

# Task 001: Export format option

> Add `--format csv|json` to the CLI's `export` command, so it can write JSON as well as CSV.

## Context

`export()` (`cli/export.py:38-52`) always calls `write_csv(rows, out)`. A second writer, `write_json(rows, out)`, does not exist yet. The shared argument parser is built in `cli/parser.py:build_parser()`.

## Files

| Action | Path | What changes |
|---|---|---|
| Modify | `cli/parser.py:build_parser()` | add `--format`, `choices=["csv", "json"]`, default `"csv"` |
| Modify | `cli/export.py:38-52` | call `write_json` when `args.format == "json"`, else `write_csv` |

## Instructions

1. In `cli/parser.py`, inside `build_parser()`, add `parser.add_argument("--format", choices=["csv", "json"], default="csv")` next to the existing `export` sub-parser's arguments.
2. In `cli/export.py`, add `write_json(rows, out)` that calls `json.dump(rows, out)`.
3. In `cli/export.py:44`, replace the direct `write_csv(rows, out)` call with a two-way branch on `args.format`, calling `write_json` for `"json"` and `write_csv` otherwise.

## Decision log

| Decision | Source |
|---|---|
| `--format` is validated by the shared parser's `choices`, not inside `export()` | interview Q1 B |

## Acceptance / Verification

| # | Criterion | Proof | Expected |
|---|---|---|---|
| 1 | WHEN `export` runs with `--format json`, THE SYSTEM SHALL write JSON | `python -m cli export --format json --out /tmp/out.json` then read the file | valid JSON, same rows as the CSV output |

## Progress Log

#### 2026-09-22
- Status: not-started
- Approved by the user; readiness checklist passed.
```

The guidance comment that the template carries under `## Progress Log` is replaced by that first entry, like every other placeholder in a template.

## 3. A Progress Log entry

```
#### 2026-09-22
- Status: in-progress -> done
- Did: added `--format` to the shared parser and the JSON writer in `cli/export.py`.
- Review: cli/parser.py, cli/export.py; Critical 0, Important 0, Minor 0; fixed: none; deferred: none
- Verified:
  - Run: `python skills/planning-dev/scripts/validate_plan.py plans/plan-cli-export --check`
    Result: `OK: plans/plan-cli-export is consistent (1 task(s)) -- 1 Done / 0 In Progress / 0 Not Started / 0 Blocked / 0 Delegated`
  - Run: `python -m cli export --format json --out /tmp/out.json && python -c "import json; json.load(open('/tmp/out.json'))"`
    Result: no error; the file parses as JSON
```

A reader six weeks later can rerun both commands, see the same output, and knows the change is proven, not just described.

## 4. A worked message of a task interview

The second message of a task interview, after the user answered `1A`, for a plan `s3-storage` and task 3 of 6:

```
`Plan: s3-storage · Phase 2 Planning · Task 3 of 6`

**Interview result**

| Decisions made | Open items | Ledger changes |
|---|---|---|
| Q1 = A (buckets and one small object through curl); defaults 1-3 accepted | None. | none |

**Implementation preview**

| Action | What changes | Where | How |
|---|---|---|---|
| Touch | checks B0-B8 run from the user's machine | outside the repository | the commands in the acceptance table; the user pastes the output with secrets removed |
| Modify | statuses of the checked assumptions in the registry | `research.md` §8 | the agent updates them after reading the output |

**Acceptance**

| # | Criterion | Proof | Expected |
|---|---|---|---|
| B2 | WHEN an anonymous S3 request arrives, THE SYSTEM SHALL reject it over valid TLS | `curl -w '%{http_code} %{ssl_verify_result}'` against the S3 host | `403 0` |
| B8 | WHEN a request targets a SeaweedFS port on the public IP, THE SYSTEM SHALL not answer | a `curl -m 5` loop over `8333`, `8888`, `9333` | a non-zero exit code for every port |

**Readiness**

| Item | Holds | Evidence |
|---|---|---|
| Paths and symbols verified | yes | hosts and ports read from the compose file of task 1 |
| Assumptions verified or user-decided | yes | `ASM-002` verified, `ASM-010` user-decided; the rest are checked by this task |
| Decisions in the decision log | yes | Q1 and defaults 1-3 |
| Acceptance checks behaviour | yes | B2-B8 read real answers |
| Interfaces named | yes | consumes the deployment of task 2; produces an updated registry |

Size M; the size test passes.

---

> **Decision — task 3 "Verify public boundaries"**
>
> The item that most needs your word: the dry run, because the task has many commands and failure branches.
>
> - approve: I write the task file
> - run the dry run first (recommended): a fresh agent reads the task without context and looks for gaps
> - amend: say what to change
> - delegate: turn the task into a sub-plan
```
