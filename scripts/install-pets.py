#!/usr/bin/env python3
"""Install the bundled Codex custom pets on the current computer."""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PET_ROOT = ROOT / "pets"


def load_catalog() -> list[dict]:
    with (PET_ROOT / "index.json").open(encoding="utf-8") as handle:
        return json.load(handle)["pets"]


def codex_home(value: str | None) -> Path:
    return Path(value).expanduser() if value else Path(os.environ.get("CODEX_HOME", Path.home() / ".codex")).expanduser()


def update_selection(config_path: Path, pet_id: str) -> None:
    config_path.parent.mkdir(parents=True, exist_ok=True)
    line = f'selected-avatar-id = "custom:{pet_id}"'
    if config_path.exists():
        text = config_path.read_text(encoding="utf-8")
        pattern = re.compile(r"(?m)^selected-avatar-id\s*=.*(?:\n|$)")
        text = pattern.sub(line + "\n", text, count=1) if pattern.search(text) else text.rstrip() + "\n" + line + "\n"
    else:
        text = line + "\n"
    config_path.write_text(text, encoding="utf-8")


def install(entry: dict, destination: Path) -> None:
    source = PET_ROOT / entry["directory"]
    if not (source / "pet.json").is_file() or not (source / "spritesheet.webp").is_file():
        raise FileNotFoundError(f"Incomplete pet package: {source}")
    target = destination / entry["id"]
    target.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source / "pet.json", target / "pet.json")
    shutil.copy2(source / "spritesheet.webp", target / "spritesheet.webp")
    png = source / "spritesheet.png"
    if png.is_file():
        shutil.copy2(png, target / "spritesheet.png")


def main() -> int:
    parser = argparse.ArgumentParser(description="Install portable Codex custom pets")
    parser.add_argument("--pet", action="append", dest="pets", help="Pet id to install; repeat for multiple pets")
    parser.add_argument("--all", action="store_true", help="Install all four pets")
    parser.add_argument("--select", help="Set this pet as the active Codex avatar after installing")
    parser.add_argument("--codex-home", help="Override CODEX_HOME (useful for testing or another profile)")
    parser.add_argument("--list", action="store_true", help="List bundled pets and exit")
    args = parser.parse_args()

    catalog = load_catalog()
    by_id = {entry["id"]: entry for entry in catalog}
    if args.list:
        for entry in catalog:
            print(f'{entry["id"]}\t{entry["displayName"]}\t{entry["grid"]}')
        return 0

    requested = list(dict.fromkeys(args.pets or []))
    if args.all or not requested:
        requested = [entry["id"] for entry in catalog]
    unknown = [pet_id for pet_id in requested if pet_id not in by_id]
    if unknown:
        parser.error("Unknown pet id: " + ", ".join(unknown))
    if args.select and args.select not in by_id:
        parser.error("Unknown --select pet id: " + args.select)

    home = codex_home(args.codex_home)
    destination = home / "pets"
    for pet_id in requested:
        install(by_id[pet_id], destination)
        print(f"installed {pet_id} -> {destination / pet_id}")
    if args.select:
        update_selection(home / "config.toml", args.select)
        print(f"selected {args.select}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
