import difflib

class ChangeAnalyzer:
    def analyze(self, file_path, old_content, new_content):
        matcher = difflib.SequenceMatcher(None, old_content.splitlines(), new_content.splitlines())
        ranges = []
        for tag, i1, i2, j1, j2 in matcher.get_opcodes():
            if tag != "equal":
                ranges.append({
                    "operation": tag,
                    "old_start": i1 + 1, "old_end": i2,
                    "new_start": j1 + 1, "new_end": j2,
                })
        return {"file": file_path, "changed_ranges": ranges, "localized": len(ranges) <= 3}
