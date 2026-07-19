"""JSON-backed storage for watchlist/watched/swipes/profiles.

Port of the old server/db.js + routes/*.js — same schema, same semantics,
just called directly in-process instead of over HTTP.
"""

import json
import uuid
from datetime import datetime, timezone

from app.config import DB_PATH

EMPTY_DB = {"watchlist": [], "watched": [], "swipes": [], "profiles": []}


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def read_db() -> dict:
    if not DB_PATH.exists():
        return {**EMPTY_DB}
    with open(DB_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)
    return {**EMPTY_DB, **data}


def write_db(db: dict) -> None:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(DB_PATH, "w", encoding="utf-8") as f:
        json.dump(db, f, indent=2)


def get_watchlist() -> list:
    return read_db()["watchlist"]


def get_watched() -> list:
    return read_db()["watched"]


def get_swipes(profile: str | None = None) -> list:
    swipes = read_db()["swipes"]
    if profile:
        return [s for s in swipes if s["profile"] == profile]
    return swipes


def get_profiles() -> list:
    return read_db()["profiles"]


def add_to_watchlist(item: dict) -> dict:
    db = read_db()
    existing = next(
        (i for i in db["watchlist"] if i["catalogId"] == item["catalogId"] and i["mediaType"] == item["mediaType"]),
        None,
    )
    if existing:
        return existing
    created = {
        "id": str(uuid.uuid4()),
        "catalogId": item["catalogId"],
        "mediaType": item["mediaType"],
        "title": item["title"],
        "posterPath": item.get("posterPath"),
        "year": item.get("year"),
        "genres": item.get("genres", []),
        "addedAt": _now(),
    }
    db["watchlist"].append(created)
    write_db(db)
    return created


def remove_from_watchlist(record_id: str) -> bool:
    db = read_db()
    before = len(db["watchlist"])
    db["watchlist"] = [i for i in db["watchlist"] if i["id"] != record_id]
    removed = len(db["watchlist"]) < before
    if removed:
        write_db(db)
    return removed


def mark_watched(item: dict) -> dict:
    db = read_db()
    existing = next(
        (i for i in db["watched"] if i["catalogId"] == item["catalogId"] and i["mediaType"] == item["mediaType"]),
        None,
    )
    if existing:
        return existing
    created = {
        "id": str(uuid.uuid4()),
        "catalogId": item["catalogId"],
        "mediaType": item["mediaType"],
        "title": item["title"],
        "posterPath": item.get("posterPath"),
        "year": item.get("year"),
        "genres": item.get("genres", []),
        "watchedAt": _now(),
    }
    db["watched"].append(created)
    # Marking something watched also removes it from the watchlist, since it's done.
    db["watchlist"] = [
        i for i in db["watchlist"]
        if not (i["catalogId"] == created["catalogId"] and i["mediaType"] == created["mediaType"])
    ]
    write_db(db)
    return created


def remove_from_watched(record_id: str) -> bool:
    db = read_db()
    before = len(db["watched"])
    db["watched"] = [i for i in db["watched"] if i["id"] != record_id]
    removed = len(db["watched"]) < before
    if removed:
        write_db(db)
    return removed


def record_swipe(catalog_id: str, media_type: str, profile: str, liked: bool) -> dict:
    db = read_db()
    db["swipes"] = [
        s for s in db["swipes"]
        if not (s["catalogId"] == catalog_id and s["mediaType"] == media_type and s["profile"] == profile)
    ]
    created = {"catalogId": catalog_id, "mediaType": media_type, "profile": profile, "liked": liked, "swipedAt": _now()}
    db["swipes"].append(created)
    write_db(db)
    return created


def clear_swipes(profile: str) -> None:
    db = read_db()
    db["swipes"] = [s for s in db["swipes"] if s["profile"] != profile]
    write_db(db)


def create_profile(name: str) -> dict:
    name = name.strip()
    db = read_db()
    existing = next((p for p in db["profiles"] if p["name"].lower() == name.lower()), None)
    if existing:
        return existing
    created = {"id": str(uuid.uuid4()), "name": name}
    db["profiles"].append(created)
    write_db(db)
    return created
