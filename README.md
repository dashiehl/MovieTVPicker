# Watch Picker

A local desktop app for deciding what to watch. Swipe, take a mood quiz,
browse with filters, or hit "surprise me" — solo or with a group — then
track a watchlist and watched history. Built with PySide6 (Qt for Python)
and runs entirely on your machine: no account, no cloud service, no API key.

Movie/TV data comes from a curated local catalog (~450 well-known movies
and TV shows spanning the 1930s through the present), bundled with the
app — see "Updating the catalog" below.

## 1. Install & run

From the project root:

```bash
python -m venv .venv
.venv\Scripts\activate      # Windows
pip install -r requirements.txt
python main.py
```

## Data storage

Your watchlist, watched history, and swipe preferences are stored locally
in `data/db.json`. Poster images are cached in `data/image_cache/` after
first load so the app stays fast (and mostly usable offline) after that.
Nothing leaves your machine.

## Updating the catalog

Because there's no live API, every discovery mode pulls from a fixed
local catalog at `data/catalog.json`. The app shows a reminder under the
nav bar once that file gets old (180+ days), and Settings has a
"Rebuild catalog now" button that does the same thing without leaving
the app.

To refresh it from a terminal instead:

```bash
python scripts/build_catalog.py
```

This reads the source list at `scripts/catalog_seed.json` (just
`id`/`mediaType`/`title`/`year`/`genres` per entry) and, for each title,
looks up its Wikipedia page to pull a poster image and short blurb — no
API key needed. To add or remove titles, edit `catalog_seed.json` and
re-run the command. It's incremental (only re-fetches titles missing a
poster), but a first build or a big addition can take several minutes
since it's one request per title.

Poster images are pulled from Wikipedia at build time (not committed as
binaries) — reasonable for a personal, non-commercial local app, but
worth knowing if you ever plan to distribute it further.

## Building a standalone executable

```bash
pip install pyinstaller
pyinstaller packaging/app.spec
```

The built app lands in `dist/WatchPicker/` — a folder you can copy
anywhere, containing `WatchPicker.exe` alongside its own `data/` folder
(so it keeps reading/writing `catalog.json`/`db.json` right next to
itself, same as running from source).

## Project layout

- `main.py` — entry point (creates the QApplication, applies the theme, shows the main window).
- `app/` — the application: `config.py` (paths + color tokens), `theme.py`
  (QSS builder), `db.py`/`catalog_store.py`/`library_store.py`/`state.py`
  (data layer), `image_loader.py` (async poster loading + cache),
  `logic/` (pure filtering/matching functions), `widgets/` (shared UI
  pieces), `pages/` (the actual screens).
- `scripts/` — `catalog_seed.json` (the editable source list) and
  `build_catalog.py` (what `python scripts/build_catalog.py` and the
  Settings page's "Rebuild catalog" button both run).
- `data/` — `catalog.json` (bundled, committed) and `db.json` (your
  personal data, gitignored).
- `packaging/app.spec` — PyInstaller build spec.
