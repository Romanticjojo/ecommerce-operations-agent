"""Build immutable analytical snapshots from local Olist-format CSV files."""

import csv
import hashlib
import json
import os
import shutil
from datetime import date
from decimal import Decimal
from pathlib import Path
from tempfile import TemporaryDirectory

import duckdb

from .demo import demo_data
from .schema import CREATE_VIEWS, DESCRIPTIONS, INT, KEYS, METRICS, MONEY, RAW, RAW_DESCRIPTIONS, TIME, TRANSLATION, VIEWS

__all__ = ['build_db', 'catalog', 'overview', 'demo_data', 'VIEWS']


def rows(con, sql):
    cursor = con.execute(sql)
    columns = [field[0] for field in cursor.description]

    def json_value(value):
        if isinstance(value, date):
            return value.isoformat()
        if isinstance(value, Decimal):
            return float(value)
        return value

    return [dict(zip(columns, map(json_value, record))) for record in cursor.fetchall()]


def _load_table(con, path, table, schema):
    with path.open(encoding='utf-8-sig', newline='') as stream:
        header = next(csv.reader(stream), [])
    if set(header) != set(schema) or len(header) != len(schema):
        raise ValueError(f'{table}: unexpected header; required columns: {", ".join(schema)}')

    # Only known, validated header names are interpolated. Read records in source order
    # with one CSV reader to retain a stable tie-break even with multiline reviews.
    columns = '{' + ', '.join(f"'{name}':'VARCHAR'" for name in header) + '}'
    try:
        con.execute(f"""
            CREATE OR REPLACE TEMP TABLE incoming AS
            SELECT *, ordinality AS source_row FROM read_csv(?, header=true, auto_detect=false,
                columns={columns}, delim=',', quote='"', escape='"', parallel=false) WITH ORDINALITY
        """, [str(path)])
    except duckdb.Error:
        raise ValueError(f'{table}: invalid CSV records or encoding') from None

    checks = []
    for name, kind in schema.items():
        if kind in (INT, MONEY, TIME):
            invalid = f'try_cast({name} AS {kind}) IS NULL'
            if kind == INT:
                invalid += f" OR NOT regexp_full_match(trim({name}), '[+-]?[0-9]+')"
            if kind == MONEY:
                invalid += f" OR NOT regexp_full_match(trim({name}), '[+-]?[0-9]+([.][0-9]{{1,2}})?')"
            if kind == TIME:
                invalid += f' OR NOT isfinite(try_cast({name} AS TIMESTAMP))'
            checks.append((name, f'count(*) FILTER (WHERE {name} IS NOT NULL AND ({invalid}))'))
    if checks:
        counts = con.execute('SELECT ' + ', '.join(expr for _, expr in checks) + ' FROM incoming').fetchone()
        bad = [name for (name, _), count in zip(checks, counts) if count]
        if bad:
            raise ValueError(f'{table}: invalid values in {", ".join(bad)}')

    fields = [f'cast({name} AS {kind}) AS {name}' for name, kind in schema.items()]
    if table == 'order_reviews':
        fields.append('source_row')
    con.execute(f"CREATE TABLE {table} AS SELECT {', '.join(fields)} FROM incoming")
    if table in KEYS:
        keys = KEYS[table]
        missing = ' OR '.join(f'{key} IS NULL' for key in keys)
        duplicates = con.execute(f"SELECT 1 FROM {table} GROUP BY {', '.join(keys)} HAVING count(*) > 1 OR {missing} LIMIT 1").fetchone()
        if duplicates:
            raise ValueError(f'{table}: missing or duplicate key ({", ".join(keys)})')
    return con.execute(f'SELECT count(*) FROM {table}').fetchone()[0]


def _quality(con):
    def count(sql):
        return con.execute(sql).fetchone()[0]

    # An orphan includes an absent key. Retain these records for audit instead of
    # multiplying other facts or attributing an unknown order to a valid status.
    relations = [
        ('orders', 'customers', 'customer_id'), ('order_items', 'orders', 'order_id'),
        ('order_items', 'products', 'product_id'), ('order_items', 'sellers', 'seller_id'),
        ('order_payments', 'orders', 'order_id'), ('order_reviews', 'orders', 'order_id'),
    ]
    orphans = {
        f'{child}.{key}': count(f'SELECT count(*) FROM {child} c ANTI JOIN {parent} p ON c.{key}=p.{key}')
        for child, parent, key in relations
    }
    missing = {}
    for table, schema in RAW.items():
        counts = con.execute('SELECT ' + ', '.join(f'count(*)-count({col})' for col in schema) + f' FROM {table}').fetchone()
        missing[table] = dict(zip(schema, counts))
    return {
        'missing_values': missing,
        'orphan_foreign_keys': orphans,
        'invalid_review_scores': count('SELECT count(*) FROM order_reviews WHERE review_score IS NULL OR review_score NOT BETWEEN 1 AND 5'),
        'repeated_review_ids': count('SELECT count(*) FROM (SELECT review_id FROM order_reviews WHERE review_id IS NOT NULL GROUP BY 1 HAVING count(*)>1)'),
        'review_ids_on_multiple_orders': count('SELECT count(*) FROM (SELECT review_id FROM order_reviews WHERE review_id IS NOT NULL GROUP BY 1 HAVING count(DISTINCT order_id)>1)'),
        'orders_with_multiple_eligible_reviews': count('SELECT count(*) FROM (SELECT order_id FROM review_delivery GROUP BY 1 HAVING count(*)>1)'),
        'delivered_orders_without_items': count("SELECT count(*) FROM order_summary WHERE status='delivered' AND item_count=0"),
    }


