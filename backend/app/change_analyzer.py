import difflib
from typing import Any, Dict


class ChangeAnalyzer:
    """Measures whether a proposed change is localized."""

    def analyze(self, file_path: str, old_content: str, new_content: str) -> Dict[str, Any]:
        old_lines = old_content.splitlines()
        new_lines = new_content.splitlines()
        matcher = difflib.SequenceMatcher(None, old_lines, new_lines)

        ranges = []
        changed_old_lines = 0
        changed_new_lines = 0

        for tag, i1, i2, j1, j2 in matcher.get_opcodes():
            if tag == "equal":
                continue
            ranges.append({
                "operation": tag,
                "old_start": i1 + 1,
                "old_end": i2,
                "new_start": j1 + 1,
                "new_end": j2,
            })
            changed_old_lines += i2 - i1
            changed_new_lines += j2 - j1

        changed_lines = max(changed_old_lines, changed_new_lines)
        baseline = max(len(old_lines), len(new_lines), 1)
        ratio = changed_lines / baseline
        localized = len(ranges) <= 3 and (baseline <= 10 or ratio <= 0.40)

        return {
            "file": file_path,
            "changed_ranges": ranges,
            "changed_range_count": len(ranges),
            "changed_lines": changed_lines,
            "total_lines": baseline,
            "change_ratio": round(ratio, 4),
            "localized": localized,
            "reason": (
                "Change is localized."
                if localized
                else "Change affects too much of the file or too many separate sections."
            ),
        }
