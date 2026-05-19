# Notes — Schema contract

- **Prod bronze default:** `{tables: "evolve", columns: "freeze", data_type: "freeze"}`. New tables happen (sources add objects); new columns are a human decision.
- **First-run paradox.** You can't freeze `tables` on the very first run — there's no schema yet. dlt-hub's idiom: run once to materialize, *then* tighten the contract in version 2.
- **`discard_row` is forensic gold.** Bad event blocks the load? `discard_row` drops only the offender, keeps the rest, logs the drop. Great for marketing-pixel firehoses where 0.1% of rows are malformed.
- **Pydantic models** can stand in for column lists — `columns=MyPydantic` — and the schema-contract mapping is: `freeze→forbid`, `evolve→allow`, `discard_value→ignore`.
- **Layer-aware policy.** Bronze is permissive on `tables`, strict on `columns`. Silver / gold should be strict on all three — drift must die at bronze.
