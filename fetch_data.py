#!/usr/bin/env python3
"""
Fetches Lucky 10 Ball results from auluckylottery.com
and saves to data/results.json
"""

import json
import re
import sys
import os
from datetime import datetime, timezone
from pathlib import Path

try:
    import requests
    from bs4 import BeautifulSoup
except ImportError:
    os.system("pip install requests beautifulsoup4 -q")
    import requests
    from bs4 import BeautifulSoup

DATA_FILE = Path(__file__).parent / "data" / "results.json"
URL = "https://www.auluckylottery.com/results/lucky-ball-10/"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
    "Referer": "https://www.auluckylottery.com/",
    "Connection": "keep-alive",
}


def load_existing():
    if DATA_FILE.exists():
        try:
            return json.loads(DATA_FILE.read_text())
        except Exception:
            pass
    return {"updated": "", "draws": []}


def fetch_draws():
    resp = requests.get(URL, headers=HEADERS, timeout=20)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")

    draws = []

    # Find all result blocks — each draw has a time + 10 number balls
    # The site renders them inside specific containers; try multiple selectors
    result_blocks = soup.select(".draw-result, .result-row, [class*='draw'], [class*='result']")

    if not result_blocks:
        # Fallback: find all groups of exactly 10 numbers in sequence
        all_text = soup.get_text(separator="\n")
        # Look for patterns like "Draw: 21210241" followed by 10 numbers
        pattern = re.findall(
            r"Draw[:\s]+(\d+).*?(\d{2}/\d{2}/\d{4}|\w+,\s+\w+\s+\d+,\s+\d+).*?(\d{2}:\d{2})\s*[ap]m.*?([1-9]|10)[\s·]+([1-9]|10)[\s·]+([1-9]|10)[\s·]+([1-9]|10)[\s·]+([1-9]|10)[\s·]+([1-9]|10)[\s·]+([1-9]|10)[\s·]+([1-9]|10)[\s·]+([1-9]|10)[\s·]+([1-9]|10)",
            all_text,
            re.IGNORECASE | re.DOTALL
        )
        for m in pattern[:30]:
            draw_id = m[0][-4:]  # last 4 digits
            time_str = m[2]
            nums = [int(x) for x in m[3:13]]
            if len(set(nums)) == 10 and all(1 <= n <= 10 for n in nums):
                draws.append({
                    "draw": draw_id,
                    "time": time_str,
                    "numbers": nums
                })

    # Alternative: parse raw page text for number sequences
    if not draws:
        text = resp.text
        # Find draw numbers and ball sequences
        draw_matches = re.findall(
            r"Draw[:\s]*(\d{7,9}).*?(\d{1,2}:\d{2})\s*(?:am|pm).*?"
            r"(?<!\d)([1-9]|10)[\s·,]+([1-9]|10)[\s·,]+"
            r"([1-9]|10)[\s·,]+([1-9]|10)[\s·,]+"
            r"([1-9]|10)[\s·,]+([1-9]|10)[\s·,]+"
            r"([1-9]|10)[\s·,]+([1-9]|10)[\s·,]+"
            r"([1-9]|10)[\s·,]+([1-9]|10)(?!\d)",
            text,
            re.IGNORECASE | re.DOTALL
        )
        for m in draw_matches[:30]:
            draw_id = str(int(m[0]) % 10000)  # short ID
            time_str = m[1]
            nums = [int(x) for x in m[2:12]]
            if len(set(nums)) == 10 and all(1 <= n <= 10 for n in nums):
                draws.append({
                    "draw": draw_id,
                    "time": time_str,
                    "numbers": nums
                })

    # Deduplicate by draw ID
    seen = set()
    unique = []
    for d in draws:
        if d["draw"] not in seen:
            seen.add(d["draw"])
            unique.append(d)

    return unique[:30]  # keep newest 30


def merge(existing, new_draws):
    """Merge new draws into existing, deduplicate, keep newest 40."""
    combined = {d["draw"]: d for d in existing.get("draws", [])}
    for d in new_draws:
        combined[d["draw"]] = d
    # Sort by draw number descending
    sorted_draws = sorted(combined.values(), key=lambda x: int(x["draw"]) if x["draw"].isdigit() else 0, reverse=True)
    return sorted_draws[:40]


def main():
    existing = load_existing()
    print(f"Existing draws: {len(existing.get('draws', []))}")

    try:
        new_draws = fetch_draws()
        print(f"Fetched {len(new_draws)} draws from site")
    except Exception as e:
        print(f"Fetch failed: {e}", file=sys.stderr)
        # Keep existing data, just update timestamp
        new_draws = []

    merged = merge(existing, new_draws)
    print(f"Total after merge: {len(merged)}")

    DATA_FILE.parent.mkdir(exist_ok=True)
    result = {
        "updated": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "source": "auluckylottery.com",
        "draws": merged
    }
    DATA_FILE.write_text(json.dumps(result, ensure_ascii=False, indent=2))
    print(f"Saved to {DATA_FILE}")

    if not merged:
        sys.exit(1)


if __name__ == "__main__":
    main()
