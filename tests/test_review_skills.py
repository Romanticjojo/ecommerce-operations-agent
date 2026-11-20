import json

import duckdb
import pytest

from commerce.data import build_db, rows
from test_warehouse import order, review, write_sources


def make_db(tmp_path, purchases, lines, ratings, sellers, products):
    write_sources(tmp_path, {
        'orders': purchases, 'order_items': [
            dict(order_id=oid, order_item_id=n, product_id=p, seller_id=s)
            for oid, n, p, s in lines
        ], 'order_reviews': ratings,
        'sellers': [dict(seller_id=s) for s in sellers],
        'products': [dict(product_id=p) for p in products],
    })
    db = tmp_path / 'snapshot'
    build_db(tmp_path, db, 'fixture')
    return duckdb.connect(str(db), read_only=True)


def test_product_text_signals_latest_review_and_attribution(tmp_path):
    from commerce.review_skills import run

    comments = ['NÃO RECOMENDO, produto quebrado', 'Ótimo, mas a entrega atrasou.',
                'sem problemas', 'Recebido', None, 'Excelente', 'Produto ruim']
    ids = list('ABCDEFG')
    reviews = [dict(review(key, score), review_comment_message=message)
               for key, score, message in zip(ids, [1, 2, 5, 3, 2, 5, 1], comments)]
    reviews.append(dict(review('A', 5, 'older', '2018-01-19'), review_comment_title='Excelente'))
    reviews.append(dict(review('A', 0, 'invalid', '2018-01-25')))
    lines = [(key, 1, 'P', 'S') for key in ids]
    lines += [('A', 2, 'P', 'S'), ('F', 2, 'Q', 'S'), ('G', 2, None, 'S')]
    with make_db(tmp_path, [order(k, delivery=None) for k in ids], lines, reviews, ['S'], ['P', 'Q']) as con:
        result = run(con, 'reviews-aftercare', '2018-01-01', '2018-01-02')
        assert rows(con, result['sql']) == result['table']
        total, product = result['table']
        assert total['scope'] == 'All attributable products'
        assert product['product_id'] == 'P'
        for row in result['table']:
            assert row['rated_orders'] == 5 and row['low_ratings'] == 3
            assert row['written_comments'] == 4 and row['text_coverage_pct'] == 80
            assert (row['positive_text'], row['negative_text'], row['mixed_text'], row['unclassified_text']) == (1, 1, 1, 1)
            assert row['quality_mentions'] == 1 and row['delivery_mentions'] == 1
        assert all(not comment or comment not in json.dumps(result, ensure_ascii=False) for comment in comments)
        assert not run(con, 'reviews-aftercare', None, '2018-01-01')['table']


def test_score_shrinkage_tie_and_independent_denominators(tmp_path):
    from commerce.review_skills import run

    purchases, lines, ratings = [], [], []
    sellers = ['A', 'B', 'C', 'small']
    for seller in sellers:
        for i in range(1 if seller == 'small' else 20):
            oid = f'{seller}{i}'
            purchases.append(order(oid, delivery='2018-01-10 23:00' if seller in 'AC' else '2018-01-11'))
            lines.append((oid, 1, 'P', seller))
            ratings.append(review(oid, 5 if seller in 'AC' else 1))
    # An unrated delivery counts for punctuality. A missing timestamp still permits a rating.
    purchases += [order('unrated'), order('untimed', delivery=None), order('mixed'), order('unknown')]
    lines += [('A0', 2, 'P', 'A'), ('unrated', 1, 'P', 'A'), ('untimed', 1, 'P', 'C'),
              ('mixed', 1, 'P', 'B'), ('mixed', 2, 'P', 'A'),
              ('unknown', 1, 'P', 'A'), ('unknown', 2, 'P', None)]
    ratings += [review('untimed', 5), review('mixed', 1), review('unknown', 1)]
    with make_db(tmp_path, purchases, lines, ratings, sellers, ['P']) as con:
        result = run(con, 'merchant-score', None, None)
        assert rows(con, result['sql']) == result['table']
        ranked = {r['seller_id']: r for r in result['table']}
        assert set(ranked) == {'A', 'B', 'C'}
        assert (ranked['A']['rated_orders'], ranked['A']['timed_orders']) == (20, 21)
        assert (ranked['C']['rated_orders'], ranked['C']['timed_orders']) == (21, 20)
        # Rating and on-time priors each pool 41 successes out of 62 observations.
        expected = 100 * (0.7 * (20 + 20 * 41/62) / 40 + 0.3 * (21 + 20 * 41/62) / 41)
        assert ranked['A']['score'] == round(expected, 2)
        assert ranked['C']['rank'] == 1 and ranked['B']['rank'] == 3
        assert not run(con, 'merchant-score', '2018-01-02', None)['table']


def test_no_score_without_enough_timed_orders(tmp_path):
    from commerce.review_skills import run

    purchases = [order(str(i), delivery=None) for i in range(25)]
    lines = [(str(i), 1, 'P', 'S') for i in range(25)]
    with make_db(tmp_path, purchases, lines, [review(str(i), 5) for i in range(25)], ['S'], ['P']) as con:
        assert not run(con, 'merchant-score', None, None)['table']
        with pytest.raises(ValueError):
            run(con, 'reviews-aftercare', "2018-01-01' OR true --", None)


def test_all_eligible_sellers_share_rank_and_have_stable_display_order(tmp_path):
    from commerce.review_skills import run

    sellers = [f'S{i:02}' for i in range(21)]
    orders = [(f'{seller}-{n}', seller) for seller in sellers for n in range(20)]
    with make_db(tmp_path, [order(oid) for oid, _ in orders], [(oid, 1, 'P', seller) for oid, seller in orders],
                 [review(oid, 5) for oid, _ in orders], sellers, ['P']) as con:
        result = run(con, 'merchant-score')
        assert len(result['table']) == 21
        assert [r['seller_id'] for r in result['table']] == sellers
        assert {r['rank'] for r in result['table']} == {1}
        assert {r['eligible_sellers'] for r in result['table']} == {21}
        assert 'share' in result['answer']


def test_plain_praise_greetings_and_common_negations(tmp_path):
    from commerce.review_skills import run

    examples = ['Produto bom', 'Boa tarde!', 'Não é bom', 'Não atrasou', 'Qualidade não é ruim']
    purchases = [order(str(i)) for i in range(len(examples))]
    lines = [(str(i), 1, 'P', 'S') for i in range(len(examples))]
    opinions = [dict(review(str(i), 3), review_comment_title=text) for i, text in enumerate(examples)]
    with make_db(tmp_path, purchases, lines, opinions, ['S'], ['P']) as con:
        result = run(con, 'reviews-aftercare')['table'][0]
        assert [result[k] for k in ('positive_text', 'negative_text', 'mixed_text', 'unclassified_text')] == [3, 1, 0, 1]
