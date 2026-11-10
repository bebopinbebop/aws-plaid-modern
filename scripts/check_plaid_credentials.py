#!/usr/bin/env python3
"""Verify saved Sandbox credentials with a read-only Plaid institution lookup."""

import argparse
import json
import os
from pathlib import Path
import stat

import requests

from save_plaid_credentials import DEFAULT_PATH


def check_credentials(path: Path) -> bool:
    if path.is_symlink() or path.parent.is_symlink():
        raise ValueError("Refusing symlink credential storage.")
    info = path.stat()
    if info.st_uid != os.getuid() or stat.S_IMODE(info.st_mode) != 0o600:
        raise ValueError("Credential file must be owned by you with permissions 600.")
    if stat.S_IMODE(path.parent.stat().st_mode) != 0o700:
        raise ValueError("Credential directory must have permissions 700.")
    data = json.loads(path.read_text())
    if data.get("environment") != "sandbox" or data.get("endpoint") != "https://sandbox.plaid.com":
        raise ValueError("Only the explicit Plaid Sandbox endpoint is permitted.")
    if not data.get("client_id") or not data.get("client_secret"):
        raise ValueError("Missing credential fields.")
    response = requests.post(
        "https://sandbox.plaid.com/institutions/get",
        json={
            "client_id": data["client_id"],
            "secret": data["client_secret"],
            "count": 1,
            "offset": 0,
            "country_codes": ["US"],
        },
        timeout=(5, 20),
    )
    return response.status_code == 200


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--credentials", type=Path, default=DEFAULT_PATH)
    args = parser.parse_args()
    try:
        success = check_credentials(args.credentials)
    except (OSError, ValueError, TypeError, requests.RequestException) as error:
        print(
            f"Sandbox credential check did not complete ({type(error).__name__}); no secret values shown."
        )
        return 1
    print(
        "Sandbox authentication verified by read-only institution lookup."
        if success
        else "Sandbox authentication check failed; verify the saved client ID, Sandbox secret and Plaid access."
    )
    return 0 if success else 1


if __name__ == "__main__":
    raise SystemExit(main())
