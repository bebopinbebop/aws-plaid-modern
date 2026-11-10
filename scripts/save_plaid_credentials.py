#!/usr/bin/env python3
"""Save Sandbox credentials outside the repository; never overwrite a file."""

import getpass
import json
import os
from pathlib import Path
import sys

DEFAULT_PATH = Path.home() / ".config" / "aws-plaid-modern" / "plaid-sandbox.json"


def save_credentials(path: Path, client_id: str, secret: str) -> None:
    if not client_id.strip() or not secret.strip():
        raise ValueError("Both credentials are required.")
    directory = path.parent
    if directory.is_symlink():
        raise ValueError("Refusing a symlink credential directory.")
    directory.mkdir(mode=0o700, parents=True, exist_ok=True)
    if directory.stat().st_uid != os.getuid():
        raise ValueError("Credential directory must be owned by the current user.")
    directory.chmod(0o700)
    payload = {
        "client_id": client_id.strip(),
        "client_secret": secret.strip(),
        "endpoint": "https://sandbox.plaid.com",
        "environment": "sandbox",
    }
    descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(descriptor, "w") as stream:
        json.dump(payload, stream)
        stream.write("\n")


def main() -> int:
    if DEFAULT_PATH.exists() or DEFAULT_PATH.is_symlink():
        print(f"Credentials already exist at {DEFAULT_PATH}; nothing overwritten.", file=sys.stderr)
        return 1
    if not sys.stdin.isatty():
        print("Run this helper in an interactive terminal for hidden prompts.", file=sys.stderr)
        return 1
    try:
        client_id = getpass.getpass("Plaid Sandbox client ID (hidden): ")
        secret = getpass.getpass("Plaid Sandbox secret (hidden): ")
        save_credentials(DEFAULT_PATH, client_id, secret)
    except (EOFError, KeyboardInterrupt):
        print("\nCancelled; no credentials saved.", file=sys.stderr)
        return 1
    except (OSError, ValueError) as error:
        print(f"Credentials were not saved: {type(error).__name__}.", file=sys.stderr)
        return 1
    print(f"Saved private Sandbox credentials to {DEFAULT_PATH}.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
