"""Optional browser acceptance against an already running, populated local workbench.

pip install playwright && python -m playwright install chromium
python scripts/browser_smoke.py http://127.0.0.1:8731
Set BROWSER_CHANNEL=chrome to use an installed Google Chrome.
"""

import os
import sys
from playwright.sync_api import sync_playwright

base = (sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:8731").rstrip("/")
with sync_playwright() as playwright:
    browser = playwright.chromium.launch(channel=os.getenv("BROWSER_CHANNEL"))
    context = browser.new_context(
        viewport={"width": 1440, "height": 960},
        permissions=["clipboard-read", "clipboard-write"],
    )
    page = context.new_page()
    errors = []
    page.on("pageerror", lambda error: errors.append(str(error)))
    page.goto(base, wait_until="networkidle")
    page.get_by_role("heading", name="运营概览", exact=True).wait_for()
    page.get_by_role("link", name="比较延迟与准时送达订单").click()
    page.get_by_role("heading", name="差评调查", exact=True).wait_for()
    page.get_by_role("link", name="分析工作台", exact=True).click()
    page.get_by_role("button", name="总销售额", exact=True).click()
    assert page.locator("#question").input_value() == "总销售额"
    page.locator("#question").fill(
        "Show the top 10 product categories by item revenue in 2018."
    )
    with page.expect_response("**/api/query") as query:
        page.get_by_role("button", name="运行分析").click()
    result = query.value.json()
    assert result["status"] == "ok" and result["table"]
    page.get_by_role("button", name="表格", exact=True).click()
    assert page.locator("tbody tr").count() == len(result["table"])
    page.get_by_text("查询证据与 SQL", exact=True).click()
    page.get_by_role("button", name="复制 SQL").click()
    assert page.evaluate("navigator.clipboard.readText()") == result["evidence"]["sql"]
    with page.expect_download() as exported:
        page.get_by_role("button", name="导出结果").click()
    assert exported.value.suggested_filename.endswith(".json")
    page.get_by_role("link", name="差评调查", exact=True).click()
    with page.expect_response("**/api/investigation") as investigation:
        page.get_by_role("button", name="运行调查").click()
    assert investigation.value.json()["status"] == "completed"
    page.get_by_text("95% 置信区间", exact=True).wait_for()
    page.get_by_role("link", name="运行历史", exact=True).click()
    page.get_by_role(
        "button", name="Show the top 10 product categories", exact=False
    ).first.click()
    page.get_by_text("查询证据与 SQL", exact=True).wait_for()
    for width in (390, 768, 1440):
        page.set_viewport_size({"width": width, "height": 900})
        for route in (
            "overview",
            "ask",
            "investigation",
            "data",
            "evaluation",
            "history",
        ):
            page.goto(f"{base}/#{route}", wait_until="networkidle")
            page.locator("main h1").wait_for()
            assert page.evaluate(
                "document.documentElement.scrollWidth <= window.innerWidth"
            ), (route, width)
    assert not errors, errors
    print(
        "Passed: query, table, SQL clipboard, JSON export, investigation, history, 6 routes at 3 widths."
    )
    browser.close()
