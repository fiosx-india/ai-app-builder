from backend.app.validation_engine import ValidationEngine

def test_valid_project(tmp_path):
    (tmp_path / "main.py").write_text("print('ok')", encoding="utf-8")
    assert ValidationEngine().validate(str(tmp_path))["valid"] is True

def test_invalid_python(tmp_path):
    (tmp_path / "main.py").write_text("def broken(:", encoding="utf-8")
    result = ValidationEngine().validate(str(tmp_path))
    assert result["valid"] is False
    assert result["errors"][0]["type"] == "syntax_error"
