from backend.app.project_scanner import ProjectScanner

def test_project_intelligence(tmp_path):
    (tmp_path / "main.py").write_text("print('x')\n", encoding="utf-8")
    (tmp_path / "requirements.txt").write_text("fastapi\n", encoding="utf-8")
    result = ProjectScanner().scan(str(tmp_path))
    assert "Python" in result["intelligence"]["languages"]
    assert result["intelligence"]["dependency_files"]
    assert "main.py" in result["intelligence"]["entry_points"]
