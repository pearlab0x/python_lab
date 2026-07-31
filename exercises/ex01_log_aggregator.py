#!/usr/bin/env python3
"""Exercise 1 — Log aggregator.

Parse an nginx access log; print the top 10 client IPs by request count, and a
total count of 5xx responses.

Usage:      ./ex01_log_aggregator.py access.log
Done when:  top 10 IPs printed most-frequent-first; total 5xx printed;
            exits 0 on success, non-zero if the file can't be read.
"""

import re
import sys
from collections import Counter
from pathlib import Path

LOG_RE = re.compile(
    r"""
    ^(\S+)          # client IP
    .*              # skip timestamp etc.
    "[A-Z]+\ [^"]*" # the quoted request line
    \ (\d{3})       # status code
""",
    re.VERBOSE,
)


def aggregate(lines: list[str]) -> tuple[Counter[str], int]:
    """Return (ip_counts, count_of_5xx). Pure function -> easy to unit-test."""
    ip_counts: Counter[str] = Counter()
    fivexx = 0
    for line in lines:
        # TODO: pull the client IP (first field) and status code from each line.
        #   combined format: IP - - [time] "GET /path HTTP/1.1" 200 1234 "..." "..."
        #   a regex or a careful .split() both work; a 5xx starts with "5".
        ...
        m = LOG_RE.match(line)
        if not m:
            continue
        ip, status = m.group(1), m.group(2)
        ip_counts[ip] += 1
        if status.startswith("5"):
            fivexx += 1
    return ip_counts, fivexx

    return ip_counts, fivexx


def main() -> int:
    if len(sys.argv) != 2:
        print(f"usage: {sys.argv[0]} <access.log>", file=sys.stderr)
        return 2
    path = Path(sys.argv[1])
    # TODO: read the file, call aggregate(), print top 10 + the 5xx total.
    try:
        lines = path.read_text().splitlines()
    except OSError as e:
        print(f"cannot read {path}: {e}", file=sys.stderr)
        return 1

    ip_counts, fivexx = aggregate(lines)

    print("Top IPs:")
    for ip, count in ip_counts.most_common(10):
        print(f"  {count:>6} {ip}")
    print(f"\nTotal 5xx responses: {fivexx}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
