#!/bin/bash
set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PIPELINE_DIR="$SCRIPT_DIR/../../lca-lessons/pipeline"

usage() {
    cat <<HELP
Usage: ./$(basename "$0") [OPTIONS]

Convert Markdown lesson files in thinkific/src/ to HTML in thinkific/docs/.
Must be run as ./da_convert.sh (not sourced, not by name alone).

Options:
  --pipeline DIR   Path to the convert.py pipeline directory
                   (default: $PIPELINE_DIR)
  --help           Show this help message

Paths:
  Source:  $SCRIPT_DIR/src/
  Output:  $SCRIPT_DIR/docs/

To serve output after conversion:
  python -m http.server 8080 --directory $SCRIPT_DIR/docs
  Then open http://localhost:8080 in your browser
HELP
}

# Parse arguments
while [[ $# -gt 0 ]]; do
    case "$1" in
        --pipeline)
            PIPELINE_DIR="$2"
            shift 2
            ;;
        --help|-h)
            usage
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            usage
            exit 1
            ;;
    esac
done

# Validate src dir
if [ ! -d "$SCRIPT_DIR/src" ]; then
    echo "Error: Source directory not found: $SCRIPT_DIR/src"
    exit 1
fi

# Validate pipeline
if [ ! -f "$PIPELINE_DIR/convert.py" ]; then
    echo "Error: convert.py not found in pipeline directory: $PIPELINE_DIR"
    echo "Use --pipeline to specify the correct path."
    exit 1
fi

echo "Source:   $SCRIPT_DIR/src"
echo "Output:   $SCRIPT_DIR/docs"
echo "Pipeline: $PIPELINE_DIR"
echo

uv run --project "$(dirname "$PIPELINE_DIR")" python - <<EOF
import sys
import shutil
from pathlib import Path

sys.path.insert(0, '$PIPELINE_DIR')
from convert import convert_file

src_dir = Path('$SCRIPT_DIR/src')
docs_dir = Path('$SCRIPT_DIR/docs')

md_files = list(src_dir.glob('**/*.md'))
print(f"Found {len(md_files)} file(s)")
print()

for md_file in md_files:
    rel = md_file.relative_to(src_dir)
    output = docs_dir / rel.with_suffix('.html')
    convert_file(md_file, output)

print()
print("Copying images...")
images_found = False
for images_src in src_dir.glob('**/images'):
    if images_src.is_dir():
        images_found = True
        rel = images_src.relative_to(src_dir)
        images_dest = docs_dir / rel
        shutil.copytree(images_src, images_dest, dirs_exist_ok=True)
        print(f"  ✓ Copied {rel}")
if not images_found:
    print("  (none found)")

print()
print("Copying shared assets...")
shared_src = src_dir / 'shared'
if shared_src.exists():
    shutil.copytree(shared_src, docs_dir / 'shared', dirs_exist_ok=True)
    print("  ✓ Copied shared/")
else:
    print("  (no shared/ directory found)")

print()
print("Copying symbols...")
symbols_src = Path('$PIPELINE_DIR') / 'symbols'
if symbols_src.exists():
    copied = []
    for subdir in sorted(docs_dir.iterdir()):
        if subdir.is_dir() and any(subdir.glob('*.html')):
            shutil.copytree(str(symbols_src), str(subdir / 'symbols'), dirs_exist_ok=True)
            copied.append(subdir.name)
    if any(docs_dir.glob('*.html')):
        shutil.copytree(str(symbols_src), str(docs_dir / 'symbols'), dirs_exist_ok=True)
        copied.append('(root)')
    print(f"  ✓ Copied symbols/ → {', '.join(copied)}" if copied else "  (no HTML subdirs found)")
else:
    print("  (symbols directory not found in pipeline)")

print()
print("Done! To view the output:")
print("  python -m http.server 8080 --directory '$SCRIPT_DIR/docs'")
print("  Then open http://localhost:8080 in your browser")
EOF
