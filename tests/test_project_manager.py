from backend.app.project_manager import ProjectManager

def test_create_project(tmp_path):
    project = tmp_path / "demo"
    assert ProjectManager().create_project(str(project))["success"] is True
