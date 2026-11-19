"""15 opt-in acceptance cases for the real Kaggle data. Run as described in README.md."""

import duckdb

from oracle import group_summary


def test_k01_import(probe):
    """Imported tables match the source files
    Fetch the catalog and compare the row count and SHA-256 of each imported file with
    its downloaded CSV. The import covers seven core tables and the category translation table.
    The download manifest also includes geolocation."""
    cat = probe.api("GET", "/api/catalog")
    expected = {
        name: {"rows": entry["rows"], "sha256": entry["sha256"]}
        for name, entry in probe.ref.files.items()
        if name != "olist_geolocation_dataset.csv"
    }
    observed = {
        v["filename"]: {"rows": v["rows"], "sha256": v["sha256"]}
        for v in cat["audit"]["files"].values()
    }
    probe.check("Row counts and SHA-256 hashes of imported CSVs", expected, observed)
    probe.check(
        "Dataset source and snapshot ID",
        ["olist", probe.snapshot],
        [cat["source"], cat["snapshot"]],
    )


def test_k02_order_count(probe):
    """Total delivered orders
    Ask for the delivered order count. Count distinct order IDs with status
    delivered in the orders CSV and compare the total with the response."""
    answer = probe.ask("Show total delivered order count.")
    probe.check(
        "Distinct delivered orders", [{"order_count": len(probe.ref.delivered)}], answer["table"]
    )


def test_k03_revenue(probe):
    """Item revenue from delivered orders
    Ask for total item revenue. Sum item prices for delivered orders using decimal
    arithmetic, then compare the API result with the CSV total to the cent in Brazilian reais."""
    answer = probe.ask("What is total item revenue?")
    probe.check(
        "Delivered item revenue (BRL)",
        [{"item_revenue": float(probe.ref.revenue)}],
        answer["table"],
    )


def test_k04_aov(probe):
    """Average order value
    Divide item revenue from delivered orders by the number of distinct delivered
    orders. Compare the result with the reported average to the nearest cent."""
    answer = probe.ask("What is the average order value?")
    want = round(float(probe.ref.revenue / len(probe.ref.delivered)), 2)
    probe.check("Average order value (BRL)", want, round(answer["table"][0]["aov"], 2))


def test_k05_months(probe):
    """Monthly delivered orders in 2017
    Group delivered orders in the CSV by purchase month. Compare every month,
    count and position in the API response for 2017 with the reference series."""
    answer = probe.ask("Show monthly delivered orders in 2017.")
    want = [
        {"month": m + "-01", "order_count": n}
        for m, n in sorted(probe.ref.month_counts.items())
        if m.startswith("2017-")
    ]
    probe.check("Delivered order count by month", want, answer["table"])


def test_k06_categories(probe):
    """Top ten categories by 2018 item revenue
    Join delivered items to products and category translations in the CSVs, keeping
    the source category when a translation is missing. Rank by revenue descending, then
    by category name ascending for ties. Compare all ten categories and amounts."""
    answer = probe.ask("What are the top 10 categories by item revenue in 2018?")
    ranked = sorted(
        probe.ref.categories_2018.items(), key=lambda pair: (-pair[1], pair[0])
    )[:10]
    probe.check(
        "Top ten categories and item revenue (BRL)",
        [{"category": k, "item_revenue": float(v)} for k, v in ranked],
        answer["table"],
    )


def test_k07_half_open(probe):
    """January revenue with an exclusive end date
    Request revenue for purchases from January 1 up to February 1, 2018. Sum delivered
    items purchased in January in the CSVs and check both date bounds in the query evidence."""
    start, end = "2018-01-01", "2018-02-01"
    answer = probe.ask("What is total item revenue?", start=start, end=end)
    probe.check(
        "January item revenue (BRL)",
        [{"item_revenue": float(probe.ref.month_revenue["2018-01"])}],
        answer["table"],
    )
    filters = answer["evidence"]["filters"]
    probe.check("Purchase date bounds", [start, end], [filters["start"], filters["end"]])


def test_k08_join(probe):
    """Item and payment totals for orders with multiple rows
    Select delivered orders with multiple item rows and multiple payment rows.
    Sum each file separately per order. Compare the order count, item revenue and
    payments with the same cohort in the read-only order_summary view."""
    sql = """SELECT count(*),sum(item_revenue),sum(payment_total) FROM order_summary
        WHERE status='delivered' AND item_count>1 AND order_id IN
        (SELECT order_id FROM order_payments GROUP BY order_id HAVING count(*)>1)"""
    probe.record["requests"].append({"method": "DuckDB read-only", "executed_sql": sql})
    with duckdb.connect(str(probe.db), read_only=True) as con:
        count, items, paid = con.execute(sql).fetchone()
    assert probe.ref.fanout["orders"] > 0
    probe.check(
        "Order count, item revenue and payments for the cohort",
        probe.ref.fanout,
        {"orders": count, "items_brl": float(items), "payments_brl": float(paid)},
    )


