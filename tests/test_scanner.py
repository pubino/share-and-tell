from pathlib import Path

from share_and_tell.scanner import scan_directory


def create_files(target: Path, count: int) -> None:
    for index in range(count):
        (target / f"file_{index}.txt").write_text("sample", encoding="utf-8")


def test_scan_directory_filters_by_min_files(tmp_path: Path) -> None:
    create_files(tmp_path, 1)

    dept_a = tmp_path / "dept_a"
    dept_a.mkdir()
    create_files(dept_a, 3)

    dept_b = tmp_path / "dept_b"
    dept_b.mkdir()
    create_files(dept_b, 2)

    result = scan_directory(tmp_path, max_depth=4, min_files=3)
    folders = [item.as_dict()["folder"] for item in result.folders]

    assert folders == [".", "dept_a"]
    assert "dept_b" not in folders


def test_scan_directory_applies_comment_map(tmp_path: Path) -> None:
    team_dir = tmp_path / "team"
    team_dir.mkdir()
    create_files(team_dir, 4)

    comments = {"team": "Primary data folder"}

    result = scan_directory(tmp_path, comments=comments)
    team_info = next(item for item in result.folders if item.relative_path.parts == ("team",))
    assert team_info.comment == "Primary data folder"
