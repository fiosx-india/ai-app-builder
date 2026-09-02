from pathlib import Path

class ProjectManager:
    def create_project(self, project_path):
        root = Path(project_path)
        root.mkdir(parents=True, exist_ok=True)
        return {"success": True, "project_path": str(root)}

    def list_files(self, project_path):
        root = Path(project_path)
        if not root.exists():
            raise ValueError("Project path does not exist.")
        return [str(p.relative_to(root)) for p in root.rglob("*") if p.is_file()]
