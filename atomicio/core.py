import re
import tempfile
import contextlib
import os
from typing import Any, Optional, Union
from pathlib import Path
from threading import RLock
from filelock import FileLock
from .formats import load_data, dump_data, list_supported_formats

def resolve_path(path: str = None, dirpath: str = None, filename: str = None) -> Path:
    """
    Resolves an absolute path from:
    - an absolute or relative path (param path)
    - or a combination of dirpath + filename
    """
    if path:
        return Path(path).expanduser().resolve()
    elif dirpath and filename:
        return Path(dirpath).expanduser().resolve() / filename
    else:
        raise ValueError("Debes pasar 'path' o 'dirpath' y 'filename'.")

def create_file(*, path: str = None, dirpath: str = None, filename: str = None, content: str = "", overwrite: bool = False) -> Path:
    """
    Creates a file at the indicated path. If it exists and overwrite=False, raises an exception.
    You can pass an absolute/relative path, or dirpath+filename.
    """
    file_path = resolve_path(path, dirpath, filename)
    if file_path.exists() and not overwrite:
        raise FileExistsError(f"El archivo ya existe: {file_path}")
    file_path.parent.mkdir(parents=True, exist_ok=True)
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(content)
    return file_path

def delete_file(*, path: str = None, dirpath: str = None, filename: str = None, missing_ok: bool = True) -> None:
    """
    Deletes a file. If missing_ok=False and it does not exist, raises an exception.
    You can pass an absolute/relative path, or dirpath+filename.
    """
    file_path = resolve_path(path, dirpath, filename)
    try:
        file_path.unlink()
    except FileNotFoundError:
        if not missing_ok:
            raise

def find_project_root(start_path=None, git=False):
    """
    Searches for the project root from start_path (or cwd) upwards.
    Considers as root if it finds .git, .venv, .vscode, etc.
    Returns Path or None if not found.
    """
    markers = {'.git', '.venv', 'venv'}

    if git:
        markers = {'.git'}

    path = Path(start_path or os.getcwd()).resolve()
    for parent in [path] + list(path.parents):
        for marker in markers:
            if (parent / marker).exists():
                return parent
    return None

def find_project_files(pattern: str, dirpath: str = None, recursive: bool = True, ignore_dirs=None, verbose: bool = False):
    """
    Searches for files by regex in the project (auto-detected) or in dirpath.
    - pattern: regex on the file name (not path).
    - dirpath: if specified, searches there; if not, detects project root.
    - recursive: searches recursively.
    - ignore_dirs: list of subdirectory names to ignore (name only, not path).
    Returns a list of absolute Paths, or an empty list if none found and False if could not determine the project root and dirpath was not provided.
    """
    base_dir = Path(dirpath).expanduser().resolve() if dirpath else find_project_root()
    if base_dir is None:
        if verbose:
            print("Could not detect project root and dirpath was not specified, returning False...")
        return False
    regex = re.compile(pattern)
    ignore_dirs = set(ignore_dirs or [])
    result = []
    if recursive:
        for root, dirs, files in os.walk(base_dir):
            dirs[:] = [d for d in dirs if d not in ignore_dirs]
            for f in files:
                if regex.search(f):
                    result.append(Path(root) / f)
    else:
        for f in base_dir.iterdir():
            if f.is_file() and regex.search(f.name):
                result.append(f)
    if verbose:
        if not result:
            print("Found 0 files.")
        else:
            print(f"Found {len(result)} files:")
            for idx, file in enumerate(result, 1):
                print(f"  {idx}) filename: {file.name} | path: {file}")
    return result

@contextlib.contextmanager
def atomic_write(path, mode="w", encoding=None, overwrite=True):
    """
    Atomic file writing (text or binary) using only the stdlib.
    Supports modes "w" and "wb" and optional encoding.
    """
    path = str(path)
    dirpath = os.path.dirname(os.path.abspath(path))
    with tempfile.NamedTemporaryFile(delete=False, dir=dirpath, mode=mode, encoding=encoding) as tf:
        try:
            yield tf
            tf.flush()
            os.fsync(tf.fileno())
        finally:
            tf.close()
    if overwrite:
        os.replace(tf.name, path)
    else:
        os.link(tf.name, path)
        os.unlink(tf.name)

_thread_lock = RLock()

