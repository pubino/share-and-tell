import csv
import io
from pathlib import Path

from share_and_tell.output import render_csv, _escape, render_html
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


def test_escape_html():
    assert _escape("<script>alert('xss')</script>") == "&lt;script&gt;alert(&#x27;xss&#x27;)&lt;/script&gt;"
    assert _escape('"quoted"') == "&quot;quoted&quot;"
    assert _escape("normal text") == "normal text"


def test_render_html_structure(tmp_path: Path) -> None:
    """Integration test for HTML output structure and content."""
    # Create test directory structure
    course_dir = tmp_path / "Course Offerings"
    course_dir.mkdir()
    _write_file(course_dir, "overview.txt")

    sub_dir = course_dir / "1_FacultyRequests_2025"
    sub_dir.mkdir()
    _write_file(sub_dir, "request.txt")

    sub_sub_dir = sub_dir / "submitted"
    sub_sub_dir.mkdir()
    _write_file(sub_sub_dir, "final.pdf")

    result = scan_directory(tmp_path, max_depth=3, min_files=1)
    html_output = render_html(result, tmp_path, max_depth=3, min_files=1)

    # Verify HTML document structure
    assert html_output.startswith("<!DOCTYPE html>")
    assert "<html lang=\"en\">" in html_output
    assert "<head>" in html_output
    assert "<title>Share and Tell Report</title>" in html_output
    assert "<style>" in html_output
    assert "</head>" in html_output
    assert "<body>" in html_output
    assert "<h1>Share and Tell Report</h1>" in html_output
    assert "</body>" in html_output
    assert "</html>" in html_output

    # Verify metadata section
    assert "Root:" in html_output
    assert "Max Depth:" in html_output
    assert "Min Files:" in html_output
    assert "Generated:" in html_output

    # Verify table structure
    assert "<table>" in html_output
    assert "<thead>" in html_output
    assert "<th>Folder</th>" in html_output
    assert "<th>Depth</th>" in html_output
    assert "<th>Files</th>" in html_output
    assert "<th>Comment</th>" in html_output
    assert "<tbody>" in html_output
    assert "</tbody>" in html_output
    assert "</table>" in html_output

    # Verify folder data in table
    assert "Course Offerings" in html_output
    assert "Course Offerings/1_FacultyRequests_2025" in html_output

    # Verify outline view section
    assert "<h2>Outline View</h2>" in html_output
    assert "outline-root" in html_output
    assert "folder" in html_output  # CSS class for folder names

    # Verify CSS styling is embedded
    assert "font-family: Arial, sans-serif" in html_output
    assert "border-collapse: collapse" in html_output
    assert ".comment" in html_output
    assert ".warnings" in html_output


def test_render_html_with_comments_and_warnings(tmp_path: Path) -> None:
    """Test HTML output with comments and warnings."""
    # Create test directory
    test_dir = tmp_path / "test_project"
    test_dir.mkdir()
    _write_file(test_dir, "file1.txt")
    _write_file(test_dir, "file2.txt")

    result = scan_directory(tmp_path, max_depth=3, min_files=1)
    # Add a comment to test comment rendering
    if result.folders:
        result.folders[0].comment = "Test comment with <script>alert('xss')</script>"

    # Add a warning to test warning rendering
    result.warnings = ["Test warning message"]

    html_output = render_html(result, tmp_path, max_depth=3, min_files=1)

    # Verify comments are HTML-escaped and styled
    assert "&lt;script&gt;alert(&#x27;xss&#x27;)&lt;/script&gt;" in html_output
    assert "comment" in html_output  # CSS class

    # Verify warnings section
    assert "<h2>Warnings</h2>" in html_output
    assert "Test warning message" in html_output
    assert "warnings" in html_output  # CSS class


def test_render_html_empty_result(tmp_path: Path) -> None:
    """Test HTML output when no folders meet criteria."""
    # Create an empty directory - root will still be included but no subfolders
    result = scan_directory(tmp_path, max_depth=3, min_files=1)  # min_files=1 so root (0 files) doesn't qualify
    html_output = render_html(result, tmp_path, max_depth=3, min_files=1)

    # Should still have basic HTML structure
    assert "<!DOCTYPE html>" in html_output
    assert "<h1>Share and Tell Report</h1>" in html_output
    assert "<table>" in html_output
    assert "<h2>Outline View</h2>" in html_output

    # Root directory should be shown in outline view since it exists
    # but the table should be empty or only show root if it meets criteria
    assert "outline-root" in html_output


def test_cancellable_scanner_basic(tmp_path: Path) -> None:
    """Test basic functionality of cancellable scanner."""
    from share_and_tell.cancellable_scanner import CancellableDirectoryScanner, ScanConfig
    
    config = ScanConfig(min_files=1)
    scanner = CancellableDirectoryScanner(config)
    
    # Create a test directory
    test_dir = tmp_path / "basic_test"
    test_dir.mkdir()
    (test_dir / "file.txt").write_text("content")
    
    result = scanner.scan_directory(test_dir)
    
    # Should find the directory
    assert len(result.folders) >= 1
    assert result.folders[0].file_count >= 1


def test_cancellable_scanner_cancellation(tmp_path: Path) -> None:
    """Test that scanner can be cancelled."""
    from share_and_tell.cancellable_scanner import CancellableDirectoryScanner, ScanConfig, ScanCancelledException
    
    config = ScanConfig()
    scanner = CancellableDirectoryScanner(config)
    
    # Test that cancel sets the event
    scanner.cancel()
    assert scanner.is_cancelled()
    
    # Test that _check_cancelled raises exception
    try:
        scanner._check_cancelled()
        assert False, "Should have raised ScanCancelledException"
    except ScanCancelledException:
        pass  # Expected
