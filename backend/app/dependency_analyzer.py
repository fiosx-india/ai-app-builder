from pathlib import Path
import ast

class DependencyAnalyzer:
    def analyze_file(self, file_path):
        path = Path(file_path)
        tree = ast.parse(path.read_text(encoding="utf-8"))
        imports = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imports.extend(a.name for a in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imports.append(node.module)
        return {"file": str(path), "imports": sorted(set(imports))}
