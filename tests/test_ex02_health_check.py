import ex02_health_check as m


class FakeResp:
    def __init__(self, status_code):
        self.status_code = status_code


def test_returns_true_on_first_2xx(monkeypatch):
    calls = {"n": 0}

    def fake_get(url, timeout):
        calls["n"] += 1
        return FakeResp(200)

    monkeypatch.setattr(m.requests, "get", fake_get)
    monkeypatch.setattr(m.time, "sleep", lambda s: None)  # don't actually wait
    # TODO: assert m.check("http://x", retries=3, timeout=1) is True
    # TODO: assert calls["n"] == 1  (success first try = no retries)
    ...
    assert m.check("http://x", retries=3, timeout=1) is True
    assert calls["n"] == 1


def test_retries_then_gives_up(monkeypatch):
    calls = {"n": 0}

    def fake_get(url, timeout):
        calls["n"] += 1
        raise m.requests.RequestException("boom")

    monkeypatch.setattr(m.requests, "get", fake_get)
    monkeypatch.setattr(m.time, "sleep", lambda s: None)
    # TODO: assert m.check("http://x", retries=3, timeout=1) is False
    # TODO: assert calls["n"] == 3  (tried the full budget)
    ...
    assert m.check("http://x", retries=3, timeout=1) is False
    assert calls["n"] == 3
