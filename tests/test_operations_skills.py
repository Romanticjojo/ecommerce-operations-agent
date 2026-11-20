"""Small, countable fixtures for the six commerce operations playbooks."""
from datetime import date
from calendar import monthrange

import duckdb
import pytest

from commerce.data import rows


@pytest.fixture
def con():
    connection = duckdb.connect()
    connection.execute("CREATE TABLE order_summary(order_id VARCHAR, customer_id VARCHAR, status VARCHAR, purchased_at TIMESTAMP, item_revenue DECIMAL(18,2))")
    connection.execute("CREATE TABLE customers(customer_id VARCHAR, customer_unique_id VARCHAR)")
    connection.execute("CREATE TABLE category_sales(order_id VARCHAR, purchased_at TIMESTAMP, category VARCHAR, product_id VARCHAR, seller_id VARCHAR, item_revenue DECIMAL(18,2))")
    # Five or more orders in each full month. The same buyer uses a fresh customer_id
    # each month. An isolated April record cannot establish a full April.
    for month, count, price in [(1, 5, 10), (2, 6, 12), (3, 7, 14), (4, 1, 80)]:
        for i in range(count):
            day = monthrange(2018, month)[1] if i == count - 1 and month != 4 else 1
            purchased = date(2018, month, day)
            oid = f'{month}-{i}'
            buyer = 'repeat' if i == 0 else oid
            connection.execute("INSERT INTO order_summary VALUES (?,?,'delivered',?,?)", [oid, oid, purchased, price])
            connection.execute("INSERT INTO customers VALUES (?,?)", [oid, buyer])
            connection.execute("INSERT INTO category_sales VALUES (?,?,'books','p','s',?)", [oid, purchased, price])
    yield connection
    connection.close()


def invoke(con, name, start=None, end=None):
    from commerce.operations_skills import run
    result = run(con, name, start, end)
    assert rows(con, result['sql']) == result['table']
    assert result['answer'] and isinstance(result['warnings'], list)
    return result


def test_growth_and_assortment(con):
    growth = invoke(con, 'sales-growth')['table']
    revenue = next(row for row in growth if row['measure'] == 'Item revenue')
    assert (revenue['previous_value'], revenue['latest_value'], revenue['change']) == (72, 98, 26)
    category = next(row for row in growth if row['measure'] == 'Category / books')
    assert category['change'] == revenue['change']
    assortment = invoke(con, 'assortment')['table'][0]
    assert (assortment['category'], assortment['previous_units'], assortment['latest_units'], assortment['active_sellers']) == ('books', 6, 7, 1)


def test_product_and_seller_trajectories(con):
    result = invoke(con, 'product-trend')
    product = result['table'][0]
    assert (product['product_id'], product['first_units'], product['middle_units'], product['latest_units']) == ('p', 5, 6, 7)
    assert product['middle_month'] == '2018-02-01'
    assert product['planning_units'] == 6
    assert '2018-04' in result['answer'] and 'reorder' in result['answer'].lower()
    seller = invoke(con, 'seller-growth')['table'][0]
    assert seller['seller_id'] == 's' and seller['growth_months'] == 2
    assert (seller['first_revenue'], seller['middle_revenue'], seller['latest_revenue']) == (50, 72, 98)
    assert seller['latest_revenue_share_pct'] == 100


def test_retention_complete_followup_and_identity(con):
    result = invoke(con, 'retention')['table'][0]
    # Only the four Jan 1 buyers had a full 90 days through the Apr 1 purchase.
    assert (result['first_category'], result['buyers'], result['repeat_buyers'], result['no_repeat_by_90d']) == ('books', 4, 1, 3)
    assert result['repeat_pct'] == 25
    assert invoke(con, 'retention', end='2018-03-31')['table'] == []


def test_price_pairs_include_only_same_product_and_consecutive_months(con):
    con.execute("INSERT INTO category_sales VALUES ('x','2018-02-20','books','other','s',99)")
    row = invoke(con, 'price-volume')['table'][0]
    assert row['price_direction'] == 'Higher' and row['sku_month_pairs'] == 2 and row['distinct_products'] == 1
    assert row['median_unit_change'] == 1


@pytest.mark.parametrize('name', ['sales-growth', 'assortment', 'seller-growth', 'product-trend', 'price-volume'])
def test_partial_or_missing_months_cannot_create_comparisons(con, name):
    assert invoke(con, name, '2018-02-02', '2018-03-15')['table'] == []
    con.execute("DELETE FROM order_summary WHERE month(purchased_at) = 2")
    assert invoke(con, name)['table'] == []


def test_newly_observed_product_needs_launch_check(con):
    con.execute("""INSERT INTO category_sales
        SELECT 'mar', '2018-03-03', 'new', 'new-product', 's', 10 FROM range(12)""")
    r = invoke(con, 'product-trend')
    launch = next(item for item in r['table'] if item['product_id'] == 'new-product')
    assert (launch['first_units'], launch['middle_units'], launch['latest_units']) == (0, 0, 12)
    assert 'launch' in launch['next_action'].lower()
    assert 'reorder' in r['answer'].lower()


def test_retention_first_observed_purchase_precedes_date_filter(con):
    # A long enough follow-up makes February first-time buyers eligible. Jan's
    # repeat buyer must not be reclassified as new in the February cohort.
    con.execute("INSERT INTO order_summary VALUES ('tail','tail','delivered','2018-08-01',0)")
    result = invoke(con, 'retention', '2018-02-01', '2018-05-06')['table'][0]
    assert (result['buyers'], result['repeat_buyers']) == (4, 0)


def test_seller_share_is_unknown_when_market_revenue_is_zero(con):
    con.execute("UPDATE category_sales SET item_revenue = 0 WHERE month(purchased_at) = 3")
    result = invoke(con, 'seller-growth')
    assert result['table'][0]['latest_revenue_share_pct'] is None
    assert 'unavailable' in result['answer']
