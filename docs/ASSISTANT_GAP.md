# Today versus proposed

This contrast is a pattern demonstration. It is not an observation of Ferrara’s or Ferrero’s internal systems. No production portal was probed.

## Today

A commercial question — trade rate, win rate, brand margin — becomes a one-off export or an email to an analyst. The answer depends on who pulled the file. Nothing records the definition, the role scope, or the fact that some questions cannot be answered from the warehouse.

## Proposed

The assistant accepts a short question and does one of two things:

1. Route it to one approved metric, return the rows, the SQL, and the bound account parameter, and write an audit row.
2. Refuse it when the question asks for syndicated share, a demand-planning forecast, or an MDM / S/4 program.

The router is deterministic keyword matching. Offline, it is not a language model. There is no path that invents a number outside `METRICS`.

## What a later model could add

A semantic layer can sit in front of the same metric list. A model may paraphrase the question and choose a metric id. It should still be unable to emit warehouse SQL of its own. The audit row stays. The refusals stay.
