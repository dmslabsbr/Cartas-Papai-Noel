"""
Simple version bump script (semantic version, patch increment by default).
Usage:
  py scripts/bump_version.py [major|minor|patch]
"""
from __future__ import annotations
import sys
from pathlib import Path

def bump(part: str = "patch") -> str:
    version_file = Path(__file__).resolve().parents[1] / "VERSION"
    current = version_file.read_text(encoding="utf-8").strip()
    major, minor, patch = (int(x) for x in current.split("."))
    if part == "major":
        major, minor, patch = major + 1, 0, 0
    elif part == "minor":
        minor, patch = minor + 1, 0
    else:
        patch += 1
    new_v = f"{major}.{minor}.{patch}"
    version_file.write_text(new_v, encoding="utf-8")
    print(new_v)
    return new_v

if __name__ == "__main__":
    arg = sys.argv[1] if len(sys.argv) > 1 else "patch"
    bump(arg)
