FINAL INTEGRATION FILES

Replace only these files:
1. backend/app/workflow_engine.py

Add these tests:
2. tests/test_dependency_impact_engine.py
3. tests/test_risk_gate.py

Purpose:
- Actually execute DependencyImpactEngine during plan creation.
- Include dependency impact reports in plan analysis.
- Block protected paths such as .env and .git before approval.
- Evaluate RiskGate after transaction validation/tests complete.
- Keep WorkflowEngine as the only orchestration layer.
- Do not create any new production module.

After copying:
pytest -q

Then send the complete test output for final release-readiness review.
