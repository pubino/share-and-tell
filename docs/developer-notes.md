# Developer Notes

## Architecture

- Core scanning logic lives in `src/share_and_tell/scanner.py` and produces `FolderInfo` records via `scan_directory`.
- Rendering helpers in `src/share_and_tell/output.py` are responsible for JSON, HTML, and CSV serialisation.
- The CLI entry point in `src/share_and_tell/cli.py` orchestrates argument parsing, scanning, and output, including loading comments from existing files.
- Tests reside under `tests/` and use `pytest`.
- The desktop client lives under `electron-app/` and mirrors the Python scanning/rendering logic in TypeScript for reuse across the Electron main and renderer processes.

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

## Electron Workflow

- Install dependencies with `npm install` from inside `electron-app/`.
- Run `npm run dev` for a live-reloading development session or `npm start` for a single build-and-launch cycle.
- Shared logic resides in `electron-app/src/shared/` so the main process and renderer stay DRY.
- Package distributions for Windows/macOS with `npm run package` (uses `electron-builder`).

### Packaging Notes

- macOS DMG output is written to `electron-app/dist/share-and-tell-electron-<version>-arm64.dmg`.
- Windows NSIS output is written to `electron-app/dist/share-and-tell-electron Setup <version>.exe`; build on Windows or install Wine when cross-compiling from macOS.
- The app currently uses the default Electron icon; provide a `.icns`/`.ico` pair and update the Electron builder config when branding is ready.
- For macOS signing, download a *Developer ID Application* certificate from the Apple Developer portal (or via Xcode → Settings → Accounts → Manage Certificates) and import it into your login Keychain. Once present, either set `CSC_IDENTITY_AUTO_DISCOVERY=true` or export the certificate as `DeveloperIDApplication.p12` and point `CSC_LINK`/`CSC_KEY_PASSWORD` to it when running `npm run package`.
- To notarise, supply your Apple ID credentials and issuer information via `APPLE_ID`, `APPLE_APP_SPECIFIC_PASSWORD`, and `ASC_PROVIDER`. Electron Builder automatically submits the DMG for notarisation when those variables are set.
