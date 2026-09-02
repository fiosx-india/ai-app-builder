from backend.app.patch_engine import PatchEngine

def test_local_patch(tmp_path):
    path = tmp_path / "main.py"
    old, new = "a = 1\nb = 2\n", "a = 10\nb = 2\n"
    path.write_text(old, encoding="utf-8")
    result = PatchEngine().validate_patch(str(path), old, new)
    assert result["approved_for_review"] is True
