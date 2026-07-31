from pathlib import Path

from ex01_log_aggregator import aggregate

FIXTURES = Path(__file__).parent / "fixtures"


# --- reference test: pure function, in-memory input ---
def test_counts_ips_and_5xx():
    lines = [
        '10.0.0.1 - - [t] "GET / HTTP/1.1" 200 1 "-" "-"',
        '10.0.0.1 - - [t] "GET / HTTP/1.1" 500 1 "-" "-"',
        '10.0.0.2 - - [t] "GET / HTTP/1.1" 503 1 "-" "-"',
    ]
    ips, fivexx = aggregate(lines)
    assert ips["10.0.0.1"] == 2
    assert ips.most_common(1)[0] == ("10.0.0.1", 2)
    assert fivexx == 2


# --- Part B, your turn: same idea, sourced from the fixture file ---
def test_against_fixture_file():
    lines = (FIXTURES / "access.log").read_text().splitlines()
    ips, fivexx = aggregate(lines)
    # TODO: assert the known counts — 10.0.0.1 -> 3, 10.0.0.2 -> 2, 5xx total -> 3
    ...
    assert ips["10.0.0.1"] == 3
    assert ips["10.0.0.2"] == 2
    assert fivexx == 3
