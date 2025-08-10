from pathlib import Path
import tomli

def get_version():
    pyproject = Path(__file__).parent.parent / "pyproject.toml"
    if not pyproject.exists():
        return "0.0.0"
    with pyproject.open("rb") as f:
        data = tomli.load(f)
    return data.get("project", {}).get("version", "0.0.0")

__version__ = get_version()
