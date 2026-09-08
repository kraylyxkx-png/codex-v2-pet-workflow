#!/usr/bin/env python3
"""Check whether a machine is ready for the Codex v2 pet workflow.

The report never prints credential values. It only reports whether a supported
credential source exists and whether the deterministic pet tools are present.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import os
from pathlib import Path
import platform
import sys
import tomllib


def read_json(path: Path) -> dict[str, object]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return value if isinstance(value, dict) else {}


def read_toml(path: Path) -> dict[str, object]:
    try:
        value = tomllib.loads(path.read_text(encoding="utf-8"))
    except (OSError, tomllib.TOMLDecodeError):
        return {}
    return value if isinstance(value, dict) else {}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--codex-home",
        type=Path,
        default=Path(os.environ.get("CODEX_HOME", Path.home() / ".codex")),
    )
    parser.add_argument(
        "--workspace",
        type=Path,
        default=Path.cwd(),
        help="Workspace containing scripts/imagegen-from-codex-auth.py.",
    )
    parser.add_argument(
        "--require-cli",
        action="store_true",
        help="Exit non-zero unless an API-backed image generation route is ready.",
    )
    args = parser.parse_args()

    codex_home = args.codex_home.expanduser().resolve()
    workspace = args.workspace.expanduser().resolve()
    config = read_toml(codex_home / "config.toml")
    auth = read_json(codex_home / "auth.json")

    provider = config.get("model_provider")
    providers = config.get("model_providers", {})
    provider_config = (
        providers.get(provider, {})
        if isinstance(provider, str) and isinstance(providers, dict)
        else {}
    )
    base_url = (
        provider_config.get("base_url")
        if isinstance(provider_config, dict)
        else None
    )

    imagegen_dir = codex_home / "skills" / ".system" / "imagegen"
    hatch_pet_dir = codex_home / "skills" / "hatch-pet"
    provider_bridge = workspace / "scripts" / "imagegen-from-codex-auth.py"
    env_key_present = bool(os.environ.get("OPENAI_API_KEY"))
    codex_key_present = bool(auth.get("OPENAI_API_KEY"))
    shell_key_matches_codex_auth = bool(
        env_key_present
        and codex_key_present
        and os.environ.get("OPENAI_API_KEY") == auth.get("OPENAI_API_KEY")
    )
    pillow_present = importlib.util.find_spec("PIL") is not None
    python_ready = sys.version_info >= (3, 11)
    deterministic_ready = all(
        [
            python_ready,
            pillow_present,
            (hatch_pet_dir / "scripts" / "prepare_pet_run.py").is_file(),
            (hatch_pet_dir / "scripts" / "validate_atlas.py").is_file(),
        ]
    )
    normalized_base_url = base_url.rstrip("/") if isinstance(base_url, str) else None
    provider_is_official = normalized_base_url in {
        None,
        "https://api.openai.com",
        "https://api.openai.com/v1",
    }
    official_cli_ready = all(
        [
            env_key_present,
            (imagegen_dir / "scripts" / "image_gen.py").is_file(),
            provider_is_official or not shell_key_matches_codex_auth,
        ]
    )
    provider_cli_ready = all(
        [
            codex_key_present,
            isinstance(base_url, str) and bool(base_url),
            provider_bridge.is_file(),
            (imagegen_dir / "scripts" / "image_gen.py").is_file(),
        ]
    )

    report = {
        "ok": deterministic_ready and (
            not args.require_cli or official_cli_ready or provider_cli_ready
        ),
        "platform": platform.platform(),
        "python": {
            "executable": sys.executable,
            "version": platform.python_version(),
            "requires_3_11_or_newer": python_ready,
            "pillow": pillow_present,
        },
        "codex_home": str(codex_home),
        "skills": {
            "imagegen": imagegen_dir.is_dir(),
            "hatch_pet": hatch_pet_dir.is_dir(),
        },
        "authentication": {
            "shell_openai_api_key_present": env_key_present,
            "codex_auth_api_key_present": codex_key_present,
            "shell_key_matches_codex_auth": shell_key_matches_codex_auth,
            "codex_model_provider": provider,
            "codex_provider_base_url": base_url,
            "official_openai_cli_ready": official_cli_ready,
            "codex_provider_cli_ready": provider_cli_ready,
            "credential_values_printed": False,
        },
        "paths": {
            "imagegen_cli": str(imagegen_dir / "scripts" / "image_gen.py"),
            "hatch_pet_scripts": str(hatch_pet_dir / "scripts"),
            "provider_bridge": str(provider_bridge),
        },
        "notes": [
            "Built-in image generation availability is task-specific and cannot be detected by this script.",
            "An API key and its base URL must belong to the same provider; presence checks do not make a live API request.",
            "Use the provider bridge only for credentials stored by Codex for the configured provider.",
        ],
    }
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
