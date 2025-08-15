import re
import tempfile
import contextlib
import os
import time
import asyncio
import threading
import functools
from typing import Any, Optional, Union, Awaitable
from pathlib import Path
from threading import RLock
from filelock import FileLock
from .formats import load_data, dump_data, list_supported_formats


# Custom exceptions for better error handling
class AtomicIOError(Exception):
    """Base exception for all atomicio operations."""
    pass


class FileOperationError(AtomicIOError):
    """Raised when file I/O operations fail."""
    pass


class FileReadError(FileOperationError):
    """Raised when file reading fails."""
    pass


class FileWriteError(FileOperationError):
    """Raised when file writing fails."""
    pass


class FileAppendError(FileOperationError):
    """Raised when file appending fails."""
    pass


class AsyncTimeoutError(AtomicIOError):
    """Raised when async operations timeout."""
    def __init__(self, message: str, timeout: float, path: Union[str, Path] = None):
        super().__init__(message)
        self.timeout = timeout
        self.path = str(path) if path else None


class AsyncLockError(AtomicIOError):
    """Raised when async lock operations fail."""
    pass


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
            print(f"\nFound 0 files with pattern '{pattern}' in '{base_dir}'{' and its subdirs' if recursive else ''}\n")
        else:
            print(f"---\nFound {len(result)} files with pattern '{pattern}' in '{base_dir}'{' and its subdirs' if recursive else ''}:")
            for idx, file in enumerate(result, 1):
                print(f"  {idx}) filename: {file.name} | path: {file}")
            print("---\n")
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

# Global dictionary to store per-file thread locks (used by SafeFile.locked() and ThreadedSafeFile)
_thread_locks = {}
_thread_locks_lock = threading.Lock()

class SafeFile:
    """
    Simple safe file operations (synchronous and atomic).

    - Inter-process locking with FileLock (.lock file)
    - Basic thread safety with global thread lock
    - Atomic writing to avoid corruption
    - Support for formats by extension (plugins)
    - Designed for straightforward sync code that needs atomic file operations

    Example usage:
        from atomicio import SafeFile
        sf = SafeFile('file.yaml')

        # Simple individual operations
        data = sf.read() or {}
        data['x'] = 1
        sf.write(data)

        # Basic context manager (ensures same instance, no cross-operation locking)
        with sf:
            data = sf.read() or {}
            data['y'] = 2
            sf.write(data)  # Each operation gets its own lock cycle

    For cross-operation locking (holding locks across multiple operations):
        Use ThreadedSafeFile with tsf.locked() context manager instead.

    To add support for new formats:
        from atomicio import register_format
        def my_loader(f: IO): ...
        def my_dumper(data, f: IO): ...
        register_format('.myext', my_loader, my_dumper)
    """

    def __init__(self, path: Union[str, os.PathLike], timeout: Union[bool, int, float, None] = True):
        """
        Initialize a SafeFile for atomic, thread-safe, and process-safe file operations.

        Args:
            path: Path to the file.
            timeout: Controls how long to wait for the file lock:
                - True (default): use default timeout (10 seconds)
                - False or None: wait forever (no timeout)
                - int or float: wait that many seconds
        Raises:
            ValueError: If timeout is not a valid type.
        """
        self.path = Path(path)
        # Validate and normalize timeout value for FileLock
        if timeout is True:
            lock_timeout = 15
        elif timeout is False or timeout is None:
            lock_timeout = -1
        elif isinstance(timeout, (int, float)):
            lock_timeout = timeout
        else:
            raise ValueError(f"Invalid value for timeout: {timeout!r}. Must be True, False, None, int, or float.")
        self.file_lock = FileLock(str(self.path) + ".lock", timeout=lock_timeout)

    def __enter__(self):
        """
        Acquire both thread and file lock. Waits according to the timeout policy set in __init__.
        """
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
                    raise FileReadError(f"Failed to read '{self.path}': {e}") from e

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
                    raise FileWriteError(f"Failed to write '{self.path}': {e}") from e

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
                    raise FileAppendError(f"Failed to append to '{self.path}': {e}") from e

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
                    raise FileReadError(f"Failed to read bytes from '{self.path}': {e}") from e

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
                    raise FileWriteError(f"Failed to write bytes to '{self.path}': {e}") from e

    @staticmethod
    def supported_formats() -> list:
        """
        Lists currently supported file extensions.
        """
        return list_supported_formats()


