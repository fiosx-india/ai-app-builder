import subprocess, sys

class TestEngine:
    def run_pytest(self, project_path):
        result = subprocess.run(
            [sys.executable, "-m", "pytest", "-q"],
            cwd=project_path, capture_output=True, text=True
        )
        return {
            "passed": result.returncode == 0,
            "return_code": result.returncode,
            "stdout": result.stdout,
            "stderr": result.stderr,
        }
