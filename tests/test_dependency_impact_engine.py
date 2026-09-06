from backend.app.dependency_impact_engine import DependencyImpactEngine

def test_detects_direct_dependent(tmp_path):
    (tmp_path / "changed.py").write_text("VALUE = 1\n", encoding="utf-8")
    (tmp_path / "consumer.py").write_text("import changed\n", encoding="utf-8")

    result = DependencyImpactEngine().analyze(
        str(tmp_path),
        "changed.py",
    )

    assert "changed.py" in result["impacted_files"]
    assert "consumer.py" in result["direct_dependents"]
