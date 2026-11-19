# 0001 · Local e-commerce analysis agent

**Status** — System delivered. Real-provider experiments and human review of the benchmark remain open. The work packages below describe the engineering delivery. [Product requirements](../PRD.md) · [Verification record](../verification.md)

| Work package | Delivered item | Trace |
|---|---|---|
| WP-01 | Data import and quality audits | FR-04, UT-01, FT-05 |
| WP-02 | Metric views and catalog | FR-01, UT-01 |
| WP-03 | Compatible model adapter and typed plans | FR-05, FT-07 |
| WP-04 | Bounded, read-only SQL | NFR-01, UT-02, FT-03 |
| WP-05 | Controller, evidence and run history | FR-01, FR-03, FT-01, FT-03 |
| WP-06 | Negative-review statistics and sensitivity analysis | FR-02, UT-03, FT-02 |
| WP-07 | Workbench and accessibility | FR-07, FR-08, UX-01, UX-02 |
| WP-08 | Direct/full comparison runner, 55 questions and evaluation report | FR-06, FT-08 |
| WP-09 | Deployment, CI, documentation and clean install | NFR-05, FT-04 |
| WP-10 | Acceptance record and public repository | RELEASE-01 |

Work began with data and metric definitions (01–02), followed by the adapter and guard (03–04), controller (05) and statistics (06). The workbench and evaluation runner (07–08) depend on those contracts. Their checks feed deployment and release (09–10).

When scope changes, identify the affected requirement and test IDs, then update the PRD, metric contract and verification record together.
