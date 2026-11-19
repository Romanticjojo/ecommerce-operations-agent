"""Generate reproducible synthetic records using Olist's public column layout."""

import calendar
import csv
import random
from datetime import datetime, timedelta
from pathlib import Path

from .schema import RAW, TRANSLATION


def demo_data(directory: Path):
    """Write the seven CSVs and category translations for 24 purchase months."""
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=True)
    rng = random.Random(201811)
    tables = {name: [] for name in RAW}
    categories = [
        ('cama_mesa_banho', 'bed_bath_table', 89), ('beleza_saude', 'health_beauty', 96),
        ('esporte_lazer', 'sports_leisure', 110), ('informatica_acessorios', 'computers_accessories', 120),
        ('moveis_decoracao', 'furniture_decor', 165), ('utilidades_domesticas', 'housewares', 78),
        ('relogios_presentes', 'watches_gifts', 195), ('telefonia', 'telephony', 145),
        ('brinquedos', 'toys', 69), ('automotivo', 'auto', 128),
        ('papelaria', 'stationery', 36), ('livros_interesse_geral', 'books_general_interest', 40),
    ]
    markets = [('SP', 'sao paulo', '01000'), ('RJ', 'rio de janeiro', '20000'),
               ('MG', 'belo horizonte', '30000'), ('RS', 'porto alegre', '90000'),
               ('PR', 'curitiba', '80000'), ('BA', 'salvador', '40000')]
    for i in range(72):
        category = categories[i % len(categories)][0]
        tables['products'].append((f'p{i:03}', category, 20+i%35, 80+i*3, 1+i%4, 200+30*i, 18, 8, 12))
    for i in range(30):
        state, city, zip_code = markets[i % len(markets)]
        tables['sellers'].append((f's{i:02}', zip_code, city, state))

    def brl(cents):
        return f'{cents // 100}.{cents % 100:02}'

    index = 0
    for month_index in range(24):
        year, month = 2017 + month_index // 12, month_index % 12 + 1
        volume = 75 + month_index * 4 + rng.randint(-9, 9) + (60 if month in (11, 12) else 0)
        for _ in range(volume):
            index += 1
            oid, cid = f'o{index:05}', f'c{index:05}'
            state, city, zip_code = rng.choices(markets, weights=(43, 16, 14, 10, 9, 8))[0]
            tables['customers'].append((cid, f'u{rng.randrange(1, 2301):05}', zip_code, city, state))
            purchase = datetime(year, month, rng.randint(1, calendar.monthrange(year, month)[1]),
                                rng.randint(0, 23), rng.randint(0, 59))
            estimate = (purchase + timedelta(days=rng.randint(8, 24))).replace(hour=0, minute=0)
            delta = rng.choices([-5, -3, -2, -1, 0, 1, 3, 6], weights=[13, 18, 22, 18, 10, 8, 7, 4])[0]
            delivery = estimate + timedelta(days=delta, hours=rng.randint(8, 20))
            status = rng.choices(['delivered', 'canceled', 'shipped', 'unavailable'], weights=[95, 2, 2, 1])[0]
            carrier = purchase + timedelta(days=2)
            tables['orders'].append((oid, cid, status, purchase, purchase+timedelta(minutes=20),
                                     carrier if status in ('delivered', 'shipped') else '',
                                     delivery if status=='delivered' and index%451 else '', estimate))
            amount = 0
            for item in range(1, rng.choices([1, 2, 3], weights=[72, 22, 6])[0]+1):
                product = rng.randrange(72)
                cents = categories[product%len(categories)][2] * rng.randint(65, 145)
                freight = rng.randint(770, 3150)
                tables['order_items'].append((oid, item, f'p{product:03}', f's{rng.randrange(30):02}',
                                              carrier + timedelta(days=1), brl(cents), brl(freight)))
                amount += cents + freight
            voucher = amount // 5 if index%9 == 0 else 0
            tables['order_payments'].append((oid, 1, 'credit_card', rng.randint(1, 4), brl(amount-voucher)))
            if voucher:
                tables['order_payments'].append((oid, 2, 'voucher', 1, brl(voucher)))
            if status=='delivered' and index%18:
                creation = delivery + timedelta(days=1)
                negative = rng.random() < (.31 if delta>0 else .08)
                score = rng.choice((1, 2)) if negative else rng.choice((3, 4, 5, 5, 5))
                tables['order_reviews'].append((f'r{index:05}', oid, score, '', '', creation, creation+timedelta(hours=6)))
                if index%77 == 0:
                    tables['order_reviews'].append((f'r{index:05}b', oid, rng.randint(2, 5), '', '',
                                                    creation, creation+timedelta(days=2)))

    for name, schema in RAW.items():
        with (directory / f'olist_{name}_dataset.csv').open('w', newline='', encoding='utf-8') as stream:
            writer = csv.writer(stream)
            writer.writerow(schema)
            writer.writerows(tables[name])
    with (directory / 'product_category_name_translation.csv').open('w', newline='', encoding='utf-8') as stream:
        writer = csv.writer(stream)
        writer.writerow(TRANSLATION)
        writer.writerows((pt, en) for pt, en, _ in categories)
