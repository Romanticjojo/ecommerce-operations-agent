"""Single-request orchestration for the demo grammar, model planner and direct baseline."""
import re
from pathlib import Path
from time import perf_counter

import duckdb
from pydantic import ValidationError

from . import model
from .plans import Plan, bounds, compile_plan, demo_plan, iso_day
from .query_guard import InvalidSQL, QueryError, Rejected, execute, validate_sql
from .schema import METRICS
from .settings import model_status


_MESSAGES = {
    "clarification_required": ("请指定支持的指标、分组和日期范围。离线演示可使用页面上的示例问题。", "Please specify a supported metric, grouping and date range. In demo mode, try one of the example questions."),
    "rejected": ("此工作台仅支持对经营数据进行受限的只读分析。", "This workbench supports bounded, read-only analysis of the reporting views."),
    "insufficient_data": ("所选范围内没有足够的符合条件的数据。", "There is insufficient eligible data in the selected range."),
    "model_configuration": ("请在服务端配置模型名称与兼容接口地址。", "Configure the model name and compatible API URL on the server."),
    "model_authentication": ("模型服务拒绝认证。请检查服务端凭据。", "The model service denied authentication. Check the server-side credentials."),
    "model_rate_limited": ("模型服务触发限流，请稍后重试。", "The model service rate limit was reached. Try again later."),
    "model_timeout": ("模型请求超时，请稍后重试。", "The model request timed out. Try again later."),
    "model_connection": ("模型服务连接失败，请检查服务地址与网络。", "The model service could not be reached. Check its URL and network connection."),
    "model_service_error": ("模型服务未能完成请求。", "The model service could not complete this request."),
    "model_invalid_response": ("模型返回的内容不符合结构化响应要求。", "The model returned an invalid structured response."),
    "invalid_plan": ("模型计划未通过字段校验。", "The model plan failed field validation."),
    "invalid_sql": ("查询未通过字段或语法校验。", "The query failed syntax or column validation."),
    "query_timeout": ("查询超过执行时限，已停止。", "The query exceeded its time limit and was stopped."),
    "query_execution_failed": ("只读查询未能完成，请检查本地数据快照。", "The read-only query could not complete. Check the local data snapshot."),
}
_METRICS = {
    "item_revenue": ("商品成交额", "item revenue"), "aov": ("客单价", "average order value"),
    "order_count": ("订单数", "order count"), "payment_total": ("支付金额", "payment total"),
    "negative_count": ("差评订单数", "negative review count"), "negative_rate": ("差评率", "negative review rate"),
    "reviewed_order_count": ("有效评价订单数", "reviewed order count"),
}
_UNSAFE = re.compile(r"\b(drop|truncate|delete|insert|attach|detach|pragma|install|uninstall)\b|\b(update|alter|create)\s+(?:the\s+)?(?:orders?|tables?|database|set)\b|\b(read_csv|read_parquet|read_text)\s*\(|删除(?:数据|表|所有)|清空(?:数据|表)", re.I)


def _text(key, en):
    return _MESSAGES[key][int(en)]


def _summary(rows, plan, en):
    first = next(row for row in rows if row[plan.metric] is not None)
    label = _METRICS[plan.metric][int(en)]
    value = first[plan.metric]
    if plan.metric == "negative_rate":
        display = f"{value:.2%}"
    elif plan.metric in {"aov", "item_revenue", "payment_total"}:
        display = f"BRL {value:,.2f}"
    else:
        display = f"{value:,}"
    if plan.dimension == "total":
        return f"{label.capitalize()} is {display}." if en else f"{label}为 {display}。"
    group = first[plan.dimension]
    if en:
        return f"Returned {len(rows)} groups. For {group}, {label} is {display}."
    return f"返回 {len(rows)} 个分组。{group} 的{label}为 {display}。"


def _investigate(db, plan, left, right, out, en):
    from .stats import investigate

    if any((plan.metric, plan.state, plan.category, plan.delivery_group, plan.sort, plan.limit,
            plan.status != "delivered", plan.dimension != "total")):
        raise ValueError("unsupported_investigation_scope")
    if left and right and left >= right:
        out.update(status="insufficient_data", answer=_text("insufficient_data", en))
        return
    started = perf_counter()
    out["evidence"]["generated_sql"] = True
    try:
        stat = investigate(db, start=left, end=right, grain=plan.grain)
    except duckdb.Error:
        raise QueryError("query_execution_failed") from None
    out["evidence"]["statistics_ms"] = round((perf_counter() - started) * 1000, 2)
    out["evidence"]["sql_success"] = True
    groups = [{"group": name, **values} for name, values in stat["groups"].items()]
    out["evidence"].update(sql=stat["sql"], filters=dict(stat["filters"], status="delivered"), grain=plan.grain, row_count=len(groups),
                           metric_ids=["negative_rate", "risk_difference"], statistics={
                               k: stat[k] for k in ("risk_difference", "ci95", "p_value", "test", "exclusions", "limitations", "exclusions_sql")
                           })
    ok = stat["status"] == "completed"
    if ok:
        effect = stat["risk_difference"] * 100
        answer = (f"The late group’s negative review rate differs from the on-time group’s by {effect:+.2f} percentage points. This observational comparison cannot establish causation." if en else
                  f"延迟组差评率比准时组相差 {effect:+.2f} 个百分点。该观察性比较不能确立因果关系。")
    else:
        answer = _text("insufficient_data", en)
    out.update(status="ok" if ok else "insufficient_data", table=groups, answer=answer)