def test_k09_sample(probe):
    """Delivery investigation cohort and exclusions
    Classify each source order as undelivered, missing a delivery timestamp, missing
    a valid review, or included. Compare the counts with the delivery investigation."""
    result = probe.api("POST", "/api/investigation", {"grain": "timestamp"})
    probe.check("Included and excluded orders", probe.ref.exclusions, result["exclusions"])


def rounded(summary):
    return {
        "groups": {
            k: {**g, "rate": round(g["rate"], 9)} for k, g in summary["groups"].items()
        },
        "risk_difference": round(summary["risk_difference"], 9),
        "ci95": [round(v, 9) for v in summary["ci95"]],
    }


def test_k10_timestamp(probe):
    """Difference in negative review rates by delivery timestamp
    Use each order's latest valid review. Flag deliveries that arrived after the estimated
    timestamp. Independently compute each group's negative review count and rate, the risk
    difference, and its Newcombe-Wilson 95% confidence interval. Compare to nine decimal places."""
    result = probe.api("POST", "/api/investigation", {"grain": "timestamp"})
    actual = {
        **result,
        "groups": {
            g["group"]: {k: g[k] for k in ("n", "negative", "rate")}
            for g in result["groups"]
        },
    }
    probe.check(
        "Review counts, rates, risk difference and interval",
        rounded(group_summary(probe.ref.groups["timestamp"])),
        rounded(actual),
    )
    probe.check(
        "Pearson chi-squared test with p below 0.001",
        ["pearson_chi2", True],
        [result["test"], 0 <= result["p_value"] < 0.001],
    )


def test_k11_calendar(probe):
    """Sensitivity to measuring delays by calendar day
    Compare actual and estimated delivery dates, counting same-day arrivals as on time.
    Check the order count and negative review count for both groups against the CSVs."""
    result = probe.api("POST", "/api/investigation", {"grain": "day"})
    probe.check(
        "Orders and negative reviews under the calendar-day definition",
        probe.ref.groups["day"],
        {g["group"]: [g["n"], g["negative"]] for g in result["groups"]},
    )


def test_k12_empty(probe):
    """Revenue request for a year without orders
    Ask for 2099 item revenue. This dataset has no orders from that year.
    Expect the insufficient_data status and an empty result table."""
    answer = probe.ask("What is total item revenue in 2099?")
    probe.check(
        "Status and result table", ["insufficient_data", []], [answer["status"], answer["table"]]
    )


def test_k13_invalid_dates(probe):
    """Reversed date range
    Submit a delivery investigation with an end date earlier than its start. Expect
    HTTP 422 and a validation error that explains the required date order."""
    result = probe.api(
        "POST",
        "/api/investigation",
        {"start": "2018-02-01", "end": "2018-01-01"},
        code=422,
    )
    probe.check(
        "Validation error explains the required date order",
        True,
        any("End date must be later than start date" in e["msg"] for e in result["detail"]),
    )


def test_k14_unavailable_metric(probe):
    """Clarification for an unavailable profit metric
    Ask for after-tax net profit, which the offline catalog does not cover. Expect
    a request for clarification, zero result rows and no executed SQL."""
    answer = probe.ask("What was net profit after tax in 2018?")
    probe.check(
        "Clarification status, row count and executed SQL",
        ["clarification_required", 0, None],
        [answer["status"], len(answer["table"]), answer["evidence"]["sql"]],
    )


def test_k15_replay(probe):
    """Replaying a saved revenue query
    Ask for 2017 item revenue and retrieve the saved run by ID. Check its snapshot,
    question, SQL and output. Replay the SQL on the same read-only snapshot and
    reconcile both amounts with the 2017 CSV total."""
    answer = probe.ask("What is total item revenue in 2017?")
    stored = probe.api("GET", "/api/runs/" + answer["request_id"])
    probe.check("Retrieved run matches the original response", True, stored == answer)
    probe.check("Saved snapshot ID", probe.snapshot, stored["evidence"]["snapshot"])
    sql = stored["evidence"]["sql"]
    with duckdb.connect(str(probe.db), read_only=True) as con:
        value = con.execute(sql).fetchone()[0]
    expected = float(
        sum(v for m, v in probe.ref.month_revenue.items() if m.startswith("2017-"))
    )
    probe.check(
        "CSV total compared with saved and replayed totals (BRL)",
        [expected, expected],
        [stored["table"][0]["item_revenue"], float(value)],
    )
