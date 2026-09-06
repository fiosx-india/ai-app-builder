from backend.app.transaction_manager import TransactionManager

class PassingValidation:
    def run(self, project_path):
        return {"valid": True}

class FailingValidation:
    def run(self, project_path):
        return {"valid": False}

def test_create_success(tmp_path):
    manager = TransactionManager()
    manager.validation = PassingValidation()
    result = manager.apply(str(tmp_path), [{
        "file": "new.py", "action": "create",
        "old_content": "", "new_content": "x = 1\n"
    }])
    assert result["success"] is True
    assert (tmp_path / "new.py").exists()

def test_create_rollback(tmp_path):
    manager = TransactionManager()
    manager.validation = FailingValidation()
    result = manager.apply(str(tmp_path), [{
        "file": "new.py", "action": "create",
        "old_content": "", "new_content": "x = 1\n"
    }])
    assert result["success"] is False
    assert result["rolled_back"] is True
    assert not (tmp_path / "new.py").exists()
