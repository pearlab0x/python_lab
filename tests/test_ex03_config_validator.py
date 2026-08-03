from pathlib import Path

import ex03_config_validator as m

FIXTURES = Path(__file__).parent / "fixtures"


def test_valid_config_has_no_problems():
    cfg = {"host": "web01", "port": 8080, "threshold": 85, "enabled": True}
    # TODO: assert m.validate(cfg) == []
    ...
    assert m.validate(cfg)


def test_reports_every_problem():
    cfg = {"host": "web01", "port": "8080", "enabled": 1}
    problems = m.validate(cfg)
    # TODO: assert len(problems) == 3  (missing threshold, port type, enabled type)
    #   and each problem string names its offending key
    ...
    assert len(problems) == 3
    joined = " ".join(problems)
    assert "threshold" in joined
    assert "port" in joined
    assert "enabled" in joined


def test_loader_handles_yaml_and_json():
    valid = m.load(FIXTURES / "config_valid.yaml")
    invalid = m.load(FIXTURES / "config_invalid.json")
    # TODO: assert m.validate(valid) == [] and m.validate(invalid) != []
    ...
    valid = m.load(FIXTURES / "config_valid.yaml")
    invalid = m.load(FIXTURES / "config_invalid.json")
    assert m.validate(valid) == []
    assert m.validate(invalid) == []
