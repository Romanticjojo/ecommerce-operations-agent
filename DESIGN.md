# Commerce Lens interface design

Commerce Lens is the workbench for **E-commerce Operations Agent**. Operators need to read an amount, see which orders contributed, and trace the result to its query. The Apple design reference informed the system typography, white surfaces and blue controls. The application uses its own graphics and the fonts installed on the device. [Design reference](https://designmd.me/discover/apple)

## Visual system

| Token | Value and use |
|---|---|
| Background / surface | `#F5F5F7` / `#FFFFFF` |
| Text / secondary text | `#1D1D1F` / `#6E6E73`. Check secondary text against its background. |
| Border | `#D2D2D7` |
| Accent / hover | `#0071E3` / `#0055C6` for interactive elements |
| Status | Pair green, orange or red with a text label or icon. Give loading, empty, configuration and error states a readable message. |
| Type | `-apple-system`, `BlinkMacSystemFont`, system sans-serif. Body 15–17 px, line height 1.5–1.65. Titles 36–48 px on desktop and 28–32 px on mobile, weight 600. |
| Numbers | Use tabular figures and label amounts in BRL. |
| Spacing | 4, 8, 12, 16, 24, 32, 48 and 64 px |
| Corners | Controls 10–12 px, panels 18–24 px |
| Elevation | Delineate inputs and panels with fine borders. Reserve subtle shadows for depth. |

Charts show actual results and include a table alternative. Use white space and clear headings to guide the reader from the question to the evidence.

## Pages and interactions

The desktop layout uses a 232 px navigation rail and a main area up to 1,280 px wide. Show dataset, mode and configuration status near the top. On small screens, collapse navigation, stack panels in reading order and let wide tables scroll within their containers.

- **Overview.** Identify the dataset and observed purchase dates. Show delivered item revenue beside BRL, the freight definition, order count and average order value. Pair these figures with the monthly trend. Show category ranking, review sample and a link to the delivery investigation. When the snapshot is empty, link to data preparation.
- **Ask the agent.** Keep custom questions, analysis skills and their evidence in one workspace. Pair the composer with a compact skill index. On narrow screens, show a native skill selector above the form. A selected skill shows its purpose, scope, question and expandable steps before execution. Keep purchase dates editable and display the local execution mode. Preserve the custom draft while users inspect a skill. Bring the completed answer into focus, with its interpretation notes, data, copyable SQL and export.
- **Delivery comparison within Ask.** Link here from the overview and the older investigation bookmark. State the eligibility rule. Show group sizes, negative-review rates, their difference, the confidence interval and test result. Keep the observational limitation visible. Switching between timestamp and calendar-day definitions updates the comparison.
- **Data reference within Ask.** Link here from the overview and the older data bookmark. Show tables, row grain, metric definitions, import quality, timestamp and snapshot. Keep wide dictionary and results tables independently scrollable.
- **Evaluation.** Show per-question outcome, mode, model, snapshot, accuracy and timing. Give the user an explicit empty state before a run and explain local model configuration. Identify the source of every result.
- **History.** Let the reader reopen a recorded request and inspect or export its evidence.

## Accessibility checks

Provide 44 × 44 px interaction targets, accessible names, associated input labels, visible focus and keyboard access throughout. Announce state changes where appropriate. Use 120–200 ms transitions and respect reduced-motion preferences. Check widths of 390, 768 and 1,440 px, local horizontal scrolling for tables and browser zoom at 200%.
