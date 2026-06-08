import os
import re
import tempfile

from .theme_manager import ThemeManager


class SlideGenerator:
    def __init__(self, theme_manager: ThemeManager):
        self.theme_manager = theme_manager
        self.theme = theme_manager.get_theme()

    def generate_pdf(self, parsed_slides: list[str], output_path="output.pdf"):
        html = self._build_html(parsed_slides)
        tmp_html = self._write_temp_html(html)
        try:
            engine = self.theme.get("pdf_engine", "pypandoc")
            self._convert_to_pdf(tmp_html, output_path, engine)
        finally:
            os.unlink(tmp_html)

    def _build_html(self, parsed_slides: list[str]) -> str:
        css = self._generate_css()
        numbering = self.theme_manager.is_slide_numbering_enabled()

        slides_html = []
        for idx, slide in enumerate(parsed_slides, start=1):
            number_tag = ""
            if numbering:
                number_tag = (
                    f'<div class="slide-number">{idx} / {len(parsed_slides)}</div>'
                )
            slides_html.append(
                f'<div class="slide">\n{slide}\n{number_tag}\n</div>'
            )

        body = "\n".join(slides_html)
        title = self._extract_title(parsed_slides)

        return f"""<!DOCTYPE html>
<html lang="fr">
<head>
<meta charset="utf-8"/>
<title>{title}</title>
<style>{css}</style>
</head>
<body>
{body}
</body>
</html>"""

    @staticmethod
    def _extract_title(parsed_slides: list[str]) -> str:
        for slide in parsed_slides:
            match = re.search(r"<h1>(.*?)</h1>", slide)
            if match:
                return re.sub(r"<[^>]+>", "", match.group(1))
        return "Slides"

    def _generate_css(self) -> str:
        t = self.theme
        header_bg = t.get("header_bg", t["primary_color"])
        header_text = t.get("header_text", t["secondary_color"])
        link_color = t.get("link_color", t["primary_color"])
        border_color = t.get("border_color", "#C8E6C9")

        return f"""
@import url('https://fonts.googleapis.com/css2?family={t["font"]}:wght@300;400;500;700&display=swap');
@import url('https://fonts.googleapis.com/css2?family=Fira+Code:wght@400;500&display=swap');

@page {{
    size: {t["slide_width"]} {t["slide_height"]};
    margin: 0;
}}

* {{
    margin: 0;
    padding: 0;
    box-sizing: border-box;
}}

body {{
    font-family: '{t["font"]}', 'Segoe UI', sans-serif;
    color: #333333;
    background: {t["secondary_color"]};
    font-weight: 400;
    -webkit-font-smoothing: antialiased;
}}

.slide {{
    width: {t["slide_width"]};
    height: {t["slide_height"]};
    padding: {t["slide_padding"]};
    position: relative;
    page-break-after: always;
    background: {t["secondary_color"]};
    overflow: hidden;
}}

.slide::before {{
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    height: 6px;
    background: linear-gradient(90deg, {header_bg}, #2E7D32, #66BB6A);
}}

.slide::after {{
    content: '';
    position: absolute;
    bottom: 0;
    left: 35mm;
    right: 35mm;
    height: 1px;
    background: {border_color};
}}

.slide:last-child {{
    page-break-after: avoid;
}}

h1 {{
    color: {header_bg};
    font-size: {t["font_size_h1"]};
    font-weight: 700;
    margin-bottom: 20px;
    padding-bottom: 12px;
    border-bottom: 3px solid {header_bg};
    letter-spacing: -0.5px;
}}

h2 {{
    color: {t["primary_color"]};
    font-size: {t["font_size_h2"]};
    font-weight: 500;
    margin-bottom: 16px;
}}

h3 {{
    color: {t["primary_color"]};
    font-size: {t["font_size_h3"]};
    font-weight: 500;
    margin-bottom: 12px;
}}

p {{
    font-size: {t["font_size_body"]};
    line-height: {t["line_height_body"]};
    margin-bottom: 14px;
    color: #333;
}}

ul, ol {{
    font-size: {t["font_size_list"]};
    line-height: {t["line_height_list"]};
    margin-left: 30px;
    margin-bottom: 14px;
    color: #444;
}}

li {{
    margin-bottom: 6px;
}}

li strong {{
    color: {t["primary_color"]};
}}

blockquote {{
    border-left: {t["blockquote_border_width"]} solid {header_bg};
    padding: 14px 22px;
    margin: 18px 0;
    font-style: italic;
    font-size: {t["font_size_blockquote"]};
    background: {t["accent_color"]};
    border-radius: 0 8px 8px 0;
    color: #555;
}}

pre {{
    background: {t["code_bg_color"]};
    color: {t["code_text_color"]};
    padding: 20px 24px;
    border-radius: 10px;
    font-size: {t["font_size_code"]};
    overflow-x: auto;
    margin: 16px 0;
    border-left: 4px solid {header_bg};
    box-shadow: 0 2px 8px rgba(0,0,0,0.15);
}}

code {{
    font-family: {t["code_font"]};
    font-size: {t["font_size_code"]};
}}

p > code {{
    background: {t["inline_code_bg"]};
    padding: 3px 8px;
    border-radius: 4px;
    color: {t["primary_color"]};
    font-weight: 500;
}}

table {{
    border-collapse: separate;
    border-spacing: 0;
    width: 100%;
    margin: 16px 0;
    font-size: {t["font_size_table"]};
    border-radius: 8px;
    overflow: hidden;
    box-shadow: 0 1px 4px rgba(0,0,0,0.08);
}}

th {{
    background: {header_bg};
    color: {header_text};
    padding: 12px 18px;
    text-align: left;
    font-weight: 500;
}}

td {{
    border-bottom: 1px solid {border_color};
    padding: 10px 18px;
    color: #444;
}}

tr:nth-child(even) {{
    background: {t["accent_color"]};
}}

tr:last-child td {{
    border-bottom: none;
}}

img {{
    max-width: {t["image_max_width"]};
    max-height: {t["image_max_height"]};
    display: block;
    margin: 16px auto;
    border-radius: 6px;
    box-shadow: 0 2px 10px rgba(0,0,0,0.1);
}}

a {{
    color: {link_color};
    text-decoration: none;
    border-bottom: 1px dotted {link_color};
}}

em {{
    font-size: {t["font_size_caption"]};
    color: {t["caption_color"]};
}}

strong {{
    color: {t["primary_color"]};
    font-weight: 700;
}}

.slide-number {{
    position: absolute;
    bottom: 10mm;
    right: 15mm;
    font-size: {t["font_size_slide_number"]};
    color: {t["primary_color"]};
    opacity: {t["slide_number_opacity"]};
    font-weight: 300;
}}
"""

    @staticmethod
    def _write_temp_html(html: str) -> str:
        fd, path = tempfile.mkstemp(suffix=".html")
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(html)
        return path

    @staticmethod
    def _convert_to_pdf(html_path: str, output_path: str, engine: str = "pypandoc"):
        converters = {
            "pypandoc": SlideGenerator._convert_pypandoc,
            "weasyprint": SlideGenerator._convert_weasyprint,
            "wkhtmltopdf": SlideGenerator._convert_wkhtmltopdf,
        }
        converter = converters.get(engine)
        if converter:
            try:
                converter(html_path, output_path)
                return
            except (ImportError, FileNotFoundError):
                pass

        for name, func in converters.items():
            if name == engine:
                continue
            try:
                func(html_path, output_path)
                return
            except (ImportError, FileNotFoundError):
                continue

        raise RuntimeError(
            "No PDF engine available. Install one of: pypandoc, weasyprint, wkhtmltopdf."
        )

    @staticmethod
    def _convert_wkhtmltopdf(html_path: str, output_path: str):
        import shutil
        import subprocess

        cmd = shutil.which("wkhtmltopdf")
        if cmd is None:
            raise FileNotFoundError("wkhtmltopdf not found in PATH")

        result = subprocess.run(
            [
                cmd,
                "--orientation", "Landscape",
                "--page-size", "A4",
                "--margin-top", "0",
                "--margin-bottom", "0",
                "--margin-left", "0",
                "--margin-right", "0",
                "--disable-smart-shrinking",
                "--enable-local-file-access",
                "--load-error-handling", "ignore",
                "--load-media-error-handling", "ignore",
                "--print-media-type",
                html_path,
                output_path,
            ],
            capture_output=True, text=True,
        )
        if result.returncode not in (0, 1):
            raise RuntimeError(f"wkhtmltopdf failed: {result.stderr}")

    @staticmethod
    def _convert_pypandoc(html_path: str, output_path: str):
        import shutil
        import subprocess

        wk = shutil.which("wkhtmltopdf")
        if wk is None:
            import pypandoc
            pypandoc.convert_file(
                html_path, "pdf", outputfile=output_path, format="html",
                extra_args=["--metadata", "title= "],
            )
            return

        result = subprocess.run(
            [
                wk,
                "--orientation", "Landscape",
                "--page-size", "A4",
                "--margin-top", "0",
                "--margin-bottom", "0",
                "--margin-left", "0",
                "--margin-right", "0",
                "--disable-smart-shrinking",
                "--enable-local-file-access",
                "--load-error-handling", "ignore",
                "--load-media-error-handling", "ignore",
                "--print-media-type",
                html_path,
                output_path,
            ],
            capture_output=True, text=True,
        )
        if result.returncode not in (0, 1):
            raise RuntimeError(f"wkhtmltopdf failed: {result.stderr}")

    @staticmethod
    def _convert_weasyprint(html_path: str, output_path: str):
        import weasyprint

        weasyprint.HTML(filename=html_path).write_pdf(output_path)
