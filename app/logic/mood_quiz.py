import random

TONE_GENRES = {
    "Light & fun": ["Comedy", "Family", "Animation", "Musical"],
    "Intense": ["Thriller", "Horror", "Action", "Crime"],
    "Thought-provoking": ["Drama", "Mystery", "Sci-Fi", "Biography"],
}

FAMILIARITY_OPTIONS = ["An older classic", "Something recent"]


def resolve_quiz(catalog_items: list[dict], answers: dict) -> dict | None:
    """answers: {mediaType, genre, tone, familiarity} -> a single matching item, or None."""
    base = [
        item for item in catalog_items
        if item["mediaType"] == answers["mediaType"] and answers["genre"] in item["genres"]
    ]
    tone_genres = TONE_GENRES[answers["tone"]]
    tone_filtered = [item for item in base if any(g in tone_genres for g in item["genres"])]
    pool = tone_filtered or base

    sorted_pool = sorted(pool, key=lambda item: item["year"])
    midpoint = -(-len(sorted_pool) // 2)  # ceil division
    half = sorted_pool[:midpoint] if answers["familiarity"] == "An older classic" else sorted_pool[midpoint:]
    candidates = half or sorted_pool

    return random.choice(candidates) if candidates else None
