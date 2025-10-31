import json
import pytest
from pathlib import Path

from share_and_tell.cli import load_existing


def test_load_existing_none():
    assert load_existing(None) == {}


def test_load_existing_valid(tmp_path: Path):
    data = {
        "generated_at": "2023-01-01T00:00:00Z",
        "root": "/some/path",
        "max_depth": 3,
        "min_files": 3,
        "folders": [
            {"folder": "folder1", "absolute_path": "/path/folder1", "depth": 1, "file_count": 5, "comment": "Comment 1"},
            {"folder": "folder2", "absolute_path": "/path/folder2", "depth": 1, "file_count": 3, "comment": "Comment 2"}
        ],
        "warnings": []
    }
    file = tmp_path / "existing.json"
    file.write_text(json.dumps(data), encoding="utf-8")
    
    comments = load_existing(file)
    assert comments == {"folder1": "Comment 1", "folder2": "Comment 2"}


def test_load_existing_missing_keys(tmp_path: Path):
    data = {"generated_at": "2023-01-01T00:00:00Z"}  # Missing required keys
    file = tmp_path / "invalid.json"
    file.write_text(json.dumps(data), encoding="utf-8")
    
    with pytest.raises(SystemExit, match="missing required keys"):
        load_existing(file)


def test_load_existing_invalid_folders(tmp_path: Path):
    data = {
        "generated_at": "2023-01-01T00:00:00Z",
        "root": "/some/path",
        "max_depth": 3,
        "min_files": 3,
        "folders": "not a list",
        "warnings": []
    }
    file = tmp_path / "invalid.json"
    file.write_text(json.dumps(data), encoding="utf-8")
    
    with pytest.raises(SystemExit, match="'folders' must be a list"):
        load_existing(file)


def test_load_existing_folder_missing_keys(tmp_path: Path):
    data = {
        "generated_at": "2023-01-01T00:00:00Z",
        "root": "/some/path",
        "max_depth": 3,
        "min_files": 3,
        "folders": [{"folder": "folder1"}],  # Missing comment
        "warnings": []
    }
    file = tmp_path / "invalid.json"
    file.write_text(json.dumps(data), encoding="utf-8")
    
    with pytest.raises(SystemExit, match="must have 'folder' and 'comment'"):
        load_existing(file)


def test_load_existing_non_string_comment(tmp_path: Path):
    data = {
        "generated_at": "2023-01-01T00:00:00Z",
        "root": "/some/path",
        "max_depth": 3,
        "min_files": 3,
        "folders": [{"folder": "folder1", "comment": 123}],  # Comment not string
        "warnings": []
    }
    file = tmp_path / "invalid.json"
    file.write_text(json.dumps(data), encoding="utf-8")
    
    with pytest.raises(SystemExit, match="Comment must be a string"):
        load_existing(file)


def test_load_existing_file_not_found():
    with pytest.raises(SystemExit, match="not found"):
        load_existing(Path("nonexistent.json"))


def test_load_existing_invalid_json(tmp_path: Path):
    file = tmp_path / "invalid.json"
    file.write_text("not json", encoding="utf-8")
    
    with pytest.raises(SystemExit, match="Failed to parse"):
        load_existing(file)