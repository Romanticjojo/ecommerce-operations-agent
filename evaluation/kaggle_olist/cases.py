"""15 opt-in acceptance cases for the real Kaggle data. Run as described in README.md."""

import duckdb

from oracle import group_summary


def test_k01_import(probe):
    """导入清单与原始文件一致
    请求数据目录。对照下载目录中 CSV 的 SHA-256 和按 CSV 记录计数的行数，逐表核对七张核心表及翻译表。地理坐标文件只列入下载清单。"""
    cat = probe.api("GET", "/api/catalog")
    expected = {
        name: {"rows": entry["rows"], "sha256": entry["sha256"]}
        for name, entry in probe.ref.files.items()
        if name != "olist_geolocation_dataset.csv"
    }
    observed = {
        v["filename"]: {"rows": v["rows"], "sha256": v["sha256"]}
        for v in cat["audit"]["files"].values()
    }
    probe.check("业务表、翻译表的行数与摘要", expected, observed)
    probe.check(
        "数据来源与导入快照",
        ["olist", probe.snapshot],
        [cat["source"], cat["snapshot"]],
    )


def test_k02_order_count(probe):
    """汇总已送达订单
    用英文查询订单数。以原始订单表中状态为 delivered 的不同订单 ID 数为期望值。"""
    answer = probe.ask("Show total delivered order count.")
    probe.check(
        "已送达订单数", [{"order_count": len(probe.ref.delivered)}], answer["table"]
    )


def test_k03_revenue(probe):
    """核对已送达商品成交额
    请求“总销售额”。独立累加已送达订单下的商品价格，使用十进制定点数，单位 BRL，精确到分。"""
    answer = probe.ask("总销售额")
    probe.check(
        "商品成交额（BRL）",
        [{"item_revenue": float(probe.ref.revenue)}],
        answer["table"],
    )


def test_k04_aov(probe):
    """核对客单价
    请求“客单价”。将已送达商品成交额除以已送达订单数，比对保留两位小数的 BRL 金额。"""
    answer = probe.ask("客单价")
    want = round(float(probe.ref.revenue / len(probe.ref.delivered)), 2)
    probe.check("客单价（BRL）", want, round(answer["table"][0]["aov"], 2))


def test_k05_months(probe):
    """2017 年逐月订单趋势
    请求 2017 年月度已送达订单数。从 CSV 按购买年月计数，完整比较每月标签、行数、数值及顺序。"""
    answer = probe.ask("Show monthly delivered orders in 2017.")
    want = [
        {"month": m + "-01", "order_count": n}
        for m, n in sorted(probe.ref.month_counts.items())
        if m.startswith("2017-")
    ]
    probe.check("各月订单数", want, answer["table"])


def test_k06_categories(probe):
    """2018 年成交额前十品类
    按 CSV 关联已送达订单行、商品和品类翻译，缺翻译时回退到原始品类。按金额降序、品类名升序取十项，核对完整排名。"""
    answer = probe.ask("2018 年哪些品类的商品成交额最高？")
    ranked = sorted(
        probe.ref.categories_2018.items(), key=lambda pair: (-pair[1], pair[0])
    )[:10]
    probe.check(
        "前十品类及 BRL 金额",
        [{"category": k, "item_revenue": float(v)} for k, v in ranked],
        answer["table"],
    )


def test_k07_half_open(probe):
    """日期窗口按购买日左闭右开
    查询 2018-01-01 至 2018-02-01（不含）商品成交额。独立汇总购买月份为 2018-01 的商品行，并核对证据中的实际日期范围。"""
    start, end = "2018-01-01", "2018-02-01"
    answer = probe.ask("总销售额", start=start, end=end)
    probe.check(
        "一月商品成交额",
        [{"item_revenue": float(probe.ref.month_revenue["2018-01"])}],
        answer["table"],
    )
    filters = answer["evidence"]["filters"]
    probe.check("日期边界", [start, end], [filters["start"], filters["end"]])


def test_k08_join(probe):
    """多商品且多支付的订单不会放大金额
    仅取商品行数和支付行数均大于一的已送达订单。独立 CSV 逐单累加商品及支付，再用只读连接检查 order_summary 中相同子集的行数和两种金额。"""
    sql = """SELECT count(*),sum(item_revenue),sum(payment_total) FROM order_summary
        WHERE status='delivered' AND item_count>1 AND order_id IN
        (SELECT order_id FROM order_payments GROUP BY order_id HAVING count(*)>1)"""
    probe.record["requests"].append({"method": "DuckDB read-only", "executed_sql": sql})
    with duckdb.connect(str(probe.db), read_only=True) as con:
        count, items, paid = con.execute(sql).fetchone()
    assert probe.ref.fanout["orders"] > 0
    probe.check(
        "交叉子集的订单数、商品额与支付额",
        probe.ref.fanout,
        {"orders": count, "items_brl": float(items), "payments_brl": float(paid)},
    )


