# Worked Example

> Three fragments from a real plan, showing the *density* the templates ask for. `templates.md`
> says which fields exist; this file says what goes in them. Read it once before writing your
> first artifact.

The example throughout is one small feature: an OAuth client that refreshes an expired access
token without the caller noticing.

---

## 1. An Asking round at Low confidence

Confidence came in at 54% — the codebase showed an OAuth client but no token storage, and the
request said only "handle token expiry". At Low, the band allows one opening batch. This is what
that looks like on screen:

> **My current assumptions:**
>
> - Refresh happens inside `OAuthClient`, transparently — callers never see a 401.
> - Tokens persist between processes; an in-memory cache is not enough.
> - The refresh token itself never expires within a session, so a failed refresh is an error, not
>   a re-login prompt.
>
> Four questions, most impactful first:
>
> 1. Where should tokens live between runs — the existing `~/.config/app/state.json`, the OS
>    keyring, or somewhere else? This decides whether we take a new dependency.
> 2. When a refresh fails (revoked token, network down), should the client raise, or fall back to
>    an interactive login?
> 3. Is concurrent refresh a real case here — two threads hitting a 401 at once — or is the client
>    single-threaded in practice?
> 4. Python floor: the repo's `pyproject.toml` says `>=3.9`, but the CI matrix only tests 3.11+.
>    Which is binding?
>
> Answer all, answer selectively, or say "proceed" and I'll continue on my stated assumptions.

Why these and not others: each one changes the plan. A question whose answer would not move a
task boundary, a REQ, or an acceptance criterion does not earn a slot in the batch.

The user answered 1, 2 and 4 and skipped 3. Confidence moved to 78% (Medium), so the next round
drops to one question at a time — and the skipped concurrency question becomes an entry in §8
Unconfirmed Assumptions, not a re-ask.

---

## 2. A filled-in task

Note the frontmatter is machine-readable, the `>` line stands alone as the index entry, and every
instruction names a file, a symbol and a decision.

```markdown
---
status: in-progress
milestone: M2
satisfies: [REQ-001, REQ-003]
depends_on: [task_001]
sub_plan: null
updated: 2026-09-04
---

# Task 002: Transparent token refresh

> Refresh an expired access token inside the client, so callers never see a 401.

## Context
`OAuthClient.request()` (`src/oauth/client.py:118-160`) currently returns the raw `httpx.Response`.
Token persistence landed in task_001 as `TokenStore.load()` / `.save()` (`src/oauth/store.py`),
which returns a `Token` dataclass with an `expires_at: datetime` field.

Shared context: see `plan.md §5` — the retry budget is also relevant to task_004.

## Files
| Action | Path |
|---|---|
| Modify | `src/oauth/client.py:118-160` |
| Create | `src/oauth/errors.py` |
| Create | `tests/oauth/test_refresh.py` |

## Instructions
1. In `src/oauth/errors.py`, define `class RefreshError(Exception)` carrying `.reason: str`.
2. In `client.py`, before each request, compare `token.expires_at` against
   `datetime.now(timezone.utc)` with a 30-second skew margin. The margin is not arbitrary — the
   server clock drifts and a token that expires mid-flight surfaces as a confusing 401.
3. When the token is stale, `POST` to `{base_url}/oauth/token` with
   `grant_type=refresh_token&refresh_token={token.refresh}`, then `store.save()` the result
   before retrying the original request once.
4. On a non-2xx refresh response, raise `RefreshError(reason=body.get("error", "unknown"))`.
   Do not fall back to interactive login — the user ruled that out (`research.md §3`).
5. Guard the refresh with the module-level `threading.Lock` already in `client.py:41`, so two
   threads hitting a 401 together perform one refresh, not two.

## Acceptance / Verification
| # | Criterion | Proof | Expected |
|---|---|---|---|
| 1 | WHEN the access token is expired, THE SYSTEM SHALL refresh it and retry once, transparently | `pytest tests/oauth/test_refresh.py -k transparent` | `1 passed` |
| 2 | WHEN the refresh call fails, THE SYSTEM SHALL raise `RefreshError` | `pytest tests/oauth/test_refresh.py -k raises` | `1 passed` |
| 3 | WHEN two threads see a 401 together, THE SYSTEM SHALL refresh once | `pytest tests/oauth/test_refresh.py -k concurrent` | `1 passed` |

## Progress Log
```

### The calibration that matters

The gap between a task that passes review and one that is actually executable in isolation:

| ❌ Not executable | ✅ Executable |
|---|---|
| `3. Add error handling to the parser.` | `3. In src/oauth/parse.py:87, wrap the json.loads(body) call in try/except json.JSONDecodeError; on failure return ParseResult(ok=False, error=str(e)) — do not raise, the caller at client.py:142 branches on .ok.` |
| `4. Add appropriate tests.` | `4. Add tests/oauth/test_parse.py::test_malformed_body_returns_not_ok feeding b"{" and asserting result.ok is False.` |
| `5. Handle the concurrency case.` | `5. Guard the refresh with the module-level threading.Lock at client.py:41, so two threads hitting a 401 together perform one refresh.` |

The left column is not *wrong* — it is unfinished. It defers the decision to whoever executes,
which is exactly what the plan exists to prevent. Every left-column step passes a superficial
read of the template; none survives `validate_plan.py --check` plus a reviewer who never saw the
conversation.

---

## 3. A Progress Log entry

Fresh evidence means the literal command and what it actually printed — not a summary of it, and
not a claim about it.

```markdown
#### 2026-09-04
- Status: in-progress -> done
- Did: added the skew-margin check and the locked refresh path in `client.py`; `RefreshError`
  in the new `errors.py`; three tests.
- Verified:
  - Run: `python scripts/validate_plan.py plans/plan-oauth-login --check`
    Result: `OK: ... is consistent (4 task(s)) -- 2 Done / 1 In Progress / 1 Not Started / 0 Blocked / 0 Delegated`
  - Run: `pytest tests/oauth/test_refresh.py -q`
    Result: `3 passed in 0.41s`
  - Run: `pytest tests/oauth -q`
    Result: `17 passed in 1.902s`  (ran the whole package to check nothing regressed)
- Review: fresh subagent over `src/oauth/client.py`, `errors.py`, `tests/oauth/test_refresh.py`.
  1 Important — the 30-second margin was hard-coded in two places; extracted to
  `CLOCK_SKEW = timedelta(seconds=30)` at `client.py:44`. 0 Critical. 1 Minor deferred
  (docstring wording), noted here rather than fixed.
```

What makes this entry load-bearing rather than decorative: a reader six weeks later can rerun
every command, see the same output, and knows what the reviewer objected to and what was done
about it.

Compare with what fails the gate:

| ❌ | Why it fails |
|---|---|
| `Verified: tests pass` | No command, no output. Unfalsifiable. |
| `Verified: Run: pytest — Result: all green` | "all green" is a paraphrase, not the output. |
| `Verified: (from the earlier run) 3 passed` | Evidence must be produced in this session. |
| `Verified: implementation looks correct` | Re-reading your own diff is not verification. |
