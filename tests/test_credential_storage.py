import importlib.util
from pathlib import Path
import stat
import json

import pytest

spec = importlib.util.spec_from_file_location(
    "save_plaid_credentials",
    Path(__file__).resolve().parents[1] / "scripts" / "save_plaid_credentials.py",
)
helper = importlib.util.module_from_spec(spec)
spec.loader.exec_module(helper)


def test_private_storage_and_no_overwrite(tmp_path):
    path = tmp_path / "private" / "plaid-sandbox.json"
    helper.save_credentials(path, "fake-client", "fake-secret")
    assert stat.S_IMODE(path.parent.stat().st_mode) == 0o700
    assert stat.S_IMODE(path.stat().st_mode) == 0o600
    data = json.loads(path.read_text())
    assert data["endpoint"] == "https://sandbox.plaid.com"
    assert data["environment"] == "sandbox"
    before = path.read_bytes()
    with pytest.raises(FileExistsError):
        helper.save_credentials(path, "different-client", "different-secret")
    assert path.read_bytes() == before


def test_empty_credentials_do_not_create_storage(tmp_path):
    path = tmp_path / "new" / "plaid-sandbox.json"
    with pytest.raises(ValueError):
        helper.save_credentials(path, "", "fake-secret")
    assert not path.exists()


def test_symlink_directory_is_rejected(tmp_path):
    target = tmp_path / "target"
    target.mkdir()
    link = tmp_path / "link"
    link.symlink_to(target, target_is_directory=True)
    with pytest.raises(ValueError):
        helper.save_credentials(link / "plaid-sandbox.json", "fake-client", "fake-secret")
    assert not (target / "plaid-sandbox.json").exists()


def test_check_uses_sandbox_read_only_endpoint(tmp_path, monkeypatch):
    import sys
    from types import SimpleNamespace

    monkeypatch.setitem(sys.modules, "save_plaid_credentials", helper)
    check_spec = importlib.util.spec_from_file_location(
        "check_plaid_credentials",
        Path(__file__).resolve().parents[1] / "scripts" / "check_plaid_credentials.py",
    )
    checker = importlib.util.module_from_spec(check_spec)
    check_spec.loader.exec_module(checker)
    path = tmp_path / "private" / "plaid-sandbox.json"
    helper.save_credentials(path, "fake-client", "fake-secret")
    calls = []

    def post(url, **kwargs):
        calls.append((url, kwargs))
        return SimpleNamespace(status_code=200)

    monkeypatch.setattr(checker.requests, "post", post)
    assert checker.check_credentials(path)
    assert calls[0][0] == "https://sandbox.plaid.com/institutions/get"
    assert calls[0][1]["timeout"] == (5, 20)
    data = json.loads(path.read_text())
    data["endpoint"] = "https://production.plaid.com"
    path.write_text(json.dumps(data))
    with pytest.raises(ValueError):
        checker.check_credentials(path)
    assert len(calls) == 1
