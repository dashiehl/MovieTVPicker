def catalog_key(item: dict) -> str:
    """Uniquely identifies a catalog item or a watchlist/watched/swipe record
    that references one. Records store the reference as 'catalogId'; raw
    catalog items use 'id' directly."""
    return f"{item['mediaType']}:{item.get('catalogId', item.get('id'))}"


def display_text(text: str) -> str:
    """Escape '&' before putting arbitrary text (e.g. a movie title) on a QLabel/
    QPushButton — otherwise Qt treats a lone '&' as a mnemonic marker, silently
    dropping it and underlining the next letter (e.g. "Law & Order")."""
    return text.replace("&", "&&")