def test_k09_sample(probe):
    """调查样本筛选与排除数
    运行配送调查，检查未送达、缺配送时间、缺有效评价、纳入分析四项互斥计数；与原始文件逐单分类结果比对。"""
    result = probe.api("POST", "/api/investigation", {"grain": "timestamp"})
    probe.check("订单纳入与排除", probe.ref.exclusions, result["exclusions"])


def rounded(summary):
    return {
        "groups": {
            k: {**g, "rate": round(g["rate"], 9)} for k, g in summary["groups"].items()
        },
        "risk_difference": round(summary["risk_difference"], 9),
        "ci95": [round(v, 9) for v in summary["ci95"]],
    }


def test_k10_timestamp(probe):
    """时间戳口径下的风险差与区间
    按每单最新有效评价，将签收时间晚于预计时间的订单分入延迟组。独立计算两组差评数、率、风险差及 Newcombe-Wilson 95% 区间，比较到小数点后九位。"""
    result = probe.api("POST", "/api/investigation", {"grain": "timestamp"})
    actual = {
        **result,
        "groups": {
            g["group"]: {k: g[k] for k in ("n", "negative", "rate")}
            for g in result["groups"]
        },
    }
    probe.check(
        "时间戳分组与统计量",
        rounded(group_summary(probe.ref.groups["timestamp"])),
        rounded(actual),
    )
    probe.check(
        "版本 2 的大样本检验",
        ["pearson_chi2", True],
        [result["test"], 0 <= result["p_value"] < 0.001],
    )


def test_k11_calendar(probe):
    """自然日口径的敏感性分析
    将实际和预计签收时间截到日期后重算两组，核对各组样本量和差评数；同日较晚签收的订单归入准时组。"""
    result = probe.api("POST", "/api/investigation", {"grain": "day"})
    probe.check(
        "按日分组（订单数、差评数）",
        probe.ref.groups["day"],
        {g["group"]: [g["n"], g["negative"]] for g in result["groups"]},
    )


def test_k12_empty(probe):
    """缺少订单时给出数据不足状态
    查询 2099 年的成交额。此数据版本在该年度没有订单，预期状态为 insufficient_data 且结果表为空。"""
    answer = probe.ask("What is total item revenue in 2099?")
    probe.check(
        "状态与结果表", ["insufficient_data", []], [answer["status"], answer["table"]]
    )


def test_k13_invalid_dates(probe):
    """拒绝反向日期区间
    对差评调查提交早于起始日的结束日。预期返回 HTTP 422，响应包含日期范围校验错误。"""
    result = probe.api(
        "POST",
        "/api/investigation",
        {"start": "2018-02-01", "end": "2018-01-01"},
        code=422,
    )
    probe.check(
        "说明结束日期必须晚于开始日期",
        True,
        any("结束日期" in e["msg"] for e in result["detail"]),
    )


def test_k14_unavailable_metric(probe):
    """离线模式处理缺失的利润指标
    提问税后净利润。离线问题目录没有该指标，预期请求澄清，结果表为空，且没有执行 SQL。"""
    answer = probe.ask("2018 年税后净利润是多少？")
    probe.check(
        "澄清状态、行数与执行 SQL",
        ["clarification_required", 0, None],
        [answer["status"], len(answer["table"]), answer["evidence"]["sql"]],
    )


def test_k15_replay(probe):
    """历史记录与执行证据可重放
    查询 2017 年商品成交额，按返回 ID 取回历史记录。核对快照、问题、SQL 和输出，在同一只读快照重放该 SQL，并与 2017 年 CSV 合计对账。"""
    answer = probe.ask("What is total item revenue in 2017?")
    stored = probe.api("GET", "/api/runs/" + answer["request_id"])
    probe.check("历史记录完整回读", True, stored == answer)
    probe.check("历史快照", probe.snapshot, stored["evidence"]["snapshot"])
    sql = stored["evidence"]["sql"]
    with duckdb.connect(str(probe.db), read_only=True) as con:
        value = con.execute(sql).fetchone()[0]
    expected = float(
        sum(v for m, v in probe.ref.month_revenue.items() if m.startswith("2017-"))
    )
    probe.check(
        "CSV、历史表格、SQL 重放（BRL）",
        [expected, expected],
        [stored["table"][0]["item_revenue"], float(value)],
    )
