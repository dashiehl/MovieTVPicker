from app.utils import catalog_key

SORTS = {
    "Newest": lambda item: -item["year"],
    "Oldest": lambda item: item["year"],
    "Title A–Z": lambda item: item["title"].lower(),
}


def filter_catalog(
    items: list[dict],
    query: str = "",
    media_type: str = "all",
    genre: str = "",
    year_from: int | None = None,
    year_to: int | None = None,
    exclude_keys: set[str] | None = None,
    sort: str = "Newest",
) -> list[dict]:
    exclude_keys = exclude_keys or set()
    result = items
    if query:
        q = query.strip().lower()
        result = [i for i in result if q in i["title"].lower()]
    if media_type != "all":
        result = [i for i in result if i["mediaType"] == media_type]
    if genre:
        result = [i for i in result if genre in i["genres"]]
    if year_from is not None:
        result = [i for i in result if i["year"] >= year_from]
    if year_to is not None:
        result = [i for i in result if i["year"] <= year_to]
    result = [i for i in result if catalog_key(i) not in exclude_keys]
    return sorted(result, key=SORTS.get(sort, SORTS["Newest"]))
