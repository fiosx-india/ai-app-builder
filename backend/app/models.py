from dataclasses import dataclass, field
from typing import Any, Dict, List


@dataclass
class Change:
    file: str
    action: str
    description: str
    old_content: str = ""
    new_content: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ValidationResult:
    valid: bool
    error_count: int = 0
    errors: List[Dict[str, Any]] = field(default_factory=list)
