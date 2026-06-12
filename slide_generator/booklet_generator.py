import os
import re
import tempfile

from .booklet_theme_manager import BookletThemeManager


class BookletGenerator:
    """Generates a continuous-flow A4 portrait academic booklet from Markdown.

    Each ``# Heading`` (h1) triggers a page break (new chapter).
    Auto-generated TOC with dot leaders and page numbers (WeasyPrint required).
    Running header and page numbering via CSS paged media.
    """

    def __init__(self, theme_manager: BookletThemeManager):
        self.theme_manager = theme_manager
        self.theme = theme_manager.get_theme()

    def generate_pdf(self, markdown_text: str, output_path: str = "booklet.pdf"):
        """Convert *markdown_text* to a booklet PDF at *output_path*."""
        html = self._build_html(markdown_text)
        tmp_html = self._write_temp_html(html)
        try:
            engine = self.theme.get("pdf_engine", "weasyprint")
            self._convert_to_pdf(tmp_html, output_path, engine)
        finally:
            os.unlink(tmp_html)

    def _build_html(self, markdown_text: str) -> str:
        import markdown
        from markdown.extensions.toc import TocExtension

        md = markdown.Markdown(
            extensions=[
                "extra",
                "codehilite",
                "md_in_html",
                TocExtension(permalink=False, toc_depth=3),
            ]
        )
        content_html = md.convert(markdown_text)
        title = self._extract_title(content_html)
        css = self._generate_css(title)

        toc_html = ""
        if self.theme_manager.is_toc_enabled():
            toc_html = self._build_toc_html(getattr(md, "toc_tokens", []))

        return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8"/>
<title>{title}</title>
<style>{css}</style>
</head>
<body>
{toc_html}
<div class="booklet-body">
{content_html}
</div>
</body>
</html>"""

    @staticmethod
    def _extract_title(html: str) -> str:
        match = re.search(r"<h1[^>]*>(.*?)</h1>", html, re.DOTALL)
        if match:
            return re.sub(r"<[^>]+>", "", match.group(1)).strip()
        return "Booklet"

    def _build_toc_html(self, toc_tokens: list) -> str:
        """Build a <nav class="toc"> from python-markdown toc_tokens."""

        def render_items(tokens: list) -> str:
            if not tokens:
                return ""
            rows = []
            for tok in tokens:
                level_class = f"toc-h{tok['level']}"
                rows.append(
                    f'<li class="{level_class}">'
                    f'<a href="#{tok["id"]}">{tok["name"]}</a>'
                )
                children = render_items(tok.get("children", []))
                if children:
                    rows.append(f"<ul>{children}</ul>")
                rows.append("</li>")
            return "\n".join(rows)

        items_html = render_items(toc_tokens)
        if not items_html:
            return ""

        return (
            '<nav class="toc">\n'
            '<h2 class="toc-title">Table of Contents</h2>\n'
            f"<ul>\n{items_html}\n</ul>\n"
            "</nav>\n"
        )

    def _generate_css(self, title: str = "") -> str:  # noqa: C901
        t = self.theme
        pc = t["primary_color"]
        cc = t["chapter_color"]
        bc = t["border_color"]
        ac = t["accent_color"]

        return f"""
@import url('https://fonts.googleapis.com/css2?family=Libre+Baskerville:ital,wght@0,400;0,700;1,400&display=swap');
@import url('https://fonts.googleapis.com/css2?family=Fira+Code:wght@400;500&display=swap');

@page {{
    size: {t['page_width']} {t['page_height']};
    margin: {t['page_margin_top']} {t['page_margin_right']} {t['page_margin_bottom']} {t['page_margin_left']};

    @top-center {{
        content: "{title}";
        font-family: '{t['font']}', serif;
        font-size: 8pt;
        color: #AAAAAA;
        font-style: italic;
        border-bottom: 0.5pt solid {bc};
        padding-bottom: 4pt;
    }}

    @bottom-center {{
        content: counter(page);
        font-family: '{t['font']}', serif;
        font-size: {t['font_size_page_number']};
        color: #999999;
    }}
}}

/* First page (cover/TOC): no header, no page number */
@page :first {{
    @top-center    {{ content: none; }}
    @bottom-center {{ content: none; }}
}}

