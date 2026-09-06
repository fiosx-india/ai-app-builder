from backend.app.approval_engine import ApprovalEngine
from backend.app.workflow_engine import WorkflowEngine


class FakeScanner:
    def scan(self, project_path):
        return {"file_count": 1}


class FakeAI:
    def create_plan(self, command, project_path):
        return {"architecture": {}, "affected_files": ["safe.py"]}


class FakeGenerator:
    def propose(self, *args, **kwargs):
        return {
            "risk": "low",
            "changes": [{
                "file": "safe.py",
                "action": "modify",
                "old_content": "x = 1\n",
                "new_content": "x = 2\n",
            }],
        }


class FakeTransaction:
    def apply(self, project_path, changes):
        return {
            "success": True,
            "validation": {
                "valid": True,
                "tests": {"passed": True},
            },
        }


class FakeImpact:
    def analyze(self, project_path, changed_file):
        return {"changed_file": changed_file, "impacted_files": [changed_file]}


class FakeScope:
    def inspect_plan(self, changes, approved_files):
        return {"allowed": True}


def test_workflow_blocks_protected_file(tmp_path):
    engine = WorkflowEngine(approval_engine=ApprovalEngine())
    engine.scanner = FakeScanner()
    engine.ai_engine = FakeAI()
    engine.code_generator = FakeGenerator()

    engine.code_generator.propose = lambda *a, **k: {
        "risk": "low",
        "changes": [{
            "file": ".env",
            "action": "modify",
            "old_content": "A=1\n",
            "new_content": "A=2\n",
        }],
    }

    created = engine.create_plan("change env", str(tmp_path))
    engine.approve(created["approval_id"])
    result = engine.apply_approved_plan(created["approval_id"])

    assert result["transaction"]["stage"] == "security_blocked"


def test_workflow_release_gate_passes(monkeypatch, tmp_path):
    engine = WorkflowEngine(approval_engine=ApprovalEngine())
    engine.scanner = FakeScanner()
    engine.ai_engine = FakeAI()
    engine.code_generator = FakeGenerator()
    engine.transaction = FakeTransaction()
    engine.dependency_impact_engine = FakeImpact()

    monkeypatch.setattr(
        "backend.app.workflow_engine.ChangeScopeGuard",
        lambda project_path: FakeScope(),
    )

    created = engine.create_plan("change safe file", str(tmp_path))
    engine.approve(created["approval_id"])
    result = engine.apply_approved_plan(created["approval_id"])

    assert result["transaction"]["success"] is True
    assert result["transaction"]["risk_gate"]["allowed"] is True
    assert result["plan"]["workflow"]["deployment_allowed"] is True