class SafeFile:
    """
    Safe file operations (synchronous and atomic).

    - Inter-process locking with FileLock (.lock file)
    - In-memory lock for threads (thread-safe)
    - Atomic writing to avoid corruption
    - Support for formats by extension (plugins)

    Example usage:
        from atomicio import SafeFile
        sf = SafeFile('file.yaml')
        with sf.locked() as f:
            data = f.read() or {}
            data['x'] = 1
            f.write(data)

    To add support for new formats:
        from atomicio import register_format
        def my_loader(f: IO): ...
        def my_dumper(data, f: IO): ...
        register_format('.myext', my_loader, my_dumper)
    """

    def __init__(self, path: Union[str, os.PathLike], timeout: int = 10):
        self.path = Path(path)
        self.file_lock = FileLock(str(self.path) + ".lock", timeout=timeout)

    def __enter__(self):
        _thread_lock.acquire()
        self.file_lock.acquire()
        return self

    def __exit__(self, exc_type, exc, tb):
        import time
        # Intentar liberar el file_lock hasta 3 veces
        for attempt in range(3):
            try:
                self.file_lock.release()
                break
            except Exception as e:
                if attempt == 2:
                    print(f"[SafeFile] Could not release file_lock after 3 attempts: {e}")
                else:
                    time.sleep(0.1)
        # Intentar liberar el thread_lock hasta 3 veces
        for attempt in range(3):
            try:
                _thread_lock.release()
                break
            except Exception as e:
                if attempt == 2:
                    print(f"[SafeFile] Could not release thread_lock after 3 attempts: {e}")
                else:
                    time.sleep(0.1)

        # Si el archivo está en un repo git, asegurar que .gitignore incluya '*.lock'
        try:
            project_root = find_project_root(self.path, git=True)
            if project_root:
                gitignore_path = project_root / '.gitignore'
                lock_pattern = '*.lock\n'
                if gitignore_path.exists():
                    with open(gitignore_path, 'r+', encoding='utf-8') as f:
                        lines = f.readlines()
                        if not any(line.strip() == '*.lock' for line in lines):
                            if lines and not lines[-1].endswith('\n'):
                                f.write('\n')
                            f.write(lock_pattern)
                else:
                    with open(gitignore_path, 'w', encoding='utf-8') as f:
                        f.write(lock_pattern)
        except Exception as e:
            print(f"[SafeFile] Warning: Could not ensure exclusion of '*.lock' in .gitignore: {e}")

    def read(self) -> Optional[Any]:
        """
        Reads and deserializes the file according to its extension. Returns None if it does not exist.
        """
        with _thread_lock:
            with self.file_lock:
                if not self.path.exists():
                    return None
                mode = "rb" if self.path.suffix.lower() == ".toml" else "r"
                encoding = None if mode == "rb" else "utf-8"
                try:
                    with open(self.path, mode, encoding=encoding) as f:
                        return load_data(f, self.path.suffix)
                except Exception as e:
                    raise RuntimeError(f"Error leyendo '{self.path}': {e}") from e

    def write(self, data: Any) -> None:
        """
        Serializes and writes data atomically according to the file extension.
        """
        with _thread_lock:
            with self.file_lock:
                try:
                    with atomic_write(self.path, mode="w", encoding="utf-8", overwrite=True) as f:
                        dump_data(data, f, self.path.suffix)
                except Exception as e:
                    raise RuntimeError(f"Error escribiendo '{self.path}': {e}") from e

    def append(self, text: str) -> None:
        """
        Appends text to the end of the file under lock (not atomic).
        """
        with _thread_lock:
            with self.file_lock:
                try:
                    with open(self.path, "a", encoding="utf-8") as f:
                        f.write(str(text))
                except Exception as e:
                    raise RuntimeError(f"Error en append '{self.path}': {e}") from e

    def read_bytes(self) -> Optional[bytes]:
        """
        Reads the file as bytes. Returns None if it does not exist.
        """
        with _thread_lock:
            with self.file_lock:
                if not self.path.exists():
                    return None
                try:
                    return self.path.read_bytes()
                except Exception as e:
                    raise RuntimeError(f"Error leyendo bytes '{self.path}': {e}") from e

    def write_bytes(self, data: bytes) -> None:
        """
        Writes bytes atomically.
        """
        with _thread_lock:
            with self.file_lock:
                try:
                    with atomic_write(self.path, mode="wb", overwrite=True) as f:
                        f.write(data)
                except Exception as e:
                    raise RuntimeError(f"Error escribiendo bytes '{self.path}': {e}") from e

    def locked(self) -> 'SafeFile._LockedContext':
        """
        Context manager for manual locking (threads + process).

        Usage:
            with SafeFile('file.yaml').locked() as sf:
                data = sf.read()
                data['x'] = 1
                sf.write(data)
        """
        class _LockedContext:
            def __init__(self, outer):
                self.outer = outer

            def __enter__(self):
                _thread_lock.acquire()
                self.outer.file_lock.acquire()
                return self.outer

            def __exit__(self, exc_type, exc, tb):
                import time
                # Intentar liberar el file_lock hasta 3 veces
                for attempt in range(3):
                    try:
                        self.file_lock.release()
                        break
                    except Exception as e:
                        if attempt == 2:
                            print(f"[SafeFile] Could not release file_lock after 3 attempts: {e}")
                        else:
                            time.sleep(0.1)
                # Intentar liberar el thread_lock hasta 3 veces
                for attempt in range(3):
                    try:
                        _thread_lock.release()
                        break
                    except Exception as e:
                        if attempt == 2:
                            print(f"[SafeFile] Could not release thread_lock after 3 attempts: {e}")
                        else:
                            time.sleep(0.1)

                # Si el archivo está en un repo git, asegurar que .gitignore incluya '*.lock'
                try:
                    project_root = find_project_root(self.path, git=True)
                    if project_root:
                        gitignore_path = project_root / '.gitignore'
                        lock_pattern = '*.lock\n'
                        if gitignore_path.exists():
                            with open(gitignore_path, 'r+', encoding='utf-8') as f:
                                lines = f.readlines()
                                if not any(line.strip() == '*.lock' for line in lines):
                                    if lines and not lines[-1].endswith('\n'):
                                        f.write('\n')
                                    f.write(lock_pattern)
                        else:
                            with open(gitignore_path, 'w', encoding='utf-8') as f:
                                f.write(lock_pattern)
                except Exception as e:
                    print(f"[SafeFile] Warning: Could not ensure exclusion of '*.lock' in .gitignore: {e}")

        return _LockedContext(self)

    @staticmethod
    def supported_formats() -> list:
        """
        Lists currently supported file extensions.
        """
        return list_supported_formats()
