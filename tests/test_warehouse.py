import csv

import duckdb
import pytest
from scipy.stats import chi2_contingency, fisher_exact

from commerce.data import build_db, catalog, demo_data, overview
from commerce.stats import investigate


HEADERS = {
    'orders': 'order_id customer_id order_status order_purchase_timestamp order_approved_at order_delivered_carrier_date order_delivered_customer_date order_estimated_delivery_date',
    'order_items': 'order_id order_item_id product_id seller_id shipping_limit_date price freight_value',
    'order_payments': 'order_id payment_sequential payment_type payment_installments payment_value',
    'order_reviews': 'review_id order_id review_score review_comment_title review_comment_message review_creation_date review_answer_timestamp',
    'customers': 'customer_id customer_unique_id customer_zip_code_prefix customer_city customer_state',
    'sellers': 'seller_id seller_zip_code_prefix seller_city seller_state',
    'products': 'product_id product_category_name product_name_lenght product_description_lenght product_photos_qty product_weight_g product_length_cm product_height_cm product_width_cm',
}


def write_sources(directory, rows):
    directory.mkdir(exist_ok=True)
    for name, fields in HEADERS.items():
        with (directory / f'olist_{name}_dataset.csv').open('w', newline='') as stream:
            writer = csv.DictWriter(stream, fieldnames=fields.split())
            writer.writeheader()
            writer.writerows(rows.get(name, []))


def order(key, *, delivery='2018-01-09', status='delivered'):
    return dict(order_id=key, customer_id='C', order_status=status,
                order_purchase_timestamp='2018-01-01', order_delivered_customer_date=delivery,
                order_estimated_delivery_date='2018-01-10')


def review(key, score, suffix='', answered='2018-01-20'):
    return dict(order_id=key, review_id='r' + key + suffix, review_score=score,
                review_creation_date='2018-01-15', review_answer_timestamp=answered)


def test_amounts_idempotence_atomic_error(tmp_path):
    rows = {
        'orders': [order('A')],
        'order_items': [dict(order_id='A', order_item_id=i, price=p, product_id='P', seller_id='S')
                        for i, p in [(1, 10), (2, 20)]],
        'order_payments': [dict(order_id='A', payment_sequential=i, payment_value=p)
                           for i, p in [(1, 12), (2, 18)]],
        'products': [dict(product_id='P', product_category_name='artes')],
        'customers': [dict(customer_id='C', customer_state='SP')],
        'sellers': [dict(seller_id='S')],
    }
    data, db = tmp_path / 'csv', tmp_path / 'db'
    write_sources(data, rows)
    audit = build_db(data, db, 'fixture')
    assert build_db(data, db, 'fixture') == audit
    summary = overview(db)
    assert (summary['order_count'], summary['item_revenue'], summary['aov'], summary['payment_total']) == (1, 30, 30, 30)
    assert summary['top_categories'] == [{'category': 'artes', 'item_revenue': 30.0}]
    assert summary['monthly_sales'][0]['item_revenue'] == 30
    with duckdb.connect(str(db), read_only=True) as con:
        assert con.execute('SELECT order_id, item_revenue, payment_total FROM order_summary').fetchall() == [('A', 30, 30)]
    original = db.read_bytes()
    rows['order_items'][0]['price'] = 'banana'
    write_sources(data, rows)
    with pytest.raises(ValueError, match='price'):
        build_db(data, db, 'fixture')
    assert db.read_bytes() == original
    (data / 'olist_orders_dataset.csv').write_text('order_id\nA\n')
    with pytest.raises(ValueError, match='orders'):
        build_db(data, db, 'fixture')
    assert db.read_bytes() == original


