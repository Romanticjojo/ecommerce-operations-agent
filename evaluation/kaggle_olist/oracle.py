"""Independent CSV reference calculations. No application modules or DuckDB views."""

import csv
import hashlib
from collections import Counter, defaultdict
from decimal import Decimal
from math import hypot, sqrt
from statistics import NormalDist


def read_rows(path):
    with path.open(encoding="utf-8-sig", newline="") as file:
        yield from csv.DictReader(file)


def manifest(directory):
    files = {}
    for path in sorted(directory.glob("*.csv")):
        with path.open("rb") as file:
            sha = hashlib.file_digest(file, "sha256").hexdigest()
        files[path.name] = dict(
            sha256=sha, rows=sum(1 for _ in read_rows(path)), bytes=path.stat().st_size
        )
    return files


class Reference:
    def __init__(self, directory):
        def rows(name):
            return read_rows(directory / f"olist_{name}_dataset.csv")

        self.files = manifest(directory)
        self.orders = {r["order_id"]: r for r in rows("orders")}
        self.delivered = {
            k for k, v in self.orders.items() if v["order_status"] == "delivered"
        }
        self.month_counts = Counter(
            self.orders[k]["order_purchase_timestamp"][:7] for k in self.delivered
        )
        products = {
            r["product_id"]: r["product_category_name"] for r in rows("products")
        }
        translations = {
            r["product_category_name"]: r["product_category_name_english"]
            for r in read_rows(directory / "product_category_name_translation.csv")
        }
        self.revenue = Decimal(0)
        self.month_revenue = defaultdict(Decimal)
        self.categories_2018 = defaultdict(Decimal)
        line_count = Counter()
        item_per_order = defaultdict(Decimal)
        payment_count = Counter()
        payment_per_order = defaultdict(Decimal)
        for item in rows("order_items"):
            oid = item["order_id"]
            if oid not in self.delivered:
                continue
            amount = Decimal(item["price"])
            month = self.orders[oid]["order_purchase_timestamp"][:7]
            line_count[oid] += 1
            item_per_order[oid] += amount
            self.revenue += amount
            self.month_revenue[month] += amount
            category = products.get(item["product_id"]) or "unknown"
            if month.startswith("2018-"):
                self.categories_2018[translations.get(category, category)] += amount
        for r in rows("order_payments"):
            oid = r["order_id"]
            if oid in self.delivered:
                payment_count[oid] += 1
                payment_per_order[oid] += Decimal(r["payment_value"])
        cohort = [
            oid
            for oid in self.delivered
            if line_count[oid] > 1 and payment_count[oid] > 1
        ]
        self.fanout = {
            "orders": len(cohort),
            "items_brl": float(sum(item_per_order[o] for o in cohort)),
            "payments_brl": float(sum(payment_per_order[o] for o in cohort)),
        }

        choices = defaultdict(list)
        for n, r in enumerate(rows("order_reviews"), 1):
            if r["review_score"] in {"1", "2", "3", "4", "5"}:
                choices[r["order_id"]].append(
                    (
                        r["review_answer_timestamp"],
                        r["review_creation_date"],
                        r["review_id"],
                        n,
                        int(r["review_score"]),
                    )
                )
        self.exclusions = dict(
            total_orders=len(self.orders),
            not_delivered=len(self.orders) - len(self.delivered),
            missing_delivery_time=0,
            no_valid_review=0,
            included_orders=0,
        )
        self.groups = {
            g: {label: [0, 0] for label in ("late", "on_time")}
            for g in ("timestamp", "day")
        }
        for oid in self.delivered:
            order = self.orders[oid]
            actual, estimate = (
                order["order_delivered_customer_date"],
                order["order_estimated_delivery_date"],
            )
            if not (actual and estimate):
                self.exclusions["missing_delivery_time"] += 1
                continue
            reviews = choices.get(oid)
            if not reviews:
                self.exclusions["no_valid_review"] += 1
                continue
            self.exclusions["included_orders"] += 1
            latest = max(r[:2] for r in reviews)
            chosen = min(
                (r for r in reviews if r[:2] == latest),
                key=lambda r: (not r[2], r[2], r[3]),
            )
            for grain, late in (
                ("timestamp", actual > estimate),
                ("day", actual[:10] > estimate[:10]),
            ):
                bucket = self.groups[grain]["late" if late else "on_time"]
                bucket[0] += 1
                bucket[1] += int(chosen[4] <= 2)


def group_summary(groups):
    """Newcombe method 10, using separately calculated Wilson score intervals."""

    def wilson(n, k):
        z = NormalDist().inv_cdf(0.975)
        p = k / n
        den = 1 + z * z / n
        center = (p + z * z / (2 * n)) / den
        half = z * sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / den
        return center - half, center + half

    late_n, late_k = groups["late"]
    on_n, on_k = groups["on_time"]
    a, b = late_k / late_n, on_k / on_n
    al, ah = wilson(late_n, late_k)
    bl, bh = wilson(on_n, on_k)
    diff = a - b
    return {
        "groups": {
            label: {"n": n, "negative": k, "rate": k / n}
            for label, (n, k) in groups.items()
        },
        "risk_difference": diff,
        "ci95": [diff - hypot(a - al, bh - b), diff + hypot(ah - a, b - bl)],
    }
