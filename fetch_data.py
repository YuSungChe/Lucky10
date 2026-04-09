#!/usr/bin/env python3
"""
Fetches Lucky 10 Ball results using Playwright (headless browser).
Bypasses 403 blocks that affect plain HTTP requests.
"""

import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

DATA_FILE = Path(__file__).parent / "data" / "results.json"
URL = "https://www.auluckylottery.com/results/lucky-ball-10/"


def load_existing():
    if DATA_FILE.exists():
        try:
            return json.loads(DATA_FILE.read_text())
        except Exception:
            pass
    return {"updated": "", "source": "sample", "draws": []}


def parse_page_text(text):
    """
    Parse draw results from page text.
    Format found on site: Draw: 21210241 · 4 · 8 · 1 · 7 · 10 · 9 · 6 · 5 · 2 · 3
    """
    draws = []

    # Match full draw blocks: Draw ID followed by exactly 10 numbers (1-10)
    pattern = re.compile(
        r'Draw[:\s]+(\d{6,10})'       # Draw number
        r'(?:.*?)'                     # anything in between
        r'((?:(?:10|[1-9])[\s·,\-]+){9}(?:10|[1-9]))',  # 10 numbers
        re.DOTALL
    )

    for m in pattern.finditer(text):
        draw_full = m.group(1)
        nums_raw  = m.group(2)
        nums = [int(x) for x in re.findall(r'\b(10|[1-9])\b', nums_raw)]
        if len(nums) == 10 and len(set(nums)) == 10 and all(1 <= n <= 10 for n in nums):
            draws.append({
                "draw": draw_full[-4:],   # last 4 digits as short ID
                "draw_full": draw_full,
                "time": "",
                "numbers": nums
            })

    # Deduplicate by full draw number
    seen = set()
    unique = []
    for d in draws:
        key = d["draw_full"]
        if key not in seen:
            seen.add(key)
            unique.append(d)

    return unique[:30]


def fetch_with_playwright():
    from playwright.sync_api import sync_playwright

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        ctx = browser.new_context(
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/123.0.0.0 Safari/537.36"
            ),
            locale="en-AU",
            timezone_id="Australia/Adelaide",
        )
        page = ctx.new_page()
        page.goto(URL, wait_until="networkidle", timeout=30000)
        # Wait for result elements to appear
        try:
            page.wait_for_selector("text=Draw:", timeout=10000)
        except Exception:
            pass
        content = page.content()
        text    = page.inner_text("body")
        browser.close()
        return text, content


def merge(existing, new_draws):
    combined = {d.get("draw_full", d["draw"]): d for d in existing.get("draws", [])}
    for d in new_draws:
        key = d.get("draw_full", d["draw"])
        combined[key] = d
    sorted_draws = sorted(
        combined.values(),
        key=lambda x: int(x.get("draw_full", x["draw"])) if x.get("draw_full", x["draw"]).isdigit() else 0,
        reverse=True
    )
    return sorted_draws[:40]


def main():
    existing = load_existing()
    print(f"Existing draws: {len(existing.get('draws', []))}")

    new_draws = []
    try:
        print("Launching headless browser...")
        text, _ = fetch_with_playwright()
        print(f"Page text length: {len(text)}")
        new_draws = parse_page_text(text)
        print(f"Parsed {len(new_draws)} draws")
        if new_draws:
            print(f"Latest: Draw {new_draws[0].get('draw_full')} → {new_draws[0]['numbers']}")
    except Exception as e:
        print(f"Fetch failed: {e}", file=sys.stderr)

    merged = merge(existing, new_draws)
    print(f"Total after merge: {len(merged)}")

    DATA_FILE.parent.mkdir(exist_ok=True)
    result = {
        "updated": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "source": "auluckylottery.com" if new_draws else existing.get("source", "sample"),
        "draws": merged
    }
    DATA_FILE.write_text(json.dumps(result, ensure_ascii=False, indent=2))
    print(f"Saved {len(merged)} draws to {DATA_FILE}")

    if not merged:
        sys.exit(1)


if __name__ == "__main__":
    main()
