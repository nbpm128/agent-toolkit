# Phase 6 — Finishing

Integrate completed work cleanly. The integration decision is the user's — this phase verifies,
detects the environment, presents the choices, and executes the one chosen.

**Announce at start:** "Using planning — Phase 6: Finishing. Integrating this work."

**Core principle:** verify tests → detect environment → present options → execute choice → clean
up.

**Prerequisite:** the plan's tasks are `Done` and, ideally, certified via Phase 5. If acceptance
has not run, offer to run it first.

## Gate: git integration is opt-in

This phase performs **git** operations (branch, merge, push, PR). Git in this workflow is opt-in —
many users manage integration themselves. **Only enter this phase when the user has asked you to
handle git.**

- If the user has not asked for git integration, do **not** enter it. Report that the plan is
  complete and verified, and leave branch/merge/PR to them. You may offer once: "Want me to handle
  git integration (merge / PR), or will you take it from here?"
- Even inside this phase, **push and PR are dangerous, outward-facing operations**: confirm the
  exact remote / branch / base before running them, and never push or open a PR on a general "yes"
  alone.
- Verifying the test suite (Step 1) is safe and read-only — you may always do that. Everything
  past Step 4 that writes git state requires the user's explicit choice.

## Step 1 — Verify the full suite

Run the project's whole test suite (`npm test` / `pytest` / `cargo test` / `go test ./...` —
whatever the repo uses).

- **Fail** → report the failures and stop. No integration menu on a red suite.
- **Pass** → continue. State the result with evidence (e.g. `42/42 pass`).

## Step 2 — Detect the git environment

```bash
GIT_DIR=$(cd "$(git rev-parse --git-dir)" 2>/dev/null && pwd -P)
GIT_COMMON=$(cd "$(git rev-parse --git-common-dir)" 2>/dev/null && pwd -P)
WORKTREE_PATH=$(git rev-parse --show-toplevel)   # capture now; later steps change directory
```

| State | Menu | Cleanup |
|-------|------|---------|
| `GIT_DIR == GIT_COMMON` (normal repo) | 3 options | nothing to clean up |
| `GIT_DIR != GIT_COMMON`, named branch | 3 options | remove the worktree after integration |
| `GIT_DIR != GIT_COMMON`, detached HEAD | 2 options (no local merge) | externally managed — leave in place |

## Step 3 — Confirm the base branch

The base is whatever this work forked from — usually named in `plan.md`, the branch upstream, or
the conversation. If unknown, ask: "This branch split from `<best guess>` — correct?" Merging into
the wrong base is expensive to undo, so confirm before merging.

## Step 4 — Present options (verbatim, then wait)

**Normal repo / named-branch worktree:**

```
Implementation complete and tests pass. What would you like to do?

1. Merge back to <base-branch> locally
2. Push and create a Pull Request
3. Keep the branch as-is (I'll handle it later)

Which option?
```

**Detached HEAD:**

```
Implementation complete and tests pass. You're on a detached HEAD (externally managed workspace).

1. Push as a new branch and create a Pull Request
2. Keep as-is (I'll handle it later)

Which option?
```

Wait for the answer. Never discard the work unless the user explicitly asks. Creating a PR is an
outward-facing action — confirm the target and get the go-ahead before pushing/opening it.

## Step 5 — Execute the choice

- **Merge locally:** fast-forward or `--no-ff` per repo convention into the confirmed base; report
  the merge commit.
- **PR:** push the branch, open the PR (title + body summarizing the plan and what shipped), and
  return the URL. Confirm before opening.
- **Keep as-is:** do nothing to the branch.

## Step 6 — Clean up

- Normal repo: nothing to remove.
- Named-branch worktree, after a successful merge/PR: offer to remove the worktree
  (`git worktree remove <path>`), from a safe CWD (the main repo root, captured earlier).
- Detached HEAD: leave the workspace in place.

## Step 7 — Close out the plan

Update `plans/plan-<plan-name>/`:

- Set every integrated task's status and `_index.md` to reflect completion.
- Append a `plan.md` Revision Log line: date + how the work was integrated (merged to X / PR #N /
  kept).
