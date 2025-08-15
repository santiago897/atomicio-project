"""
atomicio - Atomic file operations with different locking strategies

This library provides three file operation classes designed for different use cases:

1. SafeFile - Simple atomic operations
   =====================================
   - Basic atomic file operations with FileLock for inter-process safety
   - Global thread lock for basic thread safety
   - Best for: Simple sync code that needs atomic file operations
   - Each operation (read/write) gets its own lock cycle

   Example:
       from atomicio import SafeFile
       sf = SafeFile('config.json')
       data = sf.read() or {}
       data['setting'] = 'value'
       sf.write(data)

2. ThreadedSafeFile - Cross-operation locking for complex scenarios
   =================================================================
   - Per-file thread locks with proper timeout handling
   - locked() context manager holds locks across multiple operations
   - Best for: Complex sync operations requiring exclusive access across multiple operations

   Example:
       from atomicio import ThreadedSafeFile
       tsf = ThreadedSafeFile('data.json')
       with tsf.locked() as f:
           data = f.read() or {}
           time.sleep(2)  # Still holding lock
           data['batch_operation'] = True
           f.write(data)

3. AsyncSafeFile - Proper async coordination
   ===========================================
   - Per-file async locks with proper async/await support
   - locked() context manager for async cross-operation locking
   - Best for: Async code with proper async coordination

   Example:
       from atomicio import AsyncSafeFile
       asf = AsyncSafeFile('async_data.json')
       async with asf.locked() as f:
           data = await f.read() or {}
           await asyncio.sleep(2)  # Still holding lock
           data['async_operation'] = True
           await f.write(data)

Use SafeFile for basic atomic operations in straightforward sync code.
Use ThreadedSafeFile when you need to hold locks across multiple operations in sync code.
Use AsyncSafeFile for async code with proper async lock coordination.
"""

from .core import (
    SafeFile, AsyncSafeFile, ThreadedSafeFile, resolve_path, create_file, delete_file, find_project_files,
    # Exceptions
    AtomicIOError, FileOperationError, FileReadError, FileWriteError,
    FileAppendError, AsyncTimeoutError, AsyncLockError
)
from .formats import register_format, list_supported_formats
from .version import __version__

# Import defaults so that default formats are registered automatically
from . import defaults

__all__ = [
    "SafeFile", "AsyncSafeFile", "ThreadedSafeFile", "register_format", "list_supported_formats", "resolve_path", "create_file", "delete_file", "find_project_files",
    # Exceptions
    "AtomicIOError", "FileOperationError", "FileReadError", "FileWriteError",
    "FileAppendError", "AsyncTimeoutError", "AsyncLockError"
]