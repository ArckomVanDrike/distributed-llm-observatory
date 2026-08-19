import json
import re
from pathlib import Path
from urllib.parse import urlparse

EXTENSION_ROOT = Path(
    "consumer_probe/extension"
)

MANIFEST_PATH = (
    EXTENSION_ROOT / "manifest.json"
)

FORBIDDEN_PERMISSIONS = {
    "cookies",
    "webRequest",
    "webRequestBlocking",
    "declarativeNetRequest",
    "history",
}

FORBIDDEN_REMOTE_HOSTS = {
    "chatgpt.com",
    "api.openai.com",
    "claude.ai",
    "api.anthropic.com",
    "gemini.google.com",
    "generativelanguage.googleapis.com",
}

FORBIDDEN_BROWSER_AUTOMATION_MARKERS = {
    "document.cookie",
    "cookieStore",
    "MutationObserver",
    "new KeyboardEvent",
    "new InputEvent",
    ".requestSubmit(",
    ".submit(",
    "document.execCommand(",
}


def load_manifest() -> dict:
    return json.loads(
        MANIFEST_PATH.read_text(
            encoding="utf-8"
        )
    )


def javascript_sources() -> list[Path]:
    return sorted(
        EXTENSION_ROOT.rglob("*.js")
    )


def combined_javascript() -> str:
    return "\n".join(
        path.read_text(
            encoding="utf-8"
        )
        for path in javascript_sources()
    )


def test_extension_has_no_sensitive_browser_permissions():
    manifest = load_manifest()

    permissions = set(
        manifest.get(
            "permissions",
            [],
        )
    )

    assert permissions.isdisjoint(
        FORBIDDEN_PERMISSIONS
    )


def test_extension_has_no_permanent_host_permissions():
    manifest = load_manifest()

    assert "host_permissions" not in manifest


def test_optional_network_permission_is_loopback_only():
    manifest = load_manifest()

    assert manifest.get(
        "optional_host_permissions"
    ) == [
        "http://127.0.0.1/*"
    ]


def test_extension_http_urls_are_loopback_only():
    source = combined_javascript()

    urls = re.findall(
        r"https?://[^\"'`\s]+",
        source,
    )

    assert urls

    for raw_url in urls:
        parsed = urlparse(raw_url)

        assert parsed.hostname == "127.0.0.1", (
            "Consumer Probe contains a non-local "
            f"network target: {raw_url}"
        )


def test_extension_does_not_target_consumer_service_endpoints():
    source = combined_javascript()

    for hostname in FORBIDDEN_REMOTE_HOSTS:
        assert (
            f"https://{hostname}" not in source
        ), (
            "Consumer Probe must not call consumer "
            f"service endpoints directly: {hostname}"
        )


def test_extension_does_not_access_cookies():
    source = combined_javascript()

    assert "document.cookie" not in source
    assert ".cookies." not in source
    assert "cookieStore" not in source


def test_extension_does_not_contain_dom_scraping_or_submission_primitives():
    source = combined_javascript()

    for marker in FORBIDDEN_BROWSER_AUTOMATION_MARKERS:
        assert marker not in source, (
            "Forbidden Consumer Probe automation "
            f"primitive detected: {marker}"
        )


def test_consumer_probe_keeps_response_capture_disabled():
    popup = (
        EXTENSION_ROOT
        / "popup"
        / "popup.js"
    ).read_text(
        encoding="utf-8"
    )

    assert (
        "response_capture_enabled: false"
        in popup
    )

    assert (
        "response_capture_enabled: true"
        not in popup
    )


def test_consumer_probe_persists_null_response_text():
    popup = (
        EXTENSION_ROOT
        / "popup"
        / "popup.js"
    ).read_text(
        encoding="utf-8"
    )

    assignments = re.findall(
        r"response_text\s*:\s*([^,\n}]+)",
        popup,
    )

    assert assignments

    assert all(
        value.strip() == "null"
        for value in assignments
    )


def test_bridge_csp_does_not_allow_remote_llm_connections():
    manifest = load_manifest()

    csp = manifest.get(
        "content_security_policy",
        {},
    ).get(
        "extension_pages",
        "",
    )

    assert (
        "http://127.0.0.1:8765"
        in csp
    )

    for hostname in FORBIDDEN_REMOTE_HOSTS:
        assert hostname not in csp
