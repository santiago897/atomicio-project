
from pathlib import Path
from threading import RLock
from filelock import FileLock
from atomicwrites import atomic_write
from typing import Any, Optional, Union, IO
import os

from .formats import load_data, dump_data, list_supported_formats

_thread_lock = RLock()

class SafeFile:
    """
    Operaciones de archivo seguras (síncronas y atómicas).

    - Bloqueo inter-proceso con FileLock (.lock file)
    - Lock en memoria para hilos (thread-safe)
    - Escritura atómica para evitar corrupciones
    - Soporte para formatos por extensión (plugins)

    Ejemplo de uso:
        from atomicio import SafeFile
        sf = SafeFile('archivo.yaml')
        with sf.locked() as f:
            data = f.read() or {}
            data['x'] = 1
            f.write(data)

    Para agregar soporte a nuevos formatos:
        from atomicio import register_format
        def my_loader(f: IO): ...
        def my_dumper(data, f: IO): ...
        register_format('.myext', my_loader, my_dumper)
    """

    def __init__(self, path: Union[str, os.PathLike], timeout: int = 10):
        self.path = Path(path)
        self.file_lock = FileLock(str(self.path) + ".lock", timeout=timeout)

    def read(self) -> Optional[Any]:
        """
        Reads and deserializes the file according to its extension. Returns None if it does not exist. (English)
        Lee y deserializa el archivo según su extensión. Devuelve None si no existe. (Español)
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
        Serializes and writes data atomically according to the file extension. (English)
        Serializa y escribe datos de forma atómica según la extensión. (Español)
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
        Appends text to the end of the file under lock (not atomic). (English)
        Agrega texto al final del archivo bajo lock (no atómico). (Español)
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
        Reads the file as bytes. Returns None if it does not exist. (English)
        Lee el archivo como bytes. Devuelve None si no existe. (Español)
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
        Writes bytes atomically. (English)
        Escribe bytes de forma atómica. (Español)
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
        Context manager for manual locking (threads + process). (English)
        Context manager para lock manual (hilos + proceso). (Español)

        Usage / Uso:
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
                try:
                    self.outer.file_lock.release()
                finally:
                    _thread_lock.release()

        return _LockedContext(self)

    @staticmethod
    @staticmethod
    def supported_formats() -> list:
        """
        Lists currently supported file extensions. (English)
        Lista las extensiones soportadas actualmente. (Español)
        """
        return list_supported_formats()
