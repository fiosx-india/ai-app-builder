import re

class ErrorIntelligence:
    def analyze(self, error_text):
        match = re.search(r'File "([^"]+)", line (\d+)', error_text)
        return {
            "file": match.group(1) if match else None,
            "line": int(match.group(2)) if match else None,
            "error": error_text.strip(),
            "cause": "Requires diagnostic analysis from validation/execution output.",
            "impact": "Do not mark the change successful until resolved.",
            "suggested_action": "Inspect the smallest affected section and apply a minimal patch.",
        }
