# Developer Notes

## Architecture

- Core scanning logic lives in `src/share_and_tell/scanner.py` and produces `FolderInfo` records via `scan_directory`.
- Rendering helpers in `src/share_and_tell/output.py` are responsible for JSON, HTML, and CSV serialisation.
- The CLI entry point in `src/share_and_tell/cli.py` orchestrates argument parsing, scanning, and output.
- Tests reside under `tests/` and use `pytest`.

## Coding Guidelines

- Target Python 3.10+.
- Keep functions small and composable; prefer pure functions that accept explicit arguments.
- Avoid following symbolic links when traversing directories to prevent recursive cycles.
- Sort filesystem output to guarantee deterministic reports.
- Use `_escape` in HTML rendering to avoid introducing raw markup.

## Comments and Documentation

- Document edge cases or rationale with brief comments when the reasoning is not obvious from the code.
- Reflect user-facing changes in `README.md` and update `copilot-instructions.md` if the workflow changes.

## Testing

- Run `pytest` before committing changes.
- Use the helper `create_files` in tests to populate temporary directories instead of reimplementing loops.

## Docker Workflow

- The `Dockerfile` builds a minimal image using the Python 3.12 base.
- `docker-compose.yml` demonstrates mounting a host directory at `/share` in read-only mode and exporting results to `/output`.
