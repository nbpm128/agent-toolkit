{{Starting outline for an audit, written as the questions the reader asks, in their order. Row
1 is the summary: the answer first. Replace every title with the answer to its question, in at
most 12 words ("Two of five defences are missing"). `proves` says what the visual shows that makes the title true.
Merge, split or reorder rows to fit the data, but keep one question per section and each fact in
one place. `part` is summary, main, method or appendix; depth detailed needs a method and an
appendix row. Show this table in the chat and get the user's approve before writing src. Delete
this paragraph when the table is filled.}}

| # | part | title | visual | proves | detail |
|---|---|---|---|---|---|
| 1 | summary | {{The answer in one line}} | r-summary | {{what happened, what it means, what the reader must do}} | {{the action line is addressed to the audience in the brief}} |
| 2 | main | {{Where are the load and the risk?}} | r-chart (bar or treemap) | {{breakdown by service, host or component}} | {{one unit per quantity}} |
| 3 | main | {{Which controls hold and which do not?}} | r-status or r-table with highlight | {{every checked item and its state}} | {{ok / warn / fail}} |
| 4 | main | {{Which risks matter?}} | r-grid of r-callout risk | {{each risk with its evidence and impact}} | {{the evidence, not the guess}} |
| 5 | main | {{What should be fixed, in what order?}} | r-callout decision + r-status | {{the fixes ranked by risk and effort}} | {{only open items}} |
| 6 | method | {{Data & method}} | r-text + r-table | {{what the verdict rests on}} | {{period, data, what was excluded or redacted, limitations}} |
| 7 | appendix | {{Findings in full}} | r-table with highlight and mono | {{every finding the reader may look up}} | {{what, where, how often, status; terms}} |
