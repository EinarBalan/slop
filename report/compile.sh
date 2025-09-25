#!/usr/bin/env bash
set -euo pipefail

# Always operate from the script's directory
cd "$(dirname "$0")"

usage() {
  echo "Usage: $0 [main.tex]"
  echo "- If no file is provided, tries capstone.tex, acl_lualatex.tex, then acl_latex.tex"
}

if [[ "${1:-}" == "-h" || "${1:-}" == "--help" ]]; then
  usage
  exit 0
fi

# Choose main TeX file
main_tex="${1:-}"
if [[ -z "$main_tex" ]]; then
  if [[ -f "capstone.tex" ]]; then
    main_tex="capstone.tex"
  elif [[ -f "acl_lualatex.tex" ]]; then
    main_tex="acl_lualatex.tex"
  elif [[ -f "acl_latex.tex" ]]; then
    main_tex="acl_latex.tex"
  else
    echo "Error: No main .tex specified and no capstone.tex, acl_lualatex.tex, or acl_latex.tex found." >&2
    exit 1
  fi
fi

if [[ ! -f "$main_tex" ]]; then
  echo "Error: '$main_tex' not found." >&2
  exit 1
fi

# Decide engine by scanning the source for unicode/font features
engine="pdflatex"
if grep -Eq '\\usepackage\s*\{fontspec\}|\\babelfont|bidi=' "$main_tex"; then
  engine="lualatex"
fi

echo "Compiling $main_tex using $engine..."

if command -v latexmk >/dev/null 2>&1; then
  # Prefer latexmk for robust incremental builds
  if [[ "$engine" == "lualatex" ]]; then
    latexmk -lualatex -interaction=nonstopmode -file-line-error -halt-on-error "$main_tex"
  else
    latexmk -pdf -pdflatex="pdflatex -interaction=nonstopmode -file-line-error" -halt-on-error "$main_tex"
  fi
else
  # Fallback manual build sequence
  if ! command -v "$engine" >/dev/null 2>&1; then
    echo "Error: $engine not found. Please install MacTeX/TeXLive." >&2
    exit 1
  fi

  "$engine" -interaction=nonstopmode -file-line-error "$main_tex" || true

  # Run bibtex if bibliography is present/referenced
  base_name="${main_tex%.tex}"
  if grep -q "\\bibliography{" "$main_tex" 2>/dev/null || [[ -f "$base_name.bib" ]]; then
    if command -v bibtex >/dev/null 2>&1; then
      bibtex "$base_name" || true
    fi
  fi

  "$engine" -interaction=nonstopmode -file-line-error "$main_tex" || true
  "$engine" -interaction=nonstopmode -file-line-error "$main_tex" || true
fi

echo "Done. PDF: ${main_tex%.tex}.pdf"


