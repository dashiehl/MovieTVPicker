from PySide6.QtWidgets import QApplication, QWidget


def refresh_style(widget: QWidget) -> None:
    """Call after changing a dynamic property (e.g. 'active') so QSS re-evaluates it."""
    widget.style().unpolish(widget)
    widget.style().polish(widget)


def build_stylesheet(tokens: dict) -> str:
    return f"""
    QMainWindow, QWidget {{
        background: {tokens['bg']};
        color: {tokens['text']};
        font-family: 'Segoe UI', sans-serif;
        font-size: 13px;
    }}

    QLabel[role="muted"] {{
        color: {tokens['text_muted']};
    }}

    QLabel[role="empty-state"] {{
        color: {tokens['text_muted']};
        padding: 48px 16px;
        font-size: 14px;
    }}

    QLabel[role="h1"] {{
        font-size: 18px;
        font-weight: 600;
    }}

    QLabel[role="h2"] {{
        font-size: 15px;
        font-weight: 600;
    }}

    /* --- Nav bar --- */
    #navBar {{
        background: {tokens['bg']};
        border-bottom: 1px solid {tokens['border']};
    }}

    QPushButton[class="nav-link"] {{
        background: transparent;
        border: none;
        border-radius: 8px;
        padding: 8px 14px;
        color: {tokens['text_muted']};
        font-weight: 500;
    }}
    QPushButton[class="nav-link"]:hover {{
        background: {tokens['surface_alt']};
    }}
    QPushButton[class="nav-link"][active="true"] {{
        background: {tokens['surface_alt']};
        color: {tokens['text']};
    }}

    QPushButton[class="mode-toggle"] {{
        background: {tokens['surface_alt']};
        border: none;
        border-radius: 999px;
        padding: 6px 16px;
        color: {tokens['text_muted']};
        font-weight: 600;
    }}
    QPushButton[class="mode-toggle"][active="true"] {{
        background: {tokens['accent']};
        color: {tokens['accent_text']};
    }}

    /* --- Home page --- */
    QLabel[role="home-title"] {{
        font-size: 22px;
        font-weight: 700;
    }}
    QLabel[role="home-subtitle"] {{
        color: {tokens['text_muted']};
        font-size: 13px;
    }}
    QPushButton[class="choice-card"] {{
        background: {tokens['surface']};
        border: 1px solid {tokens['border']};
        border-radius: 12px;
        padding: 18px;
        color: {tokens['text']};
        font-size: 15px;
        font-weight: 600;
        text-align: left;
    }}
    QPushButton[class="choice-card"]:hover {{
        background: {tokens['surface_alt']};
    }}
    QPushButton[class="choice-card"][active="true"] {{
        background: {tokens['accent']};
        border-color: {tokens['accent']};
        color: {tokens['accent_text']};
    }}

    /* --- Sub-nav (discover mode switcher) --- */
    QPushButton[class="sub-nav"] {{
        background: {tokens['surface']};
        border: 1px solid {tokens['border']};
        border-radius: 8px;
        padding: 8px 16px;
        color: {tokens['text']};
    }}
    QPushButton[class="sub-nav"][active="true"] {{
        background: {tokens['accent']};
        border-color: {tokens['accent']};
        color: {tokens['accent_text']};
    }}

    /* --- Buttons --- */
    QPushButton[class="btn"] {{
        background: {tokens['accent']};
        color: {tokens['accent_text']};
        border: none;
        border-radius: 8px;
        padding: 8px 16px;
        font-weight: 600;
    }}
    QPushButton[class="btn"]:disabled {{
        background: {tokens['surface_alt']};
        color: {tokens['text_muted']};
    }}
    QPushButton[class="btn-secondary"] {{
        background: {tokens['surface_alt']};
        color: {tokens['text']};
        border: none;
        border-radius: 8px;
        padding: 8px 16px;
        font-weight: 600;
    }}
    QPushButton[class="card-action"] {{
        background: {tokens['surface_alt']};
        border: 1px solid {tokens['border']};
        border-radius: 6px;
        padding: 6px 8px;
        color: {tokens['text']};
        font-size: 12px;
    }}
    QPushButton[class="card-action"]:disabled {{
        color: {tokens['text_muted']};
    }}

    /* --- Cards --- */
    QFrame[class="card"] {{
        background: {tokens['surface']};
        border: 1px solid {tokens['border']};
        border-radius: 10px;
    }}
    QFrame[class="card"][status="none"] {{
        border-left: 3px solid {tokens['status_none']};
    }}
    QFrame[class="card"][status="watchlist"] {{
        border-left: 3px solid {tokens['status_watchlist']};
    }}
    QFrame[class="card"][status="watched"] {{
        border-left: 3px solid {tokens['status_watched']};
    }}

    /* --- Banners --- */
    QFrame[class="banner-warning"] {{
        background: {tokens['warning_bg']};
        border: 1px solid {tokens['warning_border']};
        border-radius: 8px;
    }}
    QFrame[class="banner-warning"] QLabel {{
        color: {tokens['warning_text']};
    }}
    QFrame[class="banner-error"] {{
        background: {tokens['error_bg']};
        border: 1px solid {tokens['error_border']};
        border-radius: 8px;
    }}
    QFrame[class="banner-error"] QLabel {{
        color: {tokens['error_text']};
    }}

    /* --- Inputs --- */
    QLineEdit, QComboBox, QSpinBox {{
        background: {tokens['surface']};
        border: 1px solid {tokens['border']};
        border-radius: 8px;
        padding: 6px 10px;
        color: {tokens['text']};
    }}

    QScrollArea {{
        border: none;
        background: transparent;
    }}
    QScrollArea > QWidget > QWidget {{
        background: transparent;
    }}
    """


def apply_theme(app: QApplication, tokens: dict) -> None:
    app.setStyleSheet(build_stylesheet(tokens))
