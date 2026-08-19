import json
from pathlib import Path

MANIFEST = Path("consumer_probe/extension/manifest.json")


def load_manifest():
    return json.loads(MANIFEST.read_text(encoding="utf-8"))


def test_extension_uses_manifest_v3():
    manifest = load_manifest()

    assert manifest["manifest_version"] == 3


def test_extension_bridge_permission_is_optional_and_local_only():
    manifest = load_manifest()

    assert "host_permissions" not in manifest

    assert manifest.get(
        "optional_host_permissions"
    ) == [
        "http://127.0.0.1/*"
    ]


def test_extension_uses_active_tab():
    manifest = load_manifest()

    assert "activeTab" in manifest["permissions"]
    assert "scripting" in manifest["permissions"]
    assert "storage" in manifest["permissions"]


def test_extension_uses_service_worker():
    manifest = load_manifest()

    assert manifest["background"]["service_worker"] == (
        "background/service_worker.js"
    )


def test_extension_action_uses_popup():
    manifest = load_manifest()

    assert manifest["action"]["default_popup"] == "popup/popup.html"
