# Independent fact-check

> Read before the first fact-check in a session. Use it when claims state implementation status,
> specific function, table or API names, numbers or deadlines. The checker sees only the
> package below, not this conversation.

## Package

Hand over exactly these, and nothing "as discussed":

- `claims.md`
- `brief.md` (for the variant in scope and the source scopes)
- every file listed in the brief's Sources table
- read access to the code the sources describe, when there is any

## Prompt

```
You are checking claims for a report. For every row of claims.md:

1. Open the cited source at the cited lines.
2. Verdict: SUPPORTED (the lines say it), WEAKER (the source says less, e.g. "proposed" vs
   "live", "in code" vs "deployed"), CONTRADICTED, or NOT FOUND.
3. For WEAKER or CONTRADICTED, quote the lines and state what the claim may honestly say.
4. Flag any claim whose wording comes from a source with scope "out".

Then check the claims against each other:

5. Two claims that measure the same thing (a rate, a count, a date, a duration) must agree, or
   each must name its period and unit. List every pair that disagrees.
6. Every time is in the brief's `timezone`. List every claim in another zone.

If code is available, you may grep it to confirm that names exist. A name in a checkout proves
the code exists, not that it is deployed.

Return one table: id | verdict | evidence (file:line) | honest wording. Then a second table:
ids | conflict (numbers that disagree, or a time in another zone) | fix. No other prose.
```

## Acting on the result

- SUPPORTED: keep.
- WEAKER: rewrite the claim and the report text to the honest wording.
- CONTRADICTED or NOT FOUND: remove the claim from the report, or find the right source.
- Rebuild and review again: the text changed.
