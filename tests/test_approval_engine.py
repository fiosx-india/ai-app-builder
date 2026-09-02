import pytest
from backend.app.approval_engine import ApprovalEngine

def test_approval_flow():
    engine = ApprovalEngine()
    item = engine.create_request({"actions": []})
    assert engine.approve(item["id"])["status"] == "approved"

def test_missing_approval():
    with pytest.raises(ValueError):
        ApprovalEngine().get_request("missing")
