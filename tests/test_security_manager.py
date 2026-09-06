from backend.app.security_manager import SecurityManager


def test_blocks_secret_and_traversal_paths():
    manager = SecurityManager()

    assert manager.inspect_path(".env")["safe_for_ai_write"] is False
    assert manager.inspect_path("keys/server.pem")["safe_for_ai_write"] is False
    assert manager.inspect_path("../outside.py")["safe_for_ai_write"] is False


def test_allows_normal_source_file():
    result = SecurityManager().inspect_path("backend/app/main.py")
    assert result["safe_for_ai_write"] is True


def test_batch_security_result():
    result = SecurityManager().inspect_paths(
        ["backend/app/main.py", ".env.production"]
    )
    assert result["passed"] is False
    assert ".env.production" in result["blocked_paths"]
