#!/usr/bin/env python3
"""Exercise 3 — Config validator.

Load a JSON or YAML config; check required keys exist and hold the right type;
print every problem found; exit non-zero if any.

Usage:      ./ex03_config_validator.py config.yaml
Done when:  ALL missing/wrong-typed values reported (each on its own line);
            valid config exits 0; invalid exits non-zero.
"""

import argparse
import json
import sys
from pathlib import Path

SCHEMA = {"host": str, "port": int, "threshold": int, "enabled": bool}


def type_ok(value, expected_type) -> bool:
    if expected_type is bool:
        return isinstance(value, bool)
    if expected_type is int:
        return isinstance(value, int) and not isinstance(value, bool)
    return isinstance(value, expected_type)


def validate(config: dict) -> list[str]:
    """Return a list of human-readable problems. Empty list == valid."""
    problems: list[str] = []
    for key, expected_type in SCHEMA.items():
        # TODO: missing key -> problem; present but wrong type -> problem.
        #   gotcha: bool is a subclass of int, so isinstance(True, int) is True.
        #   handle that so a bool doesn't sneak past an int check (and vice versa).
        ...
        if key not in config:
            problems.append(f"missing required key: {key}")
        elif not type_ok(config[key], expected_type):
            problems.append(
                f"key '{key}' should be {expected_type.__name__} got {type(config[key]).__name__}"
            )
    return problems


def load(path: Path) -> dict:
    text = path.read_text()
    if path.suffix in {".yaml", ".yml"}:
        import yaml  # pip install pyyaml

        return yaml.safe_load(text)
    return json.loads(text)


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("config", type=Path)
    args = p.parse_args()
    # TODO: load(), validate(), print problems to stderr, return 1 if any.
    try:
        config = load(args.config)
    except (OSError, ValueError) as e:
        print(f"cannot load {args.config}: {e}", file=sys.stderr)
        return 2

    problems = validate(config)
    for problem in problems:
        print(f" - {problem}", file=sys.stderr)

    if problems:
        print(f"{len(problems)} problem(s) found", file=sys.stderr)
        return 1
    print("config OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
