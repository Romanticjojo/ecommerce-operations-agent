# Acceptance plan

The DSC 200 project update selects UT-01 through UT-03 and FT-01 through FT-03 for grading. This plan defines their inputs and expected outcomes. The verification record reports what was exercised and which checks still require a model or human reviewer. [Verification record](verification.md)

## Selected unit tests

### UT-01 · Preserve totals across multiple items and payments

- **Requirements** — FR-01, FR-04, NFR-02.
- **Precondition and input** — An isolated fixture has one delivered order, item prices of BRL 10 and 20, and payments of BRL 12 and 18.
- **Steps** — Import the fixture, build the views, query the order and monthly summaries, then repeat the import and queries.
- **Expected** — One order, BRL 30 item revenue, BRL 30 payment total and BRL 30 average order value on each run.
- **Postcondition** — The fixture and snapshot identifier match their initial values. The test database can be discarded.

### UT-02 · Confine execution to approved analytical queries

- **Requirements** — NFR-01, FR-03.
- **Precondition and input** — Record the fixture database hash and table count. Put a unique marker in an external test file. Enable read-only resource-limited execution.
- **Steps** — Run the supplied prohibited-operation and external-access cases, including system data, multi-statement and unsupported query forms. Run a permitted aggregate.
- **Expected** — The prohibited cases produce rejection or bounded termination, the external marker stays private and the permitted aggregate returns the expected value.
- **Postcondition** — Database and source file contents match their original values, the worker exits and errors contain no credentials.

### UT-03 · Recover a known difference in negative-review rates

- **Requirement** — FR-02.
- **Precondition and input** — Twenty late orders include ten negative reviews. Twenty on-time orders include two. Add repeated reviews, invalid scores, missing dates and cancelled orders.
- **Steps** — Compare the order-level analysis with hand counts and a separate SciPy test of the 2 × 2 table. Exercise a small sample, empty group, constant outcomes and delivery later on the promised day.
- **Expected** — Group rates are 0.50 and 0.10 with a risk difference of 0.40. The 95% interval is approximately [0.116, 0.613]. Each eligible order appears once. Expected cell counts determine the test, and an empty group yields a null p-value.
- **Postcondition** — Inputs remain reusable. The result identifies the sample grain, filters, exclusions and statistical limitations.

## Selected functional tests

### FT-01 · Trace a category ranking to its source

- **Requirements** — FR-01, FR-03, FR-05, FR-07.
- **Precondition and input** — Start the workbench on a known snapshot using the offline planner or controlled test provider. Ask “Show the top 10 product categories by item revenue in 2018.”
- **Steps** — Submit, switch chart/table views, expand evidence, copy SQL and reopen the saved run.
- **Expected** — Values and order agree with independent SQL. The chart matches its table. The result identifies delivered orders, the purchase year, BRL and the active mode.
- **Postcondition** — The run ID retrieves the original SQL and snapshot. The analytical database is unchanged. A controlled provider exercises the contract. Real-model performance is evaluated separately.

### FT-02 · Compare both definitions of late delivery

- **Requirements** — FR-02, FR-03.
- **Precondition and input** — Include late and on-time orders, a delivery after midnight on its promised date, repeated reviews and missing fields. Ask “Are late deliveries associated with negative customer reviews?”
- **Steps** — Select a purchase period and run the investigation with timestamp and calendar-day definitions. Inspect each run's evidence.
- **Expected** — Counts, rates, risk difference, interval and p-value agree with independent calculations. The example order changes group, the eligible total stays constant, and the heading identifies the active definition. Show exclusions and the observational limitation.
- **Postcondition** — Both runs retain their own definitions, sample and results.

### FT-03 · Recover after an unsuccessful request

- **Requirements** — FR-03, NFR-01, NFR-03.
- **Precondition and input** — Save one successful request and the database hash. Use a controlled provider for failure cases.
- **Steps** — Ask for an unsupported causal explanation, an empty year and a prohibited operation. Simulate provider authentication failure, a provider timeout and a query timeout. Submit another supported question.
- **Expected** — Display clarification, rejection, insufficient data or error as appropriate. Preserve the question, keep credentials private and permit at most one bounded repair where supported. The final valid query succeeds.
- **Postcondition** — Accepted requests have retrievable run IDs and outcomes, the database hash matches, and the timed-out worker has exited.

## Additional acceptance criteria

| ID | Area | Pass condition |
|---|---|---|
| FT-04 | Clean install | A fresh clone can install, prepare data, start and run tests using the README. |
| FT-05 | Import failure | Missing required columns and invalid types produce an error and preserve the previous snapshot. |
| FT-06 | Offline operation | The demo handles its supported examples and asks for clarification when necessary. The UI identifies the mode. |
| FT-07 | Model adapter | URL, model and credentials are configurable. Invalid responses, rate limits and provider errors are identifiable. Missing usage remains null. |
| FT-08 | Evaluation | All 55 cases have a category, reference or expected status, tolerance and review state. Direct and full variants use the same conditions. |
| UX-01 | Responsive layout | No page overflow at 390, 768 or 1,440 px. Wide tables scroll locally. |
| UX-02 | Accessibility | Verify keyboard navigation, focus, labels, status feedback, table alternatives and 200% zoom. |
| PERF-01 | Performance | Record hardware, data size and query count. Measure local SQL and end-to-end times separately. |
| RELEASE-01 | Publication | Verify public access, commit identity and actual CI status. Exclude credentials, personal details and original course attachments. |

Report deployment, synthetic fixtures, real Olist checks, and real-model/human-reviewed evaluation separately. Document failed cases and their original denominators. [Kaggle v2 acceptance suite](../evaluation/kaggle_olist/README.md)
