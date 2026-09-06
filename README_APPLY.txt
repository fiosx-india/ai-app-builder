AI APP BUILDER - SECURITY + END-TO-END PATCH

REPLACE:
- backend/app/security_manager.py
- backend/app/workflow_engine.py

ADD:
- tests/test_security_manager.py
- tests/test_workflow_engine.py

IMPORTANT:
This patch uses the existing SecurityManager, RiskGate, ChangeScopeGuard,
DependencyImpactEngine and TransactionManager. It does not create a second
orchestration layer.

After applying:
1. Run: pytest -q
2. Run your backend startup command.
3. Send the complete output for final release-readiness verification.

If workflow_engine.py has additional custom changes in your latest GitHub
version, keep a backup before overwrite and report any merge conflict.
