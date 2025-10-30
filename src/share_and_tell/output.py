from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Tuple

from .scanner import FolderInfo, ScanResult


def render_json(
    result: ScanResult,
    root: Path,
    max_depth: int,
    min_files: int,
) -> str:
    payload = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "root": str(root),
        "max_depth": max_depth,
        "min_files": min_files,
        "folders": [item.as_dict() for item in result.folders],
        "warnings": result.warnings,
    }
    return json.dumps(payload, indent=2)


def _parts_for(path: Path) -> Tuple[str, ...]:
    if str(path) in {".", ""}:
        return tuple()
    return tuple(part for part in path.parts if part not in {"."})


def render_html(
    result: ScanResult,
    root: Path,
    max_depth: int,
    min_files: int,
) -> str:
    tree: Dict[str, Dict] = {}
    info_lookup: Dict[Tuple[str, ...], FolderInfo] = {}

    for folder in result.folders:
        parts = _parts_for(folder.relative_path)
        info_lookup[parts] = folder
        cursor = tree
        for part in parts:
            cursor = cursor.setdefault(part, {})

    def build_outline(node: Dict[str, Dict], prefix: Tuple[str, ...] = tuple()) -> str:
        if not node:
            return ""
        items: List[str] = []
        for name in sorted(node.keys()):
            child_prefix = prefix + (name,)
            info = info_lookup.get(child_prefix)
            comment = info.comment if info else ""
            comment_html = f"<span class=\"comment\">{_escape(comment)}</span>" if comment else ""
            child_outline = build_outline(node[name], child_prefix)
            item_html = (
                f"<li><span class=\"folder\">{_escape(name)}</span>"
                f"{comment_html}"
            )
            if child_outline:
                item_html += child_outline
            item_html += "</li>"
            items.append(item_html)
        return "<ul>" + "".join(items) + "</ul>"

    rows = []
    for folder in result.folders:
        rows.append(
            "<tr>"
            f"<td>{_escape(folder.as_dict()['folder'])}</td>"
            f"<td class=\"num\">{folder.depth}</td>"
            f"<td class=\"num\">{folder.file_count}</td>"
            f"<td>{_escape(folder.comment)}</td>"
            "</tr>"
        )

    warnings_html = ""
    if result.warnings:
        warning_items = "".join(f"<li>{_escape(w)}</li>" for w in result.warnings)
        warnings_html = (
            "<section><h2>Warnings</h2>"
            "<ul class=\"warnings\">"
            f"{warning_items}" "</ul></section>"
        )

    outline_body = build_outline(tree)
    root_info = info_lookup.get(tuple())
    root_comment = root_info.comment if root_info else ""
    root_label = _escape(root.name or str(root))
    root_comment_html = (
        f"<span class=\"comment\">{_escape(root_comment)}</span>" if root_comment else ""
    )
    outline_html = (
        "<div class=\"outline-root\">"
        f"<span class=\"folder\">{root_label}</span>"
        f"{root_comment_html}"
        f"{outline_body}" 
        "</div>"
    ) if outline_body else (
        "<div class=\"outline-root\">"
        f"<span class=\"folder\">{root_label}</span>"
        f"{root_comment_html}" 
        "</div>"
    )

    html = f"""<!DOCTYPE html>
<html lang=\"en\">
<head>
  <meta charset=\"utf-8\">
  <title>Share and Tell Report</title>
  <style>
    body {{ font-family: Arial, sans-serif; margin: 2rem; color: #222; }}
    table {{ border-collapse: collapse; width: 100%; max-width: 960px; margin-bottom: 2rem; }}
    th, td {{ border: 1px solid #ccc; padding: 0.5rem 0.75rem; text-align: left; }}
    th {{ background-color: #f2f2f2; }}
    td.num {{ text-align: right; width: 4rem; }}
    ul {{ list-style-type: none; padding-left: 1.25rem; }}
    ul ul {{ border-left: 1px solid #ddd; margin-left: 0.5rem; padding-left: 1.25rem; }}
    .comment {{ color: #555; margin-left: 0.5rem; font-style: italic; }}
    .warnings {{ color: #a94442; }}
    .metadata {{ margin-bottom: 1.5rem; }}
    .metadata span {{ display: inline-block; margin-right: 1.5rem; }}
    .outline-root > .folder {{ font-weight: 600; }}
    .outline-root {{ margin-left: 0.25rem; }}
  </style>
</head>
<body>
  <h1>Share and Tell Report</h1>
  <section class=\"metadata\">
    <span><strong>Root:</strong> {_escape(str(root))}</span>
    <span><strong>Max Depth:</strong> {max_depth}</span>
    <span><strong>Min Files:</strong> {min_files}</span>
    <span><strong>Generated:</strong> {datetime.now(timezone.utc).isoformat()}</span>
  </section>
  <section>
    <h2>Folder Summary</h2>
    <table>
      <thead>
        <tr><th>Folder</th><th>Depth</th><th>Files</th><th>Comment</th></tr>
      </thead>
      <tbody>
        {''.join(rows)}
      </tbody>
    </table>
  </section>
  <section>
    <h2>Outline View</h2>
    {outline_html if result.folders else '<p>No folders met the criteria.</p>'}
  </section>
  {warnings_html}
</body>
</html>
"""
    return html


def _escape(value: str) -> str:
    return (
        value.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
        .replace("'", "&#x27;")
    )
