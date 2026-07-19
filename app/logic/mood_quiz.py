import random

TONE_GENRES = {
    "Light & fun": ["Comedy", "Family", "Animation", "Musical"],
    "Intense": ["Thriller", "Horror", "Action", "Crime"],
    "Thought-provoking": ["Drama", "Mystery", "Sci-Fi", "Biography"],
}

FAMILIARITY_OPTIONS = ["An older classic", "Something recent"]


def resolve_quiz(catalog_items: list[dict], answers: dict, count: int = 1) -> list[dict]:
    """answers: {mediaType, genre, tone, familiarity}, each a list of one or more selected
    options -> up to `count` matching items (fewer if the catalog doesn't have that many)."""
    media_types = set(answers["mediaType"])
    selected_genres = set(answers["genre"])
    base = [
        item for item in catalog_items
        if item["mediaType"] in media_types and selected_genres & set(item["genres"])
    ]

    selected_tones = answers.get("tone") or list(TONE_GENRES.keys())
    tone_genres = {g for tone in selected_tones for g in TONE_GENRES[tone]}
    tone_filtered = [item for item in base if any(g in tone_genres for g in item["genres"])]
    pool = tone_filtered or base

    familiarities = set(answers.get("familiarity") or FAMILIARITY_OPTIONS)
    if familiarities >= set(FAMILIARITY_OPTIONS):
        candidates = pool
    else:
        sorted_pool = sorted(pool, key=lambda item: item["year"])
        midpoint = -(-len(sorted_pool) // 2)  # ceil division
        half = sorted_pool[:midpoint] if "An older classic" in familiarities else sorted_pool[midpoint:]
        candidates = half or sorted_pool

    if not candidates:
        return []
    return random.sample(candidates, min(count, len(candidates)))
