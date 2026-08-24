from pathlib import Path

from northsource_pipeline import http


class _FakeResponse:
    def __init__(self, body: bytes, status: int = 200):
        self._body = body
        self.status_code = status

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False

    def raise_for_status(self):
        if self.status_code >= 400:
            raise http.requests.HTTPError(f"status {self.status_code}")

    def iter_content(self, chunk_size):
        yield self._body


def test_download_writes_file(tmp_path: Path, monkeypatch):
    calls = []

    def fake_get(url, **kwargs):
        calls.append(url)
        return _FakeResponse(b"hello")

    monkeypatch.setattr(http.requests, "get", fake_get)
    dest = tmp_path / "a.txt"
    assert http.download("http://x/a", dest) == dest
    assert dest.read_bytes() == b"hello"
    assert calls == ["http://x/a"]
    assert not (tmp_path / "a.txt.part").exists()


def test_download_skips_existing(tmp_path: Path, monkeypatch):
    dest = tmp_path / "a.txt"
    dest.write_bytes(b"old")

    def fake_get(url, **kwargs):
        raise AssertionError("must not download")

    monkeypatch.setattr(http.requests, "get", fake_get)
    assert http.download("http://x/a", dest) == dest
    assert dest.read_bytes() == b"old"


def test_download_http_error_leaves_no_file(tmp_path: Path, monkeypatch):
    monkeypatch.setattr(http.requests, "get", lambda url, **kw: _FakeResponse(b"", 404))
    dest = tmp_path / "a.txt"
    try:
        http.download("http://x/a", dest)
    except http.requests.HTTPError:
        pass
    else:
        raise AssertionError("expected HTTPError")
    assert not dest.exists()
