import argparse
import glob
import os
import sys

from slide_generator.booklet_generator import BookletGenerator
from slide_generator.booklet_theme_manager import BookletThemeManager
from slide_generator.markdown_parser import MarkdownParser
from slide_generator.slide_generator import SlideGenerator
from slide_generator.theme_manager import ThemeManager


def find_config():
    candidates = ["config.yaml", "config.yml"]
    for c in candidates:
        if os.path.exists(c):
            return c
    return None


def collect_markdown(path: str) -> str:
    if os.path.isdir(path):
        files = sorted(glob.glob(os.path.join(path, "*.md")))
        if not files:
            print(f"No .md files found in {path}")
            sys.exit(1)
        parts = []
        for f in files:
            with open(f, "r", encoding="utf-8") as fh:
                parts.append(fh.read())
        return "\n---\n".join(parts)
    else:
        with open(path, "r", encoding="utf-8") as fh:
            return fh.read()


def main():
    parser = argparse.ArgumentParser(
        description="Markdown → PDF slide deck or academic booklet"
    )
    parser.add_argument(
        "input",
        nargs="?",
        default="examples/",
        help="Markdown file or directory (default: examples/)",
    )
    parser.add_argument(
        "-o", "--output",
        default=None,
        help="Output PDF path (default: output.pdf or booklet.pdf)",
    )
    parser.add_argument(
        "-c", "--config",
        default=None,
        help="YAML config file for slides (default: config.yaml)",
    )
    parser.add_argument(
        "--mode",
        choices=["slides", "booklet"],
        default="slides",
        help="Output mode: 'slides' (default) or 'booklet' (A4 portrait booklet)",
    )
    parser.add_argument(
        "--booklet-config",
        default="booklet_config.yaml",
        help="YAML config file for the booklet (default: booklet_config.yaml)",
    )
    args = parser.parse_args()

    raw_md = collect_markdown(args.input)

    if args.mode == "booklet":
        output_path = args.output or "booklet.pdf"
        booklet_theme = BookletThemeManager(args.booklet_config)
        booklet_gen = BookletGenerator(booklet_theme)
        booklet_gen.generate_pdf(raw_md, output_path)
        print(f"Booklet PDF generated → {output_path}")
        return

    output_path = args.output or "output.pdf"
    config_path = args.config or find_config()
    if config_path is None:
        print("No config.yaml found; using defaults.")
        config_path = "config.yaml"

    theme_manager = ThemeManager(config_path)
    slide_gen = SlideGenerator(theme_manager)

    md_parser = MarkdownParser(raw_md)
    parsed_slides = md_parser.parse_slides()

    print(f"Slides parsed: {len(parsed_slides)}")
    slide_gen.generate_pdf(parsed_slides, output_path)
    print(f"Slides PDF generated → {output_path}")


if __name__ == "__main__":
    main()