def _run(db, question, chosen, en, left, right, variant, out):
    evidence = out["evidence"]
    evidence["filters"] = {"start": left, "end": right}
    if _UNSAFE.search(question):
        raise Rejected("unsafe_request")
    direct = chosen == "model" and variant == "direct"
    sql = None
    plan = None
    if chosen == "demo":
        plan = demo_plan(question)
    else:
        for attempt in range(2):
            started = perf_counter()
            try:
                raw, usage = model.complete(question, variant, left, right, correction=attempt > 0)
            except model.ModelError:
                out["usage"] = None
                raise
            finally:
                evidence["model_ms"] += round((perf_counter() - started) * 1000, 2)
            if not attempt:
                out["usage"] = usage
            elif out["usage"] and usage:
                out["usage"] = {k: v + usage[k] for k, v in out["usage"].items()}
            else:
                out["usage"] = None
            if isinstance(raw.get("sql"), str) and raw["sql"].strip():
                evidence["generated_sql"] = True
            if direct and raw.get("intent") == "sql" and set(raw) == {"intent", "sql"}:
                sql = validate_sql(raw["sql"])
                break
            if "sql" in raw:
                # An unsafe candidate cannot trigger a repair. Full plans never execute provider SQL.
                validate_sql(raw["sql"])
                raise model.ModelError("invalid_plan")
            try:
                plan = Plan.model_validate(raw)
                if direct and plan.intent not in {"investigation", "clarification_required", "rejected"}:
                    raise model.ModelError("invalid_plan")
                break
            except ValidationError:
                if attempt or direct:
                    raise model.ModelError("invalid_plan") from None
                evidence["repairs"] = 1
    if plan:
        if plan.intent in {"rejected", "clarification_required"}:
            out.update(status=plan.intent, answer=_text(plan.intent, en))
            return
        if plan.start and plan.end and plan.start >= plan.end:
            raise model.ModelError("invalid_plan")
        left, right = bounds(plan, left, right)
        evidence["filters"].update(start=left, end=right)
        evidence["plan"] = plan.model_dump(exclude_none=True)
        if plan.intent == "investigation":
            _investigate(db, plan, left, right, out, en)
            return
        sql, filters = compile_plan(plan, left, right)
        evidence.update(filters=filters, metric_ids=[plan.metric], grain=plan.dimension)
        if plan.metric in {"item_revenue", "aov", "payment_total"}:
            evidence["currency"] = "BRL"
    evidence["generated_sql"] = True
    result = execute(db, sql)
    evidence["sql_success"] = True
    rows = result["rows"]
    evidence.update(sql=result["sql"], row_count=len(rows), truncated=result["truncated"], sql_ms=result["sql_ms"])
    if result["truncated"]:
        evidence["warnings"].append("Only the first 1,000 rows are shown." if en else "仅显示前 1,000 行。")
    if not rows or (plan and all(row[plan.metric] is None for row in rows)):
        out.update(status="insufficient_data", answer=_text("insufficient_data", en))
        return
    if direct:
        msg = f"Returned {len(rows)} rows." if en else f"查询返回 {len(rows)} 行。"
    else:
        msg = _summary(rows, plan, en)
        if plan.dimension != "total":
            out["chart"] = {"type": "line" if plan.dimension == "month" else "bar", "x": plan.dimension, "y": plan.metric}
    out.update(status="ok", answer=msg, table=rows)


def ask(db: Path, question: str, *, mode="auto", language="en", start=None, end=None, variant="full"):
    began = perf_counter()
    configured = model_status()
    chosen = configured["mode"] if mode == "auto" else mode
    en = language == "en"
    evidence = {"sql": None, "filters": {}, "metric_ids": [], "grain": None, "row_count": 0, "truncated": False,
                "generated_sql": False, "sql_success": False, "warnings": [], "language": language, "variant": variant, "repairs": 0, "model_ms": 0, "sql_ms": None,
                "model": configured["model"] if chosen == "model" else None,
                "prompt_version": ("demo-1" if chosen == "demo" else model.DIRECT_VERSION if variant == "direct" else model.PROMPT_VERSION)}
    out = {"status": "error", "mode": chosen, "answer": "", "table": [], "chart": None, "evidence": evidence, "usage": None}
    try:
        if chosen not in {"demo", "model"} or variant not in {"direct", "full"} or language not in {"zh", "en"}:
            raise ValueError("unsupported_option")
        if not isinstance(question, str) or not 1 <= len(question.strip()) <= 1500:
            raise ValueError("invalid_question")
        left, right = iso_day(start), iso_day(end)
        if left and right and left >= right:
            raise ValueError("invalid_period")
        _run(db, question.strip(), chosen, en, left, right, variant, out)
    except Rejected as error:
        evidence["error_code"] = str(error)
        out.update(status="rejected", answer=_text("rejected", en))
    except InvalidSQL as error:
        evidence["error_code"] = str(error)
        out["answer"] = _text("invalid_sql", en)
    except (model.ModelError, QueryError) as error:
        evidence["error_code"] = str(error)
        out["answer"] = _text(str(error), en)
    except ValueError:
        out.update(status="clarification_required", answer=_text("clarification_required", en))
    definitions = {metric["id"]: metric["definition"] for metric in METRICS}
    if evidence["filters"].get("status", "delivered") != "delivered":
        definitions["order_count"] = "Distinct orders in the selected status by purchase date."
    evidence["metric_definitions"] = {key: definitions[key] for key in evidence["metric_ids"]}
    out["timing_ms"] = round((perf_counter() - began) * 1000, 2)
    out["estimated_cost_usd"] = model.cost_usd(out["usage"])
    return out
