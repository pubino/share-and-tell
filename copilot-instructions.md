# Copilot Instructions

- Keep code changes ASCII unless interacting with legacy files that already use non-ASCII characters.
- Prefer standard library solutions before adding dependencies.
- Document non-obvious logic with concise comments; avoid restating trivial statements.
- Update `TODO.md` when adding or resolving notable work items.
- Ensure new CLI options and behaviours are reflected in `README.md` and `docs/developer-notes.md`.
- Mirror core scanning/export behaviour between the Python package and the Electron app by editing `src/share_and_tell/` and `electron-app/src/shared/` together.
- Run `pytest` before opening a pull request.
- Preserve the project structure under `src/share_and_tell/`; add new modules there and export functionality through the package.
