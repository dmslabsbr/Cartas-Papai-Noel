import pathlib

def test_version_file_exists():
    root = pathlib.Path(__file__).resolve().parents[1]
    version_path = root / "VERSION"
    assert version_path.exists(), "VERSION file must exist"
    assert version_path.read_text(encoding="utf-8").strip() != "", "VERSION must not be empty"

def test_base_template_contains_versao():
    root = pathlib.Path(__file__).resolve().parents[1]
    base_html = (root / "app" / "templates" / "base.html").read_text(encoding="utf-8")
    assert "versão:" in base_html, "Base HTML must contain the string 'versão:'"
