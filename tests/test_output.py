import csv
import io
from pathlib import Path

from share_and_tell.output import render_csv
from share_and_tell.scanner import scan_directory


def _write_file(path: Path, name: str) -> None:
    (path / name).write_text("content", encoding="utf-8")


def test_render_csv_orders_rows_by_folder_name(tmp_path: Path) -> None:
    course_dir = tmp_path / "Course Offerings"
    course_dir.mkdir()
    _write_file(course_dir, "overview.txt")

    sub_dir = course_dir / "1_FacultyRequests_2025"
    sub_dir.mkdir()
    _write_file(sub_dir, "request.txt")

    result = scan_directory(tmp_path, max_depth=3, min_files=1)
    csv_text = render_csv(result, tmp_path, max_depth=3, min_files=1)

    rows = list(csv.reader(io.StringIO(csv_text)))
    assert rows[0] == ["folder", "absolute_path", "depth", "file_count", "comment"]
    # Expect alphabetical ordering: root, parent folder, child folder
    assert rows[1][0] == "."
    assert rows[2][0] == "Course Offerings"
    assert rows[3][0] == "Course Offerings/1_FacultyRequests_2025"
