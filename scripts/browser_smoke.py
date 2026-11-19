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
    assert page.locator("html").get_attribute("lang") == "en"
    page.get_by_role("heading", name="Operations overview", exact=True).wait_for()
    page.get_by_role("link", name="Compare late and on-time orders").click()
    page.get_by_role("heading", name="Delivery and reviews", level=1, exact=True).wait_for()
    nav = page.get_by_role("navigation", name="Main navigation")
    nav.get_by_role("link", name="Ask the agent", exact=True).click()
    page.get_by_role("button", name="What is total item revenue?", exact=True).click()
    assert page.locator("#question").input_value() == "What is total item revenue?"
    page.locator("#question").fill(
        "Show the top 10 product categories by item revenue in 2018."
    )
    with page.expect_response("**/api/query") as query:
        page.get_by_role("button", name="Run analysis").click()
    result = query.value.json()
    assert result["evidence"]["language"] == "en"
    assert result["status"] == "ok" and result["table"]
    page.get_by_role("button", name="Table", exact=True).click()
    assert page.locator("tbody tr").count() == len(result["table"])
    page.get_by_text("Query evidence and SQL", exact=True).click()
    page.get_by_role("button", name="Copy SQL").click()
    assert page.evaluate("navigator.clipboard.readText()") == result["evidence"]["sql"]
    with page.expect_download() as exported:
        page.get_by_role("button", name="Export result").click()
    assert exported.value.suggested_filename.endswith(".json")
    nav.get_by_role("link", name="Delivery and reviews", exact=True).click()
    with page.expect_response("**/api/investigation") as investigation:
        page.get_by_role("button", name="Run investigation").click()
    assert investigation.value.json()["status"] == "completed"
    page.get_by_text("95% confidence interval", exact=True).wait_for()
    nav.get_by_role("link", name="Run history", exact=True).click()
    page.get_by_role(
        "button", name="Show the top 10 product categories", exact=False
    ).first.click()
    page.get_by_text("Query evidence and SQL", exact=True).wait_for()
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
