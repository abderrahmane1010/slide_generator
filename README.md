# Slide Maker

Convertisseur Markdown → PDF pour slides scientifiques.

## Installation

```bash
# Créer et activer le venv
python3 -m venv .venv
source .venv/bin/activate

# Installer les dépendances
pip install -r requirements.txt
```

### Dépendance système (PDF engine)

Au moins **un** des outils suivants doit être installé :

```bash
# Option 1 : weasyprint (recommandé, pur Python)
pip install weasyprint

# Option 2 : wkhtmltopdf
sudo apt install wkhtmltopdf

# Option 3 : pandoc + wkhtmltopdf
sudo apt install pandoc wkhtmltopdf
```

## Utilisation

```bash
# Générer un PDF à partir de tous les exemples
python main.py

# Générer à partir d'un fichier Markdown spécifique
python main.py examples/title_slide.md -o titre.pdf

# Générer à partir d'un dossier de fichiers .md
python main.py examples/ -o slides.pdf

# Spécifier un fichier de config alternatif
python main.py examples/ -c config.yaml -o slides.pdf
```

## Structure du projet

```
slide_maker/
├── config.yaml              # Configuration du thème (couleurs, police)
├── requirements.txt
├── main.py                  # Point d'entrée
├── examples/                # Exemples de slides Markdown
│   ├── title_slide.md
│   ├── text_list_slide.md
│   ├── code_slide.md
│   ├── equation_slide.md
│   └── image_slide.md
└── slide_generator/         # Package principal
    ├── __init__.py
    ├── markdown_parser.py   # MarkdownParser
    ├── slide_generator.py   # SlideGenerator
    └── theme_manager.py     # ThemeManager
```

## Configuration

Éditer `config.yaml` pour personnaliser le thème. **Tous les paramètres sont optionnels** (des valeurs par défaut sont appliquées) :

```yaml
theme:
  # Couleurs
  primary_color: "#004D25"
  secondary_color: "#FAFCFB"
  accent_color: "#E8F5E9"
  header_bg: "#006400"
  header_text: "#FFFFFF"
  code_bg_color: "#1B2631"
  code_text_color: "#E8F8F5"
  inline_code_bg: "#D5F5E3"
  caption_color: "#666666"
  link_color: "#1B8A4E"
  border_color: "#C8E6C9"

  # Police
  font: "Roboto"
  code_font: "'Fira Code', 'Consolas', 'Courier New', monospace"

  # Tailles de texte
  font_size_h1: "38pt"
  font_size_h2: "30pt"
  font_size_h3: "24pt"
  font_size_body: "20pt"
  font_size_list: "18pt"
  font_size_code: "14pt"
  font_size_caption: "14pt"
  font_size_slide_number: "13pt"
  font_size_blockquote: "18pt"
  font_size_table: "16pt"

  # Interlignes
  line_height_body: 1.7
  line_height_list: 1.9

  # Dimensions de slide (A4 paysage = 1 page PDF par slide)
  slide_width: "297mm"
  slide_height: "210mm"
  slide_padding: "25mm 35mm 30mm 35mm"

  # Bordures
  slide_border_width: "0px"
  h1_border_width: "0px"
  blockquote_border_width: "5px"

  # Images
  image_max_width: "85%"
  image_max_height: "140mm"

  # Numérotation
  slide_numbering: true
  slide_number_opacity: 0.5

  # PDF engine : pypandoc | weasyprint | wkhtmltopdf
  pdf_engine: "pypandoc"
```

## Format des slides Markdown

Séparer chaque slide par `---` :

```markdown
---

# Titre de la slide

Contenu ici.

---

# Slide suivante

- Point 1
- Point 2

---
```