* {{
    margin: 0;
    padding: 0;
    box-sizing: border-box;
}}

body {{
    width: 100%;
    font-family: '{t['font']}', 'Georgia', 'Times New Roman', serif;
    color: #2C2C2C;
    background: {t['secondary_color']};
    font-size: {t['font_size_body']};
    line-height: {t['line_height_body']};
    -webkit-font-smoothing: antialiased;
    text-rendering: optimizeLegibility;
}}

nav.toc {{
    page-break-after: always;
    padding-top: 3mm;
    padding-bottom: 5mm;
}}

.toc-title {{
    font-family: '{t['font']}', serif;
    font-size: 20pt;
    font-weight: 700;
    color: {pc};
    margin-bottom: 10px;
    padding-bottom: 5px;
    border-bottom: 1.5pt solid {bc};
    letter-spacing: 0.4px;
}}

nav.toc ul {{
    list-style: none;
    padding: 0;
    margin: 0;
}}

nav.toc li {{
    padding: 0;
    margin: 0;
}}

nav.toc .toc-h1 {{
    margin-top: 11px;
    font-size: 11pt;
    font-weight: 700;
    color: {pc};
    line-height: 1.5;
}}

nav.toc .toc-h2 {{
    margin-top: 4px;
    margin-left: 18px;
    font-size: 10pt;
    font-weight: 400;
    color: #555555;
    line-height: 1.5;
}}

nav.toc .toc-h3 {{
    margin-top: 2px;
    margin-left: 34px;
    font-size: 9.5pt;
    font-weight: 400;
    color: #777777;
    font-style: italic;
    line-height: 1.4;
}}

nav.toc a {{
    color: inherit;
    text-decoration: none;
    display: flex;
    justify-content: space-between;
    align-items: baseline;
}}

/* Dot leaders + auto page number (WeasyPrint only) */
nav.toc a::after {{
    content: leader('. ') target-counter(attr(href), page);
    font-size: 9pt;
    color: #AAAAAA;
    flex-shrink: 0;
    margin-left: 8px;
}}

.booklet-body {{
    width: 100%;
    text-align: justify;
    hyphens: auto;
}}

/* H1: page break before */
h1 {{
    font-family: '{t['font']}', serif;
    color: {pc};
    font-size: {t['font_size_h1']};
    font-weight: 700;
    line-height: 1.2;
    margin-top: 0;
    margin-bottom: 10px;
    padding-bottom: 7px;
    border-bottom: 2pt double {bc};
    page-break-before: always;
    letter-spacing: -0.3px;
}}

/* First chapter: no break */
.booklet-body > h1:first-child {{
    page-break-before: avoid;
}}

h2 {{
    font-family: '{t['font']}', serif;
    color: {pc};
    font-size: {t['font_size_h2']};
    font-weight: 700;
    margin-top: 18px;
    margin-bottom: 5px;
    padding-bottom: 3px;
    border-bottom: 0.75pt solid {bc};
    page-break-after: avoid;
}}

h3 {{
    font-family: '{t['font']}', serif;
    color: {cc};
    font-size: {t['font_size_h3']};
    font-weight: 700;
    font-style: italic;
    margin-top: 12px;
    margin-bottom: 4px;
    page-break-after: avoid;
}}

h4 {{
    font-family: '{t['font']}', serif;
    color: #3C3C3C;
    font-size: 11pt;
    font-weight: 700;
    margin-top: 10px;
    margin-bottom: 3px;
    page-break-after: avoid;
}}

p {{
    font-size: {t['font_size_body']};
    line-height: {t['line_height_body']};
    margin-bottom: 7px;
    text-align: justify;
    hyphens: auto;
    orphans: 3;
    widows: 3;
}}

ul, ol {{
    font-size: {t['font_size_list']};
    line-height: {t['line_height_list']};
    margin-left: 18px;
    margin-bottom: 6px;
    color: #333333;
}}

li {{
    margin-bottom: 2px;
}}

li strong {{
    color: {pc};
}}

blockquote {{
    border-left: {t['blockquote_border_width']} solid {cc};
    padding: 7px 14px;
    margin: 10px 0;
    font-style: italic;
    font-size: {t['font_size_blockquote']};
    background: {ac};
    color: #444444;
    page-break-inside: avoid;
}}

