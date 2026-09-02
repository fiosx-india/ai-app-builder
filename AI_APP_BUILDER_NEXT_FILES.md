# AI APP BUILDER — NEXT FILES & FOLDER PLAN

Repository:
fiosx-india/ai-app-builder

## 1. CURRENT STATUS CHECK

The current repository already contains:

backend/
  app/
    ai_engine.py
    main.py
    patch_engine.py
    validation_engine.py
  requirements.txt

Also present:
.gitignore
README.md

IMPORTANT:
main.py imports ApprovalEngine, but approval_engine.py is currently missing.
This must be added before the backend can run correctly.

## 2. IMMEDIATE FILE TO ADD

Path:
backend/app/approval_engine.py

Purpose:
Human approval gate. AI-generated changes must remain pending until the user approves them.

Code:

```python
from uuid import uuid4
from typing import Any, Dict


class ApprovalEngine:
    """Controls explicit human approval before project changes are applied."""

    def __init__(self) -> None:
        self.requests: Dict[str, Dict[str, Any]] = {}

    def create_request(self, plan: Dict[str, Any]) -> Dict[str, Any]:
        approval_id = str(uuid4())

        approval = {
            "id": approval_id,
            "status": "pending",
            "plan": plan,
        }

        self.requests[approval_id] = approval
        return approval

    def get_request(self, approval_id: str) -> Dict[str, Any]:
        if approval_id not in self.requests:
            raise ValueError("Approval request not found")

        return self.requests[approval_id]

    def approve(self, approval_id: str) -> Dict[str, Any]:
        request = self.get_request(approval_id)
        request["status"] = "approved"
        return request

    def reject(self, approval_id: str) -> Dict[str, Any]:
        request = self.get_request(approval_id)
        request["status"] = "rejected"
        return request
```

## 3. REQUIRED SUPPORT FILE

Path:
backend/app/__init__.py

Purpose:
Marks the app directory as a Python package and keeps imports predictable.

For now this file can be empty.

## 4. NEXT CORE FILES

Create these in backend/app/:

project_manager.py
Purpose: Create projects, inspect files, track project paths, and protect project boundaries.

models.py
Purpose: Shared data models for commands, plans, changes, approvals, validation results, and errors.

github_manager.py
Purpose: GitHub repository/branch/commit operations.

change_analyzer.py
Purpose: Determine exactly which file/function/section must change.

patch_engine.py
Purpose: Apply the smallest possible patch. Never rewrite unrelated code.

backup_manager.py
Purpose: Create a recoverable version before approved changes.

dependency_analyzer.py
Purpose: Detect imports, dependencies, and affected files before a change.

test_engine.py
Purpose: Run syntax, lint, unit, build, and integration checks.

error_intelligence.py
Purpose: Convert raw errors into file + line + cause + impact + recommended fix.

sandbox_runner.py
Purpose: Execute generated code in an isolated environment.

project_memory.py
Purpose: Store project history, decisions, changes, approvals, and validation results.

deployment_manager.py
Purpose: Prepare and control deployment only after validation succeeds.

## 5. TEST FILES

Create:

tests/
  __init__.py
  test_validation_engine.py
  test_patch_engine.py
  test_approval_engine.py
  test_project_manager.py

Every important safety rule must have automated tests.

## 6. FRONTEND FILES — LATER PHASE

Create:

frontend/
  package.json
  src/
    main.jsx
    App.jsx
    components/
    pages/
    services/
    store/
    styles/

The frontend will eventually contain:

- AI command box
- project explorer
- code editor
- live preview
- change review
- approval buttons
- validation/error panel
- project history
- terminal/log viewer

## 7. NON-NEGOTIABLE SAFETY RULES

1. Never delete the whole project because of a local error.
2. Never rewrite an entire file when a smaller patch is sufficient.
3. Identify the exact affected file and code region.
4. Preserve unrelated code.
5. Create a recoverable version before significant changes.
6. Validate generated changes before applying them.
7. Do not deploy when validation fails.
8. Show errors with file, line, type, cause, impact, and suggested fix.
9. A failed automatic fix must be rolled back or remain unapplied.
10. Destructive actions require explicit user approval.

## 8. IMPORTANT NOTE ABOUT CURRENT patch_engine.py

The current implementation checks whether the entire old_content exists inside new_content.

That is too strict for a real minimal-patch system.

It should eventually be replaced with a proper diff/patch mechanism that:

- targets exact lines or AST nodes
- verifies the expected old text
- changes only the requested region
- detects unexpected surrounding changes
- rejects broad rewrites
- supports rollback

Do NOT remove the current safety layer until the replacement is tested.

## 9. DEVELOPMENT ORDER

Phase 1:
ApprovalEngine + package initialization + tests

Phase 2:
ProjectManager + Models + ProjectScanner

Phase 3:
ChangeAnalyzer + improved PatchEngine + BackupManager

Phase 4:
ValidationEngine + TestEngine + ErrorIntelligence

Phase 5:
GitHubManager + branch/commit workflow

Phase 6:
OpenAI integration

Phase 7:
Code editor + AI command UI

Phase 8:
Live preview + sandbox runner

Phase 9:
Deployment manager

Phase 10:
Advanced multi-agent development system

## 10. GOLDEN WORKFLOW

USER COMMAND
    ↓
AI ANALYSIS
    ↓
PROJECT SCAN
    ↓
DEVELOPMENT PLAN
    ↓
CHANGE ANALYSIS
    ↓
APPROVAL
    ↓
BACKUP / BRANCH
    ↓
MINIMAL PATCH
    ↓
VALIDATION
    ↓
TESTS
    ↓
ERROR?
  YES → AI FIX → VALIDATE AGAIN
  NO  → CONTINUE
    ↓
FINAL APPROVAL
    ↓
COMMIT
    ↓
DEPLOY

The system must never claim success unless the relevant validation actually passes.
