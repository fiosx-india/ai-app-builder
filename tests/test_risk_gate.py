from backend.app.risk_gate import RiskGate

def test_deploy_gate_passes_when_all_checks_pass():
    result = RiskGate().can_deploy(
        risk="medium",
        validation_passed=True,
        tests_passed=True,
        security_passed=True,
        user_approved=True,
    )
    assert result["allowed"] is True

def test_deploy_gate_blocks_failed_tests():
    result = RiskGate().can_deploy(
        risk="low",
        validation_passed=True,
        tests_passed=False,
        security_passed=True,
        user_approved=True,
    )
    assert result["allowed"] is False
