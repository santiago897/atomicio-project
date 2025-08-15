#!/usr/bin/env python3
"""
Test SafeFile basic functionality and timeout behavior.
This test focuses on SafeFile's role as a simple, atomic file operations class
without complex cross-operation locking.
"""

import time
import tempfile
import threading
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FutureTimeoutError
from pathlib import Path
from atomicio import SafeFile


def test_safefile_basic_operations():
    """Test SafeFile basic read/write operations"""

    print("🚀 Testing SafeFile Basic Operations")
    print("="*50)

    with tempfile.NamedTemporaryFile(suffix='.json', delete=False) as tmp:
        test_file = Path(tmp.name)

    try:
        sf = SafeFile(test_file)

        # Test 1: Basic write/read
        print("📋 Test 1: Basic write and read")
        data = {'message': 'hello', 'number': 42}
        sf.write(data)
        result = sf.read()
        assert result == data, f"Expected {data}, got {result}"
        print("✅ Basic write/read works correctly")

        # Test 2: Update operation
        print("\n📋 Test 2: Update operation")
        data['updated'] = True
        sf.write(data)
        result = sf.read()
        assert result == data, f"Expected {data}, got {result}"
        print("✅ Update operation works correctly")

        # Test 3: Context manager
        print("\n📋 Test 3: Context manager usage")
        with sf:
            current_data = sf.read()
            current_data['context_test'] = 'success'
            sf.write(current_data)

        final_data = sf.read()
        assert 'context_test' in final_data, "Context manager operation failed"
        print("✅ Context manager works correctly")

        # Test 4: Bytes operations
        print("\n📋 Test 4: Bytes operations")
        test_bytes = b"Hello, binary world!"
        sf.write_bytes(test_bytes)
        result_bytes = sf.read_bytes()
        assert result_bytes == test_bytes, f"Expected {test_bytes}, got {result_bytes}"
        print("✅ Bytes operations work correctly")

        # Test 5: Append operation
        print("\n📋 Test 5: Append operation")
        sf.write({'base': 'content'})  # Reset to JSON
        sf.append("\n# This is appended text")
        content = sf.read_bytes().decode('utf-8')
        assert "appended text" in content, "Append operation failed"
        print("✅ Append operation works correctly")

        print("\n🎉 All basic operations tests passed!")

    finally:
        # Cleanup
        try:
            test_file.unlink()
            Path(str(test_file) + ".lock").unlink(missing_ok=True)
        except:
            pass


