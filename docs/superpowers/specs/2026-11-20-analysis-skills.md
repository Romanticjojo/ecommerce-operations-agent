# Operating decisions from the Olist order history

The operator starts in Ask the agent, selects a business question, checks the skill's population and steps, and runs it against the local snapshot. For each decision the operator can review the underlying counts, inspect the executed SQL, export the result and reopen it in history.

| Operator decision | Skill and observable evidence |
|---|---|
| Explain a change in sales | Sales growth compares buyers, purchase frequency, order value and category contributions. |
| Prioritize returning buyers | Retention uses the cross-order customer key and observed follow-up. |
| Review the range | Products and categories measures changes in purchased units. |
| Investigate pricing | Price and volume compares observed prices within products. |
| Choose sellers for support | Seller growth compares seller performance over time. |
| Investigate delivery risks | Fulfillment compares sellers and state lanes with denominators and reviewed-order counts. |
| Find recurring after-sales issues | Reviews and aftercare relates low ratings to written sentiment and recurring Portuguese-language themes at product level. |
| Rank merchants fairly | Merchant scores disclose attribution, eligibility, weights, shrinkage, tie handling, review coverage and sample sizes. |
| Plan the next sales period | Product trends identify individual SKUs with sustained movement and a conditional next action. |

The original navigation divides one analysis across three pages. Consolidate its entry points in Ask, retaining review inference, date granularity, exclusions, the data dictionary and import-quality information. Preserve existing deep links. Users should be able to complete these workflows on mobile with a keyboard or touch.

Seven Olist source relations and the category translation are already present. Use read-only queries on the installed snapshot. Product and seller identifiers are anonymous. Written reviews describe orders and can contain identifying text. Publish only aggregates, use unambiguous attribution and keep comments local. Observed sales do not measure stock on hand, missed demand, traffic, coupon lift or intent to churn.

The analytical contract is a repeatable, named procedure with an example question, scope, steps and deterministic evidence. Generic model responses carry a greater reproducibility cost for rankings. Separate analytical pages add navigation and duplicate the existing workbench. Named procedures keep the original question and evidence together in both offline and provider-configured installations.
