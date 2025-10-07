from pathlib import Path

def read_version() -> str:
    version_file = Path(__file__).resolve().parents[1] / "VERSION"
    try:
        return version_file.read_text(encoding="utf-8").strip() or "0.0.0"
    except Exception:
        return "0.0.0"
