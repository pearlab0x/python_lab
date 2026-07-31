# Python for Infrastructure & Systems Engineers

The companion to `bash-for-infra.md`. Where the bash tutorial ended — *"once your
scripts exceed ~150 lines, or need JSON/HTTP/state, rewrite in Python"* — this one
begins. Same infra tasks, same production-safe mindset, but leaning into the things
Python is actually good at: structured data, HTTP, real error handling, and code you
can test.

The goal is parity. After the bash lab you can write a safe disk-alert script in 20
lines of shell; after this one you can write the version that hits the Prometheus API,
parses the JSON, and pages you on Discord — and you know *which* of those two a given
task calls for. Knowing where the line sits is the senior signal.

---

## 0. The framing answer: Bash vs Python

Interviewers open with this. There's a scoring answer:

- **Bash** — Linux glue. Short (<~50 line) tasks orchestrating existing CLI tools,
  one-liners in CI steps, anything that's mostly "run these commands in order."
- **Python** — when the logic gets real: parsing structured data (JSON/YAML), HTTP
  APIs, ret, state, anything you'd want to *test*, anything with non-trivial data
  structures or arithmetic.
- **The line that lands:** *"the moment I'm reaching for arrays or arithmetic in bash,
  that's my cue to switch to Python."*

You do a version of this daily at team.blue. Anchor answers to that: "I'd write the
quick check in bash as an Alertmanager textfile collector, but the moment it needs to
query an API and branch on the response, it's a Python job."

---

## 1. Running scripts properly

A script is not a REPL dump. Structure every one the same way:

```python
#!/usr/bin/env python3
"""One-line description of what this does."""

import sys


def main() -> int:
    # real work here
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

Three things to internalize:

- **The `if __name__ == "__main__"` guard** — lets the file be both a runnable script
  *and* an importable module (so your functions are testable). This is the Python
  equivalent of keeping logic in bash functions instead of top-level soup.
- **`main()` returns an int, `sys.exit()` uses it** — that's your exit code, same
  contract as bash. `0` = success, non-zero = failure. Monitoring reads this.
- **The docstring** — free `--help` fodder and the first thing a reviewer reads.

Make it executable and run it like any other tool:

```bash
chmod +x check_disk.py
./check_disk.py
```

---

## 2. The environment discipline (Python's `set -euo pipefail`)

In bash, hygiene is `set -euo pipefail` + `shellcheck`. In Python, hygiene is a
**virtual environment** + a **linter/formatter**. Never install packages globally, never
`sudo pip`. One venv per project:

```bash
python -m venv .venv          # create
source .venv/bin/activate     # activate (bash/zsh)
python -m pip install --upgrade pip
```

Your prompt shows `(.venv)` when it's active. `deactivate` to leave. The `.venv/`
directory is gitignored — you commit the *list* of dependencies, not the packages.

Pin dependencies so the environment is reproducible:

```bash
pip install requests
pip freeze > requirements.txt      # snapshot exact versions
# later, on another box:
pip install -r requirements.txt
```

This is the whole reason "works on my machine" stops being a problem — and it's a
guaranteed interview talking point. On pearlabs you already think this way with Docker
images; a venv is the same idea one level down.

---

## 3. The types you actually use

Bash has strings and (clumsily) arrays. Python gives you real data structures, and
picking the right one is half of writing clean infra code.

```python
# str — f-strings are the only formatting you need
host = "web01"
pct = 92
print(f"ALERT: {host} at {pct}%")          # ALERT: web01 at 92%

# list — ordered, mutable. Your "array."
services = ["nginx", "sshd", "cron"]
services.append("postfix")

# dict — key/value. The workhorse for structured data / JSON.
host_info = {"name": "web01", "cores": 4, "role": "frontend"}
host_info["cores"]                          # 4
host_info.get("missing", "default")         # safe access, no KeyError

# set — membership + dedup, fast.
seen = set()
seen.add("10.0.0.1")
"10.0.0.1" in seen                          # True — O(1) lookup
```

The `dict` is the one to be fluent in — every JSON API response, every parsed config,
every log line you structure ends up as a dict.

---

## 4. Files & paths — use `pathlib`

Forget string-concatenating paths. `pathlib.Path` is the modern, safe way:

```python
from pathlib import Path

log_dir = Path("/var/log/myapp")
for logfile in log_dir.glob("*.log"):       # like `find -name '*.log'`
    print(logfile, logfile.stat().st_size)

# reading — context manager closes the file even on error
with open("hosts.txt") as f:
    hosts = [line.strip() for line in f if line.strip() and not line.startswith("#")]