# Global dictionary to store async locks per file path
_async_locks = {}
_async_locks_lock = asyncio.Lock()


class AsyncSafeFile:
    """
    Asynchronous safe file operations.

    - Async file locking (per-file locks) without blocking the main process
    - Atomic writing to avoid corruption
    - Support for formats by extension (plugins)
    - Thread-safe async lock management

    Example async usage:
        from atomicio import AsyncSafeFile
        async def example():
            asf = AsyncSafeFile('file.yaml')
            async with asf.locked() as f:
                data = await f.read() or {}
                data['x'] = 1
                await f.write(data)

    For synchronous code, use ThreadedSafeFile instead:
        from atomicio import ThreadedSafeFile
        def sync_example():
            tsf = ThreadedSafeFile('file.yaml')
            with tsf.locked() as f:
                data = f.read() or {}
                data['x'] = 1
                f.write(data)
    """

    def __init__(self, path: Union[str, os.PathLike], timeout: Union[bool, int, float, None] = True):
        """
        Initialize an AsyncSafeFile for async atomic and file-safe operations.

        Args:
            path: Path to the file.
            timeout: Controls how long to wait for the async lock:
                - True (default): use default timeout (15 seconds)
                - False or None: wait forever (no timeout)
                - int or float: wait that many seconds
        Raises:
            ValueError: If timeout is not a valid type.
        """
        self.path = Path(path)

        # Validate and normalize timeout value
        if timeout is True:
            self.timeout = 15.0
        elif timeout is False or timeout is None:
            self.timeout = None
        elif isinstance(timeout, (int, float)):
            self.timeout = float(timeout)
        else:
            raise ValueError(f"Invalid value for timeout: {timeout!r}. Must be True, False, None, int, or float.")

    async def _get_lock(self) -> asyncio.Lock:
        """Get or create an async lock for this file path."""
        async with _async_locks_lock:
            path_str = str(self.path)
            if path_str not in _async_locks:
                _async_locks[path_str] = asyncio.Lock()
            return _async_locks[path_str]

    async def read(self) -> Optional[Any]:
        """
        Reads and deserializes the file according to its extension. Returns None if it does not exist.
        """
        lock = await self._get_lock()

        def _do_read():
            if not self.path.exists():
                return None
            mode = "rb" if self.path.suffix.lower() == ".toml" else "r"
            encoding = None if mode == "rb" else "utf-8"
            try:
                with open(self.path, mode, encoding=encoding) as f:
                    return load_data(f, self.path.suffix)
            except Exception as e:
                raise FileReadError(f"Failed to read '{self.path}': {e}") from e

        # Use timeout with asyncio.wait_for if specified, otherwise just acquire lock
        try:
            if self.timeout is None:
                async with lock:
                    loop = asyncio.get_event_loop()
                    return await loop.run_in_executor(None, _do_read)
            else:
                # With timeout
                async def _acquire_and_execute():
                    async with lock:
                        loop = asyncio.get_event_loop()
                        return await loop.run_in_executor(None, _do_read)

                try:
                    return await asyncio.wait_for(_acquire_and_execute(), timeout=self.timeout)
                except asyncio.TimeoutError as e:
                    raise AsyncTimeoutError(
                        f"Timeout ({self.timeout}s) exceeded while reading '{self.path}'",
                        timeout=self.timeout,
                        path=self.path
                    ) from e
        except Exception as e:
            # Catch any other unexpected async errors (e.g., event loop issues, lock acquisition failures)
            if not isinstance(e, AtomicIOError):
                raise AsyncLockError(f"Unexpected error during async read operation on '{self.path}': {e}") from e
            raise  # Re-raise if it's already one of our custom exceptions

    async def write(self, data: Any) -> None:
        """
        Serializes and writes data atomically according to the file extension.
        """
        lock = await self._get_lock()

        def _do_write():
            try:
                with atomic_write(self.path, mode="w", encoding="utf-8", overwrite=True) as f:
                    dump_data(data, f, self.path.suffix)
            except Exception as e:
                raise FileWriteError(f"Failed to write '{self.path}': {e}") from e

        # Use timeout with asyncio.wait_for if specified, otherwise just acquire lock
        try:
            if self.timeout is None:
                async with lock:
                    loop = asyncio.get_event_loop()
                    await loop.run_in_executor(None, _do_write)
            else:
                # With timeout
                async def _acquire_and_execute():
                    async with lock:
                        loop = asyncio.get_event_loop()
                        await loop.run_in_executor(None, _do_write)

                try:
                    await asyncio.wait_for(_acquire_and_execute(), timeout=self.timeout)
                except asyncio.TimeoutError as e:
                    raise AsyncTimeoutError(
                        f"Timeout ({self.timeout}s) exceeded while writing '{self.path}'",
                        timeout=self.timeout,
                        path=self.path
                    ) from e
        except Exception as e:
            # Catch any other unexpected async errors (e.g., event loop issues, lock acquisition failures)
            if not isinstance(e, AtomicIOError):
                raise AsyncLockError(f"Unexpected error during async write operation on '{self.path}': {e}") from e
            raise  # Re-raise if it's already one of our custom exceptions

    async def append(self, text: str) -> None:
        """
        Appends text to the end of the file under lock.
        """
        lock = await self._get_lock()

        def _do_append():
            try:
                with open(self.path, "a", encoding="utf-8") as f:
                    f.write(str(text))
            except Exception as e:
                raise FileAppendError(f"Failed to append to '{self.path}': {e}") from e

        # Use timeout with asyncio.wait_for if specified, otherwise just acquire lock
        try:
            if self.timeout is None:
                async with lock:
                    loop = asyncio.get_event_loop()
                    await loop.run_in_executor(None, _do_append)
            else:
                # With timeout
                async def _acquire_and_execute():
                    async with lock:
                        loop = asyncio.get_event_loop()
                        await loop.run_in_executor(None, _do_append)

                try:
                    await asyncio.wait_for(_acquire_and_execute(), timeout=self.timeout)
                except asyncio.TimeoutError as e:
                    raise AsyncTimeoutError(
                        f"Timeout ({self.timeout}s) exceeded while appending to '{self.path}'",
                        timeout=self.timeout,
                        path=self.path
                    ) from e
        except Exception as e:
            # Catch any other unexpected async errors (e.g., event loop issues, lock acquisition failures)
            if not isinstance(e, AtomicIOError):
                raise AsyncLockError(f"Unexpected error during async append operation on '{self.path}': {e}") from e
            raise  # Re-raise if it's already one of our custom exceptions

    async def read_bytes(self) -> Optional[bytes]:
        """
        Reads the file as bytes. Returns None if it does not exist.
        """
        lock = await self._get_lock()

        def _do_read_bytes():
            if not self.path.exists():
                return None
            try:
                return self.path.read_bytes()
            except Exception as e:
                raise FileReadError(f"Failed to read bytes from '{self.path}': {e}") from e

        # Use timeout with asyncio.wait_for if specified, otherwise just acquire lock
        try:
            if self.timeout is None:
                async with lock:
                    loop = asyncio.get_event_loop()
                    return await loop.run_in_executor(None, _do_read_bytes)
            else:
                # With timeout
                async def _acquire_and_execute():
                    async with lock:
                        loop = asyncio.get_event_loop()
                        return await loop.run_in_executor(None, _do_read_bytes)

                try:
                    return await asyncio.wait_for(_acquire_and_execute(), timeout=self.timeout)
                except asyncio.TimeoutError as e:
                    raise AsyncTimeoutError(
                        f"Timeout ({self.timeout}s) exceeded while reading bytes from '{self.path}'",
                        timeout=self.timeout,
                        path=self.path
                    ) from e
        except Exception as e:
            # Catch any other unexpected async errors (e.g., event loop issues, lock acquisition failures)
            if not isinstance(e, AtomicIOError):
                raise AsyncLockError(f"Unexpected error during async read_bytes operation on '{self.path}': {e}") from e
            raise  # Re-raise if it's already one of our custom exceptions

    async def write_bytes(self, data: bytes) -> None:
        """
        Writes bytes atomically.
        """
        lock = await self._get_lock()

        def _do_write_bytes():
            try:
                with atomic_write(self.path, mode="wb", overwrite=True) as f:
                    f.write(data)
            except Exception as e:
                raise FileWriteError(f"Failed to write bytes to '{self.path}': {e}") from e

        # Use timeout with asyncio.wait_for if specified, otherwise just acquire lock
        try:
            if self.timeout is None:
                async with lock:
                    loop = asyncio.get_event_loop()
                    await loop.run_in_executor(None, _do_write_bytes)
            else:
                # With timeout
                async def _acquire_and_execute():
                    async with lock:
                        loop = asyncio.get_event_loop()
                        await loop.run_in_executor(None, _do_write_bytes)

                try:
                    await asyncio.wait_for(_acquire_and_execute(), timeout=self.timeout)
                except asyncio.TimeoutError as e:
                    raise AsyncTimeoutError(
                        f"Timeout ({self.timeout}s) exceeded while writing bytes to '{self.path}'",
                        timeout=self.timeout,
                        path=self.path
                    ) from e
        except Exception as e:
            # Catch any other unexpected async errors (e.g., event loop issues, lock acquisition failures)
            if not isinstance(e, AtomicIOError):
                raise AsyncLockError(f"Unexpected error during async write_bytes operation on '{self.path}': {e}") from e
            raise  # Re-raise if it's already one of our custom exceptions

    @contextlib.asynccontextmanager
    async def locked(self):
        """
        Async context manager that holds the file lock for the duration of the context.

        This allows multiple operations to be performed while holding the same lock,
        which is useful for complex operations or when you want to ensure exclusive
        access for a longer period.

        Usage:
            asf = AsyncSafeFile('file.yaml', timeout=5.0)
            async with asf.locked() as f:
                data = await f.read() or {}
                data['key'] = 'value'
                await f.write(data)
                # Lock is held during this entire block
                await asyncio.sleep(1)  # Still holding the lock
        """
        lock = await self._get_lock()

        # Create wrapper class that holds the lock and provides methods without re-acquiring
        class LockedFile:
            def __init__(self, asf_instance):
                self.asf = asf_instance

            async def read(self):
                # Don't acquire lock again - we already have it
                def _do_read():
                    if not self.asf.path.exists():
                        return None
                    mode = "rb" if self.asf.path.suffix.lower() == ".toml" else "r"
                    encoding = None if mode == "rb" else "utf-8"
                    try:
                        with open(self.asf.path, mode, encoding=encoding) as f:
                            return load_data(f, self.asf.path.suffix)
                    except Exception as e:
                        raise FileReadError(f"Failed to read '{self.asf.path}': {e}") from e

                loop = asyncio.get_event_loop()
                return await loop.run_in_executor(None, _do_read)

            async def write(self, data):
                # Don't acquire lock again - we already have it
                def _do_write():
                    try:
                        with atomic_write(self.asf.path, mode="w", encoding="utf-8", overwrite=True) as f:
                            dump_data(data, f, self.asf.path.suffix)
                    except Exception as e:
                        raise FileWriteError(f"Failed to write '{self.asf.path}': {e}") from e

                loop = asyncio.get_event_loop()
                await loop.run_in_executor(None, _do_write)

        # Apply timeout to lock acquisition
        if self.timeout is None:
            # No timeout
            async with lock:
                yield LockedFile(self)
        else:
            # Use asyncio.wait() with timeout for lock acquisition
            async def acquire_lock_task():
                async with lock:
                    # Signal that we have the lock and wait for completion
                    acquired_event.set()
                    await completion_event.wait()

            acquired_event = asyncio.Event()
            completion_event = asyncio.Event()

            # Start the lock acquisition task
            lock_task = asyncio.create_task(acquire_lock_task())

            try:
                # Wait for lock acquisition with timeout
                await asyncio.wait_for(acquired_event.wait(), timeout=self.timeout)

                # We have the lock, yield the LockedFile
                try:
                    yield LockedFile(self)
                finally:
                    # Signal completion to release the lock
                    completion_event.set()
                    await lock_task

            except asyncio.TimeoutError:
                # Cancel the lock acquisition task
                lock_task.cancel()
                try:
                    await lock_task
                except asyncio.CancelledError:
                    pass
                raise AsyncTimeoutError(
                    f"Timeout ({self.timeout}s) exceeded while acquiring lock for '{self.path}'",
                    timeout=self.timeout,
                    path=self.path
                )

    @staticmethod
    def supported_formats() -> list:
        """
        Lists currently supported file extensions.
        """
        return list_supported_formats()

    @staticmethod
    async def cleanup_locks():
        """
        Clean up unused async locks to prevent memory leaks.
        This is optional and can be called periodically in long-running applications.
        """
        async with _async_locks_lock:
            # Remove locks that are not currently held
            to_remove = []
            for path, lock in _async_locks.items():
                if not lock.locked():
                    to_remove.append(path)

            for path in to_remove:
                del _async_locks[path]