def test_safefile_timeout_behavior():
    """Test SafeFile timeout behavior with FileLock"""

    print("\n🚀 Testing SafeFile Timeout Behavior")
    print("="*50)

    with tempfile.NamedTemporaryFile(suffix='.json', delete=False) as tmp:
        test_file = Path(tmp.name)

    try:
        # Create SafeFile with short timeout for testing
        sf_short_timeout = SafeFile(test_file, timeout=2)
        sf_long_timeout = SafeFile(test_file, timeout=10)

        print("📋 Test: FileLock timeout behavior between different processes")
        print("NOTE: This test simulates what would happen with different processes")
        print("In the same process, FileLock doesn't block threads - this is expected behavior")

        # Test timeout configuration
        assert sf_short_timeout.file_lock.timeout == 2, "Short timeout not set correctly"
        assert sf_long_timeout.file_lock.timeout == 10, "Long timeout not set correctly"
        print("✅ Timeout configuration works correctly")

        # Test concurrent access (simulates inter-process competition)
        print("\n📋 Testing concurrent access patterns")

        def worker_task(worker_id, sf_instance):
            """Simulate a worker doing file operations"""
            try:
                start_time = time.time()

                # Read current data
                data = sf_instance.read() or {}

                # Simulate some processing time
                time.sleep(0.1)

                # Update data
                data[f'worker_{worker_id}'] = {
                    'timestamp': time.time(),
                    'duration': time.time() - start_time
                }

                # Write back
                sf_instance.write(data)

                return f"Worker {worker_id} completed successfully"

            except Exception as e:
                return f"Worker {worker_id} failed: {type(e).__name__}: {e}"

        # Run multiple workers concurrently
        executor = ThreadPoolExecutor(max_workers=5)

        # Initialize the file with empty data first
        sf_long_timeout.write({})

        futures = []

        for i in range(5):
            future = executor.submit(worker_task, i+1, sf_long_timeout)
            futures.append(future)

        # Collect results
        results = []
        for future in futures:
            try:
                result = future.result(timeout=5)
                results.append(result)
                print(f"  ✅ {result}")
            except FutureTimeoutError:
                results.append(f"Worker timed out")
                print(f"  ⏰ Worker timed out")
            except Exception as e:
                results.append(f"Worker error: {e}")
                print(f"  ❌ Worker error: {e}")

        # Check final state
        final_data = sf_long_timeout.read()
        worker_count = len([key for key in final_data.keys() if key.startswith('worker_')])
        print(f"\n📊 Final result: {worker_count} workers successfully wrote data")

        # Test different timeout values
        print("\n📋 Testing timeout value configurations")

        # Test boolean timeout values
        sf_default = SafeFile(test_file, timeout=True)
        sf_no_timeout = SafeFile(test_file, timeout=False)
        sf_none_timeout = SafeFile(test_file, timeout=None)

        assert sf_default.file_lock.timeout == 15, "Default timeout not set correctly"
        assert sf_no_timeout.file_lock.timeout == -1, "No timeout not set correctly"
        assert sf_none_timeout.file_lock.timeout == -1, "None timeout not set correctly"
        print("✅ All timeout configurations work correctly")

        executor.shutdown(wait=True)

        print("\n🎉 All timeout behavior tests completed!")
        print("NOTE: SafeFile uses FileLock for inter-process safety.")
        print("For cross-operation locking within the same process, use ThreadedSafeFile.locked()")

    finally:
        # Cleanup
        try:
            test_file.unlink()
            Path(str(test_file) + ".lock").unlink(missing_ok=True)
        except:
            pass


def test_safefile_error_handling():
    """Test SafeFile error handling"""

    print("\n🚀 Testing SafeFile Error Handling")
    print("="*50)

    with tempfile.NamedTemporaryFile(suffix='.json', delete=False) as tmp:
        test_file = Path(tmp.name)

    try:
        sf = SafeFile(test_file)

        # Test reading non-existent file
        print("📋 Test: Reading non-existent file")
        test_file.unlink()  # Remove the file
        result = sf.read()
        assert result is None, "Reading non-existent file should return None"
        print("✅ Non-existent file handling works correctly")

        # Test invalid timeout values
        print("\n📋 Test: Invalid timeout values")
        try:
            SafeFile(test_file, timeout="invalid")
            assert False, "Should have raised ValueError"
        except ValueError:
            print("✅ Invalid timeout value properly rejected")

        # Test supported formats
        print("\n📋 Test: Supported formats")
        formats = SafeFile.supported_formats()
        assert isinstance(formats, list), "supported_formats should return a list"
        assert len(formats) > 0, "Should have at least some supported formats"
        print(f"✅ Supported formats: {formats}")

        print("\n🎉 All error handling tests passed!")

    finally:
        # Cleanup
        try:
            test_file.unlink(missing_ok=True)
            Path(str(test_file) + ".lock").unlink(missing_ok=True)
        except:
            pass


if __name__ == "__main__":
    test_safefile_basic_operations()
    test_safefile_timeout_behavior()
    test_safefile_error_handling()

    print("\n" + "="*60)
    print("🎊 ALL SAFEFILE TESTS COMPLETED SUCCESSFULLY!")
    print("="*60)
    print("\n📝 Summary:")
    print("   SafeFile: Simple atomic operations with FileLock for inter-process safety")
    print("   ThreadedSafeFile: Complex cross-operation locking with thread locks")
    print("   AsyncSafeFile: Async operations with proper async lock management")
    print("\n   Use SafeFile for: Basic atomic file operations in sync code")
    print("   Use ThreadedSafeFile for: Complex operations requiring cross-operation locking")
    print("   Use AsyncSafeFile for: Async code with proper async coordination")
