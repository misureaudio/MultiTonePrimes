"""Regression tests for the --output-dir guard (resolve_output_dir).

Exercises ONLY the validation/normalization helper — no signal math.
No test creates anything at a drive root.
"""

import os

import pytest

from multitone.optimizer import resolve_output_dir


def test_missing_nested_dir_is_created(tmp_path):
    target = tmp_path / "a" / "b" / "c"
    result = resolve_output_dir(str(target))
    assert os.path.isdir(result)
    assert os.path.isabs(result)
    assert os.path.normpath(result) == os.path.normpath(str(target))


def test_existing_dir_is_returned(tmp_path):
    result = resolve_output_dir(str(tmp_path))
    assert os.path.normpath(result) == os.path.normpath(str(tmp_path))


def test_relative_path_resolved(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    result = resolve_output_dir("sub")
    assert os.path.normpath(result) == os.path.normpath(str(tmp_path / "sub"))
    assert os.path.isdir(result)


def test_path_that_is_a_file_exits(tmp_path):
    f = tmp_path / "afile.txt"
    f.write_text("x")
    with pytest.raises(SystemExit) as exc:
        resolve_output_dir(str(f))
    assert exc.value.code == 1


def test_parent_is_a_file_exits(tmp_path):
    f = tmp_path / "afile.txt"
    f.write_text("x")
    with pytest.raises(SystemExit) as exc:
        resolve_output_dir(str(f / "child"))
    assert exc.value.code == 1


@pytest.mark.parametrize("empty", ["", "   "])
def test_empty_string_exits(empty):
    with pytest.raises(SystemExit) as exc:
        resolve_output_dir(empty)
    assert exc.value.code == 1


def test_tilde_expanded(tmp_path, monkeypatch):
    monkeypatch.setenv("USERPROFILE", str(tmp_path))
    monkeypatch.setenv("HOME", str(tmp_path))
    result = resolve_output_dir("~/sub")
    assert os.path.normpath(result) == os.path.normpath(str(tmp_path / "sub"))
    assert os.path.isdir(result)


@pytest.mark.skipif(os.name != "nt", reason="Windows-specific MSYS path check")
@pytest.mark.parametrize("raw", ["/tmp/foo", "/d/Source/out", "/tmp/xyzzy/deep"])
def test_msys_style_path_rejected_unconditionally(raw):
    # Rejection is by path shape, before any filesystem mutation — no
    # drive-root access needed, and it holds whether or not the resolved
    # directory happens to exist.
    with pytest.raises(SystemExit) as exc:
        resolve_output_dir(raw)
    assert exc.value.code == 1
