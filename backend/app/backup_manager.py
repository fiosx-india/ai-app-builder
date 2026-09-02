from pathlib import Path
from datetime import datetime, timezone
import shutil

class BackupManager:
    def __init__(self, backup_root="./backups"):
        self.backup_root = Path(backup_root)

    def backup_file(self, file_path):
        source = Path(file_path)
        if not source.exists():
            raise ValueError(f"File does not exist: {file_path}")
        stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        destination = self.backup_root / stamp / source.name
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, destination)
        return {"success": True, "source": str(source), "backup": str(destination)}
