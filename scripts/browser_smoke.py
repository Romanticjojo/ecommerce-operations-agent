"""Exercise the locally running workbench with Playwright and the active dataset.

Install Playwright and its Chromium browser, then run
python scripts/browser_smoke.py http://127.0.0.1:8731.
Set BROWSER_CHANNEL=chrome to use an installed Google Chrome.
"""
import json
import os
import sys
from pathlib import Path

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
    nav = page.get_by_role("navigation", name="Main navigation")
    assert nav.get_by_role("link").all_text_contents() == [
        "Operations overview", "Ask the agent", "Evaluation", "Run history",
    ]
    page.get_by_role("link", name="Compare deliveries in Ask the agent").click()
    page.get_by_role("heading", name="Ask the agent", level=1).wait_for()
    page.get_by_role("heading", name="Delivery comparison", exact=True).wait_for()
    with page.expect_response("**/api/investigation") as investigation:
        page.get_by_role("button", name="Run investigation").click()
    assert investigation.value.json()["status"] == "completed"
    page.get_by_text("95% confidence interval", exact=True).wait_for()
    with page.expect_response("**/api/investigation") as rerun:
        page.get_by_label("Calendar day", exact=True).check()
    assert rerun.value.request.post_data_json["grain"] == "day"
    page.get_by_role("heading", name="Calendar-day comparison").wait_for()

    agent_tools = page.get_by_role("navigation", name="Agent tools")
    agent_tools.get_by_role("link", name="Data reference").click()
    page.get_by_role("button", name="Metric catalog").click()
    page.get_by_role("heading", name="Metric definitions").wait_for()
    page.get_by_role("button", name="Data quality").click()
    page.get_by_role("heading", name="Import quality report").wait_for()
    agent_tools.get_by_role("link", name="Questions & skills").click()
    page.get_by_role("button", name="What is total item revenue?", exact=True).click()
    assert page.locator("#question").input_value() == "What is total item revenue?"
    top_categories = "Show the top 10 product categories by item revenue in 2018."
    page.get_by_label("Business question").fill(top_categories)
    with page.expect_response("**/api/query") as query:
        page.get_by_role("button", name="Run analysis").click()
    result = query.value.json()
    assert result["evidence"]["language"] == "en"
    assert "skill_id" not in query.value.request.post_data_json
    assert result["status"] == "ok" and result["table"]
    page.get_by_role("button", name="Table", exact=True).click()
    assert page.locator("tbody tr").count() == len(result["table"])
    page.get_by_text("Query evidence and SQL", exact=True).click()
    page.get_by_role("button", name="Copy SQL").click()
    assert page.evaluate("navigator.clipboard.readText()") == result["evidence"]["sql"]
    with page.expect_download() as exported:
        page.get_by_role("button", name="Export result").click()
    assert exported.value.suggested_filename.endswith(".json")

    skills = context.request.get(f"{base}/api/skills").json()["skills"]
    assert len({s["id"] for s in skills}) == 9
    directory = page.get_by_role("complementary", name="Analysis skills")
    for skill in skills:
        directory.get_by_role("button", name=skill["title"], exact=True).click()
        sheet = page.locator(".skill-sheet")
        for content in (skill["description"], skill["scope"], skill["question"]):
            sheet.get_by_text(content, exact=True).wait_for()
        details = sheet.locator("details")
        if not details.evaluate("(el) => el.open"):
            details.get_by_text("Analysis steps").click()
        assert details.locator("li").all_text_contents() == skill["steps"]
        with page.expect_response("**/api/query") as guided:
            page.get_by_role("button", name="Run skill", exact=True).click()
        payload = guided.value.request.post_data_json
        assert (payload["skill_id"], payload["question"]) == (skill["id"], skill["question"])
        answer = guided.value.json()
        assert answer["status"] in {"ok", "insufficient_data"}, (skill["id"], answer)
        assert answer["mode"] == "skill" and answer["evidence"]["sql"]
        if answer["evidence"]["source"] == "olist":
            assert answer["status"] == "ok" and answer["table"], skill["id"]
        page.get_by_text(answer["answer"], exact=True).wait_for()
        if skill["id"] == "merchant-score" and answer["table"]:
            board = page.get_by_role("region", name="Merchant leaderboard", exact=True)
            records = answer["table"]
            assert board.locator("tbody tr").count() == min(15, len(records))
            assert board.locator("th").count() == 7
            board.get_by_label("Show all columns").check()
            assert board.locator("th").count() == len(records[0])
            if len(records) > 15:
                board.get_by_role("button", name="Next page").click()
                board.get_by_text(records[15]["seller_id"], exact=True).wait_for()
                board.get_by_role("button", name="Last page").click()
                board.get_by_text(records[-1]["seller_id"], exact=True).wait_for()
                assert board.get_by_role("button", name="Last page").is_disabled()
                board.get_by_role("button", name="First page").click()
                board.get_by_text(records[0]["seller_id"], exact=True).wait_for()
            with page.expect_download() as exported:
                page.get_by_role("button", name="Export result").click()
            assert json.loads(Path(exported.value.path()).read_text()) == answer
        if skill["id"] == "product-trend" and answer["table"]:
            outlook = page.get_by_role("region", name="Product sales outlook", exact=True)
            if len(answer["table"]) > 1:
                outlook.get_by_label("Product", exact=True).select_option("1")
            outlook.get_by_role("img", name="Units trend.", exact=False).focus()
            page.keyboard.press("ArrowRight")
            outlook.get_by_text("View product data", exact=True).click()
            assert outlook.locator("tbody tr").count() == len(answer["table"])
    page.get_by_role("button", name="Back to custom question", exact=False).click()
    assert page.get_by_label("Business question").input_value() == top_categories
    nav.get_by_role("link", name="Run history", exact=True).click()
    page.get_by_role("button", name=skills[-1]["question"], exact=False).first.click()
    page.get_by_text("Query evidence and SQL", exact=True).wait_for()

    for legacy, target in (("investigation", "delivery"), ("data", "data")):
        page.goto(f"{base}/#{legacy}", wait_until="networkidle")
        page.wait_for_url(f"**/#ask/{target}")
        page.get_by_role("heading", name="Ask the agent", level=1).wait_for()
    for width in (390, 768, 1440):
        page.set_viewport_size({"width": width, "height": 900})
        for route in ("overview", "ask", "ask/delivery", "ask/data", "evaluation", "history"):
            page.goto(f"{base}/#{route}", wait_until="networkidle")
            page.locator("main h1").wait_for()
            assert page.evaluate(
                "document.documentElement.scrollWidth <= window.innerWidth"
            ), (route, width)
    page.set_viewport_size({"width": 390, "height": 844})
    page.goto(f"{base}/#ask", wait_until="networkidle")
    page.get_by_label("Choose an analysis skill").select_option("merchant-score")
    with page.expect_response("**/api/query") as mobile:
        page.get_by_role("button", name="Run skill", exact=True).click()
    assert mobile.value.request.post_data_json["skill_id"] == "merchant-score"
    page.get_by_role("region", name="Analysis result", exact=True).wait_for()
    assert page.evaluate("document.documentElement.scrollWidth <= window.innerWidth")
    assert not errors, errors
    print("Passed four navigation destinations, nine skills, mobile input, delivery tests, "
          "data reference, legacy links, SQL copy, export, history and three screen widths.")
    browser.close()
