#!/usr/bin/env python3
"""Exercise 2 — Health check with retries.

GET a URL; retry up to N times with exponential backoff; succeed if any attempt
returns 2xx; exit non-zero if all attempts fail.

Usage:      ./ex02_health_check.py https://example.com --retries 3
Done when:  a 2xx exits 0 immediately; failures retry with growing delay
            (1s, 2s, 4s...); all-fail exits non-zero and logs why.
"""

import argparse
import sys
import time

import requests


def check(url: str, retries: int, timeout: float) -> bool:
    delay = 1.0
    for attempt in range(1, retries + 1):
        # TODO: try requests.get(url, timeout=timeout); return True on 2xx.
        #   on failure/non-2xx: sleep(delay), then delay *= 2, and loop.
        #   catch requests.RequestException so a connect error doesn't crash.
        ...
        try:
            resp = requests.get(url, timeout=timeout)
            if 200 <= resp.status_code < 300:
                return True
            print(f"attempt {attempt}: HTTP {resp.status_code}", file=sys.stderr)
        except requests.RequestException as e:
            print(f"attempt {attempt}: {e}", file=sys.stderr)
        if attempt < retries:
            time.sleep(delay)
            delay *= 2
    return False


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("url")
    p.add_argument("--retries", type=int, default=3)
    p.add_argument("--timeout", type=float, default=5.0)
    args = p.parse_args()
    return 0 if check(args.url, args.retries, args.timeout) else 1


if __name__ == "__main__":
    sys.exit(main())