class ThreadedSafeFile:
    """
    Thread-based safe file operations with proper cross-operation locking.

    - Thread-based file locking with proper lock holding across operations
    - Atomic writing to avoid corruption
    - Support for formats by extension (plugins)
    - Designed specifically for synchronous code with threading
    - Can hold locks across multiple operations like AsyncSafeFile.locked()

    Example usage:
        from atomicio import ThreadedSafeFile
        tsf = ThreadedSafeFile('file.yaml')
        with tsf.locked() as f:
            data = f.read() or {}
            data['x'] = 1
            f.write(data)
            # Lock is held during this entire block
            time.sleep(3)  # Still holding the lock

    Example direct usage:
        tsf = ThreadedSafeFile('file.yaml')
        data = tsf.read() or {}
        data['x'] = 1
        tsf.write(data)
    """

    def __init__(self, path: Union[str, os.PathLike], timeout: Union[bool, int, float, None] = True):
        """
        Initialize a ThreadedSafeFile for thread-safe atomic file operations.

        Args:
            path: Path to the file.
            timeout: Controls how long to wait for the thread lock:
                - True (default): use default timeout (15 seconds)
                - False or None: wait forever (no timeout)
                - int or float: wait that many seconds
        Raises:
            ValueError: If timeout is not a valid type.
        """
        self.path = Path(path)

        # Validate and normalize timeout value
        if timeout is True:
            self.timeout = 15.0
        elif timeout is False or timeout is None:
            self.timeout = None
        elif isinstance(timeout, (int, float)):
            self.timeout = float(timeout)
        else:
            raise ValueError(f"Invalid value for timeout: {timeout!r}. Must be True, False, None, int, or float.")

    def _get_lock(self) -> threading.RLock:
        """Get or create a thread lock for this file path."""
        with _thread_locks_lock:
            path_str = str(self.path)
            if path_str not in _thread_locks:
                _thread_locks[path_str] = threading.RLock()
            return _thread_locks[path_str]

    def read(self) -> Optional[Any]:
        """
        Reads and deserializes the file according to its extension. Returns None if it does not exist.
        """
        lock = self._get_lock()

        def _acquire_with_timeout():
            if self.timeout is None:
                lock.acquire()
                return True
            else:
                return lock.acquire(timeout=self.timeout)

        if not _acquire_with_timeout():
            raise AsyncTimeoutError(
                f"Timeout ({self.timeout}s) exceeded while acquiring lock for reading '{self.path}'",
                timeout=self.timeout,
                path=self.path
            )

        try:
            if not self.path.exists():
                return None
            mode = "rb" if self.path.suffix.lower() == ".toml" else "r"
            encoding = None if mode == "rb" else "utf-8"
            try:
                with open(self.path, mode, encoding=encoding) as f:
                    return load_data(f, self.path.suffix)
            except Exception as e:
                raise FileReadError(f"Failed to read '{self.path}': {e}") from e
        finally:
            lock.release()

    def write(self, data: Any) -> None:
        """
        Serializes and writes data atomically according to the file extension.
        """
        lock = self._get_lock()

        def _acquire_with_timeout():
            if self.timeout is None:
                lock.acquire()
                return True
            else:
                return lock.acquire(timeout=self.timeout)

        if not _acquire_with_timeout():
            raise AsyncTimeoutError(
                f"Timeout ({self.timeout}s) exceeded while acquiring lock for writing '{self.path}'",
                timeout=self.timeout,
                path=self.path
            )

        try:
            try:
                with atomic_write(self.path, mode="w", encoding="utf-8", overwrite=True) as f:
                    dump_data(data, f, self.path.suffix)
            except Exception as e:
                raise FileWriteError(f"Failed to write '{self.path}': {e}") from e
        finally:
            lock.release()

    def append(self, text: str) -> None:
        """
        Appends text to the end of the file under lock.
        """
        lock = self._get_lock()

        def _acquire_with_timeout():
            if self.timeout is None:
                lock.acquire()
                return True
            else:
                return lock.acquire(timeout=self.timeout)

        if not _acquire_with_timeout():
            raise AsyncTimeoutError(
                f"Timeout ({self.timeout}s) exceeded while acquiring lock for appending to '{self.path}'",
                timeout=self.timeout,
                path=self.path
            )

        try:
            try:
                with open(self.path, "a", encoding="utf-8") as f:
                    f.write(str(text))
            except Exception as e:
                raise FileAppendError(f"Failed to append to '{self.path}': {e}") from e
        finally:
            lock.release()

    def read_bytes(self) -> Optional[bytes]:
        """
        Reads the file as bytes. Returns None if it does not exist.
        """
        lock = self._get_lock()

        def _acquire_with_timeout():
            if self.timeout is None:
                lock.acquire()
                return True
            else:
                return lock.acquire(timeout=self.timeout)

        if not _acquire_with_timeout():
            raise AsyncTimeoutError(
                f"Timeout ({self.timeout}s) exceeded while acquiring lock for reading bytes from '{self.path}'",
                timeout=self.timeout,
                path=self.path
            )

        try:
            if not self.path.exists():
                return None
            try:
                return self.path.read_bytes()
            except Exception as e:
                raise FileReadError(f"Failed to read bytes from '{self.path}': {e}") from e
        finally:
            lock.release()

    def write_bytes(self, data: bytes) -> None:
        """
        Writes bytes atomically.
        """
        lock = self._get_lock()

        def _acquire_with_timeout():
            if self.timeout is None:
                lock.acquire()
                return True
            else:
                return lock.acquire(timeout=self.timeout)

        if not _acquire_with_timeout():
            raise AsyncTimeoutError(
                f"Timeout ({self.timeout}s) exceeded while acquiring lock for writing bytes to '{self.path}'",
                timeout=self.timeout,
                path=self.path
            )

        try:
            try:
                with atomic_write(self.path, mode="wb", overwrite=True) as f:
                    f.write(data)
            except Exception as e:
                raise FileWriteError(f"Failed to write bytes to '{self.path}': {e}") from e
        finally:
            lock.release()

    @contextlib.contextmanager
    def locked(self):
        """
        Context manager that holds the file lock for the duration of the context.

        This allows multiple operations to be performed while holding the same lock,
        which is useful for complex operations or when you want to ensure exclusive
        access for a longer period.

        Usage:
            tsf = ThreadedSafeFile('file.yaml', timeout=5.0)
            with tsf.locked() as f:
                data = f.read() or {}
                data['key'] = 'value'
                f.write(data)
                # Lock is held during this entire block
                time.sleep(1)  # Still holding the lock
        """
        lock = self._get_lock()

        def _acquire_with_timeout():
            if self.timeout is None:
                lock.acquire()
                return True
            else:
                return lock.acquire(timeout=self.timeout)

        if not _acquire_with_timeout():
            raise AsyncTimeoutError(
                f"Timeout ({self.timeout}s) exceeded while acquiring lock for '{self.path}'",
                timeout=self.timeout,
                path=self.path
            )

        # Create wrapper class that holds the lock and provides methods without re-acquiring
        class LockedFile:
            def __init__(self, tsf_instance):
                self.tsf = tsf_instance

            def read(self):
                # Don't acquire lock again - we already have it
                if not self.tsf.path.exists():
                    return None
                mode = "rb" if self.tsf.path.suffix.lower() == ".toml" else "r"
                encoding = None if mode == "rb" else "utf-8"
                try:
                    with open(self.tsf.path, mode, encoding=encoding) as f:
                        return load_data(f, self.tsf.path.suffix)
                except Exception as e:
                    raise FileReadError(f"Failed to read '{self.tsf.path}': {e}") from e

            def write(self, data):
                # Don't acquire lock again - we already have it
                try:
                    with atomic_write(self.tsf.path, mode="w", encoding="utf-8", overwrite=True) as f:
                        dump_data(data, f, self.tsf.path.suffix)
                except Exception as e:
                    raise FileWriteError(f"Failed to write '{self.tsf.path}': {e}") from e

            def append(self, text: str):
                # Don't acquire lock again - we already have it
                try:
                    with open(self.tsf.path, "a", encoding="utf-8") as f:
                        f.write(str(text))
                except Exception as e:
                    raise FileAppendError(f"Failed to append to '{self.tsf.path}': {e}") from e

            def read_bytes(self):
                # Don't acquire lock again - we already have it
                if not self.tsf.path.exists():
                    return None
                try:
                    return self.tsf.path.read_bytes()
                except Exception as e:
                    raise FileReadError(f"Failed to read bytes from '{self.tsf.path}': {e}") from e

            def write_bytes(self, data: bytes):
                # Don't acquire lock again - we already have it
                try:
                    with atomic_write(self.tsf.path, mode="wb", overwrite=True) as f:
                        f.write(data)
                except Exception as e:
                    raise FileWriteError(f"Failed to write bytes to '{self.tsf.path}': {e}") from e

        try:
            yield LockedFile(self)
        finally:
            lock.release()

    @staticmethod
    def supported_formats() -> list:
        """
        Lists currently supported file extensions.
        """
        return list_supported_formats()

    @staticmethod
    def cleanup_locks():
        """
        Clean up unused thread locks to prevent memory leaks.
        This is optional and can be called periodically in long-running applications.
        """
        with _thread_locks_lock:
            # Remove locks that are not currently held
            to_remove = []
            for path, lock in _thread_locks.items():
                # For RLock, we can't easily check if it's held, so we'll keep them
                # This is safer and RLocks are lightweight
                pass
            # Note: We don't remove locks automatically because RLock doesn't provide
            # a reliable way to check if it's currently held by any thread
