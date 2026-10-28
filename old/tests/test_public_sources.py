import socket
import threading

import pytest

from app import public_sources
from app.public_sources import SourceFetch, extract_html, public_target


def _address(ip):
    parsed = ip.split(":")
    if len(parsed) > 1:
        return (socket.AF_INET6, socket.SOCK_STREAM, 6, "", (ip, 443, 0, 0))
    return (socket.AF_INET, socket.SOCK_STREAM, 6, "", (ip, 443))


def test_public_target_pins_a_public_ip_and_normalizes_target(monkeypatch):
    calls = []

    def resolve(host, port, type):
        calls.append((host, port, type))
        return [_address("93.184.216.34")]

    monkeypatch.setattr(public_sources.socket, "getaddrinfo", resolve)

    hostname, addresses, canonical, target = public_target("https://Example.COM/a%20b?q=1#fragment")

    assert hostname == "example.com"
    assert addresses == ["93.184.216.34"]
    assert canonical == "https://example.com/a%20b?q=1"
    assert target == "/a%20b?q=1"
    assert calls == [("example.com", 443, socket.SOCK_STREAM)]


@pytest.mark.parametrize(
    "url",
    [
        "http://example.com/",
        "https://user:secret@example.com/",
        "https://example.com:444/",
        "https://example.com/a\\b",
        "https://example.com/a b",
    ],
)
def test_public_target_rejects_unsafe_url_forms_before_dns(monkeypatch, url):
    def unexpected_dns(*args, **kwargs):
        pytest.fail("unsafe URL reached DNS resolution")

    monkeypatch.setattr(public_sources.socket, "getaddrinfo", unexpected_dns)
    with pytest.raises(ValueError, match="公开来源地址校验失败"):
        public_target(url)


def test_public_target_rejects_private_or_mixed_dns_answers(monkeypatch):
    monkeypatch.setattr(
        public_sources.socket,
        "getaddrinfo",
        lambda *args, **kwargs: [_address("93.184.216.34"), _address("127.0.0.1")],
    )

    with pytest.raises(ValueError, match="非公开地址"):
        public_target("https://example.com/")


@pytest.mark.parametrize("address", ["224.0.0.1", "ff02::1", "0.0.0.0", "255.255.255.255"])
def test_public_target_rejects_non_unicast_even_if_runtime_marks_global(monkeypatch, address):
    monkeypatch.setattr(public_sources.socket, "getaddrinfo", lambda *args, **kwargs: [_address(address)])
    with pytest.raises(ValueError, match="非公开地址"):
        public_target("https://example.com/")


def test_extract_html_keeps_paragraph_locators_and_suppresses_active_content():
    html = b"""<!doctype html><html><head><title>Design &amp; Basis</title>
      <script>fake citation</script><style>.hidden { display:none }</style></head>
      <body><h2>Feed</h2><p>Water &amp; steam at 120 C.</p>
      <noscript>fallback fake citation</noscript><svg><text>fake drawing text</text></svg>
      <script><template>nested fake citation</template>still active</script>
      <p><a rel="license" href="/license">License</a></p>
      <p><a href="http://bad.example/">bad</a></p></body></html>"""

    parsed = extract_html(html, "https://example.org/source/page", "text/html; charset=utf-8")

    assert parsed["title"] == "Design & Basis"
    assert [block["text"] for block in parsed["blocks"]] == [
        "Design & Basis",
        "Feed",
        "Water & steam at 120 C.",
        "License",
        "bad",
    ]
    assert parsed["blocks"][2]["locator"] == {
        "page": None,
        "section": "Feed",
        "paragraph": 3,
    }
    assert all(block["kind"] == "html_text" and block["ocr"] is False for block in parsed["blocks"])
    assert parsed["links"] == [{"url": "https://example.org/license", "text": "License"}]
    assert parsed["license_text"] == ["https://example.org/license"]
    all_text = " ".join(block["text"] for block in parsed["blocks"])
    assert "fake citation" not in all_text
    assert "fake drawing text" not in all_text
    assert "nested fake citation" not in all_text and "still active" not in all_text


