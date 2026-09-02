from dataclasses import dataclass, field
from datetime import datetime, timezone

@dataclass
class MemoryEntry:
    file: str
    action: str
    timestamp: str
    description: str
    metadata: dict = field(default_factory=dict)

class ProjectMemory:
    def __init__(self):
        self.entries = []

    def record(self, file, action, description, metadata=None):
        entry = MemoryEntry(file, action, datetime.now(timezone.utc).isoformat(), description, metadata or {})
        self.entries.append(entry)
        return entry

    def history(self):
        return [e.__dict__ for e in self.entries]
