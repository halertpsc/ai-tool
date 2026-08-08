import pytest

from vllm_cli.tools.common import ToolError
from vllm_cli.tools.files import edit_file, list_dir, read_file, resolve_scoped_path, write_file


def test_resolve_scoped_path_within_root(tmp_path):
    (tmp_path / "a.txt").write_text("hi", encoding="utf-8")
    resolved = resolve_scoped_path(tmp_path, "a.txt")
    assert resolved == (tmp_path / "a.txt").resolve()


def test_resolve_scoped_path_rejects_traversal(tmp_path):
    with pytest.raises(ToolError):
        resolve_scoped_path(tmp_path, "../outside.txt")


def test_resolve_scoped_path_rejects_absolute_outside_root(tmp_path, monkeypatch):
    other = tmp_path.parent / "elsewhere.txt"
    with pytest.raises(ToolError):
        resolve_scoped_path(tmp_path, str(other))


def test_resolve_scoped_path_nested_subdir(tmp_path):
    (tmp_path / "sub").mkdir()
    (tmp_path / "sub" / "b.txt").write_text("hi", encoding="utf-8")
    resolved = resolve_scoped_path(tmp_path, "sub/b.txt")
    assert resolved == (tmp_path / "sub" / "b.txt").resolve()


def test_read_file_success(tmp_path):
    (tmp_path / "a.txt").write_text("hello world", encoding="utf-8")
    assert read_file(tmp_path, "a.txt") == "hello world"


def test_read_file_not_found(tmp_path):
    result = read_file(tmp_path, "missing.txt")
    assert "Error" in result


def test_read_file_traversal_rejected(tmp_path):
    result = read_file(tmp_path, "../secret.txt")
    assert "Error" in result


def test_write_file_creates_parent_dirs(tmp_path):
    result = write_file(tmp_path, "nested/dir/out.txt", "content")
    assert "Wrote" in result
    assert (tmp_path / "nested" / "dir" / "out.txt").read_text(encoding="utf-8") == "content"


def test_write_file_overwrites(tmp_path):
    (tmp_path / "a.txt").write_text("old", encoding="utf-8")
    write_file(tmp_path, "a.txt", "new")
    assert (tmp_path / "a.txt").read_text(encoding="utf-8") == "new"


def test_edit_file_unique_match(tmp_path):
    (tmp_path / "a.txt").write_text("foo bar baz", encoding="utf-8")
    result = edit_file(tmp_path, "a.txt", "bar", "qux")
    assert "Edited" in result
    assert (tmp_path / "a.txt").read_text(encoding="utf-8") == "foo qux baz"


def test_edit_file_missing_snippet(tmp_path):
    (tmp_path / "a.txt").write_text("foo bar baz", encoding="utf-8")
    result = edit_file(tmp_path, "a.txt", "nope", "qux")
    assert "Error" in result
    assert (tmp_path / "a.txt").read_text(encoding="utf-8") == "foo bar baz"


def test_edit_file_ambiguous_snippet(tmp_path):
    (tmp_path / "a.txt").write_text("bar bar bar", encoding="utf-8")
    result = edit_file(tmp_path, "a.txt", "bar", "qux")
    assert "Error" in result
    assert "ambiguous" in result
    assert (tmp_path / "a.txt").read_text(encoding="utf-8") == "bar bar bar"


def test_list_dir_returns_entries(tmp_path):
    (tmp_path / "a.txt").write_text("x", encoding="utf-8")
    (tmp_path / "sub").mkdir()
    result = list_dir(tmp_path, ".")
    assert "a.txt" in result
    assert "sub/" in result


def test_list_dir_empty(tmp_path):
    (tmp_path / "empty").mkdir()
    result = list_dir(tmp_path, "empty")
    assert result == "(empty directory)"


def test_list_dir_not_found(tmp_path):
    result = list_dir(tmp_path, "nope")
    assert "Error" in result
