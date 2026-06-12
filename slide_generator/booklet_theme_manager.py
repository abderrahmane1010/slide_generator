import yaml


BOOKLET_DEFAULTS = {
    "primary_color":          "#1A1A2E",
    "secondary_color":        "#FAFAF8",
    "accent_color":           "#F2EDE4",
    "chapter_color":          "#8B0000",
    "code_bg_color":          "#1E1E2E",
    "code_text_color":        "#CDD6F4",
    "inline_code_bg":         "#EAEAEA",
    "caption_color":          "#777777",
    "link_color":             "#8B0000",
    "border_color":           "#C9B99A",
    "font":                   "Libre Baskerville",
    "code_font":              "'Fira Code', 'Consolas', 'Courier New', monospace",
    "font_size_h1":           "26pt",
    "font_size_h2":           "17pt",
    "font_size_h3":           "13pt",
    "font_size_body":         "11pt",
    "font_size_list":         "11pt",
    "font_size_code":          "9pt",
    "font_size_caption":       "9pt",
    "font_size_page_number":   "9pt",
    "font_size_blockquote":   "11pt",
    "font_size_table":        "10pt",
    "line_height_body":  1.55,
    "line_height_list":  1.55,
    "page_width":             "210mm",
    "page_height":            "297mm",
    "page_margin_top":         "20mm",
    "page_margin_bottom":      "22mm",
    "page_margin_left":        "25mm",
    "page_margin_right":       "20mm",
    "page_numbering":          True,
    "toc":                     True,
    "blockquote_border_width": "4px",
    "image_max_width":         "90%",
    "image_max_height":        "100mm",
    "pdf_engine":              "weasyprint",
}


class BookletThemeManager:
    """Theme manager for academic booklets.

    Reads ``booklet_theme`` from the given YAML file and merges it with
    :data:`BOOKLET_DEFAULTS`.
    """

    def __init__(self, config_path: str = "booklet_config.yaml"):
        try:
            with open(config_path, "r", encoding="utf-8") as fh:
                raw = yaml.safe_load(fh) or {}
        except FileNotFoundError:
            raw = {}
        user_theme = raw.get("booklet_theme", {})
        self._theme: dict = {**BOOKLET_DEFAULTS, **user_theme}

    def get_theme(self) -> dict:
        return self._theme

    def get(self, key: str, fallback=None):
        return self._theme.get(key, fallback)

    def is_page_numbering_enabled(self) -> bool:
        return bool(self._theme.get("page_numbering", True))

    def is_toc_enabled(self) -> bool:
        return bool(self._theme.get("toc", True))
