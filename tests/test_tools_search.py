from vllm_cli.tools.search import glob_files, search_files


def test_search_files_finds_match(tmp_path):
    (tmp_path / "a.py").write_text("def foo():\n    return 1\n", encoding="utf-8")
    result = search_files(tmp_path, r"def foo")
    assert "a.py:1:def foo():" in result


def test_search_files_no_matches(tmp_path):
    (tmp_path / "a.py").write_text("nothing here\n", encoding="utf-8")
    result = search_files(tmp_path, r"missing_pattern")
    assert "No matches found" in result


def test_search_files_include_filter(tmp_path):
    (tmp_path / "a.py").write_text("target\n", encoding="utf-8")
    (tmp_path / "b.txt").write_text("target\n", encoding="utf-8")
    result = search_files(tmp_path, r"target", include="*.py")
    assert "a.py" in result
    assert "b.txt" not in result


def test_search_files_exclude_filter(tmp_path):
    (tmp_path / "a.py").write_text("target\n", encoding="utf-8")
    (tmp_path / "b.txt").write_text("target\n", encoding="utf-8")
    result = search_files(tmp_path, r"target", exclude="*.py")
    assert "b.txt" in result
    assert "a.py" not in result


def test_search_files_skips_default_excluded_dirs(tmp_path):
    noise_dir = tmp_path / "node_modules"
    noise_dir.mkdir()
    (noise_dir / "a.js").write_text("target\n", encoding="utf-8")
    result = search_files(tmp_path, r"target")
    assert "No matches found" in result


def test_search_files_skips_binary(tmp_path):
    (tmp_path / "a.bin").write_bytes(b"target\x00binary")
    result = search_files(tmp_path, r"target")
    assert "No matches found" in result


def test_search_files_caps_matches(tmp_path):
    lines = "\n".join(f"target {i}" for i in range(250))
    (tmp_path / "a.txt").write_text(lines, encoding="utf-8")
    result = search_files(tmp_path, r"target")
    assert "more matches omitted" in result


def test_search_files_invalid_regex(tmp_path):
    result = search_files(tmp_path, r"(unclosed")
    assert "Error" in result
    assert "invalid regular expression" in result


def test_glob_files_finds_match(tmp_path):
    (tmp_path / "sub").mkdir()
    (tmp_path / "sub" / "a.py").write_text("x", encoding="utf-8")
    (tmp_path / "b.txt").write_text("x", encoding="utf-8")
    result = glob_files(tmp_path, "**/*.py")
    assert "sub/a.py" in result
    assert "b.txt" not in result


def test_glob_files_no_matches(tmp_path):
    result = glob_files(tmp_path, "**/*.nonexistent")
    assert "No files matched" in result


def test_glob_files_rejects_traversal(tmp_path):
    result = glob_files(tmp_path, "../*.py")
    assert "Error" in result
