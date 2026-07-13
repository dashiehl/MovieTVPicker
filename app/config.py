from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
CATALOG_PATH = DATA_DIR / "catalog.json"
DB_PATH = DATA_DIR / "db.json"
IMAGE_CACHE_DIR = DATA_DIR / "image_cache"
CATALOG_SEED_PATH = BASE_DIR / "scripts" / "catalog_seed.json"

SOLO_PROFILE = "Solo"

STALE_AFTER_DAYS = 180

# Semantic color tokens. No widget should hardcode a color — everything
# reads from these dicts so light/dark can swap at runtime.
LIGHT_TOKENS = {
    "bg": "#f5f5f7",
    "surface": "#ffffff",
    "surface_alt": "#ececed",
    "border": "#dcdce0",
    "text": "#1c1c22",
    "text_muted": "#63636c",
    "accent": "#6c5ce7",
    "accent_text": "#ffffff",
    "danger": "#d64545",
    "warning_bg": "#fbeee3",
    "warning_border": "#e0a26f",
    "warning_text": "#8a4a1f",
    "error_bg": "#fbe7e7",
    "error_border": "#dd8f8f",
    "error_text": "#8a2020",
    # left-accent-border by watch-status
    "status_none": "#c7c7cc",
    "status_watchlist": "#2fa4a1",
    "status_watched": "#3fa564",
}

DARK_TOKENS = {
    "bg": "#14151a",
    "surface": "#1b1c22",
    "surface_alt": "#23242c",
    "border": "#2a2b33",
    "text": "#f0f0f2",
    "text_muted": "#9394a0",
    "accent": "#6c5ce7",
    "accent_text": "#ffffff",
    "danger": "#ff6b6b",
    "warning_bg": "#33251f",
    "warning_border": "#7a4a2f",
    "warning_text": "#ffd0a8",
    "error_bg": "#331f1f",
    "error_border": "#7a2f2f",
    "error_text": "#ffb3b3",
    "status_none": "#3a3b45",
    "status_watchlist": "#3fc6c2",
    "status_watched": "#6cf590",
}