```

That last line is the Python version of the bash `while IFS= read -r host; [[ -z ... ]]
&& continue` dance — one readable line, skipping blanks and comments. The `with`
statement is your `trap ... EXIT` for files: cleanup is guaranteed.

---

## 5. Error handling — fail loud, exit clean

Bash fails loud with `set -e`. Python fails loud by *default* — an unhandled exception
crashes with a stack trace and a non-zero exit. Your job is to catch what you can
handle and let the rest surface:

```python
import sys

def read_threshold(path: str) -> int:
    try:
        with open(path) as f:
            return int(f.read().strip())
    except FileNotFoundError:
        print(f"config not found: {path}", file=sys.stderr)
        sys.exit(2)
    except ValueError:
        print(f"config not an integer: {path}", file=sys.stderr)
        sys.exit(3)
```

Rules that read as senior:

- **Catch specific exceptions**, never bare `except:`. `except Exception` at most, and
  only at the top level to log-and-exit.
- **Write errors to `stderr`** (`file=sys.stderr`) — same discipline as bash `>&2`.
- **Distinct exit codes** for distinct failures — makes the script scriptable by other
  scripts.
- **`finally` / `with`** for cleanup that must always run.

---

## 6. `subprocess` — done right

This is the single most-tested Python-for-ops skill, because it's the most abused.
Shelling out is fine; doing it unsafely is the red flag.

```python
import subprocess

# GOOD: list args (no shell), fail loud, capture output, timeout
result = subprocess.run(
    ["systemctl", "is-active", "nginx"],
    capture_output=True,
    text=True,
    timeout=10,
    check=False,            # is-active returns non-zero when inactive — that's data, not an error
)
active = result.stdout.strip() == "active"
```

The four things interviewers watch for:

- **List args, not a string.** `["ls", "-l", path]` — never `f"ls -l {path}"` with
  `shell=True`. String + `shell=True` + any external input = shell injection. This is
  *the* question.
- **`check=True`** raises `CalledProcessError` on non-zero exit — use it when non-zero
  genuinely means failure. Use `check=False` and inspect `returncode` when non-zero is
  meaningful data (like `is-active`).
- **`timeout=`** so a hung command can't hang your script.
- **`text=True`** gives you `str` instead of `bytes`.

If someone reaches for `os.system()`, that's a "hasn't written production Python" tell.

---

## 7. Text processing — `re`, `csv`, and knowing when *not* to

Bash gives you `awk`/`sed`/`grep`. Python's equivalents are richer but you shouldn't
always reach for them — for a quick grep, bash is still faster to write.

```python
import re
from collections import Counter

# Count 5xx responses and top talkers from an access log — the classic.
ip_counts: Counter[str] = Counter()
status_counts: Counter[str] = Counter()

with open("access.log") as f:
    for line in f:
        m = re.match(r'(\S+).*"\s+(\d{3})\s', line)
        if m:
            ip, status = m.group(1), m.group(2)
            ip_counts[ip] += 1
            if status.startswith("5"):
                status_counts[status] += 1

for ip, n in ip_counts.most_common(5):
    print(f"{n:>6}  {ip}")
```

`collections.Counter` with `.most_common()` is the pattern that replaces
`sort | uniq -c | sort -rn` — and it's cleaner once you're also branching on the data.
For CSV, use the `csv` module (handles quoting/escaping); never `line.split(",")`.

---

## 8. Structured data — JSON is why you're here

This is the capability bash simply doesn't have. Anything with JSON should be Python.

```python
import json

# parse
with open("config.json") as f:
    config = json.load(f)          # -> dict
threshold = config["disk"]["threshold"]

# produce (e.g. for a node_exporter textfile collector or an API call)
payload = {"host": "web01", "status": "critical", "pct": 92}
print(json.dumps(payload, indent=2))
```

For YAML (Ansible, k8s, Compose land) it's the same shape with `yaml.safe_load()` from
`pyyaml` — always `safe_load`, never `load`, which can execute arbitrary objects.

---

## 9. HTTP — talking to APIs

The other bash-can't-really-do-this domain. `requests` is the ergonomic choice
(`pip install requests`); the stdlib `urllib` works with zero deps if you can't install.

```python
import requests

resp = requests.get(
    "http://prometheus:9090/api/v1/query",
    params={"query": 'node_filesystem_avail_bytes{mountpoint="/"}'},
    timeout=10,
)
resp.raise_for_status()            # loud on 4xx/5xx — your fail-fast
data = resp.json()                 # -> dict, already parsed

for result in data["data"]["result"]:
    instance = result["metric"]["instance"]
    avail = float(result["value"][1])
    print(f"{instance}: {avail / 1e9:.1f} GB free")
