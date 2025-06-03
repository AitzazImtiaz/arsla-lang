site_name: Arsla Language Documentation
site_description: The official documentation for Arsla, a stack-based golfing language.
site_url: https://aitzazimtiaz.github.io/arsla-lang/docs/
repo_url: https://github.com/aitzazimtiaz/arsla-lang
repo_name: aitzazimtiaz/arsla-lang
edit_uri: edit/main/docs/

# Theme Configuration
theme:
  name: material
  palette:
    - media: "(prefers-color-scheme: light)"
      scheme: default
      primary: deep purple
      accent: purple
      toggle:
        icon: material/brightness-4
        name: Switch to dark mode
    - media: "(prefers-color-scheme: dark)"
      scheme: slate
      primary: deep purple
      accent: purple
      toggle:
        icon: material/brightness-7
        name: Switch to light mode
  features:
    - navigation.tabs
    - navigation.sections
    - navigation.top
    - navigation.indexes
    - navigation.expand
    - search.highlight
    - search.share
    - content.tabs.link
    - content.code.copy
    - content.code.annotate
    - content.tooltips
  icon:
    logo: material/code-tags

# Optional: Footer or Social Media – REMOVE if not needed
extra:
  social:
    - icon: fontawesome/brands/github
      link: https://github.com/aitzazimtiaz
      name: GitHub

# Markdown Extensions
markdown_extensions:
  - admonition
  - attr_list
  - def_list
  - footnotes
  - md_in_html
  - toc:
      permalink: true
  - pymdownx.details
  - pymdownx.superfences
  - pymdownx.tabbed:
      alternate_style: true
  - pymdownx.highlight:
      anchor_linenums: true
  - pymdownx.arithmatex:
      generic: true
  - pymdownx.emoji:
      emoji_index: !!python/name:material.extensions.emoji.twemoji
      emoji_generator: !!python/name:material.extensions.emoji.to_svg
  - pymdownx.mark
  - pymdownx.tilde
  - pymdownx.caret
  - pymdownx.critic
  - pymdownx.keys
  - pymdownx.tasklist:
      custom_checkbox: true
  - pymdownx.saneheaders
  - pymdownx.betterem

# Plugins
plugins:
  - search:
      lang: en
  - mkdocstrings:
      handlers:
        python:
          paths: ["src"]
          options:
            docstring_style: google
            show_root_heading: true
            show_source: true
            separate_signature: true

# Navigation
nav:
  - Home: index.md
  - Getting Started:
      - Installation: getting-started/installation.md
      - Basic Usage: getting-started/basic-usage.md
  - Language Reference:
      - Overview: language-reference/overview.md
      - Built-in Functions: language-reference/builtins.md
      - Lexical Structure: language-reference/lexer.md
      - Syntax and Parsing: language-reference/parser.md
      - Error Handling: language-reference/errors.md
  - Command Line Interface (CLI): cli.md
  - Contributing: contributing.md
  - Code of Conduct: code-of-conduct.md
  - About:
      - Project Overview: about.md
      - Dedication: dedication.md
