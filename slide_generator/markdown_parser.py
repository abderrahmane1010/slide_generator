import re
import markdown


class MarkdownParser:
    SLIDE_SEPARATOR = re.compile(r"^---\s*$", re.MULTILINE)

    def __init__(self, markdown_text):
        self.raw = markdown_text

    def parse(self):
        return markdown.markdown(
            self.raw,
            extensions=["extra", "codehilite", "md_in_html"],
        )

    def split_slides(self):
        parts = self.SLIDE_SEPARATOR.split(self.raw)
        return [p.strip() for p in parts if p.strip()]

    def parse_slides(self):
        slides = self.split_slides()
        parsed = []
        for slide_md in slides:
            html = markdown.markdown(
                slide_md,
                extensions=["extra", "codehilite", "md_in_html"],
            )
            parsed.append(html)
        return parsed