```

`timeout=` and `raise_for_status()` are the non-negotiables — a script that hangs
forever or silently ignores a 500 is the thing you're being tested against. This exact
pattern — query Prometheus, branch on the result — is your real pearlabs stack, so lead
with that when it comes up.

---

## 10. Logging — not `print`

For anything scheduled or long-running, use the `logging` module. It gives you levels,
timestamps, and a stderr/file split for free:

```python
import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
)
log = logging.getLogger(__name__)

log.info("starting disk check")
log.warning("web01 at 92%%")
log.error("prometheus unreachable")
```

Rule of thumb: `print()` for a tool's actual *output* (the thing a pipe consumes),
`logging` for diagnostics about the run. Mixing them up (diagnostics on stdout) breaks
scripts that consume your output.

---

## 11. Putting it together: infra-flavored scripts

The same four scripts from the bash lab, rebuilt in Python — plus one that only Python
can do. Compare each to its bash twin; the point is to *feel* where Python earns its
keep and where it's overkill.

### 11.1 Disk-usage alert across mount points

```python
#!/usr/bin/env python3
"""Alert on mount points at or above a usage threshold."""
import shutil
import sys
from pathlib import Path


def main() -> int:
    threshold = int(sys.argv[1]) if len(sys.argv) > 1 else 85
    alerted = False

    # read real mounts from /proc/mounts, skip pseudo-filesystems
    for line in Path("/proc/mounts").read_text().splitlines():
        dev, mount, fstype, *_ = line.split()
        if fstype in {"proc", "sysfs", "tmpfs", "devtmpfs", "cgroup2"}:
            continue
        try:
            usage = shutil.disk_usage(mount)
        except (PermissionError, FileNotFoundError):
            continue
        pct = round(usage.used / usage.total * 100)
        if pct >= threshold:
            print(f"ALERT: {mount} at {pct}% ({dev})", file=sys.stderr)
            alerted = True

    return 1 if alerted else 0


if __name__ == "__main__":
    sys.exit(main())
```

Compare to the bash `df | while read` version: bash was *shorter* here. That's the
lesson — for a pure "walk mounts, check a number" task, bash wins. Python pulls ahead
the moment you want to emit JSON, hit an API, or unit-test the threshold logic.

### 11.2 Check a list of services and report

```python
#!/usr/bin/env python3
"""Report on systemd service status; non-zero exit if any are down."""
import subprocess
import sys

SERVICES = ["nginx", "sshd", "cron"]


def is_active(svc: str) -> bool:
    result = subprocess.run(
        ["systemctl", "is-active", "--quiet", svc],
        timeout=10,
        check=False,
    )
    return result.returncode == 0


