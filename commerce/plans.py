"""Bounded analytical plans. Identifiers and metric formulas come from this catalog."""
import re
import unicodedata
from datetime import date
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, StrictInt, field_validator, model_validator


SALES = {"item_revenue": "SUM(item_revenue)", "payment_total": "SUM(payment_total)",
         "order_count": "COUNT(DISTINCT order_id)",
         "aov": "SUM(item_revenue) / NULLIF(COUNT(DISTINCT order_id), 0)"}
REVIEWS = {"reviewed_order_count": "COUNT(*)",
           "negative_count": "SUM(CASE WHEN review_score <= 2 THEN 1 ELSE 0 END)",
           "negative_rate": "AVG(CASE WHEN review_score <= 2 THEN 1.0 ELSE 0.0 END)"}
STATUSES = {"delivered", "canceled", "unavailable", "invoiced", "shipped", "processing", "created", "approved"}


def iso_day(value):
    if value is None:
        return None
    if isinstance(value, date):
        value = value.isoformat()
    if not isinstance(value, str) or not re.fullmatch(r"\d{4}-\d{2}-\d{2}", value):
        raise ValueError("invalid_date")
    return date.fromisoformat(value).isoformat()


class Plan(BaseModel):
    model_config = ConfigDict(extra="forbid")
    intent: Literal["sales", "reviews", "investigation", "skill", "clarification_required", "rejected"]
    skill_id: str | None = Field(default=None, max_length=40)
    metric: Literal["item_revenue", "payment_total", "order_count", "aov", "reviewed_order_count", "negative_count", "negative_rate"] | None = None
    dimension: Literal["total", "month", "category", "state", "delivery_group"] = "total"
    sort: Literal["asc", "desc", "dimension"] | None = None
    limit: StrictInt | None = Field(default=None, ge=1, le=1000)
    year: StrictInt | None = Field(default=None, ge=1, le=9998)
    start: str | None = None
    end: str | None = None
    state: str | None = Field(default=None, pattern=r"^[A-Z]{2}$")
    category: str | None = Field(default=None, min_length=1, max_length=100)
    status: str = "delivered"
    delivery_group: Literal["late", "on_time"] | None = None
    grain: Literal["timestamp", "day"] = "timestamp"

    @model_validator(mode="after")
    def skill_parameters(self):
        if self.intent == "skill":
            from .skills import SKILLS
            if self.skill_id not in SKILLS or self.model_fields_set - {"intent", "skill_id", "start", "end", "year"}:
                raise ValueError("unsupported_skill_scope")
        elif self.skill_id is not None:
            raise ValueError("unexpected_skill")
        return self

    @field_validator("start", "end")
    @classmethod
    def valid_day(cls, value):
        return iso_day(value)


def bounds(plan, start, end):
    lefts, rights = [v for v in (plan.start, start) if v], [v for v in (plan.end, end) if v]
    if plan.year:
        lefts.append(f"{plan.year:04}-01-01")
        rights.append(f"{plan.year + 1:04}-01-01")
    return max(lefts, default=None), min(rights, default=None)


def compile_plan(plan, start, end):
    review = plan.intent == "reviews"
    category = bool(plan.category or plan.dimension == "category")
    if review:
        if (plan.metric not in REVIEWS or plan.dimension not in {"total", "month", "delivery_group"}
                or plan.state or category or plan.status != "delivered"):
            raise ValueError("unsupported_metric_scope")
        source = "order_review_delivery"
        aggregate = REVIEWS[plan.metric]
    else:
        if (plan.intent != "sales" or plan.metric not in SALES or plan.delivery_group
                or plan.dimension == "delivery_group" or plan.status not in STATUSES
                or (plan.status != "delivered" and plan.metric != "order_count")
                or (category and (plan.state or plan.dimension == "state" or plan.status != "delivered"
                                  or plan.metric not in {"item_revenue", "order_count"}))):
            raise ValueError("unsupported_metric_scope")
        source = "category_sales" if category else "order_summary"
        aggregate = SALES[plan.metric]
    late_flag = "late_" + plan.grain
    dimension_sql = {"total": None, "month": "CAST(DATE_TRUNC('month', purchased_at) AS DATE)", "category": "category",
                     "state": "state", "delivery_group": f"CASE WHEN {late_flag} THEN 'late' ELSE 'on_time' END"}[plan.dimension]
    columns = [f"{aggregate} AS {plan.metric}"]
    if dimension_sql:
        columns.insert(0, f"{dimension_sql} AS {plan.dimension}")
    conditions = []
    evidence = {"status": plan.status, "start": start, "end": end}
    if source == "order_summary":
        conditions.append(f"status = '{plan.status}'")
    if plan.dimension == "month":
        conditions.append("purchased_at IS NOT NULL")
        evidence["requires_purchase_time"] = True
    if start:
        conditions.append(f"purchased_at >= DATE '{start}'")
    if end:
        conditions.append(f"purchased_at < DATE '{end}'")
    if plan.state:
        conditions.append(f"state = '{plan.state}'")
        evidence["state"] = plan.state
    if plan.category:
        conditions.append("category = '" + plan.category.replace("'", "''") + "'")
        evidence["category"] = plan.category
    if plan.delivery_group:
        conditions.append(f"{late_flag} = " + ("TRUE" if plan.delivery_group == "late" else "FALSE"))
        evidence["delivery_group"] = plan.delivery_group
    sql = "SELECT " + ", ".join(columns) + " FROM " + source
    if conditions:
        sql += " WHERE " + " AND ".join(conditions)
    if dimension_sql:
        sql += " GROUP BY " + plan.dimension
        sort = plan.sort or ("dimension" if plan.dimension == "month" else "desc")
        if sort == "dimension":
            sql += " ORDER BY " + plan.dimension
        else:
            sql += f" ORDER BY {plan.metric} {sort.upper()}, {plan.dimension} ASC"
    else:
        sql += " HAVING COUNT(*) > 0"
    if plan.limit is not None:
        sql += f" LIMIT {plan.limit}"
    return sql, evidence