def test_extract_html_uses_http_charset_and_rejects_unreliable_decoding():
    raw = "<html><p>苯乙烯设计依据</p></html>".encode("gb2312")

    parsed = extract_html(raw, "https://example.org/spec", "text/html; charset=gb2312")

    assert parsed["encoding"].lower() == "gb2312"
    assert any("苯乙烯设计依据" == block["text"] for block in parsed["blocks"])
    with pytest.raises(ValueError, match="编码不可可靠识别"):
        extract_html(b"<html><p>\xff</p></html>", "https://example.org/spec", "text/html; charset=utf-8")

    meta_declared = "<html><head><meta charset='gb2312'></head><body><p>异丙醇回收</p></body></html>".encode("gb2312")
    assert any(b["text"] == "异丙醇回收" for b in extract_html(meta_declared)["blocks"])


class _Socket:
    def __init__(self):
        self.timeout = None
        self.closed = threading.Event()

    def settimeout(self, value):
        self.timeout = value

    def shutdown(self, _how):
        self.closed.set()

    def close(self):
        self.closed.set()


class _Response:
    def __init__(self, status, headers=(), body=b""):
        self.status = status
        self._headers = list(headers)
        self.body = body
        self.offset = 0
        self.read_calls = 0

    def getheaders(self):
        return self._headers

    def read1(self, size):
        self.read_calls += 1
        part = self.body[self.offset:self.offset+size]
        self.offset += len(part)
        return part


def _fake_connections(monkeypatch, responses):
    resolved = []
    connected = []

    def resolve(host, port, type):
        resolved.append(host)
        return [_address("93.184.216.34")]

    class Connection:
        def __init__(self, hostname, address, timeout):
            connected.append((hostname, address, timeout))
            self.sock = _Socket()
            self.requests = []
            self.closed = False

        def request(self, method, target, headers):
            self.requests.append((method, target, headers))

        def getresponse(self):
            return responses.pop(0)

        def close(self):
            self.closed = True
            self.sock.close()

    monkeypatch.setattr(public_sources.socket, "getaddrinfo", resolve)
    monkeypatch.setattr(public_sources, "PinnedHTTPS", Connection)
    return resolved, connected


def test_fetch_public_redirect_revalidates_target_and_records_peer(monkeypatch):
    resolved, connected = _fake_connections(monkeypatch, [
        _Response(302, [("Location", "https://private.example/secret")]),
    ])

    def resolve(host, port, type):
        resolved.append(host)
        if host == "private.example":
            return [_address("93.184.216.34"), _address("10.0.0.7")]
        return [_address("93.184.216.34")]

    monkeypatch.setattr(public_sources.socket, "getaddrinfo", resolve)
    with pytest.raises(ValueError, match="非公开地址"):
        public_sources.fetch_public("https://public.example/start")
    assert resolved == ["public.example", "private.example"]
    assert connected == [("public.example", "93.184.216.34", pytest.approx(45, abs=1))]


def test_fetch_public_follows_validated_redirect_and_uses_pinned_peer(monkeypatch):
    resolved, connected = _fake_connections(monkeypatch, [
        _Response(301, [("Location", "/archive/source")]),
        _Response(200, [("Content-Type", "text/plain; charset=utf-8"), ("Content-Length", "4")], b"data"),
    ])

    result = public_sources.fetch_public("https://example.org/current", timeout=3)

    assert result["content"] == b"data"
    assert result["final_url"] == "https://example.org/archive/source"
    assert [row["status"] for row in result["redirects"]] == [301, 200]
    assert resolved == ["example.org", "example.org"]
    assert [item[1] for item in connected] == ["93.184.216.34", "93.184.216.34"]


def test_pinned_https_connect_uses_ip_and_original_hostname_for_tls(monkeypatch):
    raw = _Socket()
    calls = []
    connection = public_sources.PinnedHTTPS("example.org", "93.184.216.34", 2)
    wrapped = _Socket()

    monkeypatch.setattr(public_sources.socket, "create_connection", lambda target, timeout: calls.append((target, timeout)) or raw)
    monkeypatch.setattr(connection._context, "wrap_socket", lambda sock, server_hostname: calls.append((sock, server_hostname)) or wrapped)

    connection.connect()

    assert calls[0][0] == ("93.184.216.34", 443)
    assert calls[1] == (raw, "example.org")
    assert connection.sock is wrapped
    connection.close()


