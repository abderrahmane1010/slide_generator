import argparse
import glob
import os
import sys

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
        description="Markdown → PDF slide generator"
    )
    parser.add_argument(
        "input",
        nargs="?",
        default="examples/",
        help="Markdown file or directory (default: examples/)",
    )
    parser.add_argument(
        "-o", "--output",
        default="output.pdf",
        help="Output PDF path (default: output.pdf)",
    )
    parser.add_argument(
        "-c", "--config",
        default=None,
        help="Config YAML path (default: config.yaml)",
    )
    args = parser.parse_args()

    config_path = args.config or find_config()
    if config_path is None:
        print("No config.yaml found; using defaults.")
        config_path = "config.yaml"

    theme_manager = ThemeManager(config_path)
    slide_gen = SlideGenerator(theme_manager)

    raw_md = collect_markdown(args.input)
    md_parser = MarkdownParser(raw_md)
    parsed_slides = md_parser.parse_slides()

    print(f"Parsed {len(parsed_slides)} slide(s).")
    slide_gen.generate_pdf(parsed_slides, args.output)
    print(f"PDF generated → {args.output}")


if __name__ == "__main__":
    main()
