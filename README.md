# Share and Tell

Share and Tell is a lightweight report generator that scans a file share, highlights folders that contain a meaningful number of files, and produces an artifact (JSON by default, optional HTML) that teams can enrich with descriptive comments. The resulting output can be shared with colleagues to explain the structure and purpose of a shared drive.

## Features

- Traverse a directory tree up to a configurable depth (default `3`).
- Record folders that meet a configurable importance threshold measured by the number of files (default `3`).
- Produce JSON, HTML, and CSV outputs with folder metadata and editable comment fields.
- Optional pre-population of comments from a JSON mapping.
- Docker image and `docker-compose` configuration for read-only execution against a shared path.
- Cross-platform Electron desktop app with a polished UI for choosing folders, options, and export destinations.

## Quick Start

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .[test]
share-and-tell /path/to/share --format html --output report.html
```

### CLI Usage

```bash
share-and-tell ROOT [--max-depth N] [--min-files N] [--format json|html|both]
                    [--output PATH] [--comments-file JSON]
```

- `ROOT`: Root directory to analyse (UNC paths such as `\\\\server\\share` are supported).
- `--max-depth`: Maximum depth to traverse; defaults to `3`.
- `--min-files`: Minimum number of files required in a folder; defaults to `3`.
- `--format`: `json`, `html`, `csv`, `both` (json + html), or `all` (json + html + csv); defaults to `json`.
- `--output`: Destination file (or directory for `both`/`all`).
- `--comments-file`: Path to a JSON mapping of folder paths to comments.

When running with `--format both`, supply `--output` with a directory path; the command will write `share-and-tell.json` and `share-and-tell.html` inside that directory.

### HTML Output

The HTML output includes both a sortable table and an outline-style nested list, giving readers a native alternative to a table view for exploring the hierarchy.

### Sample Output

```json
{
    "generated_at": "2025-10-30T15:00:00Z",
    "root": "\\\\storage\\team-share",
    "max_depth": 2,
    "min_files": 3,
    "folders": [
        {
            "folder": ".",
            "absolute_path": "\\\\storage\\team-share",
            "depth": 0,
            "file_count": 1,
            "comment": "Top-level share for departmental reference docs"
        },
        {
            "folder": "Finance/Invoices",
            "absolute_path": "\\\\storage\\team-share\\Finance\\Invoices",
            "depth": 2,
            "file_count": 12,
            "comment": "Monthly invoice PDFs"
        },
        {
            "folder": "HR/Policies",
            "absolute_path": "\\\\storage\\team-share\\HR\\Policies",
            "depth": 2,
            "file_count": 7,
            "comment": "Authoritative HR policy documents"
        }
    ],
    "warnings": [
        "Skipped \\storage\\team-share\\Archive: [Errno 13] Permission denied"
    ]
}
```

The accompanying HTML view renders the same information as both a table and an expandable outline, ready to share with colleagues.

```html
<table>
    <thead>
        <tr><th>Folder</th><th>Depth</th><th>Files</th><th>Comment</th></tr>
    </thead>
    <tbody>
        <tr><td>.</td><td class="num">0</td><td class="num">1</td><td>Top-level share for departmental reference docs</td></tr>
        <tr><td>Finance/Invoices</td><td class="num">2</td><td class="num">12</td><td>Monthly invoice PDFs</td></tr>
        <tr><td>HR/Policies</td><td class="num">2</td><td class="num">7</td><td>Authoritative HR policy documents</td></tr>
    </tbody>
</table>
```

You can view a full render by opening `docs/example-report.html` in a browser.

## Docker

Build the container image:

```bash
docker build -t share-and-tell:local .
```

Run with `docker-compose` and mount a share read-only:

```bash
docker compose run --rm share-and-tell --format both --output /output /share
```

Edit `docker-compose.yml` to point to the correct host path.

### Platform Notes

- **Windows (Docker Desktop / WSL 2):** Ensure the network share is mounted to a drive letter (for example `Z:`). When invoking Docker directly, map that drive into the container: `docker run --rm -v Z:/:/share:ro -v %cd%/reports:/output share-and-tell:local --format both --output /output /share`. If you launch the container from an Ubuntu WSL shell, reference the same drive through `/mnt/z` instead (`docker run --rm -v /mnt/z:/share:ro ...`). Confirm that Docker Desktop has access to the drive in *Settings → Resources → File Sharing*.
- **macOS:** Mount the share (e.g. via Finder using *Go → Connect to Server*), which will appear under `/Volumes/<ShareName>`. Invoke Docker with `docker run --rm -v /Volumes/TeamShare:/share:ro -v "$(pwd)/reports":/output share-and-tell:local --format both --output /output /share`. Adjust the `/Volumes/...` path to match the mounted volume name and ensure the share is mounted before running the container.

## Electron Desktop App

The `electron-app/` directory bundles Share and Tell as a native-feeling desktop app for Windows and macOS. It wraps the same traversal and rendering logic in a UI that lets you pick the source folder, tweak thresholds, choose output formats, and name the exported files.

```bash
cd electron-app
npm install
npm run dev      # watches TypeScript and relaunches Electron
# or
npm start        # one-shot build followed by Electron

# Build signed installers (macOS dmg, Windows nsis)
npm run package
```

When prompted for the output location, choose a base name (for example `~/Desktop/share-report`). The app will append `.json`, `.html`, and/or `.csv` depending on the formats you select.

## Development

- Install development dependencies: `pip install -e .[test]`.
- Run tests: `pytest`.
- Additional notes for contributors are in `docs/developer-notes.md`.
- Track outstanding work in `TODO.md`.

## License

Released under the MIT License © Princeton University.
