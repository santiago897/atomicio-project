from typing import Callable, Any, Tuple, Dict, IO, List

# Registro global: extensión -> (loader, dumper)
FORMAT_REGISTRY: Dict[str, Tuple[Callable[[IO], Any], Callable[[Any, IO], None]]] = {}

def register_format(ext: str, loader: Callable[[IO], Any], dumper: Callable[[Any, IO], None]) -> None:
    """
    Registers a loader/dumper for a file extension.

    Args:
        ext: extension (with or without dot, e.g. '.json' or 'json')
        loader: function that receives a file-like and returns the object
        dumper: function that receives the object and a file-like

    Example:
        from atomicio import register_format
        def csv_loader(f): ...
        def csv_dumper(data, f): ...
        register_format('.csv', csv_loader, csv_dumper)

    Plugins can use entry points in pyproject.toml:
        [tool.poetry.entry-points."atomicio.formats"]
        myplugin = "myplugin.formats:register"
    """
    if not ext.startswith('.'):
        ext = '.' + ext
    FORMAT_REGISTRY[ext.lower()] = (loader, dumper)

class FormatNotRegisteredError(ValueError):
    pass

def _get_handlers(suffix: str):
    if not suffix.startswith('.'):
        suffix = '.' + suffix
    suffix = suffix.lower()
    if suffix in FORMAT_REGISTRY:
        return FORMAT_REGISTRY[suffix]
    raise FormatNotRegisteredError(f"No hay formato registrado para la extensión '{suffix}'")

def load_data(file_obj, suffix: str):
    loader, _ = _get_handlers(suffix)
    return loader(file_obj)

def dump_data(data, file_obj, suffix: str):
    _, dumper = _get_handlers(suffix)
    dumper(data, file_obj)

def list_supported_formats() -> List[str]:
    """Returns a list of currently supported extensions."""
    return sorted(FORMAT_REGISTRY.keys())
