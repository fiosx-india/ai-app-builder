import pytest
from backend.app.patch_engine import PatchEngine

def test_small_file_local_replacement(tmp_path):
    path = tmp_path / "main.py"
    old, new = "a = 1\nb = 2\n", "a = 10\nb = 2\n"
    path.write_text(old, encoding="utf-8")
    result = PatchEngine().validate_patch(str(path), old, new)
    assert result["approved_for_review"] is True
    assert result["changed_lines"] == 1

def test_create_file(tmp_path):
    path = tmp_path / "new.py"
    result = PatchEngine().validate_patch(str(path), "", "x = 1\n", action="create")
    assert result["action"] == "create"

def test_hash_mismatch(tmp_path):
    path = tmp_path / "main.py"
    old = "a = 1\n"
    path.write_text(old, encoding="utf-8")
    with pytest.raises(ValueError, match="integrity"):
        PatchEngine().validate_patch(str(path), old, "a = 2\n", expected_hash="bad")
