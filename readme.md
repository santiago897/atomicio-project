# 🗃️ Atomicio

[![Python Support](https://img.shields.io/pypi/pyversions/atomicio.svg)](https://pypi.org/project/atomicio/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Code Style: Black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

> 🎯 **Thread-safe, async-safe, and atomic file operations for Python - because data integrity should never be compromised!**

**Atomicio** is a comprehensive Python package that provides robust, thread-safe, and async-safe file operations with proper locking mechanisms. Whether you're building a simple script or a complex multi-threaded application, Atomicio ensures your file operations are reliable, consistent, and corruption-free.

**🔌 Extensible Plugin System**: Seamlessly add support for any file format (CSV, XML, binary, custom) with simple loader/dumper functions. All safety guarantees apply to custom formats automatically!

## ✨ Overview & Class Comparison

### 🔐 **Three Specialized Classes for Different Needs**

Atomicio provides three distinct classes, each optimized for specific use cases and concurrency requirements:

| Class | **SafeFile** | **ThreadedSafeFile** | **AsyncSafeFile** |
|-------|-------------|---------------------|-------------------|
| **🎯 Primary Use** | Basic atomic operations | Complex cross-operation locking | Async applications |
| **🔧 Locking Strategy** | FileLock (inter-process) + Global thread lock | Per-file RLock + FileLock | Per-file AsyncLock + FileLock |
| **⚡ Concurrency** | Thread-safe individual operations | Thread-safe operation sequences | Async-safe operation sequences |
| **🔄 Context Manager** | Basic context (`with SafeFile()`) | Advanced locked context (`with tsf.locked()`) | Async locked context (`async with asf.locked()`) |
| **📊 Performance** | Fastest for simple operations | Optimized for complex workflows | Best for async environments |
| **🎪 Complexity** | Simple and lightweight | Advanced coordination | Async-first design |

### 🧠 **Core Technologies Behind Each Class**

#### **🔒 SafeFile** - Simple Atomic Operations
- **FileLock**: Provides inter-process safety using file system locks
- **Global Thread Lock**: Ensures thread safety within the same process
- **Atomic Write**: Uses temporary files with atomic rename operations
- **Format Detection**: Automatic serialization based on file extensions

#### **🔗 ThreadedSafeFile** - Cross-Operation Coordination
- **Per-File RLock**: Individual threading.RLock for each file path
- **Reentrant Locking**: Same thread can acquire the same lock multiple times
- **Lock Persistence**: Holds locks across multiple operations in `locked()` context
- **Timeout Control**: Configurable timeout for lock acquisition

#### **⚡ AsyncSafeFile** - Async-Native Operations
- **Per-File AsyncLock**: Individual asyncio.Lock for each file path
- **Async Context Managers**: Native `async with` support
- **Non-Blocking Operations**: Designed for asyncio event loops
- **Async Timeout Control**: Proper async timeout handling with cancellation

## 🚀 Quick Start

### Installation

```bash
pip install atomicio
```

### 🎯 Quick Examples

```python
from atomicio import SafeFile, ThreadedSafeFile, AsyncSafeFile
from atomicio import register_format, list_supported_formats  # Plugin system

# 🔒 SafeFile - Simple atomic operations
sf = SafeFile('config.json')
sf.write({'setting': 'value'})
data = sf.read()

# 🔗 ThreadedSafeFile - Complex coordinated operations
tsf = ThreadedSafeFile('data.yaml', timeout=5.0)
with tsf.locked() as f:
    data = f.read() or {}
    data['processed'] = True
    f.write(data)
    # Lock held during entire operation sequence

# ⚡ AsyncSafeFile - Async operations
import asyncio

async def async_example():
    asf = AsyncSafeFile('async_data.json')
    async with asf.locked() as f:
        data = await f.read() or {}
        data['timestamp'] = time.time()
        await f.write(data)

asyncio.run(async_example())

# 🔌 Plugin System - Extend to any file format
def csv_loader(f): return list(csv.DictReader(f))
def csv_dumper(data, f): csv.DictWriter(f, data[0].keys()).writerows(data)

register_format('.csv', csv_loader, csv_dumper)
# Now CSV files work with all classes: SafeFile('data.csv'), etc.
```

---

## 🔒 SafeFile - Simple Atomic Operations

### 🧠 Working Principle

SafeFile is designed for applications that need **basic atomic file operations** with minimal complexity. It combines FileLock for inter-process safety with a global thread lock for intra-process coordination.

**Key Concepts:**
- **Atomic Writes**: Every write operation uses a temporary file that's atomically renamed
- **Format Auto-Detection**: Automatically serializes/deserializes based on file extension (.json, .yaml, .toml, .txt)
- **Inter-Process Safety**: FileLock prevents conflicts between different processes
- **Thread Safety**: Global lock ensures thread safety within the same process
- **Simplicity First**: Minimal API surface for straightforward use cases

**When to Use SafeFile:**
- ✅ Simple configuration file management
- ✅ Basic data persistence needs
- ✅ Applications with minimal concurrency requirements
- ✅ Quick prototyping and scripting
- ❌ Complex multi-step operations requiring lock persistence
- ❌ High-concurrency applications with complex coordination needs

### 📋 Complete API Reference

#### **Constructor**
```python
SafeFile(path, timeout=True)
```
- `path`: File path (str or Path object)
- `timeout`: Lock timeout (True=blocking, False=non-blocking, number=seconds)

#### **Core Methods**
```python
# Read/Write Operations
read() -> Any | None                    # Read and deserialize file content
write(data: Any) -> None               # Write and serialize data atomically
update(data: Any) -> None              # Update existing data (merge for dicts)

# Binary Operations
read_bytes() -> bytes | None           # Read raw bytes
write_bytes(data: bytes) -> None       # Write raw bytes

# Text Operations
append(text: str) -> None              # Append text to file

# Utility Methods
@staticmethod
list_supported_formats() -> list      # List supported file formats ['.json', '.yaml', ...]
```

#### **Context Manager Support**
```python
# Basic context manager
with SafeFile('config.json') as sf:
    data = sf.read()
    sf.write(updated_data)
```

#### **Supported File Formats**
- **`.json`** - JSON format with automatic pretty-printing
- **`.yaml/.yml`** - YAML format with safe loading
- **`.toml`** - TOML format support
- **`.txt`** - Plain text format
- **🔌 Custom formats** - Add any format via the plugin system (CSV, XML, binary, etc.)

#### **Custom Exceptions**
SafeFile raises specific exceptions for different error conditions:
- **`FileReadError`** - When file reading fails (corrupt file, permission issues, etc.)
- **`FileWriteError`** - When file writing fails (disk full, permission denied, etc.)
- **`FileAppendError`** - When appending to file fails (similar to write errors)

### 🎯 Use Case Example: Configuration Manager

<details>
<summary><strong>📖 Click to expand: Complete Configuration Manager Example</strong></summary>

**Scenario**: A web application needs to manage user preferences that can be updated by multiple processes (web workers) and should persist across restarts.

**Why SafeFile is Perfect:**
- Simple key-value storage requirements
- Multiple processes need safe access
- Atomic updates prevent corruption
- No complex coordination needed

```python
from atomicio import SafeFile
import time
from pathlib import Path

class ConfigManager:
    """Thread-safe and process-safe configuration manager using SafeFile."""

    def __init__(self, config_path='app_config.json'):
        self.config_file = SafeFile(config_path, timeout=2.0)
        self._ensure_config_exists()

    def _ensure_config_exists(self):
        """Create default config if file doesn't exist."""
        if not Path(self.config_file.path).exists():
            default_config = {
                'app_name': 'MyWebApp',
                'version': '1.0.0',
                'debug': False,
                'max_connections': 100,
                'created_at': time.time(),
                'user_preferences': {}
            }
            self.config_file.write(default_config)

    def get_setting(self, key, default=None):
        """Get a configuration setting safely."""
        config = self.config_file.read() or {}
        return config.get(key, default)

    def update_setting(self, key, value):
        """Update a single configuration setting atomically."""
        config = self.config_file.read() or {}
        config[key] = value
        config['last_modified'] = time.time()
        self.config_file.write(config)

    def update_user_preference(self, user_id, preference_key, value):
        """Update a user-specific preference safely."""
        config = self.config_file.read() or {}

        # Ensure user preferences structure exists
        if 'user_preferences' not in config:
            config['user_preferences'] = {}
        if user_id not in config['user_preferences']:
            config['user_preferences'][user_id] = {}

        # Update the specific preference
        config['user_preferences'][user_id][preference_key] = value
        config['last_modified'] = time.time()

        # Atomic write ensures consistency
        self.config_file.write(config)

    def get_user_preferences(self, user_id):
        """Get all preferences for a specific user."""
        config = self.config_file.read() or {}
        return config.get('user_preferences', {}).get(user_id, {})

    def reset_to_defaults(self):
        """Reset configuration to default values."""
        current_config = self.config_file.read() or {}

        # Preserve user preferences but reset system settings
        default_config = {
            'app_name': 'MyWebApp',
            'version': '1.0.0',
            'debug': False,
            'max_connections': 100,
            'created_at': current_config.get('created_at', time.time()),
            'last_modified': time.time(),
            'user_preferences': current_config.get('user_preferences', {})
        }

        self.config_file.write(default_config)

# Example usage demonstrating thread and process safety
if __name__ == "__main__":
    # This can be safely used across multiple processes/threads
    config_manager = ConfigManager()

    # Safe updates from multiple workers
    config_manager.update_setting('debug', True)
    config_manager.update_setting('max_connections', 200)

    # Safe user preference updates
    config_manager.update_user_preference('user123', 'theme', 'dark')
    config_manager.update_user_preference('user123', 'language', 'es')
    config_manager.update_user_preference('user456', 'theme', 'light')

    # Read operations are always consistent
    debug_mode = config_manager.get_setting('debug')
    user123_prefs = config_manager.get_user_preferences('user123')

    print(f"Debug mode: {debug_mode}")
    print(f"User123 preferences: {user123_prefs}")

    # Demonstrate format persistence
    import json
    with open('app_config.json', 'r') as f:
        print("Raw file content:")
        print(json.dumps(json.load(f), indent=2))
```

**Key Benefits in this Example:**
- ✅ **Atomic Updates**: No corruption even if process crashes during write
- ✅ **Multi-Process Safe**: Web workers can safely update config simultaneously
- ✅ **Auto-Serialization**: JSON format handled automatically
- ✅ **Simple API**: Minimal code required for robust behavior
- ✅ **Consistent Reads**: Always read complete, valid configuration

</details>

---

## 🔗 ThreadedSafeFile - Cross-Operation Coordination

### 🧠 Working Principle

ThreadedSafeFile is designed for applications that need **complex file operations with cross-operation locking**. It provides advanced coordination capabilities where multiple operations must be performed atomically as a sequence.

**Key Concepts:**
- **Per-File Locking**: Each file path gets its own threading.RLock instance
- **Reentrant Locks**: Same thread can acquire the same file lock multiple times
- **Lock Persistence**: The `locked()` context manager holds the lock across multiple operations
- **Cross-Operation Atomicity**: Ensure no other thread can access the file during complex workflows
- **Timeout Control**: Configurable timeouts prevent deadlocks

**When to Use ThreadedSafeFile:**
- ✅ Complex multi-step file operations that must be atomic
- ✅ Data processing pipelines with intermediate steps
- ✅ Applications requiring cross-operation coordination
- ✅ Multi-threaded applications with complex synchronization needs
- ✅ Scenarios where you need to hold a lock while performing multiple operations
- ❌ Simple single-operation file access (use SafeFile)
- ❌ Async applications (use AsyncSafeFile)

### 📋 Complete API Reference

#### **Constructor**
```python
ThreadedSafeFile(path, timeout=None)
```
- `path`: File path (str or Path object)
- `timeout`: Lock timeout (None=blocking, number=seconds)

#### **Core Methods**
```python
# Read/Write Operations (each acquires and releases lock)
read() -> Any | None                    # Read and deserialize file content
write(data: Any) -> None               # Write and serialize data atomically
update(data: Any) -> None              # Update existing data (merge for dicts)

# Binary Operations
read_bytes() -> bytes | None           # Read raw bytes
write_bytes(data: bytes) -> None       # Write raw bytes

# Text Operations
append(text: str) -> None              # Append text to file

# Utility Methods
@staticmethod
list_supported_formats() -> list      # List supported file formats
```

#### **Advanced Context Manager**
```python
# Cross-operation locking context
with ThreadedSafeFile('data.yaml', timeout=5.0).locked() as f:
    # Lock is held for the entire block
    data = f.read() or {}

    # Perform complex operations while holding lock
    data['step1'] = process_data(data)
    f.write(data)

    data['step2'] = more_processing(data)
    f.write(data)

    # Lock automatically released at the end
```

#### **Lock Behavior**
- **Individual Operations**: Each `read()`, `write()`, etc. acquires and releases lock
- **Locked Context**: `locked()` holds the lock for the entire context duration
- **Reentrant**: Same thread can call `read()`, `write()` within `locked()` context
- **Per-File**: Different files have independent locks
- **Timeout**: Configurable timeout prevents indefinite blocking

#### **Custom Exceptions**
ThreadedSafeFile raises specific exceptions for different error conditions:
- **`FileReadError`** - When file reading fails (corrupt file, permission issues, etc.)
- **`FileWriteError`** - When file writing fails (disk full, permission denied, etc.)
- **`FileAppendError`** - When appending to file fails (similar to write errors)
- **`AsyncTimeoutError`** - When lock acquisition times out (prevents deadlocks)

### 🎯 Use Case Example: Data Processing Pipeline

<details>
<summary><strong>📖 Click to expand: Complete Data Processing Pipeline Example</strong></summary>

**Scenario**: A multi-threaded data analysis application where multiple workers process large datasets. Each processing stage must be atomic, and intermediate results must be safely stored and passed between stages.

**Why ThreadedSafeFile is Perfect:**
- Complex multi-stage processing requires cross-operation locking
- Multiple threads working on the same dataset files
- Intermediate results must be consistent
- Need to prevent race conditions during processing stages

```python
from atomicio import ThreadedSafeFile
import time
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from typing import List, Dict, Any
import hashlib

@dataclass
class ProcessingJob:
    """Represents a data processing job."""
    job_id: str
    input_data: List[int]
    stages_completed: List[str]
    results: Dict[str, Any]
    created_at: float
    updated_at: float

class DataProcessor:
    """
    Multi-threaded data processor using ThreadedSafeFile for safe coordination.

    This demonstrates ThreadedSafeFile's strength in complex workflows where
    multiple operations must be performed atomically as a sequence.
    """

    def __init__(self, results_file='processing_results.json'):
        self.results_file = ThreadedSafeFile(results_file, timeout=10.0)
        self.active_jobs = ThreadedSafeFile('active_jobs.json', timeout=5.0)
        self._ensure_files_exist()

    def _ensure_files_exist(self):
        """Initialize result files if they don't exist."""
        # Using individual operations for simple initialization
        if self.results_file.read() is None:
            self.results_file.write({'completed_jobs': {}, 'stats': {'total_processed': 0}})

        if self.active_jobs.read() is None:
            self.active_jobs.write({'jobs': {}, 'worker_assignments': {}})

    def submit_job(self, data: List[int]) -> str:
        """Submit a new processing job safely."""
        job_id = hashlib.md5(str(data).encode()).hexdigest()[:8]
        timestamp = time.time()

        job = ProcessingJob(
            job_id=job_id,
            input_data=data,
            stages_completed=[],
            results={},
            created_at=timestamp,
            updated_at=timestamp
        )

        # Use locked context for multi-step job submission
        with self.active_jobs.locked() as f:
            active_data = f.read()

            # Check if job already exists
            if job_id in active_data['jobs']:
                return job_id  # Job already submitted

            # Add new job and update worker assignment
            active_data['jobs'][job_id] = job.__dict__
            active_data['worker_assignments'][job_id] = None  # Not assigned yet

            f.write(active_data)
            print(f"✅ Job {job_id} submitted successfully")

        return job_id

    def process_stage_1_validation(self, job_id: str, worker_id: str) -> bool:
        """Stage 1: Validate input data (requires cross-operation locking)."""
        print(f"🔍 Worker {worker_id} starting Stage 1 (validation) for job {job_id}")

        with self.active_jobs.locked() as f:
            active_data = f.read()

            if job_id not in active_data['jobs']:
                print(f"❌ Job {job_id} not found")
                return False

            job_data = active_data['jobs'][job_id]

            # Assign worker if not already assigned
            if active_data['worker_assignments'][job_id] is None:
                active_data['worker_assignments'][job_id] = worker_id
                print(f"👷 Worker {worker_id} assigned to job {job_id}")
            elif active_data['worker_assignments'][job_id] != worker_id:
                print(f"⚠️  Job {job_id} already assigned to another worker")
                return False

            # Perform validation
            input_data = job_data['input_data']
            if not input_data or len(input_data) == 0:
                print(f"❌ Invalid input data for job {job_id}")
                return False

            # Update job progress (multiple operations under same lock)
            job_data['stages_completed'].append('validation')
            job_data['results']['validation'] = {
                'data_length': len(input_data),
                'data_range': [min(input_data), max(input_data)],
                'validation_time': time.time()
            }
            job_data['updated_at'] = time.time()

            # Save updated job state
            active_data['jobs'][job_id] = job_data
            f.write(active_data)

            print(f"✅ Stage 1 (validation) completed for job {job_id}")
            return True

    def process_stage_2_computation(self, job_id: str, worker_id: str) -> bool:
        """Stage 2: Heavy computation (requires lock persistence)."""
        print(f"🧮 Worker {worker_id} starting Stage 2 (computation) for job {job_id}")

        with self.active_jobs.locked() as f:
            active_data = f.read()

            if job_id not in active_data['jobs']:
                return False

            job_data = active_data['jobs'][job_id]

            # Verify worker assignment and prerequisites
            if active_data['worker_assignments'][job_id] != worker_id:
                print(f"⚠️  Worker {worker_id} not assigned to job {job_id}")
                return False

            if 'validation' not in job_data['stages_completed']:
                print(f"⚠️  Job {job_id} hasn't completed validation stage")
                return False

            # Perform computation while holding lock (simulated work)
            input_data = job_data['input_data']
            print(f"🔄 Computing results for {len(input_data)} data points...")

            # Simulate processing time
            time.sleep(0.5)

            # Heavy computation results
            results = {
                'sum': sum(input_data),
                'average': sum(input_data) / len(input_data),
                'squared_sum': sum(x*x for x in input_data),
                'computation_time': time.time()
            }

            # Update job with computation results
            job_data['stages_completed'].append('computation')
            job_data['results']['computation'] = results
            job_data['updated_at'] = time.time()

            active_data['jobs'][job_id] = job_data
            f.write(active_data)

            print(f"✅ Stage 2 (computation) completed for job {job_id}")
            return True

    def process_stage_3_finalization(self, job_id: str, worker_id: str) -> bool:
        """Stage 3: Finalize and move to completed (complex cross-file operation)."""
        print(f"🏁 Worker {worker_id} starting Stage 3 (finalization) for job {job_id}")

        # This demonstrates the power of ThreadedSafeFile: coordinating multiple files
        with self.active_jobs.locked() as active_f:
            active_data = active_f.read()

            if job_id not in active_data['jobs']:
                return False

            job_data = active_data['jobs'][job_id]

            # Verify prerequisites
            required_stages = ['validation', 'computation']
            if not all(stage in job_data['stages_completed'] for stage in required_stages):
                print(f"⚠️  Job {job_id} missing required stages")
                return False

            # Finalize results
            final_results = {
                'job_id': job_id,
                'input_length': len(job_data['input_data']),
                'validation_results': job_data['results']['validation'],
                'computation_results': job_data['results']['computation'],
                'total_processing_time': time.time() - job_data['created_at'],
                'completed_at': time.time(),
                'processed_by': worker_id
            }

            # Remove from active jobs
            del active_data['jobs'][job_id]
            del active_data['worker_assignments'][job_id]
            active_f.write(active_data)

        # Now update completed jobs (separate file operation)
        with self.results_file.locked() as results_f:
            results_data = results_f.read()

            # Add to completed jobs
            results_data['completed_jobs'][job_id] = final_results
            results_data['stats']['total_processed'] += 1

            results_f.write(results_data)

            print(f"🎉 Job {job_id} completed and finalized!")
            return True

    def process_job_complete_pipeline(self, job_id: str, worker_id: str) -> bool:
        """Process a complete job through all stages."""
        try:
            # Each stage can be called independently or as part of a pipeline
            if not self.process_stage_1_validation(job_id, worker_id):
                return False

            if not self.process_stage_2_computation(job_id, worker_id):
                return False

            if not self.process_stage_3_finalization(job_id, worker_id):
                return False

            return True

        except Exception as e:
            print(f"❌ Error processing job {job_id}: {e}")
            return False

    def get_processing_status(self) -> Dict[str, Any]:
        """Get current processing status (demonstrates safe read operations)."""
        active_data = self.active_jobs.read() or {'jobs': {}, 'worker_assignments': {}}
        results_data = self.results_file.read() or {'completed_jobs': {}, 'stats': {'total_processed': 0}}

        return {
            'active_jobs': len(active_data['jobs']),
            'completed_jobs': len(results_data['completed_jobs']),
            'total_processed': results_data['stats']['total_processed'],
            'worker_assignments': active_data['worker_assignments']
        }

# Example usage demonstrating complex multi-threaded processing
if __name__ == "__main__":
    processor = DataProcessor()

    # Submit multiple jobs
    jobs = []
    test_datasets = [
        [1, 2, 3, 4, 5],
        [10, 20, 30, 40, 50, 60],
        [100, 200, 300],
        [1, 3, 5, 7, 9, 11, 13, 15]
    ]

    for i, dataset in enumerate(test_datasets):
        job_id = processor.submit_job(dataset)
        jobs.append(job_id)
        print(f"Submitted job {i+1}: {job_id}")

    # Process jobs with multiple workers
    def worker_task(worker_id, job_ids):
        """Worker function that processes assigned jobs."""
        results = []
        for job_id in job_ids:
            print(f"\n🚀 Worker {worker_id} processing job {job_id}")
            success = processor.process_job_complete_pipeline(job_id, worker_id)
            results.append((job_id, success))
            time.sleep(0.1)  # Brief pause between jobs
        return results

    # Run with multiple workers
    with ThreadPoolExecutor(max_workers=3) as executor:
        # Distribute jobs among workers
        worker_jobs = [jobs[i::3] for i in range(3)]  # Round-robin distribution

        futures = []
        for i, job_list in enumerate(worker_jobs):
            if job_list:  # Only submit if worker has jobs
                future = executor.submit(worker_task, f"Worker-{i+1}", job_list)
                futures.append(future)

        # Wait for all workers to complete
        all_results = []
        for future in as_completed(futures):
            worker_results = future.result()
            all_results.extend(worker_results)
            print(f"Worker completed {len(worker_results)} jobs")

    # Show final status
    print("\n📊 Final Processing Status:")
    status = processor.get_processing_status()
    for key, value in status.items():
        print(f"  {key}: {value}")

    # Demonstrate successful coordination
    if status['active_jobs'] == 0 and status['completed_jobs'] == len(jobs):
        print("\n🎉 All jobs processed successfully with perfect coordination!")
    else:
        print(f"\n⚠️  Some jobs may have failed. Check the logs.")
```

**Key Benefits in this Example:**
- ✅ **Cross-Operation Atomicity**: Multiple file operations within `locked()` contexts are atomic
- ✅ **Perfect Coordination**: No race conditions between workers processing the same files
- ✅ **Complex Workflows**: Multi-stage processing with proper synchronization
- ✅ **Reentrant Safety**: Workers can call methods that internally use locks
- ✅ **Timeout Protection**: Configurable timeouts prevent deadlocks
- ✅ **Per-File Granularity**: Different files can be accessed independently

</details>

---

## ⚡ AsyncSafeFile - Async-Native Operations

### 🧠 Working Principle

AsyncSafeFile is designed specifically for **asyncio-based applications** that need thread-safe file operations without blocking the event loop. It provides native async support with proper async context managers and lock coordination.

**Key Concepts:**
- **Async-Native**: All operations are `async`/`await` compatible
- **Per-File AsyncLock**: Each file path gets its own `asyncio.Lock` instance
- **Non-Blocking**: Designed to work seamlessly with asyncio event loops
- **Async Context Managers**: `async with asf.locked()` for cross-operation coordination
- **Async Timeout Control**: Proper async timeout handling with task cancellation
- **Event Loop Safe**: All operations are safe within asyncio applications

**When to Use AsyncSafeFile:**
- ✅ Asyncio-based applications (FastAPI, aiohttp, etc.)
- ✅ Async web servers and APIs
- ✅ Async data processing pipelines
- ✅ Applications using async/await patterns
- ✅ Non-blocking file operations in event loops
- ❌ Synchronous applications (use SafeFile or ThreadedSafeFile)
- ❌ Simple scripts without async requirements

### 📋 Complete API Reference

#### **Constructor**
```python
AsyncSafeFile(path, timeout=None)
```
- `path`: File path (str or Path object)
- `timeout`: Lock timeout (None=no timeout, number=seconds)

#### **Core Async Methods**
```python
# Read/Write Operations (all async)
async read() -> Any | None              # Read and deserialize file content
async write(data: Any) -> None          # Write and serialize data atomically
async update(data: Any) -> None         # Update existing data (merge for dicts)

# Binary Operations
async read_bytes() -> bytes | None      # Read raw bytes
async write_bytes(data: bytes) -> None  # Write raw bytes

# Text Operations
async append(text: str) -> None         # Append text to file

# Utility Methods
@staticmethod
list_supported_formats() -> list       # List supported file formats (sync)
```

#### **Async Context Manager**
```python
# Cross-operation async locking context
async with AsyncSafeFile('data.json', timeout=5.0).locked() as f:
    # Async lock is held for the entire block
    data = await f.read() or {}

    # Perform complex async operations while holding lock
    data['step1'] = await async_process_data(data)
    await f.write(data)

    data['step2'] = await more_async_processing(data)
    await f.write(data)

    # Lock automatically released at the end
```

#### **Async Lock Behavior**
- **Individual Operations**: Each `await read()`, `await write()`, etc. acquires and releases lock
- **Locked Context**: `async with locked()` holds the lock for the entire context duration
- **Async-Safe**: Designed for asyncio event loops and coroutines
- **Per-File**: Different files have independent async locks
- **Timeout**: Async timeout with proper task cancellation

#### **Custom Exceptions**
AsyncSafeFile raises specific exceptions for different error conditions:
- **`FileReadError`** - When file reading fails (corrupt file, permission issues, etc.)
- **`FileWriteError`** - When file writing fails (disk full, permission denied, etc.)
- **`FileAppendError`** - When appending to file fails (similar to write errors)
- **`AsyncTimeoutError`** - When async operations timeout (includes timeout details)
- **`AsyncLockError`** - When async lock operations fail unexpectedly

### 🎯 Use Case Example: Async Web API with Data Processing

<details>
<summary><strong>📖 Click to expand: Complete Async Web API Example</strong></summary>

**Scenario**: A FastAPI-based web service that processes user uploads, analyzes data asynchronously, and stores results. Multiple async workers handle requests concurrently, and file operations must be coordinated without blocking the event loop.

**Why AsyncSafeFile is Perfect:**
- FastAPI async endpoints require non-blocking operations
- Multiple concurrent requests processing the same data files
- Need async coordination for complex data processing workflows
- Event loop must never be blocked by file I/O

```python
from atomicio import AsyncSafeFile
import asyncio
import time
import aiohttp
import aiofiles
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
from fastapi import FastAPI, UploadFile, HTTPException
import uvicorn
import hashlib
import json
from pathlib import Path

@dataclass
class AnalysisTask:
    """Represents an async data analysis task."""
    task_id: str
    filename: str
    status: str  # 'pending', 'processing', 'completed', 'failed'
    created_at: float
    started_at: Optional[float] = None
    completed_at: Optional[float] = None
    results: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None

class AsyncDataAnalyzer:
    """
    Async data analyzer using AsyncSafeFile for coordinated file operations.

    This demonstrates AsyncSafeFile's strength in async web applications where
    multiple coroutines need coordinated access to shared data files.
    """

    def __init__(self, data_dir: str = "analysis_data"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(exist_ok=True)

        # File managers for different data types
        self.tasks_file = AsyncSafeFile(self.data_dir / 'tasks.json', timeout=5.0)
        self.results_file = AsyncSafeFile(self.data_dir / 'results.json', timeout=5.0)
        self.analytics_file = AsyncSafeFile(self.data_dir / 'analytics.json', timeout=3.0)

    async def initialize(self):
        """Initialize data files asynchronously."""
        # Initialize tasks file
        if await self.tasks_file.read() is None:
            await self.tasks_file.write({'active_tasks': {}, 'task_queue': []})

        # Initialize results file
        if await self.results_file.read() is None:
            await self.results_file.write({'completed_analyses': {}, 'stats': {'total_completed': 0}})

        # Initialize analytics file
        if await self.analytics_file.read() is None:
            await self.analytics_file.write({
                'daily_stats': {},
                'performance_metrics': {'avg_processing_time': 0, 'total_requests': 0}
            })

    async def submit_analysis_task(self, file_content: bytes, filename: str) -> str:
        """Submit a new analysis task asynchronously."""
        # Generate task ID
        task_id = hashlib.md5(f"{filename}{time.time()}".encode()).hexdigest()[:12]

        # Save uploaded file
        file_path = self.data_dir / f"upload_{task_id}.json"

        try:
            # Parse uploaded JSON data
            data = json.loads(file_content.decode('utf-8'))

            # Save the uploaded data
            upload_file = AsyncSafeFile(file_path, timeout=3.0)
            await upload_file.write(data)

        except (json.JSONDecodeError, UnicodeDecodeError) as e:
            raise ValueError(f"Invalid JSON file: {str(e)}")

        # Create task record
        task = AnalysisTask(
            task_id=task_id,
            filename=filename,
            status='pending',
            created_at=time.time()
        )

        # Add task to queue using locked context for consistency
        async with self.tasks_file.locked() as f:
            tasks_data = await f.read()

            # Add to active tasks and queue
            tasks_data['active_tasks'][task_id] = asdict(task)
            tasks_data['task_queue'].append(task_id)

            await f.write(tasks_data)

        print(f"✅ Task {task_id} submitted for file: {filename}")

        # Start processing in background (don't await)
        asyncio.create_task(self._process_analysis_task(task_id))

        return task_id

    async def _process_analysis_task(self, task_id: str):
        """Process an analysis task asynchronously (background coroutine)."""
        try:
            print(f"🚀 Starting async processing for task {task_id}")

            # Update task status to processing
            async with self.tasks_file.locked() as f:
                tasks_data = await f.read()

                if task_id not in tasks_data['active_tasks']:
                    print(f"❌ Task {task_id} not found")
                    return

                task_data = tasks_data['active_tasks'][task_id]
                task_data['status'] = 'processing'
                task_data['started_at'] = time.time()

                await f.write(tasks_data)

            # Load the data file for analysis
            data_file = AsyncSafeFile(self.data_dir / f"upload_{task_id}.json", timeout=3.0)
            data = await data_file.read()

            if data is None:
                raise ValueError("Data file not found or corrupted")

            # Perform async analysis (simulated complex processing)
            results = await self._perform_async_analysis(data, task_id)

            # Move task to completed using coordinated async operations
            await self._complete_task(task_id, results)

        except Exception as e:
            await self._fail_task(task_id, str(e))

    async def _perform_async_analysis(self, data: Dict[str, Any], task_id: str) -> Dict[str, Any]:
        """Perform the actual data analysis asynchronously."""
        print(f"🧮 Analyzing data for task {task_id}...")

        # Simulate async processing with various operations
        await asyncio.sleep(1.0)  # Simulate I/O or computation

        # Extract numeric data for analysis
        numeric_values = []

        def extract_numbers(obj):
            if isinstance(obj, (int, float)):
                numeric_values.append(obj)
            elif isinstance(obj, dict):
                for value in obj.values():
                    extract_numbers(value)
            elif isinstance(obj, list):
                for item in obj:
                    extract_numbers(item)

        extract_numbers(data)

        # Simulate more async work
        await asyncio.sleep(0.5)

        # Calculate analysis results
        if numeric_values:
            results = {
                'data_points': len(numeric_values),
                'sum': sum(numeric_values),
                'average': sum(numeric_values) / len(numeric_values),
                'min_value': min(numeric_values),
                'max_value': max(numeric_values),
                'variance': await self._calculate_variance_async(numeric_values)
            }
        else:
            results = {
                'data_points': 0,
                'message': 'No numeric data found for analysis'
            }

        results['analysis_time'] = time.time()
        results['data_structure_info'] = await self._analyze_structure_async(data)

        return results

    async def _calculate_variance_async(self, values: List[float]) -> float:
        """Calculate variance asynchronously (simulated async math operation)."""
        await asyncio.sleep(0.1)  # Simulate async computation

        mean = sum(values) / len(values)
        variance = sum((x - mean) ** 2 for x in values) / len(values)
        return variance

    async def _analyze_structure_async(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze data structure asynchronously."""
        await asyncio.sleep(0.2)  # Simulate async operation

        def count_types(obj, counts=None):
            if counts is None:
                counts = {'dict': 0, 'list': 0, 'str': 0, 'int': 0, 'float': 0, 'bool': 0, 'null': 0}

            if isinstance(obj, dict):
                counts['dict'] += 1
                for value in obj.values():
                    count_types(value, counts)
            elif isinstance(obj, list):
                counts['list'] += 1
                for item in obj:
                    count_types(item, counts)
            elif isinstance(obj, str):
                counts['str'] += 1
            elif isinstance(obj, int):
                counts['int'] += 1
            elif isinstance(obj, float):
                counts['float'] += 1
            elif isinstance(obj, bool):
                counts['bool'] += 1
            elif obj is None:
                counts['null'] += 1

            return counts

        return count_types(data)

    async def _complete_task(self, task_id: str, results: Dict[str, Any]):
        """Complete a task and update all relevant files atomically."""
        completion_time = time.time()

        # Complex multi-file coordination using async locked contexts
        async with self.tasks_file.locked() as tasks_f:
            tasks_data = await tasks_f.read()

            if task_id not in tasks_data['active_tasks']:
                print(f"⚠️  Task {task_id} not found in active tasks")
                return

            task_data = tasks_data['active_tasks'][task_id]

            # Update task completion info
            task_data['status'] = 'completed'
            task_data['completed_at'] = completion_time
            task_data['results'] = results

            # Remove from active tasks and queue
            del tasks_data['active_tasks'][task_id]
            if task_id in tasks_data['task_queue']:
                tasks_data['task_queue'].remove(task_id)

            await tasks_f.write(tasks_data)

        # Update results file
        async with self.results_file.locked() as results_f:
            results_data = await results_f.read()

            # Add completed task
            results_data['completed_analyses'][task_id] = {
                'task_id': task_id,
                'filename': task_data['filename'],
                'completed_at': completion_time,
                'processing_time': completion_time - task_data['started_at'],
                'results': results
            }

            results_data['stats']['total_completed'] += 1

            await results_f.write(results_data)

        # Update analytics
        await self._update_analytics(task_data['started_at'], completion_time)

        print(f"✅ Task {task_id} completed successfully")

    async def _fail_task(self, task_id: str, error_message: str):
        """Mark a task as failed."""
        print(f"❌ Task {task_id} failed: {error_message}")

        async with self.tasks_file.locked() as f:
            tasks_data = await f.read()

            if task_id in tasks_data['active_tasks']:
                task_data = tasks_data['active_tasks'][task_id]
                task_data['status'] = 'failed'
                task_data['error_message'] = error_message
                task_data['completed_at'] = time.time()

                # Keep failed tasks in active_tasks for debugging
                await f.write(tasks_data)

    async def _update_analytics(self, started_at: float, completed_at: float):
        """Update analytics with processing performance."""
        processing_time = completed_at - started_at

        async with self.analytics_file.locked() as f:
            analytics_data = await f.read()

            # Update performance metrics
            metrics = analytics_data['performance_metrics']
            total_requests = metrics['total_requests']
            current_avg = metrics['avg_processing_time']

            # Calculate new average
            new_total = total_requests + 1
            new_avg = ((current_avg * total_requests) + processing_time) / new_total

            metrics['total_requests'] = new_total
            metrics['avg_processing_time'] = new_avg

            # Update daily stats
            today = time.strftime('%Y-%m-%d')
            if today not in analytics_data['daily_stats']:
                analytics_data['daily_stats'][today] = {'count': 0, 'total_time': 0}

            analytics_data['daily_stats'][today]['count'] += 1
            analytics_data['daily_stats'][today]['total_time'] += processing_time

            await f.write(analytics_data)

    async def get_task_status(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Get status of a specific task."""
        # Check active tasks first
        tasks_data = await self.tasks_file.read()
        if task_id in tasks_data['active_tasks']:
            return tasks_data['active_tasks'][task_id]

        # Check completed tasks
        results_data = await self.results_file.read()
        if task_id in results_data['completed_analyses']:
            return results_data['completed_analyses'][task_id]

        return None

    async def get_analytics_summary(self) -> Dict[str, Any]:
        """Get comprehensive analytics summary."""
        analytics_data = await self.analytics_file.read()
        results_data = await self.results_file.read()
        tasks_data = await self.tasks_file.read()

        return {
            'performance_metrics': analytics_data['performance_metrics'],
            'daily_stats': analytics_data['daily_stats'],
            'current_status': {
                'active_tasks': len(tasks_data['active_tasks']),
                'queued_tasks': len(tasks_data['task_queue']),
                'total_completed': results_data['stats']['total_completed']
            }
        }

# FastAPI application demonstrating AsyncSafeFile in web context
app = FastAPI(title="Async Data Analyzer", version="1.0.0")
analyzer = AsyncDataAnalyzer()

@app.on_event("startup")
async def startup_event():
    """Initialize the analyzer on startup."""
    await analyzer.initialize()
    print("🚀 Async Data Analyzer initialized")

@app.post("/analyze/")
async def upload_and_analyze(file: UploadFile):
    """Upload a JSON file for analysis."""
    if not file.filename.endswith('.json'):
        raise HTTPException(status_code=400, detail="Only JSON files are supported")

    try:
        # Read file content asynchronously
        content = await file.read()

        # Submit for analysis
        task_id = await analyzer.submit_analysis_task(content, file.filename)

        return {
            "message": "File uploaded and analysis started",
            "task_id": task_id,
            "status": "pending"
        }

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")

@app.get("/status/{task_id}")
async def get_analysis_status(task_id: str):
    """Get the status of an analysis task."""
    status = await analyzer.get_task_status(task_id)

    if status is None:
        raise HTTPException(status_code=404, detail="Task not found")

    return status

@app.get("/analytics/")
async def get_analytics():
    """Get comprehensive analytics summary."""
    return await analyzer.get_analytics_summary()

@app.get("/health/")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "timestamp": time.time()}

# Example usage and testing
async def example_usage():
    """Demonstrate the async analyzer with multiple concurrent operations."""
    analyzer = AsyncDataAnalyzer()
    await analyzer.initialize()

    # Sample data for testing
    test_data = [
        {"name": "dataset1", "values": [1, 2, 3, 4, 5], "metadata": {"source": "test"}},
        {"name": "dataset2", "values": [10, 20, 30], "metrics": {"accuracy": 0.95}},
        {"name": "dataset3", "data": {"x": [1, 2, 3], "y": [4, 5, 6]}, "config": {"normalize": True}}
    ]

    # Submit multiple tasks concurrently
    tasks = []
    for i, data in enumerate(test_data):
        content = json.dumps(data).encode('utf-8')
        task_id = await analyzer.submit_analysis_task(content, f"test_file_{i+1}.json")
        tasks.append(task_id)
        print(f"Submitted task {i+1}: {task_id}")

    # Wait for all tasks to complete
    print("\n⏳ Waiting for tasks to complete...")
    await asyncio.sleep(3)  # Give time for processing

    # Check results
    print("\n📊 Task Results:")
    for task_id in tasks:
        status = await analyzer.get_task_status(task_id)
        if status:
            print(f"Task {task_id}: {status['status']}")
            if status['status'] == 'completed' and 'results' in status:
                results = status['results']
                print(f"  - Data points: {results.get('data_points', 'N/A')}")
                print(f"  - Average: {results.get('average', 'N/A')}")

    # Show analytics
    print("\n📈 Analytics Summary:")
    analytics = await analyzer.get_analytics_summary()
    print(f"  - Total completed: {analytics['current_status']['total_completed']}")
    print(f"  - Average processing time: {analytics['performance_metrics']['avg_processing_time']:.2f}s")

if __name__ == "__main__":
    # Run the example
    print("🧪 Running AsyncSafeFile example...")
    asyncio.run(example_usage())

    # To run the FastAPI server:
    # uvicorn script_name:app --reload
```

**Key Benefits in this Example:**
- ✅ **Non-Blocking**: All file operations are async and don't block the event loop
- ✅ **Concurrent Safety**: Multiple async requests can safely access shared files
- ✅ **Async Coordination**: Complex multi-file operations are properly coordinated
- ✅ **Event Loop Friendly**: Perfect integration with FastAPI and asyncio patterns
- ✅ **Scalable**: Can handle many concurrent requests without blocking
- ✅ **Async Context Management**: `async with locked()` provides safe cross-operation coordination

</details>

---

## � Exception Handling & Error Management

### 🎯 Exception Hierarchy

Atomicio provides a comprehensive exception hierarchy for precise error handling:

```python
AtomicIOError                    # Base exception for all atomicio operations
├── FileOperationError           # Base for file I/O related errors
│   ├── FileReadError           # File reading failures
│   ├── FileWriteError          # File writing failures
│   └── FileAppendError         # File appending failures
├── AsyncTimeoutError           # Async/threading timeout errors
└── AsyncLockError              # Async lock operation failures
```

### 🔧 Importing Exceptions

```python
from atomicio import (
    # Main classes
    SafeFile, ThreadedSafeFile, AsyncSafeFile,
    # Exceptions
    AtomicIOError, FileReadError, FileWriteError,
    FileAppendError, AsyncTimeoutError, AsyncLockError
)
```

### 🎯 Exception Handling Examples

#### **Basic Error Handling**
```python
from atomicio import SafeFile, FileReadError, FileWriteError

def safe_config_update(config_path, updates):
    """Update configuration with proper error handling."""
    config_file = SafeFile(config_path)

    try:
        # Try to read existing config
        config = config_file.read() or {}

    except FileReadError as e:
        print(f"Failed to read config: {e}")
        return False

    try:
        # Update and write back
        config.update(updates)
        config_file.write(config)
        return True

    except FileWriteError as e:
        print(f"Failed to save config: {e}")
        return False
```

#### **Timeout Handling with ThreadedSafeFile**
```python
from atomicio import ThreadedSafeFile, AsyncTimeoutError

def process_with_timeout(data_path, timeout_seconds=10):
    """Process data with timeout protection."""
    data_file = ThreadedSafeFile(data_path, timeout=timeout_seconds)

    try:
        with data_file.locked() as f:
            data = f.read() or {}
            # Long processing operation
            processed_data = heavy_processing(data)
            f.write(processed_data)

    except AsyncTimeoutError as e:
        print(f"Operation timed out after {e.timeout}s on file {e.path}")
        return None
    except (FileReadError, FileWriteError) as e:
        print(f"File operation failed: {e}")
        return None
```

#### **Async Error Handling**
```python
from atomicio import AsyncSafeFile, AsyncTimeoutError, AsyncLockError

async def async_data_processor(file_path):
    """Async data processing with comprehensive error handling."""
    data_file = AsyncSafeFile(file_path, timeout=5.0)

    try:
        async with data_file.locked() as f:
            data = await f.read() or {}
            processed = await async_heavy_processing(data)
            await f.write(processed)
            return processed

    except AsyncTimeoutError as e:
        print(f"Async timeout ({e.timeout}s): {e}")
        return None

    except AsyncLockError as e:
        print(f"Async lock error: {e}")
        return None

    except (FileReadError, FileWriteError, FileAppendError) as e:
        print(f"File operation error: {e}")
        return None
```

#### **Generic Exception Handling**
```python
from atomicio import SafeFile, AtomicIOError

def robust_file_operation(file_path, data):
    """Handle any atomicio exception generically."""
    file_obj = SafeFile(file_path)

    try:
        file_obj.write(data)
        return True

    except AtomicIOError as e:
        # Catches any atomicio-specific exception
        print(f"Atomicio error: {type(e).__name__}: {e}")
        return False

    except Exception as e:
        # Catch any other unexpected errors
        print(f"Unexpected error: {e}")
        return False
```

<details>
<summary><strong>🎯 Best Practices for Exception Handling</strong></summary>

#### **✅ Recommended Patterns**
- **Specific Exceptions**: Catch specific exceptions (`FileReadError`) rather than generic ones
- **Timeout Handling**: Always handle `AsyncTimeoutError` when using timeouts
- **Graceful Degradation**: Provide fallback behavior when operations fail
- **Logging**: Log exceptions with context information for debugging

#### **❌ Avoid These Patterns**
```python
# Don't do this - too generic
try:
    safe_file.write(data)
except Exception:
    pass  # Silent failures are bad

# Don't do this - missing timeout handling
threaded_file = ThreadedSafeFile('data.json', timeout=5)
# No try/except for AsyncTimeoutError

# Don't do this - no error context
try:
    result = safe_file.read()
except FileReadError:
    print("Read failed")  # No details about what/why
```

#### **✅ Better Patterns**
```python
# Specific exception handling with context
try:
    safe_file.write(data)
except FileWriteError as e:
    logger.error(f"Failed to write {safe_file.path}: {e}")
    raise  # Re-raise if appropriate

# Complete timeout and error handling
try:
    with threaded_file.locked() as f:
        data = f.read()
        f.write(processed_data)
except AsyncTimeoutError as e:
    logger.warning(f"Lock timeout ({e.timeout}s) for {e.path}")
    return None
except (FileReadError, FileWriteError) as e:
    logger.error(f"File operation failed: {e}")
    return None

# Informative error handling
try:
    result = safe_file.read()
except FileReadError as e:
    logger.error(f"Cannot read config from {safe_file.path}: {e}")
    # Provide fallback or default behavior
    result = get_default_config()
```

</details>

---

## �🔌 Plugin System & Custom File Formats

### 🎯 Overview

Atomicio provides a powerful plugin system that allows you to seamlessly extend support to any file format. Whether you need CSV, XML, binary formats, or custom serialization, the plugin system makes it easy to integrate new formats while maintaining all the atomic safety guarantees.

**Key Features:**
- ✅ **Simple Registration**: Register new formats with just a few lines of code
- ✅ **Entry Point Support**: Distribute plugins as separate packages
- ✅ **Format Auto-Detection**: Automatic format detection based on file extensions
- ✅ **Full Integration**: Custom formats work with all three classes (SafeFile, ThreadedSafeFile, AsyncSafeFile)
- ✅ **Consistent API**: Same `read()`, `write()`, `update()` methods for all formats

### 🛠️ Core Plugin Functions

#### **`register_format(ext, loader, dumper)`**
Register a new file format with custom serialization/deserialization functions.

```python
from atomicio import register_format

def register_format(ext: str, loader: Callable[[IO], Any], dumper: Callable[[Any, IO], None]) -> None:
    """
    Register a loader/dumper pair for a file extension.

    Args:
        ext: File extension (with or without dot, e.g. '.csv' or 'csv')
        loader: Function that reads from a file-like object and returns data
        dumper: Function that writes data to a file-like object

    Example:
        register_format('.csv', csv_loader, csv_dumper)
    """
```

#### **`list_supported_formats()`**
Get a list of all currently supported file formats.

```python
from atomicio import list_supported_formats

# Get all supported extensions
formats = list_supported_formats()
print(formats)  # ['.json', '.yaml', '.yml', '.toml', '.txt', '.csv', ...]
```

### 📝 Creating Custom Format Plugins

#### **Example 1: CSV Format Plugin**

<details>
<summary><strong>📊 Click to expand: Complete CSV Plugin Example</strong></summary>

```python
import csv
import io
from atomicio import register_format, SafeFile

def csv_loader(file_obj):
    """Load CSV data into a list of dictionaries."""
    # Reset file pointer to beginning
    file_obj.seek(0)
    content = file_obj.read()

    if not content.strip():
        return []

    # Use StringIO to handle CSV parsing
    csv_data = io.StringIO(content)
    reader = csv.DictReader(csv_data)
    return list(reader)

def csv_dumper(data, file_obj):
    """Write data as CSV format."""
    if not data:
        return

    # Assume data is a list of dictionaries
    if isinstance(data, list) and len(data) > 0 and isinstance(data[0], dict):
        fieldnames = data[0].keys()
        writer = csv.DictWriter(file_obj, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(data)
    else:
        raise ValueError("CSV format requires a list of dictionaries")

# Register the CSV format
register_format('.csv', csv_loader, csv_dumper)

# Now CSV files work seamlessly with all Atomicio classes!
csv_file = SafeFile('data.csv')

# Write CSV data
data = [
    {'name': 'Alice', 'age': 30, 'city': 'New York'},
    {'name': 'Bob', 'age': 25, 'city': 'San Francisco'},
    {'name': 'Charlie', 'age': 35, 'city': 'Chicago'}
]
csv_file.write(data)

# Read CSV data
loaded_data = csv_file.read()
print(loaded_data)
# [{'name': 'Alice', 'age': '30', 'city': 'New York'}, ...]

# Update CSV data (append new records)
new_records = [{'name': 'Diana', 'age': '28', 'city': 'Boston'}]
csv_file.update(new_records)  # This will merge/append the data
```

</details>

#### **Example 2: XML Format Plugin**

<details>
<summary><strong>🔧 Click to expand: Complete XML Plugin Example</strong></summary>

```python
import xml.etree.ElementTree as ET
from atomicio import register_format, ThreadedSafeFile

def xml_loader(file_obj):
    """Load XML data into a structured dictionary."""
    file_obj.seek(0)
    content = file_obj.read()

    if not content.strip():
        return None

    try:
        root = ET.fromstring(content)
        return xml_to_dict(root)
    except ET.ParseError as e:
        raise ValueError(f"Invalid XML format: {e}")

def xml_dumper(data, file_obj):
    """Write data as XML format."""
    if data is None:
        return

    root = dict_to_xml(data)
    tree = ET.ElementTree(root)
    tree.write(file_obj, encoding='unicode', xml_declaration=True)

def xml_to_dict(element):
    """Convert XML element to dictionary."""
    result = {}

    # Add attributes
    if element.attrib:
        result['@attributes'] = element.attrib

    # Add text content
    if element.text and element.text.strip():
        if len(element) == 0:  # No children
            return element.text.strip()
        else:
            result['#text'] = element.text.strip()

    # Add children
    for child in element:
        child_data = xml_to_dict(child)
        if child.tag in result:
            if not isinstance(result[child.tag], list):
                result[child.tag] = [result[child.tag]]
            result[child.tag].append(child_data)
        else:
            result[child.tag] = child_data

    return result or None

def dict_to_xml(data, root_name='root'):
    """Convert dictionary to XML element."""
    if isinstance(data, dict) and len(data) == 1:
        root_name = list(data.keys())[0]
        data = data[root_name]

    root = ET.Element(root_name)

    if isinstance(data, dict):
        for key, value in data.items():
            if key == '@attributes':
                root.attrib.update(value)
            elif key == '#text':
                root.text = str(value)
            else:
                child = dict_to_xml(value, key)
                root.append(child)
    else:
        root.text = str(data)

    return root

# Register the XML format
register_format('.xml', xml_loader, xml_dumper)

# Example usage
xml_file = ThreadedSafeFile('config.xml')

# Write XML data
config_data = {
    'configuration': {
        '@attributes': {'version': '1.0'},
        'database': {
            'host': 'localhost',
            'port': '5432',
            'name': 'myapp'
        },
        'features': {
            'feature': [
                {'@attributes': {'name': 'auth'}, '#text': 'enabled'},
                {'@attributes': {'name': 'cache'}, '#text': 'disabled'}
            ]
        }
    }
}

xml_file.write(config_data)

# Use with complex locking for configuration updates
with xml_file.locked() as f:
    config = f.read()

    # Update database port
    config['configuration']['database']['port'] = '5433'

    # Add new feature
    features = config['configuration']['features']['feature']
    features.append({'@attributes': {'name': 'logging'}, '#text': 'enabled'})

    f.write(config)
```

</details>

#### **Example 3: Binary Format Plugin with Pickle**

<details>
<summary><strong>🔒 Click to expand: Complete Binary/Pickle Plugin Example</strong></summary>

```python
import pickle
from atomicio import register_format, AsyncSafeFile

def pickle_loader(file_obj):
    """Load pickled data."""
    file_obj.seek(0)
    content = file_obj.read()

    if not content:
        return None

    # For pickle, we need to work with bytes
    if isinstance(content, str):
        content = content.encode('latin1')

    return pickle.loads(content)

def pickle_dumper(data, file_obj):
    """Write data as pickled format."""
    pickled_data = pickle.dumps(data)

    # Write as text if the file was opened in text mode
    try:
        file_obj.write(pickled_data.decode('latin1'))
    except AttributeError:
        # Binary mode
        file_obj.write(pickled_data)

# Register the pickle format
register_format('.pkl', pickle_loader, pickle_dumper)
register_format('.pickle', pickle_loader, pickle_dumper)

# Example with complex Python objects
async def async_pickle_example():
    pickle_file = AsyncSafeFile('data.pkl')

    # Store complex Python objects
    complex_data = {
        'model_params': {'learning_rate': 0.001, 'epochs': 100},
        'trained_weights': [[1.2, 3.4], [5.6, 7.8]],
        'metadata': {
            'training_date': '2024-01-15',
            'accuracy': 0.95,
            'custom_objects': {'special_function': lambda x: x**2}
        }
    }

    await pickle_file.write(complex_data)

    # Load and use the data
    loaded_data = await pickle_file.read()
    print(f"Model accuracy: {loaded_data['metadata']['accuracy']}")

    # Update training results
    async with pickle_file.locked() as f:
        data = await f.read()
        data['metadata']['last_updated'] = '2024-01-16'
        data['metadata']['accuracy'] = 0.97  # Improved accuracy
        await f.write(data)

# Run the async example
import asyncio
asyncio.run(async_pickle_example())
```

</details>

### 🏗️ Creating Distributable Plugins

<details>
<summary><strong>📦 Click to expand: Complete Guide to Creating Distributable Plugins</strong></summary>

You can create separate Python packages that automatically register formats when installed.

#### **Step 1: Plugin Package Structure**

```
my_atomicio_plugin/
├── pyproject.toml
├── my_atomicio_plugin/
│   ├── __init__.py
│   └── formats.py
└── README.md
```

#### **Step 2: Plugin Implementation (`formats.py`)**

```python
# my_atomicio_plugin/formats.py
import json
import gzip
from atomicio import register_format

def compressed_json_loader(file_obj):
    """Load compressed JSON data."""
    file_obj.seek(0)
    content = file_obj.read()

    if not content:
        return None

    # Decompress and parse JSON
    if isinstance(content, str):
        content = content.encode('utf-8')

    decompressed = gzip.decompress(content)
    return json.loads(decompressed.decode('utf-8'))

def compressed_json_dumper(data, file_obj):
    """Write data as compressed JSON."""
    json_str = json.dumps(data, indent=2)
    compressed = gzip.compress(json_str.encode('utf-8'))

    # Write as text (base64 encoded) for text mode compatibility
    import base64
    encoded = base64.b64encode(compressed).decode('ascii')
    file_obj.write(encoded)

def register_all_formats():
    """Register all formats provided by this plugin."""
    register_format('.json.gz', compressed_json_loader, compressed_json_dumper)
    register_format('.cjson', compressed_json_loader, compressed_json_dumper)

# Auto-register when imported
register_all_formats()
```

#### **Step 3: Plugin Configuration (`pyproject.toml`)**

```toml
[tool.poetry]
name = "my-atomicio-plugin"
version = "0.1.0"
description = "Compressed JSON format plugin for Atomicio"
authors = ["Your Name <your.email@example.com>"]

[tool.poetry.dependencies]
python = "^3.8"
atomicio = "^1.0.0"

[build-system]
requires = ["poetry-core>=1.0.0"]
build-backend = "poetry.core.masonry.api"

# Entry point for automatic registration
[tool.poetry.plugins."atomicio.formats"]
compressed_json = "my_atomicio_plugin.formats:register_all_formats"
```

#### **Step 4: Plugin Usage**

```python
# After installing: pip install my-atomicio-plugin
from atomicio import SafeFile, list_supported_formats

# The plugin formats are automatically available!
print(list_supported_formats())
# ['.json', '.yaml', '.yml', '.toml', '.txt', '.json.gz', '.cjson']

# Use compressed JSON seamlessly
compressed_file = SafeFile('large_data.json.gz')

large_data = {
    'records': [{'id': i, 'data': f'record_{i}'} for i in range(10000)],
    'metadata': {'total_records': 10000, 'compressed': True}
}

# Automatically compressed when written
compressed_file.write(large_data)

# Automatically decompressed when read
loaded_data = compressed_file.read()
print(f"Loaded {len(loaded_data['records'])} records")
```

</details>

### 🎯 Advanced Plugin Patterns

<details>
<summary><strong>⚙️ Click to expand: Advanced Plugin Development Patterns</strong></summary>

#### **Error Handling in Plugins**

```python
from atomicio import register_format
import logging

def robust_csv_loader(file_obj):
    """CSV loader with comprehensive error handling."""
    try:
        file_obj.seek(0)
        content = file_obj.read()

        if not content.strip():
            return []

        # Detect delimiter automatically
        import csv
        sample = content[:1024]
        sniffer = csv.Sniffer()
        delimiter = sniffer.sniff(sample).delimiter

        csv_data = io.StringIO(content)
        reader = csv.DictReader(csv_data, delimiter=delimiter)
        return list(reader)

    except csv.Error as e:
        logging.error(f"CSV parsing error: {e}")
        raise ValueError(f"Invalid CSV format: {e}")
    except UnicodeDecodeError as e:
        logging.error(f"CSV encoding error: {e}")
        raise ValueError(f"CSV file encoding issue: {e}")

def robust_csv_dumper(data, file_obj):
    """CSV dumper with validation and error handling."""
    if not data:
        return

    try:
        if not isinstance(data, list):
            raise ValueError("CSV data must be a list")

        if data and not isinstance(data[0], dict):
            raise ValueError("CSV data must be a list of dictionaries")

        import csv
        fieldnames = data[0].keys() if data else []
        writer = csv.DictWriter(file_obj, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(data)

    except (AttributeError, KeyError) as e:
        logging.error(f"CSV structure error: {e}")
        raise ValueError(f"Invalid CSV data structure: {e}")

register_format('.csv', robust_csv_loader, robust_csv_dumper)
```

#### **Format Validation and Schema Support**

```python
from atomicio import register_format
import jsonschema

# JSON Schema for validation
USER_SCHEMA = {
    "type": "object",
    "properties": {
        "users": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "id": {"type": "integer"},
                    "name": {"type": "string"},
                    "email": {"type": "string", "format": "email"}
                },
                "required": ["id", "name", "email"]
            }
        }
    },
    "required": ["users"]
}

def validated_json_loader(file_obj):
    """JSON loader with schema validation."""
    import json
    file_obj.seek(0)
    content = file_obj.read()

    if not content.strip():
        return None

    data = json.loads(content)

    # Validate against schema
    try:
        jsonschema.validate(data, USER_SCHEMA)
        return data
    except jsonschema.ValidationError as e:
        raise ValueError(f"Data validation failed: {e.message}")

def validated_json_dumper(data, file_obj):
    """JSON dumper with pre-write validation."""
    if data is None:
        return

    # Validate before writing
    try:
        jsonschema.validate(data, USER_SCHEMA)
    except jsonschema.ValidationError as e:
        raise ValueError(f"Data validation failed: {e.message}")

    import json
    json.dump(data, file_obj, indent=2)

register_format('.users.json', validated_json_loader, validated_json_dumper)

# Usage with automatic validation
user_file = SafeFile('users.users.json')

# This will be validated automatically
valid_data = {
    "users": [
        {"id": 1, "name": "Alice", "email": "alice@example.com"},
        {"id": 2, "name": "Bob", "email": "bob@example.com"}
    ]
}

user_file.write(valid_data)  # ✅ Succeeds

# This will fail validation
invalid_data = {
    "users": [
        {"id": "not_a_number", "name": "Alice"}  # Missing email, wrong type
    ]
}

try:
    user_file.write(invalid_data)  # ❌ Raises ValueError
except ValueError as e:
    print(f"Validation error: {e}")
```

</details>

### 🎁 Built-in Helper Functions

<details>
<summary><strong>🛠️ Click to expand: Plugin Development Helper Functions</strong></summary>

Atomicio also provides several helper functions to make plugin development easier:

#### **Format Detection Utilities**

```python
from atomicio.formats import list_supported_formats, FORMAT_REGISTRY

# Check what formats are available
supported = list_supported_formats()
print("Supported formats:", supported)

# Check if a specific format is registered
def is_format_supported(extension):
    if not extension.startswith('.'):
        extension = '.' + extension
    return extension.lower() in FORMAT_REGISTRY

# Usage
print(is_format_supported('.csv'))    # True (if CSV plugin is loaded)
print(is_format_supported('xml'))     # True (if XML plugin is loaded)
print(is_format_supported('.unknown')) # False
```

#### **Plugin Discovery**

```python
# Discover all installed format plugins
def discover_format_plugins():
    """Discover all available format plugins via entry points."""
    import pkg_resources

    plugins = {}
    for entry_point in pkg_resources.iter_entry_points('atomicio.formats'):
        try:
            register_func = entry_point.load()
            plugins[entry_point.name] = {
                'module': entry_point.module_name,
                'function': register_func.__name__,
                'loaded': True
            }
        except Exception as e:
            plugins[entry_point.name] = {
                'module': entry_point.module_name,
                'loaded': False,
                'error': str(e)
            }

    return plugins

# Show all discovered plugins
plugins = discover_format_plugins()
for name, info in plugins.items():
    if info['loaded']:
        print(f"✅ Plugin '{name}' loaded from {info['module']}")
    else:
        print(f"❌ Plugin '{name}' failed: {info['error']}")
```

</details>

### 🚀 Quick Start: Adding a New Format

Here's the quickest way to add support for a new format:

```python
from atomicio import register_format, SafeFile

# 1. Define your loader function
def my_format_loader(file_obj):
    # Your loading logic here
    data = file_obj.read()
    return process_data(data)

# 2. Define your dumper function
def my_format_dumper(data, file_obj):
    # Your saving logic here
    processed = serialize_data(data)
    file_obj.write(processed)

# 3. Register the format
register_format('.myformat', my_format_loader, my_format_dumper)

# 4. Use it immediately!
my_file = SafeFile('data.myformat')
my_file.write({'my': 'data'})
loaded = my_file.read()
```

**That's it!** Your new format now works with all Atomicio classes (SafeFile, ThreadedSafeFile, AsyncSafeFile) and benefits from all the atomic safety guarantees.

---

## 🧪 Testing

The package includes comprehensive tests to ensure reliability and accuracy across all concurrency scenarios.

### Quick Test Commands

```bash
# Install development dependencies
pip install pytest pytest-asyncio pytest-cov

# Run all tests
pytest tests/

# Run tests with verbose output
pytest tests/ -v

# Run with coverage report
pytest tests/ --cov=atomicio --cov-report=html

# Run specific test categories
pytest tests/test_safefile_basic.py -v                    # SafeFile tests
pytest tests/test_threaded_safefile_basic.py -v          # ThreadedSafeFile tests
pytest tests/test_async_safefile_basic.py -v             # AsyncSafeFile tests

# Run stress tests (30 seconds each)
python tests/test_coordinated_threaded.py                # ThreadedSafeFile stress test
python tests/test_coordinated_async.py                   # AsyncSafeFile stress test
```

### Test Coverage

Current test coverage:
- **SafeFile**: 100% of basic operations, timeout behavior, error handling
- **ThreadedSafeFile**: 100% of cross-operation locking, concurrency, timeout behavior
- **AsyncSafeFile**: 100% of async operations, async locking, async concurrency
- **Integration Tests**: 30-second stress tests validating perfect locking coordination
- **Overall**: Comprehensive coverage across all scenarios

### Test Categories

- **Unit Tests**: Test individual methods and basic functionality
- **Integration Tests**: Test cross-operation coordination and complex workflows
- **Concurrency Tests**: Test thread/async safety under high contention
- **Stress Tests**: 30-second endurance tests with multiple workers
- **Timeout Tests**: Verify proper timeout behavior and error handling

## 🚀 Installation & Requirements

### Basic Installation

```bash
pip install atomicio
```

### Requirements

- **Python 3.8+**
- **Dependencies**:
  - `filelock ^3.12.2`: For inter-process file locking
  - `pyyaml ^6.0`: For YAML format support
  - `tomli ^2.0.1`: For TOML format support (Python < 3.11)
  - `atomicwrites ^1.4.1`: For atomic file operations

### Supported File Formats

**Built-in Formats:**
- **`.json`** - JSON format with automatic pretty-printing
- **`.yaml/.yml`** - YAML format with safe loading/dumping
- **`.toml`** - TOML format support
- **`.txt`** - Plain text format

**Plugin Ecosystem:**
- **CSV, XML, Binary formats** - Available via the plugin system
- **Custom formats** - Easy to create and distribute as separate packages
- **Community plugins** - Installable via pip with automatic format registration

```python
# Check currently available formats
from atomicio import list_supported_formats
print(list_supported_formats())  # ['.json', '.yaml', '.yml', '.toml', '.txt', ...]
```

## 🤝 Contributing

We welcome contributions! Here's how to get started:

1. **Fork the repository**
2. **Create a feature branch**: `git checkout -b feature/amazing-feature`
3. **Make your changes** and add tests
4. **Run the test suite**: `pytest tests/`
5. **Commit your changes**: `git commit -m 'Add amazing feature'`
6. **Push to the branch**: `git push origin feature/amazing-feature`
7. **Open a Pull Request**

### Development Setup

```bash
# Clone the repo
git clone https://github.com/santiago897/atomicio-project.git
cd atomicio-project

# Install with development dependencies
pip install -e .[dev]

# Run tests
pytest tests/

# Run stress tests
python tests/test_coordinated_threaded.py
python tests/test_coordinated_async.py
```

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **[filelock](https://github.com/tox-dev/py-filelock)** and **[PyYAML](https://pyyaml.org/)** - This project wouldn't be possible without these excellent libraries
- The Python asyncio community for async patterns and best practices
- The Python threading community for concurrent programming insights

## 🔗 Links

- **GitHub**: https://github.com/santiago897/atomicio-project
- **Documentation**: Coming soon!
- **Issues**: https://github.com/santiago897/atomicio-project/issues

---

<div align="center">

**Made with ❤️ by [Santiago Matta](https://github.com/santiago897)**

*"Because data integrity should never be compromised!"* 🔒

</div>
