#!/usr/bin/env python3
"""Run the bundled imagegen CLI using Codex's stored API-key auth.

This wrapper does not persist or print secrets. It reads ~/.codex/auth.json at
runtime, injects OPENAI_API_KEY for the child process, and forwards all args to
the system imagegen script.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
import sys
import tomllib


def read_api_key(codex_home: Path) -> str:
    auth_path = codex_home / "auth.json"
    try:
        data = json.loads(auth_path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        raise SystemExit(f"Codex auth file not found: {auth_path}")
    except json.JSONDecodeError as exc:
        raise SystemExit(f"Codex auth file is not valid JSON: {exc}") from exc

    key = data.get("OPENAI_API_KEY")
    if not isinstance(key, str) or not key:
        raise SystemExit(f"OPENAI_API_KEY is missing in {auth_path}")
    return key


def read_codex_base_url(codex_home: Path) -> str | None:
    config_path = codex_home / "config.toml"
    if not config_path.exists():
        return None

    try:
        config = tomllib.loads(config_path.read_text(encoding="utf-8"))
    except (OSError, tomllib.TOMLDecodeError) as exc:
        raise SystemExit(f"Could not read Codex config {config_path}: {exc}") from exc

    provider = config.get("model_provider")
    providers = config.get("model_providers", {})
    if isinstance(provider, str) and isinstance(providers, dict):
        provider_config = providers.get(provider, {})
        if isinstance(provider_config, dict):
            base_url = provider_config.get("base_url")
            if isinstance(base_url, str) and base_url:
                return base_url
    return None


def main() -> int:
    codex_home = Path(os.environ.get("CODEX_HOME", Path.home() / ".codex")).expanduser()
    imagegen = codex_home / "skills" / ".system" / "imagegen" / "scripts" / "image_gen.py"
    if not imagegen.exists():
        raise SystemExit(f"Bundled imagegen script not found: {imagegen}")

    env = os.environ.copy()
    # This wrapper intentionally follows Codex's configured provider. A shell-level
    # OPENAI_API_KEY may target a different endpoint and must not override it.
    env["OPENAI_API_KEY"] = read_api_key(codex_home)

    base_url = read_codex_base_url(codex_home)
    if base_url:
        env["OPENAI_BASE_URL"] = base_url

    python = sys.executable
    return subprocess.call([python, str(imagegen), *sys.argv[1:]], env=env)


if __name__ == "__main__":
    raise SystemExit(main())