def test_fetch_public_enforces_declared_and_streamed_size_caps(monkeypatch):
    _, _ = _fake_connections(monkeypatch, [_Response(200, [("Content-Length", "6")], b"123456")])
    with pytest.raises(ValueError, match="超过25 MiB限制"):
        public_sources.fetch_public("https://example.org/large", max_bytes=5)

    _, _ = _fake_connections(monkeypatch, [_Response(200, [], b"123456")])
    with pytest.raises(ValueError, match="超过25 MiB限制"):
        public_sources.fetch_public("https://example.org/large", max_bytes=5)


def test_fetch_public_deadline_interrupts_slow_drip_body(monkeypatch):
    sock = _Socket()

    class SlowResponse(_Response):
        def read1(self, size):
            assert sock.closed.wait(0.5), "watchdog did not interrupt response read"
            raise socket.timeout("deadline")

    monkeypatch.setattr(public_sources.socket, "getaddrinfo", lambda *args, **kwargs: [_address("93.184.216.34")])

    class Connection:
        def __init__(self, *args):
            self.sock = sock

        def request(self, *args, **kwargs):
            pass

        def getresponse(self):
            return SlowResponse(200)

        def close(self):
            sock.close()

    monkeypatch.setattr(public_sources, "PinnedHTTPS", Connection)
    with pytest.raises(ValueError, match="连接失败|超过45秒"):
        public_sources.fetch_public("https://example.org/slow", timeout=0.03)


def test_extract_html_fails_instead_of_silently_truncating_over_limit():
    raw = ("<p>x</p>" * 10001).encode()

    with pytest.raises(ValueError, match="超过提取限制"):
        extract_html(raw, "https://example.org/large", "text/html; charset=utf-8")


def test_import_source_persists_original_quote_and_retrieval_provenance(monkeypatch):
    import app.documents
    import app.fulltext

    content = b"<html><p>Design pressure is 2 bar.</p></html>"
    requested = "https://example.org/design-basis"
    final = "https://example.org/archive/design-basis"
    captured = {}
    fake_artifact = {"id": "artifact-1", "kind": "html", "metadata": {}}

    monkeypatch.setattr(
        public_sources,
        "fetch_public",
        lambda url: {
            "content": content,
            "final_url": final,
            "redirects": [{"url": requested, "peer_ip": "93.184.216.34", "status": 301}],
            "headers": {"content-type": "text/html; charset=utf-8", "etag": '"v1"'},
        },
    )

    def ingest(project_id, name, raw, **kwargs):
        captured.update(project_id=project_id, name=name, raw=raw, **kwargs)
        return {"id": "artifact-1"}

    monkeypatch.setattr(app.documents, "ingest", ingest)
    monkeypatch.setattr(app.documents, "public_artifact", lambda row: {"id": row["id"], "kind": "html"})
    monkeypatch.setattr(public_sources, "one", lambda *args: fake_artifact)
    monkeypatch.setattr(app.fulltext, "extract_document", lambda project_id, request: {
        "snapshot_id": "snapshot-1",
        "blocks": [{"id": "b00001", "text": "Design pressure is 2 bar."}],
        "request": request,
    })

    result = public_sources.import_source(
        "project-1", SourceFetch(url=requested, purpose="Verify design basis pressure")
    )

    source = captured["metadata_extra"]["public_source"]
    assert captured["project_id"] == "project-1"
    assert captured["raw"] == content
    assert captured["name"].endswith(".html")
    assert source["requested_url"] == requested
    assert source["source_url"] == final
    assert source["purpose"] == "Verify design basis pressure"
    assert source["redirects"][0]["peer_ip"] == "93.184.216.34"
    assert source["headers"]["etag"] == '"v1"'
    assert source["license_status"] == "unknown"
    assert source["authenticity_review"] == "not_reviewed"
    assert captured["html_extraction"]["blocks"][0]["text"] == "Design pressure is 2 bar."
    assert result["status"] == "retrieved_not_verified"
    assert result["extraction"]["snapshot_id"] == "snapshot-1"
