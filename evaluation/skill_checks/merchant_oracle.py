"""Compare the local review skills with independent full-range calculations from Olist CSVs.

From the project root, use python -m evaluation.skill_checks.merchant_oracle CSV_DIR DB_PATH.
"""

import argparse
from collections import Counter, defaultdict
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path

import duckdb

from commerce.review_skills import run
from evaluation.kaggle_olist.oracle import read_rows


def rounded(value, digits):
    return float(value.quantize(Decimal(1).scaleb(-digits), rounding=ROUND_HALF_UP))


def source_counts(directory):
    def source(table):
        return read_rows(directory / f'olist_{table}_dataset.csv')

    # Stable sorts retain source order after the last documented tiebreaker.
    valid = [r for r in source('order_reviews') if r['review_score'] in ('1', '2', '3', '4', '5')]
    valid.sort(key=lambda r: (not r['review_id'], r['review_id']))
    valid.sort(key=lambda r: r['review_creation_date'], reverse=True)
    valid.sort(key=lambda r: r['review_answer_timestamp'], reverse=True)
    latest = {}
    for review in valid:
        latest.setdefault(review['order_id'], review)

    seller_ids = {r['seller_id'] for r in source('sellers')}
    product_ids = {r['product_id'] for r in source('products')}
    order_sellers, order_products = defaultdict(set), defaultdict(set)
    for item in source('order_items'):
        order_sellers[item['order_id']].add(item['seller_id'])
        order_products[item['order_id']].add(item['product_id'])

    sellers, products = defaultdict(Counter), defaultdict(Counter)
    for order in source('orders'):
        if order['order_status'] != 'delivered':
            continue
        oid = order['order_id']
        review = latest.get(oid)
        rated = Counter()
        if review:
            stars = int(review['review_score'])
            rated.update(rated_orders=1, stars=stars, low_ratings=int(stars <= 2),
                         written_comments=int(bool((review['review_comment_title'] + ' ' + review['review_comment_message']).strip())))
        if len(order_products[oid]) == 1 and review:
            product = next(iter(order_products[oid]))
            if product in product_ids:
                products[product].update(rated)
        if len(order_sellers[oid]) != 1:
            continue
        seller = next(iter(order_sellers[oid]))
        if seller not in seller_ids:
            continue
        counts = sellers[seller]
        counts.update(rated)
        counts['delivered_orders'] += 1
        actual = order['order_delivered_customer_date'][:10]
        estimated = order['order_estimated_delivery_date'][:10]
        if actual and estimated:
            counts['timed_orders'] += 1
            counts['on_time_orders'] += int(actual <= estimated)
    return sellers, products


def merchant_reference(sellers):
    market = Counter()
    for counts in sellers.values():
        market.update(counts)
    if not market['rated_orders'] or not market['timed_orders']:
        return []
    rating_prior = Decimal(market['stars'] - market['rated_orders']) / (4 * market['rated_orders'])
    delivery_prior = Decimal(market['on_time_orders']) / market['timed_orders']
    ranked = []
    for seller_id, counts in sellers.items():
        n, m = counts['rated_orders'], counts['timed_orders']
        if min(n, m) < 20:
            continue
        rating_sum = Decimal(counts['stars'] - n) / 4
        quality = 100 * (rating_sum + 20 * rating_prior) / (n + 20)
        punctuality = 100 * (counts['on_time_orders'] + 20 * delivery_prior) / (m + 20)
        ranked.append(dict(
            seller_id=seller_id, score=rounded((7 * quality + 3 * punctuality) / 10, 2),
            rating_component=rounded(quality, 2), delivery_component=rounded(punctuality, 2),
            rated_orders=n, timed_orders=m, delivered_orders=counts['delivered_orders'],
            on_time_orders=counts['on_time_orders'], written_comments=counts['written_comments'],
            mean_stars=rounded(Decimal(counts['stars']) / n, 3),
            text_coverage_pct=rounded(Decimal(100 * counts['written_comments']) / n, 1),
            market_rating_points=rounded(100 * rating_prior, 4),
            market_delivery_points=rounded(100 * delivery_prior, 4),
        ))
    ranked.sort(key=lambda r: (-r['score'], r['seller_id']))
    previous = None
    for index, row in enumerate(ranked, 1):
        if row['score'] != previous:
            rank = index
        row['rank'] = rank
        row['eligible_sellers'] = len(ranked)
        previous = row['score']
    return ranked


def compare(expected, actual, label):
    if len(expected) != len(actual):
        raise AssertionError(f'{label}: expected {len(expected)} rows, found {len(actual)}')
    for index, (want, got) in enumerate(zip(expected, actual), 1):
        for field, value in want.items():
            if got[field] != value:
                raise AssertionError(f'{label} row {index} {field}: expected {value}, found {got[field]}')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('csv_dir', type=Path)
    parser.add_argument('db_path', type=Path)
    args = parser.parse_args()
    sellers, products = source_counts(args.csv_dir)
    ranks = merchant_reference(sellers)
    if not ranks or not products:
        raise ValueError('The input must contain eligible merchants and reviewed products.')
    totals = Counter()
    for counts in products.values():
        totals.update(counts)
    top_products = sorted(products, key=lambda key: (-products[key]['low_ratings'], -products[key]['rated_orders'], key))[:20]
    product_rows = []
    for product_id in [None, *top_products]:
        stats = totals if product_id is None else products[product_id]
        product_rows.append(dict(product_id=product_id, rated_orders=stats['rated_orders'],
                                 low_ratings=stats['low_ratings'], written_comments=stats['written_comments']))
    with duckdb.connect(str(args.db_path), read_only=True) as con:
        compare(ranks, run(con, 'merchant-score')['table'], 'Merchant')
        compare(product_rows, run(con, 'reviews-aftercare')['table'], 'Product')
    print(f'PASS: {len(ranks)} merchant ranks, scores, components and denominators match CSVs. '
          f'{len(top_products)} product rows and their overall population of {totals["rated_orders"]:,} rated orders match.')


if __name__ == '__main__':
    main()
