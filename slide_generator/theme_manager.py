import yaml


DEFAULTS = {
    "primary_color": "#004D25",
    "secondary_color": "#FAFCFB",
    "accent_color": "#E8F5E9",
    "header_bg": "#006400",
    "header_text": "#FFFFFF",
    "code_bg_color": "#1B2631",
    "code_text_color": "#E8F8F5",
    "inline_code_bg": "#D5F5E3",
    "caption_color": "#666666",
    "link_color": "#1B8A4E",
    "border_color": "#C8E6C9",
    "font": "Roboto",
    "code_font": "'Fira Code', 'Consolas', 'Courier New', monospace",
    "font_size_h1": "38pt",
    "font_size_h2": "30pt",
    "font_size_h3": "24pt",
    "font_size_body": "20pt",
    "font_size_list": "18pt",
    "font_size_code": "14pt",
    "font_size_caption": "14pt",
    "font_size_slide_number": "13pt",
    "font_size_blockquote": "18pt",
    "font_size_table": "16pt",
    "line_height_body": 1.7,
    "line_height_list": 1.9,
    "slide_width": "297mm",
    "slide_height": "210mm",
    "slide_padding": "25mm 35mm 30mm 35mm",
    "slide_border_width": "0px",
    "h1_border_width": "0px",
    "blockquote_border_width": "5px",
    "image_max_width": "85%",
    "image_max_height": "140mm",
    "slide_numbering": True,
    "slide_number_opacity": 0.5,
    "pdf_engine": "wkhtmltopdf",
}


class ThemeManager:
    def __init__(self, config_path="config.yaml"):
        with open(config_path, "r") as f:
            raw = yaml.safe_load(f) or {}
        user_theme = raw.get("theme", {})
        self._theme = {**DEFAULTS, **user_theme}

    def get_theme(self):
        return self._theme

    def get(self, key, fallback=None):
        return self._theme.get(key, fallback)

    def is_slide_numbering_enabled(self):
        return self._theme.get("slide_numbering", True)
