# Merchant scoring and product feedback

Use **Ask the agent → Merchant scorecard** to compare sellers. Use **Reviews and aftercare** to find products generating the largest low-rating workload. Both skills run locally against the active snapshot. Each answer includes the executed SQL, purchase-date filters and sample counts.

## Which orders count?

The merchant score covers delivered orders where every item points to the same known Olist seller. The product review analysis independently requires every item to point to the same known product. Multiple units of that product count as one customer experience. If an order contains two products from one seller, it can contribute to the seller score. Its rating is ambiguous at the product level and is excluded from product results. Orders with missing or unmatched identifiers are excluded from the corresponding scope.

The date filter applies to purchase timestamps, including the start and excluding the end. Among reviews with an integer score from 1 through 5, the analysis selects the most recently answered per order. Ties use latest survey creation, then ascending review ID, then the original CSV row number. The score uses final recorded outcomes for orders purchased during the filter window. A historical cutoff for what the analyst knew on the purchase date would require a separate as-of analysis.

## Score calculation

Each seller receives two component scores on a 0–100 scale.

| Component | Observation | Weight |
|---|---|---|
| Customer rating | Convert a valid 1–5 star review into points using `(stars − 1) / 4`. One star contributes 0, three stars 0.5 and five stars 1. | 70% |
| On-time delivery | One point if the actual delivery calendar date falls on or before the estimated date, zero otherwise. Both timestamps must be present. | 30% |

Compute an order-weighted marketplace average for each component using **all** attributable sellers in the selected period, including sellers below the ranking thresholds. Let `r` be the mean normalized rating and `d` the share of timed deliveries on time. Let `R` be a seller's sum of normalized rating points, `n` its count of valid ratings, `T` its count of on-time deliveries and `m` its count of timed deliveries.

```text
rating component    = 100 × (R + 20 × r) / (n + 20)
delivery component  = 100 × (T + 20 × d) / (m + 20)
merchant score      = round(0.70 × rating component + 0.30 × delivery component, 2)
```

The 20-observation prior pulls small samples toward their period average. At 20 observations the seller and marketplace each carry half of the component's weight. At 100 observations, the seller carries five-sixths. Each denominator counts its own available observations. An unrated order can count for punctuality, and an order missing a delivery date can still contribute its rating.

A seller needs **at least 20 rated orders and 20 timed deliveries** to rank. These cutoffs, the prior strength and the weights are operational choices. They give customer ratings greater influence and reduce the influence of small samples. The weights have not been fitted to profit, repeat purchase or service cost. Carrier performance and customer mix can influence both components. Use the score to choose which merchants to examine and read the sample counts before drawing performance conclusions.

Sort by the final two-decimal score, descending. Equal scores share a competition rank, for example 1, 1, 3. Within a tied score, seller ID sets the display order. The table includes the full eligible population, with pagination in the workbench. Export the result to retain every ranked seller and its component scores.

## Reading the review evidence

The Portuguese rules analyze the selected review's optional title and message. They lowercase the text, remove accents and normalize punctuation and spaces. Common phrases handle simple negations, such as *não recomendo* and *sem problemas*, before individual words are matched. The complete patterns appear in each run's SQL.

| Result | Interpretation |
|---|---|
| Positive / negative | The text contains a recognized cue of one polarity only. |
| Mixed | Positive and negative cues occur together. |
| Unclassified | Text is present, but no cue matched. |
| No written comment | A blank title and message contribute to rated orders only. |
| Text coverage | Number of rated orders with a nonblank title or message divided by rated orders. |

Written comments are optional. The rank uses stars and delivery outcomes so that a merchant's score does not depend on how many customers choose to write comments. Sarcasm, spelling variants, context and subtle negations can escape the rules. The labels describe detected expressions and have no calibrated probability or measured human-label accuracy.

The product view shows one overall row and up to 20 products ordered by number of 1–2 star ratings, total rated orders, then product ID. The volume ordering identifies where the most customers reported a poor experience. The low-rating rate and sample count give context when comparing high- and low-volume products.

Four optional theme counts look only at text from **1–2 star reviews**. Delivery uses mentions of lateness, deadlines, carriers or freight. Quality covers damage, defects, fragility or function. Listing covers descriptions, photos, wrong or different items. Service covers support, contact and responses. Each order contributes at most one count per theme and can appear in multiple themes. A mention prompts investigation. The text alone cannot establish which party caused a problem, and Olist has no case-resolution or refund ledger. Raw text stays inside the local DuckDB query. The output contains aggregate counts and public anonymized product and seller identifiers.

## Worked example from Olist v2

With the full purchase range, 95,203 delivered orders map to one known seller each. Of these, 94,571 have a valid rating and 95,195 have both delivery dates. Across 2,948 attributable sellers, 784 meet both ranking thresholds. The marketplace rating prior is `75,022.5 / 94,571 = 0.793293`, and the delivery prior is `88,674 / 95,195 = 0.931499` (rounded).

| Rank | Seller ID | Adjusted rating / 100 | Adjusted delivery / 100 | Score / 100 |
|---|---|---:|---:|---:|
| 1 | `48efc9d94a9834137efd9ea76b065a38` | 92.20 | 97.42 | 93.76 |
| 2 | `b410bdd36d5db7a65dcd42b7ead933b8` | 90.11 | 97.79 | 92.41 |

The first seller received 33 five-star ratings and all 33 timed orders arrived on time. Its score is below 100 because the calculation incorporates marketplace experience. It had 26 written reviews. The rules recognized positive language alone in 22 and classified the remaining four as unclassified.

For products, 92,673 rated orders map to a single product. Of these, 11,206 received one or two stars and 38,783 included written feedback. The rules marked 20,179 comments positive, 5,016 negative, 616 mixed and 12,972 unclassified. Delivery was mentioned in 2,271 low-rating cases. The product with the largest low-rating workload, `99a4788cb24856965c36a24e339b6058` in bed/bath/table, had 53 low ratings in 397 rated orders. Fifteen of its low ratings mentioned quality and eleven mentioned delivery. A product owner could inspect quality complaints first while independently reviewing delivery handling.

The CSV oracle reproduced the full set of 784 merchant IDs, ranks, scores, components and denominators. It also reproduced all 20 product IDs in order, their rating and comment denominators and the population totals. Run it from the repository root with the directory containing the original CSVs and the imported database path. [Independent CSV oracle](../evaluation/skill_checks/merchant_oracle.py)

```sh
.venv/bin/python -m evaluation.skill_checks.merchant_oracle /path/to/olist-csvs runtime/commerce.duckdb
```

The fixture tests cover attribution, prior weights, ties, missing fields and date boundaries. [Review skill tests](../tests/test_review_skills.py)
