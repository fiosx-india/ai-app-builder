class SecurityManager:
    PROTECTED = {".env", ".git", "id_rsa"}

    def inspect_path(self, path):
        parts = set(path.replace("\\", "/").split("/"))
        protected = bool(parts & self.PROTECTED)
        return {"path": path, "protected": protected, "safe_for_ai_write": not protected}