def test_review_selection_statistics_and_sensitivity(tmp_path):
    orders, reviews = [], []
    for i in range(40):
        key = str(i)
        delivered = '2018-01-11' if i < 19 else '2018-01-09'
        if i == 19:
            delivered = '2018-01-10 12:00:00'
        orders.append(order(key, delivery=delivered))
        reviews.append(review(key, 1 if i < 10 or i in (20, 21) else 5))
    orders += [order('missing', delivery=''), order('invalid'), order('cancelled', status='canceled')]
    reviews += [review('0', 5, 'older', '2018-01-19'), review('invalid', 6), review('cancelled', 1)]
    write_sources(tmp_path, {'orders': orders, 'order_reviews': reviews})
    db = tmp_path / 'db'
    build_db(tmp_path, db, 'fixture')
    report = investigate(db)
    assert report['groups'] == {'late': {'n': 20, 'negative': 10, 'rate': .5},
                                 'on_time': {'n': 20, 'negative': 2, 'rate': .1}}
    assert report['risk_difference'] == pytest.approx(.4)
    assert report['ci95'] == pytest.approx([0.115930, 0.613271], abs=.00005)
    assert report['test'] == 'pearson_chi2'
    assert report['p_value'] == pytest.approx(chi2_contingency([[10, 10], [2, 18]], correction=False).pvalue)
    assert report['exclusions'] == dict(total_orders=43, not_delivered=1, missing_delivery_time=1,
                                        no_valid_review=1, included_orders=40)
    assert report['review_records'] == dict(n=41, negative=12, rate=12 / 41)
    assert investigate(db, grain='day')['groups']['late']['n'] == 19
    assert investigate(db, '2017-01-01', '2018-01-01')['status'] == 'insufficient_data'
    assert investigate(db, '2018-01-01', '2018-01-02')['groups'] == report['groups']
    with pytest.raises(ValueError):
        investigate(db, '2018-01-01', '2017-12-31')


@pytest.mark.parametrize('scores,test,p', [([1, 3, 5], 'fisher_exact', fisher_exact([[1, 0], [0, 2]]).pvalue),
                                           ([4, 5, 5], None, None)])
def test_sparse_and_constant_tables(tmp_path, scores, test, p):
    rows = {'orders': [order(str(i), delivery='2018-01-11' if i == 0 else '2018-01-09') for i in range(3)],
            'order_reviews': [review(str(i), s) for i, s in enumerate(scores)]}
    write_sources(tmp_path, rows)
    db = tmp_path / 'db'
    build_db(tmp_path, db, 'fixture')
    result = investigate(db)
    assert result['test'] == test
    assert result['p_value'] == p
    assert result['ci95'][0] <= result['risk_difference'] <= result['ci95'][1]


def test_demo_deterministic_and_documented(tmp_path):
    data, db = tmp_path / 'data', tmp_path / 'demo.db'
    demo_data(data)
    audit = build_db(data, db, 'synthetic')
    demo_data(data)
    assert build_db(data, db, 'synthetic') == audit
    assert {t['name'] for t in catalog(db)['tables']} >= {'order_summary', 'category_sales', 'monthly_sales', 'order_review_delivery'}
    assert len(overview(db)['monthly_sales']) >= 20
    assert overview(db)['order_count'] > 100
    assert investigate(db)['status'] == 'completed'


def test_multiline_reviews_tie_break_and_orphan_audit(tmp_path):
    first = review('A', 2)
    first.update(review_id='r', review_comment_message='two\nquoted, lines')
    second = dict(first, review_score=4)
    earlier_id = dict(first, review_id='b', review_score=5)
    rows = {
        'orders': [order('A'), order('B')],
        'order_reviews': [earlier_id, dict(first, review_id='a'), dict(second, review_id='a'),
                          dict(first, order_id='B', review_id='b'), dict(first, order_id='absent')],
    }
    write_sources(tmp_path, rows)
    db = tmp_path / 'db'
    audit = build_db(tmp_path, db, 'fixture')
    quality = audit['quality']
    assert quality['repeated_review_ids'] == 2
    assert quality['review_ids_on_multiple_orders'] == 1
    assert quality['orders_with_multiple_eligible_reviews'] == 1
    assert quality['orphan_foreign_keys']['order_reviews.order_id'] == 1
    assert audit['files']['order_reviews']['rows'] == 5
    with duckdb.connect(str(db), read_only=True) as con:
        picks = con.execute('SELECT order_id, source_row, review_score FROM order_review_delivery ORDER BY 1').fetchall()
    assert picks == [('A', 2, 2), ('B', 4, 2)]
    result = investigate(db)
    assert result['status'] == 'insufficient_data'
    assert result['test'] is None and result['p_value'] is None
    assert result['contingency_table'] == [[0, 0], [2, 0]]


def test_reject_duplicate_keys_and_bad_integer(tmp_path):
    db = tmp_path / 'db'
    write_sources(tmp_path, {'orders': [order('A'), order('A')]})
    with pytest.raises(ValueError, match='duplicate key'):
        build_db(tmp_path, db, 'fixture')
    assert not db.exists()
    write_sources(tmp_path, {'orders': [order('A')], 'order_reviews': [review('A', 1.9)]})
    with pytest.raises(ValueError, match='review_score'):
        build_db(tmp_path, db, 'fixture')
    assert not db.exists()
