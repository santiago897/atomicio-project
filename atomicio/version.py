from pathlib import Path
import sys

# Handle tomli/tomllib based on Python version
if sys.version_info >= (3, 11):
    import tomllib as tomli
else:
    import tomli

def get_version():
    pyproject = Path(__file__).parent.parent / "pyproject.toml"
    if not pyproject.exists():
        return "0.0.0"
    with pyproject.open("rb") as f:
        data = tomli.load(f)
    # Poetry uses tool.poetry.version, not project.version
    return data.get("tool", {}).get("poetry", {}).get("version", "0.0.0")

__version__ = get_version()