def build_db(csv_dir: Path, db: Path, source: str):
    """Validate all inputs, build beside the target, then atomically publish."""
    csv_dir, db = Path(csv_dir), Path(db)
    db.parent.mkdir(parents=True, exist_ok=True)
    files = {}
    with TemporaryDirectory(dir=db.parent) as work:
        staging = Path(work)
        candidate = staging / 'snapshot.duckdb'
        with duckdb.connect(str(candidate)) as con:
            con.execute('SET threads=1')
            for table, schema in {**RAW, 'category_translation': TRANSLATION}.items():
                if table == 'category_translation':
                    name = 'product_category_name_translation.csv'
                else:
                    name = f'olist_{table}_dataset.csv'
                source_file = csv_dir / name
                if table == 'category_translation' and not source_file.exists():
                    con.execute('CREATE TABLE category_translation(product_category_name VARCHAR, product_category_name_english VARCHAR)')
                    continue
                if not source_file.is_file():
                    raise ValueError(f'Missing required CSV: {name}')
                # Hash and import the same immutable bytes, even if a source changes mid-import.
                frozen = staging / name
                shutil.copyfile(source_file, frozen)
                with frozen.open('rb') as stream:
                    digest = hashlib.file_digest(stream, 'sha256').hexdigest()
                columns = [{'name': col, 'type': kind, 'description': RAW_DESCRIPTIONS[col]}
                           for col, kind in schema.items()]
                files[table] = {'filename': name, 'sha256': digest, 'rows': _load_table(con, frozen, table, schema),
                                'columns': columns}
            con.execute(CREATE_VIEWS)
            coverage = rows(con, 'SELECT min(order_purchase_timestamp)::DATE AS start, max(order_purchase_timestamp)::DATE AS "end" FROM orders')[0]
            # Include the transform version so a revised business definition can identify a new snapshot.
            fingerprint = {'version': 1, 'files': {key: value['sha256'] for key, value in files.items()}}
            snapshot_id = hashlib.sha256(json.dumps(fingerprint, sort_keys=True).encode()).hexdigest()
            audit = dict(snapshot_id=snapshot_id, source=source, files=files, quality=_quality(con), date_range=coverage)
            con.execute('CREATE TABLE snapshot_metadata(audit VARCHAR, imported_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP)')
            con.execute('INSERT INTO snapshot_metadata(audit) VALUES (?)', [json.dumps(audit)])
        os.replace(candidate, db)
    return audit


def read_audit(con):
    return json.loads(con.execute('SELECT audit FROM snapshot_metadata').fetchone()[0])


def catalog(db):
    with duckdb.connect(str(db), read_only=True) as con:
        audit = read_audit(con)
        fields = {row[0] for row in con.execute('DESCRIBE snapshot_metadata').fetchall()}
        imported_at = con.execute('SELECT CAST(imported_at AS VARCHAR) FROM snapshot_metadata').fetchone()[0] if 'imported_at' in fields else audit.get('imported_at')
        tables = []
        for table, grain in VIEWS.items():
            fields = con.execute(f'DESCRIBE {table}').fetchall()
            columns = [{'name': field, 'type': kind, 'description': DESCRIPTIONS[field]} for field, kind, *_ in fields]
            tables.append({'name': table, 'grain': grain, 'columns': columns})
    return {key: audit[key] for key in ('snapshot_id', 'source', 'date_range')} | {'imported_at': imported_at, 'tables': tables, 'metrics': METRICS, 'audit': audit}


def overview(db):
    with duckdb.connect(str(db), read_only=True) as con:
        audit = read_audit(con)
        summary = rows(con, """
            SELECT count(*) AS order_count, coalesce(sum(item_revenue), 0) AS item_revenue,
                avg(item_revenue) AS aov, coalesce(sum(payment_total), 0) AS payment_total
            FROM order_summary WHERE status='delivered'
        """)[0]
        summary['negative_rate'] = con.execute('SELECT avg((review_score <= 2)::INT) FROM order_review_delivery').fetchone()[0]
        summary['monthly_sales'] = rows(con, 'SELECT * FROM monthly_sales ORDER BY month')
        summary['top_categories'] = rows(con, """
            SELECT category, sum(item_revenue) AS item_revenue FROM category_sales GROUP BY category
            ORDER BY item_revenue DESC NULLS LAST, category LIMIT 10
        """)
        summary['states'] = rows(con, """
            SELECT state, count(*) AS order_count, sum(item_revenue) AS item_revenue
            FROM order_summary WHERE status='delivered' GROUP BY state ORDER BY order_count DESC, state
        """)
    return {key: audit[key] for key in ('snapshot_id', 'source', 'date_range')} | summary