blockquote p {{
    margin-bottom: 0;
    text-align: left;
}}

pre {{
    background: {t['code_bg_color']};
    color: {t['code_text_color']};
    padding: 10px 14px;
    border-radius: 3px;
    font-size: {t['font_size_code']};
    overflow-x: auto;
    margin: 8px 0;
    border-left: 3px solid {cc};
    page-break-inside: avoid;
    line-height: 1.45;
}}

code {{
    font-family: {t['code_font']};
    font-size: {t['font_size_code']};
}}

p > code,
li > code,
td > code {{
    background: {t['inline_code_bg']};
    padding: 2px 5px;
    border-radius: 3px;
    color: {cc};
    font-weight: 500;
    font-size: calc({t['font_size_code']} * 0.95);
}}

table {{
    border-collapse: collapse;
    width: 100%;
    margin: 8px 0;
    font-size: {t['font_size_table']};
    page-break-inside: avoid;
}}

th {{
    background: {pc};
    color: #FFFFFF;
    padding: 5px 10px;
    text-align: left;
    font-weight: 700;
    font-size: 10pt;
    border-bottom: 1.5px solid {bc};
}}

td {{
    border-bottom: 0.5pt solid {bc};
    padding: 4px 10px;
    color: #333333;
    vertical-align: top;
}}

tr:nth-child(even) td {{
    background: {ac};
}}

img {{
    max-width: {t['image_max_width']};
    max-height: {t['image_max_height']};
    display: block;
    margin: 8px auto;
}}

figure {{
    margin: 10px 0;
    text-align: center;
    page-break-inside: avoid;
}}

figcaption {{
    font-size: {t['font_size_caption']};
    color: {t['caption_color']};
    font-style: italic;
    margin-top: 6px;
}}

a {{
    color: {t['link_color']};
    text-decoration: none;
    border-bottom: 0.5pt dotted {t['link_color']};
}}

em {{
    font-style: italic;
    color: {t['caption_color']};
}}

strong {{
    font-weight: 700;
    color: {pc};
}}

hr {{
    border: none;
    border-top: 0.5pt solid {bc};
    margin: 10px 0;
}}
"""

    @staticmethod
    def _write_temp_html(html: str) -> str:
        fd, path = tempfile.mkstemp(suffix=".html")
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            fh.write(html)
        return path

    def _convert_to_pdf(self, html_path: str, output_path: str, engine: str):
        converters = {
            "weasyprint":  BookletGenerator._convert_weasyprint,
            "wkhtmltopdf": BookletGenerator._convert_wkhtmltopdf,
            "pypandoc":    BookletGenerator._convert_pypandoc,
        }
        ordered = [engine] + [k for k in converters if k != engine]
        for name in ordered:
            func = converters.get(name)
            if func is None:
                continue
            try:
                func(html_path, output_path)
                return
            except (ImportError, FileNotFoundError, RuntimeError):
                continue

        raise RuntimeError(
            "No PDF engine available. Install weasyprint, wkhtmltopdf or pypandoc."
        )

    @staticmethod
    def _convert_weasyprint(html_path: str, output_path: str):
        import weasyprint
        weasyprint.HTML(filename=html_path).write_pdf(output_path)

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
                "--orientation",      "Portrait",
                "--page-size",        "A4",
                "--margin-top",       "28",
                "--margin-bottom",    "25",
                "--margin-left",      "32",
                "--margin-right",     "25",
                "--footer-center",    "[page]",
                "--footer-font-size", "9",
                "--footer-spacing",   "5",
                "--enable-local-file-access",
                "--load-error-handling",       "ignore",
                "--load-media-error-handling", "ignore",
                "--print-media-type",
                html_path,
                output_path,
            ],
            capture_output=True,
            text=True,
        )
        if result.returncode not in (0, 1):
            raise RuntimeError(f"wkhtmltopdf failed: {result.stderr}")

    @staticmethod
    def _convert_pypandoc(html_path: str, output_path: str):
        import pypandoc
        pypandoc.convert_file(
            html_path,
            "pdf",
            outputfile=output_path,
            format="html",
            extra_args=["--metadata", "title= "],
        )
