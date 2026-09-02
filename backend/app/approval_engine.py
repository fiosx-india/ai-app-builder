from typing import Any, Dict
from uuid import uuid4

class ApprovalEngine:
    def __init__(self):
        self.requests: Dict[str, Dict[str, Any]] = {}

    def create_request(self, plan):
        approval_id = str(uuid4())
        approval = {"id": approval_id, "status": "pending", "plan": plan}
        self.requests[approval_id] = approval
        return approval

    def get_request(self, approval_id):
        if approval_id not in self.requests:
            raise ValueError("Approval request not found")
        return self.requests[approval_id]

    def approve(self, approval_id):
        approval = self.get_request(approval_id)
        if approval["status"] != "pending":
            raise ValueError("Only pending approvals can be approved")
        approval["status"] = "approved"
        return approval

    def reject(self, approval_id):
        approval = self.get_request(approval_id)
        if approval["status"] != "pending":
            raise ValueError("Only pending approvals can be rejected")
        approval["status"] = "rejected"
        return approval
