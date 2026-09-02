from typing import Any, Dict
from uuid import uuid4


class FinalApproval:
    """
    Final approval gate before GitHub publication.
    """

    def __init__(self) -> None:
        self.requests: Dict[
            str,
            Dict[str, Any],
        ] = {}

    def create(
        self,
        validation_result: Dict[str, Any],
    ) -> Dict[str, Any]:

        if not validation_result.get(
            "valid"
        ):
            raise ValueError(
                "Final approval cannot be created "
                "because validation failed."
            )

        approval_id = str(uuid4())

        request = {
            "id": approval_id,
            "status": "pending",
            "validation": validation_result,
        }

        self.requests[
            approval_id
        ] = request

        return request

    def approve(
        self,
        approval_id: str,
    ) -> Dict[str, Any]:

        request = self.get(
            approval_id
        )

        if request["status"] != "pending":
            raise ValueError(
                "Only pending final approvals "
                "can be approved."
            )

        request["status"] = "approved"

        return request

    def reject(
        self,
        approval_id: str,
    ) -> Dict[str, Any]:

        request = self.get(
            approval_id
        )

        if request["status"] != "pending":
            raise ValueError(
                "Only pending final approvals "
                "can be rejected."
            )

        request["status"] = "rejected"

        return request

    def get(
        self,
        approval_id: str,
    ) -> Dict[str, Any]:

        if approval_id not in self.requests:
            raise ValueError(
                "Final approval request not found."
            )

        return self.requests[
            approval_id
      ]
