# Project Guidelines

## Code Style
- All functions must have type annotations
- Use f-strings for string formatting
- Maximum line length is 88 characters
- Use `pathlib.Path` for file operations, not `os.path`

## Linting
- The team uses ruff for linting (not other linters)

## Workflow
- Run tests with: `uv run pytest`
- The CI pipeline runs on every push to `main`
- Open a draft PR early so reviewers can follow along
