"""Order-level inference on independent late and on-time delivery groups."""

from datetime import date
from math import hypot

import duckdb
from scipy.stats import binomtest, chi2_contingency, fisher_exact

from .data import read_audit, rows


def _date(value):
    if value is None:
        return None
    try:
        return date.fromisoformat(str(value)).isoformat()
    except ValueError:
        raise ValueError('Use an ISO date (YYYY-MM-DD).') from None


def _group(n, negative):
    return {'n': n, 'negative': negative, 'rate': negative/n if n else None}


def investigate(db, start=None, end=None, grain='timestamp'):
    start, end = _date(start), _date(end)
    if start and end and start >= end:
        raise ValueError('Start must precede the exclusive end date.')
    if grain not in ('timestamp', 'day'):
        raise ValueError('Grain must be timestamp or day.')

    # Canonical date literals and the validated two-value grain are safe to expose
    # as the exact executable query used to produce the comparison.
    period = 'TRUE'
    if start:
        period += f" AND purchased_at >= DATE '{start}'"
    if end:
        period += f" AND purchased_at < DATE '{end}'"
    group_sql = f"""SELECT late_{grain} AS late, count(*) AS n,
       count(*) FILTER (WHERE review_score <= 2) AS negative
FROM order_review_delivery WHERE {period} GROUP BY 1 ORDER BY 1"""
    exclusions_sql = f"""WITH scoped AS (
    SELECT order_id, order_status, order_delivered_customer_date, order_estimated_delivery_date,
           order_purchase_timestamp AS purchased_at FROM orders WHERE {period}
), decisions AS (
    SELECT CASE WHEN o.order_status IS DISTINCT FROM 'delivered' THEN 'not_delivered'
        WHEN o.order_delivered_customer_date IS NULL OR o.order_estimated_delivery_date IS NULL THEN 'missing_delivery_time'
        WHEN r.order_id IS NULL THEN 'no_valid_review' ELSE 'included_orders' END AS reason
    FROM scoped o LEFT JOIN order_review_delivery r USING(order_id)
)
SELECT count(*) AS total_orders, count(*) FILTER (WHERE reason='not_delivered') AS not_delivered,
    count(*) FILTER (WHERE reason='missing_delivery_time') AS missing_delivery_time,
    count(*) FILTER (WHERE reason='no_valid_review') AS no_valid_review,
    count(*) FILTER (WHERE reason='included_orders') AS included_orders FROM decisions"""
    records_sql = f"""SELECT count(*) AS n, count(*) FILTER (WHERE review_score <= 2) AS negative
FROM review_delivery WHERE {period}"""
    groups = {'late': _group(0, 0), 'on_time': _group(0, 0)}
    with duckdb.connect(str(db), read_only=True) as con:
        audit = read_audit(con)
        for late, n, negative in con.execute(group_sql).fetchall():
            groups['late' if late else 'on_time'] = _group(n, negative)
        exclusions = rows(con, exclusions_sql)[0]
        records = _group(*con.execute(records_sql).fetchone())

    late, on_time = groups.values()
    result = {
        'status': 'completed', 'snapshot_id': audit['snapshot_id'], 'source': audit['source'],
        'grain': grain, 'start': start, 'end': end, 'filters': {'start': start, 'end': end},
        'groups': groups, 'exclusions': exclusions, 'review_records': records,
        'test': None, 'ci95': None, 'p_value': None, 'risk_difference': None,
        'sql': group_sql, 'exclusions_sql': exclusions_sql, 'review_records_sql': records_sql,
        'limitations': ['Observational association only. Unmeasured differences between orders can affect both delivery and ratings.',
                        'Only delivered orders with a valid review and both delivery timestamps enter the comparison.'],
    }
    table = [[g['negative'], g['n']-g['negative']] for g in groups.values()]
    result['contingency_table'] = table
    if not late['n'] or not on_time['n']:
        result['status'] = 'insufficient_data'
        result['limitations'].append('At least one delivery group has no eligible orders.')
        return result

    difference = late['rate'] - on_time['rate']
    # Newcombe (1998), method 10: combine separate Wilson score intervals.
    a, b = [binomtest(g['negative'], g['n']).proportion_ci(method='wilson') for g in groups.values()]
    result['ci95'] = [difference-hypot(late['rate']-a.low, b.high-on_time['rate']),
                      difference+hypot(a.high-late['rate'], on_time['rate']-b.low)]
    result['risk_difference'] = difference
    if min(map(sum, zip(*table))) == 0:
        result['limitations'].append('Every eligible order has the same binary review outcome. The association test is undefined.')
        return result
    chi = chi2_contingency(table, correction=False)
    if chi.expected_freq.min() < 5:
        result['test'], result['p_value'] = 'fisher_exact', float(fisher_exact(table, alternative='two-sided').pvalue)
    else:
        result['test'], result['p_value'] = 'pearson_chi2', float(chi.pvalue)
    if result['p_value'] == 0.0:
        result['limitations'].append('The p-value is below floating-point precision. Report p < 0.001.')
    return result
