"""Builds data/catalog.json from scripts/catalog_seed.json by pulling a poster
image and short blurb per title from Wikipedia's free, keyless REST API.

Python port of the original build-catalog.mjs — same resolution strategy
(candidate titles, disambiguation check, opensearch fallback), and the same
concurrency=1 / retry / multi-sweep approach, which turned out to be
necessary because this kind of bulk outbound HTTPS is flaky on some
networks even sequentially.

Runnable standalone: `python scripts/build_catalog.py`
Also used by the Settings page's background rebuild worker, which passes
its own progress_callback to stream log lines into the UI.
"""

import json
import sys
import time
import urllib.parse
from pathlib import Path
from typing import Callable, Optional

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import requests

from app.config import CATALOG_PATH, CATALOG_SEED_PATH

USER_AGENT = "WatchPickerBot/0.1 (personal local app; no contact - non-commercial hobby project)"
FETCH_TIMEOUT_S = 15
RETRIES = 2
SWEEPS = 3

SUMMARY_URL = "https://en.wikipedia.org/api/rest_v1/page/summary/{}"
OPENSEARCH_URL = "https://en.wikipedia.org/w/api.php"


def _fetch_json_once(url: str, params: Optional[dict] = None) -> Optional[dict]:
    try:
        res = requests.get(url, params=params, headers={"User-Agent": USER_AGENT}, timeout=FETCH_TIMEOUT_S)
        if not res.ok:
            return None
        return res.json()
    except (requests.RequestException, ValueError):
        return None


def _fetch_json(url: str, params: Optional[dict] = None) -> Optional[dict]:
    for attempt in range(RETRIES + 1):
        result = _fetch_json_once(url, params)
        if result:
            return result
        if attempt < RETRIES:
            time.sleep(0.3 * (attempt + 1))
    return None


def _summary_url(title: str) -> str:
    return SUMMARY_URL.format(urllib.parse.quote(title.replace(" ", "_")))


def _resolve_via_opensearch(query: str) -> Optional[str]:
    params = {"action": "opensearch", "search": query, "limit": 1, "namespace": 0, "format": "json"}
    data = _fetch_json(OPENSEARCH_URL, params)
    if data and len(data) > 1 and data[1]:
        return data[1][0]
    return None


def _candidate_titles(entry: dict) -> list[str]:
    title, year, media_type = entry["title"], entry["year"], entry["mediaType"]
    if media_type == "tv":
        return [f"{title} (TV series)", f"{title} ({year} TV series)", title]
    return [f"{title} (film)", f"{title} ({year} film)", title]


def _resolve_summary(entry: dict) -> Optional[dict]:
    for candidate in _candidate_titles(entry):
        summary = _fetch_json(_summary_url(candidate))
        if summary and summary.get("type") != "disambiguation":
            return summary
    query = (
        f"{entry['title']} TV series {entry['year']}"
        if entry["mediaType"] == "tv"
        else f"{entry['title']} {entry['year']} film"
    )
    resolved_title = _resolve_via_opensearch(query)
    if resolved_title:
        summary = _fetch_json(_summary_url(resolved_title))
        if summary and summary.get("type") != "disambiguation":
            return summary
    return None


def _to_item(entry: dict, summary: Optional[dict]) -> dict:
    thumbnail = (summary or {}).get("thumbnail") or {}
    return {
        "id": entry["id"],
        "mediaType": entry["mediaType"],
        "title": entry["title"],
        "year": entry["year"],
        "genres": entry["genres"],
        "posterPath": thumbnail.get("source"),
        "overview": (summary or {}).get("extract", ""),
    }


def _resolve_batch(entries: list[dict], label: str, progress: Callable[[str], None]) -> list[dict]:
    results = []
    for i, entry in enumerate(entries, start=1):
        summary = _resolve_summary(entry)
        results.append(_to_item(entry, summary))
        if i % 25 == 0 or i == len(entries):
            progress(f"  [{label}] {i}/{len(entries)}")
    return results


def _load_existing_catalog() -> dict[str, dict]:
    if not CATALOG_PATH.exists():
        return {}
    try:
        with open(CATALOG_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
        return {item["id"]: item for item in data.get("items", [])}
    except (json.JSONDecodeError, OSError):
        return {}


def build_catalog(progress_callback: Optional[Callable[[str], None]] = None) -> dict:
    """Runs the full build and returns the resulting catalog dict.

    progress_callback receives one log line at a time — defaults to print().
    """
    progress = progress_callback or print

    with open(CATALOG_SEED_PATH, "r", encoding="utf-8") as f:
        seed = json.load(f)
    existing = _load_existing_catalog()

    cached, to_fetch = [], []
    for entry in seed:
        prior = existing.get(entry["id"])
        if prior and prior.get("posterPath"):
            cached.append({**prior, "title": entry["title"], "year": entry["year"],
                           "genres": entry["genres"], "mediaType": entry["mediaType"]})
        else:
            to_fetch.append(entry)

    progress(f"{len(cached)} already cached with posters, {len(to_fetch)} to resolve...")

    resolved = _resolve_batch(to_fetch, "initial", progress) if to_fetch else []

    for sweep in range(1, SWEEPS + 1):
        seed_by_id = {e["id"]: e for e in seed}
        missing_entries = [seed_by_id[item["id"]] for item in resolved if not item["posterPath"]]
        if not missing_entries:
            break
        progress(f"Sweep {sweep}: retrying {len(missing_entries)} misses...")
        retried = _resolve_batch(missing_entries, f"sweep {sweep}", progress)
        retried_by_id = {item["id"]: item for item in retried}
        resolved = [retried_by_id.get(item["id"], item) for item in resolved]

    order = {e["id"]: i for i, e in enumerate(seed)}
    items = sorted(cached + resolved, key=lambda item: order[item["id"]])

    from datetime import datetime, timezone
    catalog = {"updatedAt": datetime.now(timezone.utc).isoformat(), "items": items}

    CATALOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(CATALOG_PATH, "w", encoding="utf-8") as f:
        json.dump(catalog, f, indent=2)

    misses = [i for i in items if not i["posterPath"]]
    progress(f"\nWrote {len(items)} items to {CATALOG_PATH}")
    progress(f"Posters found: {len(items) - len(misses)}/{len(items)}")
    if misses:
        progress(f"\nNo Wikipedia match found for {len(misses)} titles (re-run this command to retry):")
        for m in misses:
            progress(f"  - {m['title']} ({m['year']})")

    return catalog


if __name__ == "__main__":
    build_catalog()