def main() -> int:
    failed = [svc for svc in SERVICES if not is_active(svc)]
    for svc in SERVICES:
        print(f"[ OK ] {svc}" if svc not in failed else f"[FAIL] {svc}",
              file=sys.stderr if svc in failed else sys.stdout)
    if failed:
        print(f"Failed services: {', '.join(failed)}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

### 11.3 Run a command across many hosts

```python
#!/usr/bin/env python3
"""Run `uptime` across hosts listed in hosts.txt."""
import subprocess
import sys
from pathlib import Path


def main() -> int:
    hosts = [
        h.strip() for h in Path("hosts.txt").read_text().splitlines()
        if h.strip() and not h.startswith("#")
    ]
    for host in hosts:
        print(f"=== {host} ===")
        try:
            result = subprocess.run(
                ["ssh", "-o", "ConnectTimeout=5", "-o", "BatchMode=yes", host, "uptime"],
                capture_output=True, text=True, timeout=15, check=True,
            )
            print(result.stdout.strip())
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired):
            print(f"  unreachable: {host}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

Serial, like the bash version. The Python upgrade path is real, though: swap the loop
for `concurrent.futures.ThreadPoolExecutor` and you're hitting all hosts in parallel —
something that's genuinely painful in bash. Mention that as the "in production I'd..."
follow-up. (For real fleet work it's Ansible, but knowing the primitive matters.)

### 11.4 Log cleanup with a dry-run flag

```python
#!/usr/bin/env python3
"""Delete *.log files older than N days. Dry-run by default; --apply to delete."""
import argparse
import sys
import time
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("log_dir", type=Path)
    parser.add_argument("--days", type=int, default=30)
    parser.add_argument("--apply", action="store_true", help="actually delete")
    args = parser.parse_args()

    if not args.log_dir.is_dir():
        print(f"not a directory: {args.log_dir}", file=sys.stderr)
        return 2

    cutoff = time.time() - args.days * 86400
    for f in args.log_dir.glob("*.log"):
        if f.stat().st_mtime < cutoff:
            if args.apply:
                f.unlink()
                print(f"deleted: {f}")
            else:
                print(f"would delete: {f}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

Note `argparse` — this is where Python decisively beats bash. You get `--help`, type
coercion, and validation for free, versus hand-parsing `$1`/`$2`. The dry-run-by-default
discipline carries straight over from the bash lab.

### 11.5 Query Prometheus and alert (the Python-only one)

```python
#!/usr/bin/env python3
"""Query Prometheus for filesystems below a free-space threshold and report."""
import argparse
import sys

import requests

PROM = "http://localhost:9090"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--min-gb", type=float, default=5.0)
    args = parser.parse_args()

    try:
        resp = requests.get(
            f"{PROM}/api/v1/query",
            params={"query": 'node_filesystem_avail_bytes{fstype!~"tmpfs|overlay"}'},
            timeout=10,
        )
        resp.raise_for_status()
    except requests.RequestException as e:
        print(f"prometheus query failed: {e}", file=sys.stderr)
        return 2

    breaches = []
    for r in resp.json()["data"]["result"]:
        avail_gb = float(r["value"][1]) / 1e9
        if avail_gb < args.min_gb:
            inst = r["metric"].get("instance", "?")
            mount = r["metric"].get("mountpoint", "?")
            breaches.append(f"{inst}{mount}: {avail_gb:.1f} GB free")

    for b in breaches:
        print(f"LOW DISK: {b}", file=sys.stderr)
    return 1 if breaches else 0


if __name__ == "__main__":
    sys.exit(main())
```

There is no clean bash version of this. JSON parsing, HTTP with timeout and error
handling, arithmetic on the values — this is the whole reason the language exists in
your toolkit. This is the one to demo in an interview.

---

## 12. Quality: the shellcheck equivalents

Bash had `shellcheck`. Python's toolchain, in order of bang-for-buck:

```bash
pip install ruff mypy pytest

ruff check .            # linter — catches bugs, style, unused imports (fast, replaces flake8+isort)
ruff format .           # formatter — replaces black
mypy check_disk.py      # static type checker — catches type bugs before runtime
pytest                  # run your tests
```

**`ruff` is the one to run constantly** — it's the shellcheck of Python and then some.
Type hints (`def main() -> int:`) aren't just documentation; with `mypy` they become
enforced contracts. A tiny test proves the habit:

```python
# test_disk.py
def test_pct_rounding():
    used, total = 92, 100
    assert round(used / total * 100) == 92
```

```bash
pytest -q
```

The workflow *is* the skill: write it, `ruff check` until clean, add a type hint, add
one test. That loop is what "production-safe Python" means, and it's visible in your
commit history.

---

## 13. Practice exercises

Fill these in as separate scripts in the repo. Each maps to real infra work and to a
bash exercise you've already done — do them second in Python and notice the difference.

1. **Log aggregator.** Parse an nginx access log; print the top 10 IPs and a count of
   5xx responses. (Practice: `re`, `Counter`, file iteration.) *Bash twin: the
   `awk`/`sort`/`uniq` pipeline.*
2. **Health check with retries.** Hit an HTTP endpoint; retry up to 3× with exponential
   backoff; exit non-zero if all fail. (Practice: `requests`, loops, `time.sleep`,
   exit codes.)
3. **Config validator.** Read a YAML/JSON config; assert required keys exist and values
   are the right type; print every problem, exit non-zero if any. (Practice: `json`/
   `yaml`, dicts, validation, `stderr`.)
4. **Cert-expiry checker.** Given a list of hostnames, connect and report days until the
   TLS cert expires; warn under 30 days. (Practice: `ssl`, `socket`, `datetime`.)
5. **Metrics exporter.** Gather a few host metrics (load, disk, a service's status) and
   write them in Prometheus textfile-collector format to a `.prom` file. (Practice:
   file writing, string formatting, tying it to your actual monitoring stack.)

For each: structure it with `main()`, run `ruff check` until clean, add type hints and
a `--help` via `argparse`, and write at least one `pytest`. That workflow is the thing
being graded.

---

## 14. Where to go next — and when Python is too much

- **`argparse` → `click`/`typer`** once your CLIs grow subcommands.
- **`requests` → `httpx`** when you need async / HTTP/2.
- **The stdlib docs** (`docs.python.org/3/library/`) — `pathlib`, `subprocess`,
  `collections`, `json`, `logging`, `concurrent.futures` are your daily bread.
- **The upper line, mirroring bash's lower one:** when a script needs to be a long-lived
  daemon, ship as a single static binary, or squeeze real concurrency/latency, that's
  the cue to reach for **Go** — or, more often, to stop writing a script and adopt the
  real tool (Ansible, Prometheus, a proper exporter). Knowing when to *stop* writing
  Python is the same senior signal as knowing when to leave bash.

---

*Keep this file as the README-adjacent reference in `python_lab`. Add each exercise
script alongside it, run `ruff` and `pytest` before every commit, and let the commit
history double as proof of the habit — same as the bash lab, one rung up the ladder.*