# Offline grammar admits whole supported requests only. Trailing qualifiers must never disappear.
_Y = r"(?: in (\d{4}))?"
_DEMOS = (
    (rf"(?:show |list |what are )?(?:the )?top (\d{{1,3}}) (?:product )?categories by (?:item )?revenue{_Y}", "category", "item_revenue"),
    (rf"(?:show |list )?(?:the )?monthly (?:delivered )?(?:orders|order count){_Y}", "month", "order_count"),
    (rf"(?:show |list )?(?:the )?monthly (?:item )?revenue{_Y}", "month", "item_revenue"),
    (rf"(?:show |what is |what was )?(?:the )?total (?:item )?revenue{_Y}", "total", "item_revenue"),
    (rf"(?:show |what is |what was )?(?:the )?(?:average order value|aov){_Y}", "total", "aov"),
    (rf"(?:how many delivered orders were there|(?:show )?(?:total )?delivered order count){_Y}", "total", "order_count"),
)
_ASSOCIATION = {
    "are late deliveries associated with negative customer reviews",
    "are late deliveries associated with negative reviews",
    "配送延迟与差评是否相关", "配送延迟是否与差评有关", "延迟配送和差评有关联吗",
    "延迟配送与差评是否相关", "延迟配送是否与差评相关",
}


def demo_plan(question):
    text = " ".join(unicodedata.normalize("NFKC", question).casefold().split()).rstrip(" ?.。!")
    if text in _ASSOCIATION:
        return Plan(intent="investigation")
    for pattern, dim, metric in _DEMOS:
        match = re.fullmatch(pattern, text)
        if match:
            year = match.groups()[-1]
            return Plan(intent="sales", metric=metric, dimension=dim, year=int(year) if year else None,
                        limit=int(match[1]) if dim == "category" else None)
    text = text.replace(" ", "")
    year = None
    prefix = re.match(r"^(\d{4})年", text)
    if prefix:
        year, text = int(prefix[1]), text[prefix.end():]
    if text == "哪些品类的商品成交额最高":
        return Plan(intent="sales", metric="item_revenue", dimension="category", year=year, limit=10)
    category = re.fullmatch(r"(?:按)?(?:商品)?(?:成交额|销售额|收入|销售收入)(?:排名)?前(\d{1,3})(?:的|名)?(?:个)?(?:商品)?品类(?:有哪些|是什么)?", text)
    if category:
        return Plan(intent="sales", metric="item_revenue", dimension="category", year=year, limit=int(category[1]))
    chinese = {
        "每月已交付订单数": ("month", "order_count"), "每月已送达订单数": ("month", "order_count"),
        "每月已完成订单数": ("month", "order_count"), "每月订单数": ("month", "order_count"),
        "按月统计商品成交额": ("month", "item_revenue"), "每月商品成交额": ("month", "item_revenue"), "月度商品成交额": ("month", "item_revenue"),
        "商品总成交额": ("total", "item_revenue"), "总销售额": ("total", "item_revenue"),
        "平均订单金额": ("total", "aov"), "客单价": ("total", "aov"),
    }
    dim_metric = chinese.get(re.sub(r"(?:是多少|多少)$", "", text))
    if dim_metric:
        return Plan(intent="sales", dimension=dim_metric[0], metric=dim_metric[1], year=year)
    return Plan(intent="clarification_required")
