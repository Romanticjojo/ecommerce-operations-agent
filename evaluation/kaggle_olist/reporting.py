"""Generate the complete reviewable report from actual pytest observations."""

import json


def dump(obj):
    return json.dumps(obj, ensure_ascii=False, indent=2, allow_nan=False)


def write_reports(directory, metadata, cases, exit_code):
    directory.mkdir(parents=True, exist_ok=True)
    passed = sum(c["status"] == "PASS" for c in cases)
    payload = {
        "pytest_exit_code": exit_code,
        "passed": passed,
        "total": len(cases),
        "environment": metadata,
        "cases": cases,
    }
    (directory / "results.json").write_text(dump(payload) + "\n", encoding="utf-8")
    (directory / "manifest.json").write_text(dump(metadata) + "\n", encoding="utf-8")
    lines = [
        "# Olist 真实数据验收报告",
        "",
        f"**{passed} / {len(cases)} 项通过**。pytest 退出码为 `{exit_code}`。",
        "",
        f"运行时间（UTC） `{metadata.get('utc', '—')}`。数据来源为 [Olist 官方 Kaggle 数据集](https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce)，本次解析到版本 **{metadata.get('resolved_version', '—')}**。",
        "",
        f"操作系统 `{metadata.get('platform', '—')}`，Python `{metadata.get('python', '—')}`。业务数据快照 `{metadata.get('snapshot', '—')}`。",
        "",
        "**共同前置条件**：KaggleHub 取得指定数据，在临时工作目录新建 DuckDB 快照；服务监听本机随机端口。预期数值由 Python CSV、Decimal 与独立统计公式计算。自然语言测试显式指定离线演示模式。",
        "",
        "**共同后置条件**：HTTP 查询及统计仅访问该快照，历史写入临时数据库。会话结束时关闭服务。每项耗时只计调用与断言，下载和建库时间另计。该报告衡量指定数据集上的功能与数值一致性。",
        "",
        "[机器可读结果](results.json) · [九个源文件的行数、字节数、SHA-256 与环境](manifest.json)",
        "",
        "[观看 K03 本地测试全程（MP4）](https://github.com/Romanticjojo/ecommerce-operations-agent/raw/refs/heads/main/evaluation/kaggle_olist/media/K03-revenue.mp4)",
        "",
        "## 在本地复现",
        "",
        "以下命令在本仓库或完整测试包的根目录执行（Python 3.11）。首行创建虚拟环境，随后安装锁定的应用依赖与 KaggleHub。",
        "",
        "```sh",
        "python3.11 -m venv .venv",
        ".venv/bin/python -m pip install -r evaluation/kaggle_olist/requirements.txt",
        "```",
        "",
        "本项目指定的数据集和下载入口如下。无版本号时由 KaggleHub 解析最新版；复查本报告时选用本次实测版本。",
        "",
        "```python",
        "import kagglehub",
        'path = kagglehub.dataset_download("olistbr/brazilian-ecommerce")',
        'print("Path to dataset files:", path)',
        "```",
        "",
        "```sh",
        "# 全套用例；pytest 会自行取数、建库并启动本机服务",
        f".venv/bin/python -m pytest -q evaluation/kaggle_olist/cases.py --olist-version {metadata.get('resolved_version') or '2'}",
        "# 单跑 K03，并显示实际 HTTP 输入与断言两侧的值",
        f".venv/bin/python -m pytest -q -s evaluation/kaggle_olist/cases.py::test_k03_revenue --olist-version {metadata.get('resolved_version') or '2'} --olist-trace --olist-output runtime/k03",
        "```",
        "",
        "整套用例的默认输出目录为 `runtime/kaggle-acceptance/`，上方 K03 命令使用独立的 `runtime/k03/`。两者均生成 REPORT.md、results.json 和 manifest.json。",
        "",
        "## 本次运行的数据与环境",
        "",
        f"发布者 Olist；数据许可 {metadata.get('data_license', '—')}。版本 {metadata.get('resolved_version', '—')} 的源文件如下。行数使用 CSV 解析器计数，不含表头。",
        "",
        "| 源文件 | 用途 | 记录数 | 字节数 | SHA-256 |",
        "|---|---|---:|---:|---|",
        *[
            f"| `{file}` | {'仅审计' if 'geolocation' in file else '导入'} | {entry['rows']:,} | {entry['bytes']:,} | `{entry['sha256']}` |"
            for file, entry in metadata.get("files", {}).items()
        ],
        "",
        "运行依赖："
        + "、".join(
            f"`{key} {value}`" for key, value in metadata.get("packages", {}).items()
        )
        + "。",
        "",
        "## 用例总览",
        "",
        "| 用例 | 检查内容 | 结果 | 耗时（ms） |",
        "|---|---|---|---:|",
    ]
    for case in cases:
        lines.append(
            f"| {case['id']} | {case['title']} | {case['status']} | {case['duration_ms']:.2f} |"
        )
    lines += [
        "",
        "## 用例明细",
        "",
        "HTTP 输入中的日期区间左闭右开；BRL 为巴西雷亚尔。Geo 文件包含地理位置数据，本系统使用其余八个 CSV。采集请求时保留实际执行的 SQL。",
    ]
    for case in cases:
        lines += [
            "",
            f"### {case['id']} · {case['title']}",
            "",
            case["procedure"],
            "",
            f"**实测判定**：{case['status']}。",
            "",
            "<details><summary>查看实际输入、执行 SQL、期望值与实测值</summary>",
            "",
            "```json",
            dump(
                {
                    "requests": case["requests"],
                    "checks": case["checks"],
                    **({"reason": case["reason"]} if "reason" in case else {}),
                }
            ),
            "```",
            "",
            "</details>",
        ]
    (directory / "REPORT.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
