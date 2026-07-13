import random

from app.utils import catalog_key


def pick_swipe_batch(catalog_items: list[dict], exclude_keys: set[str], size: int = 15) -> list[dict]:
    """Random batch from the catalog, excluding anything already swiped/watched."""
    eligible = [item for item in catalog_items if catalog_key(item) not in exclude_keys]
    random.shuffle(eligible)
    return eligible[:size]
