def catalog_key(item: dict) -> str:
    """Uniquely identifies a catalog item or a watchlist/watched/swipe record
    that references one. Records store the reference as 'catalogId'; raw
    catalog items use 'id' directly."""
    return f"{item['mediaType']}:{item.get('catalogId', item.get('id'))}"
