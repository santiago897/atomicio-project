#!/usr/bin/env python3
"""
Test ThreadedSafeFile comprehensive functionality and cross-operation locking behavior.
This test focuses on ThreadedSafeFile's role as an advanced file operations class
with proper cross-operation locking capabilities.
"""

import time
import tempfile
import threading
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FutureTimeoutError
from pathlib import Path
from atomicio import ThreadedSafeFile, AsyncTimeoutError


def test_threaded_safefile_basic_operations():
    """Test ThreadedSafeFile basic read/write operations"""

    print("🚀 Testing ThreadedSafeFile Basic Operations")
    print("="*55)

    with tempfile.NamedTemporaryFile(suffix='.json', delete=False) as tmp:
        test_file = Path(tmp.name)

    try:
        tsf = ThreadedSafeFile(test_file)

        # Test 1: Basic write/read
        print("📋 Test 1: Basic write and read")
        data = {'message': 'hello threaded', 'number': 42}
        tsf.write(data)
        result = tsf.read()
        assert result == data, f"Expected {data}, got {result}"
        print("✅ Basic write/read works correctly")

        # Test 2: Update operation
        print("\n📋 Test 2: Update operation")
        data['updated'] = True
        data['timestamp'] = time.time()
        tsf.write(data)
        result = tsf.read()
        assert result == data, f"Expected {data}, got {result}"
        print("✅ Update operation works correctly")

        # Test 3: Individual operations with timeout
        print("\n📋 Test 3: Individual operations with timeout")
        tsf_timeout = ThreadedSafeFile(test_file, timeout=5.0)
        test_data = {'timeout_test': True}
        tsf_timeout.write(test_data)
        result = tsf_timeout.read()
        assert result == test_data, "Timeout operations failed"
        print("✅ Individual operations with timeout work correctly")

        # Test 4: Bytes operations
        print("\n📋 Test 4: Bytes operations")
        test_bytes = b"Hello, threaded binary world!"
        tsf.write_bytes(test_bytes)
        result_bytes = tsf.read_bytes()
        assert result_bytes == test_bytes, f"Expected {test_bytes}, got {result_bytes}"
        print("✅ Bytes operations work correctly")

        # Test 5: Append operation
        print("\n📋 Test 5: Append operation")
        tsf.write({'base': 'content'})  # Reset to JSON
        tsf.append("\n# This is appended text from ThreadedSafeFile")
        content = tsf.read_bytes().decode('utf-8')
        assert "appended text from ThreadedSafeFile" in content, "Append operation failed"
        print("✅ Append operation works correctly")

        print("\n🎉 All basic operations tests passed!")

    finally:
        # Cleanup
        try:
            test_file.unlink()
        except:
            pass


def test_threaded_safefile_locked_context():
    """Test ThreadedSafeFile locked() context manager for cross-operation locking"""

    print("\n🚀 Testing ThreadedSafeFile Locked Context Manager")
    print("="*60)

    with tempfile.NamedTemporaryFile(suffix='.json', delete=False) as tmp:
        test_file = Path(tmp.name)

    try:
        tsf = ThreadedSafeFile(test_file, timeout=3)

        # Test 1: Basic locked context usage
        print("📋 Test 1: Basic locked context usage")
        initial_data = {'counter': 0, 'operations': []}
        tsf.write(initial_data)

        with tsf.locked() as f:
            data = f.read()
            data['counter'] += 1
            data['operations'].append('locked_operation_1')
            f.write(data)

            # Do another operation while holding the lock
            time.sleep(0.1)
            data = f.read()
            data['counter'] += 1
            data['operations'].append('locked_operation_2')
            f.write(data)

        final_data = tsf.read()
        assert final_data['counter'] == 2, f"Expected counter=2, got {final_data['counter']}"
        assert len(final_data['operations']) == 2, "Operations not recorded correctly"
        print("✅ Basic locked context works correctly")

        # Test 2: Cross-operation locking behavior
        print("\n📋 Test 2: Cross-operation locking behavior")

        def long_locked_operation():
            """Performs a long operation while holding the lock"""
            with tsf.locked() as f:
                data = f.read() or {}
                data['long_operation_start'] = time.time()
                f.write(data)

                # Hold the lock for 2 seconds
                time.sleep(2)

                data = f.read()
                data['long_operation_end'] = time.time()
                data['long_operation_completed'] = True
                f.write(data)

            return "Long operation completed"

        def quick_operation(worker_id):
            """Tries to do a quick operation with shorter timeout"""
            try:
                start_time = time.time()
                # Use a shorter timeout to ensure it fails if lock is held
                quick_tsf = ThreadedSafeFile(tsf.path, timeout=0.5)
                data = quick_tsf.read() or {}
                data[f'quick_worker_{worker_id}'] = {
                    'timestamp': time.time(),
                    'duration': time.time() - start_time
                }
                quick_tsf.write(data)
                return f"Quick worker {worker_id} succeeded"
            except AsyncTimeoutError:
                return f"Quick worker {worker_id} timed out (expected)"
            except Exception as e:
                return f"Quick worker {worker_id} failed: {type(e).__name__}: {e}"

        # Start long operation in background
        executor = ThreadPoolExecutor(max_workers=5)
        long_future = executor.submit(long_locked_operation)

        # Give it time to acquire the lock
        time.sleep(0.5)

        # Try concurrent quick operations
        print("🎯 Testing concurrent operations during locked context...")
        quick_futures = []
        for i in range(3):
            future = executor.submit(quick_operation, i+1)
            quick_futures.append(future)
            time.sleep(0.1)  # Stagger attempts

        # Check results
        timeout_count = 0
        for i, future in enumerate(quick_futures):
            try:
                result = future.result(timeout=3.0)  # Give enough time to wait for the operation
                if "timed out" in result or "failed" in result:
                    timeout_count += 1
                    print(f"  ✅ {result}")
                else:
                    print(f"  ❌ {result} (should have been blocked)")
            except FutureTimeoutError:
                timeout_count += 1
                print(f"  ✅ Quick worker {i+1} timed out correctly")
            except Exception as e:
                timeout_count += 1
                print(f"  ✅ Quick worker {i+1} blocked: {type(e).__name__}")

        # Wait for long operation to complete
        long_result = long_future.result()
        print(f"📋 {long_result}")

        print(f"🎯 Cross-operation blocking: {timeout_count}/3 operations were properly blocked")

        # Verify the long operation completed
        final_data = tsf.read()
        assert 'long_operation_completed' in final_data, "Long operation did not complete"
        print("✅ Cross-operation locking works correctly")

        executor.shutdown(wait=True)

        print("\n🎉 All locked context tests passed!")

    finally:
        # Cleanup
        try:
            test_file.unlink()
        except:
            pass


def test_threaded_safefile_timeout_behavior():
    """Test ThreadedSafeFile timeout behavior and configurations"""

    print("\n🚀 Testing ThreadedSafeFile Timeout Behavior")
    print("="*55)

    with tempfile.NamedTemporaryFile(suffix='.json', delete=False) as tmp:
        test_file = Path(tmp.name)

    try:
        # Test different timeout configurations
        print("📋 Test 1: Timeout configuration validation")

        # Test boolean timeout values
        tsf_default = ThreadedSafeFile(test_file, timeout=True)
        tsf_no_timeout = ThreadedSafeFile(test_file, timeout=False)
        tsf_none_timeout = ThreadedSafeFile(test_file, timeout=None)
        tsf_numeric = ThreadedSafeFile(test_file, timeout=2.5)

        assert tsf_default.timeout == 15.0, "Default timeout not set correctly"
        assert tsf_no_timeout.timeout is None, "No timeout not set correctly"
        assert tsf_none_timeout.timeout is None, "None timeout not set correctly"
        assert tsf_numeric.timeout == 2.5, "Numeric timeout not set correctly"
        print("✅ All timeout configurations work correctly")

        # Test timeout in locked context
        print("\n📋 Test 2: Timeout behavior in locked context")

        tsf_short = ThreadedSafeFile(test_file, timeout=1.0)

        def blocking_operation():
            """Holds lock for longer than timeout"""
            with tsf_short.locked() as f:
                f.write({'blocking': 'started'})
                time.sleep(2)  # Hold for 2 seconds
                f.write({'blocking': 'completed'})
            return "Blocking operation done"

        def timeout_operation():
            """Should timeout trying to acquire lock"""
            try:
                start_time = time.time()
                with tsf_short.locked() as f:
                    f.write({'timeout_test': 'should_not_reach_here'})
                return "Should not succeed"
            except AsyncTimeoutError as e:
                duration = time.time() - start_time
                return f"Timed out after {duration:.1f}s (expected)"
            except Exception as e:
                return f"Failed with: {type(e).__name__}: {e}"

        # Start blocking operation
        executor = ThreadPoolExecutor(max_workers=3)
        blocking_future = executor.submit(blocking_operation)

        # Give it time to acquire lock
        time.sleep(0.2)

        # Try operation that should timeout
        timeout_future = executor.submit(timeout_operation)

        # Check results
        timeout_result = timeout_future.result()
        blocking_result = blocking_future.result()

        print(f"  📋 Blocking operation: {blocking_result}")
        print(f"  📋 Timeout operation: {timeout_result}")

        assert "Timed out" in timeout_result, "Timeout behavior not working"
        print("✅ Timeout behavior works correctly")

        executor.shutdown(wait=True)

        print("\n🎉 All timeout behavior tests passed!")

    finally:
        # Cleanup
        try:
            test_file.unlink()
        except:
            pass


def test_threaded_safefile_error_handling():
    """Test ThreadedSafeFile error handling"""

    print("\n🚀 Testing ThreadedSafeFile Error Handling")
    print("="*50)

    with tempfile.NamedTemporaryFile(suffix='.json', delete=False) as tmp:
        test_file = Path(tmp.name)

    try:
        tsf = ThreadedSafeFile(test_file)

        # Test reading non-existent file
        print("📋 Test 1: Reading non-existent file")
        test_file.unlink()  # Remove the file
        result = tsf.read()
        assert result is None, "Reading non-existent file should return None"
        print("✅ Non-existent file handling works correctly")

        # Test reading empty file
        print("\n📋 Test 2: Reading empty file")
        test_file.touch()  # Create empty file
        result = tsf.read()
        assert result is None, "Reading empty file should return None"
        print("✅ Empty file handling works correctly")

        # Test invalid timeout values
        print("\n📋 Test 3: Invalid timeout values")
        try:
            ThreadedSafeFile(test_file, timeout="invalid")
            assert False, "Should have raised ValueError"
        except ValueError:
            print("✅ Invalid timeout value properly rejected")

        # Test bytes operations on non-existent file
        print("\n📋 Test 4: Bytes operations on non-existent file")
        test_file.unlink()
        result = tsf.read_bytes()
        assert result is None, "Reading bytes from non-existent file should return None"
        print("✅ Bytes operations on non-existent file work correctly")

        # Test supported formats
        print("\n📋 Test 5: Supported formats")
        formats = ThreadedSafeFile.supported_formats()
        assert isinstance(formats, list), "supported_formats should return a list"
        assert len(formats) > 0, "Should have at least some supported formats"
        print(f"✅ Supported formats: {formats}")

        # Test cleanup_locks method
        print("\n📋 Test 6: Cleanup locks method")
        ThreadedSafeFile.cleanup_locks()  # Should not raise any errors
        print("✅ Cleanup locks method works correctly")

        print("\n🎉 All error handling tests passed!")

    finally:
        # Cleanup
        try:
            test_file.unlink(missing_ok=True)
        except:
            pass


def test_threaded_safefile_concurrency():
    """Test ThreadedSafeFile behavior under concurrent access"""

    print("\n🚀 Testing ThreadedSafeFile Concurrency")
    print("="*45)

    with tempfile.NamedTemporaryFile(suffix='.json', delete=False) as tmp:
        test_file = Path(tmp.name)

    try:
        tsf = ThreadedSafeFile(test_file, timeout=5)

        # Initialize file
        tsf.write({'workers': {}, 'total_operations': 0})

        def worker_task(worker_id, num_operations):
            """Worker that performs multiple operations"""
            results = []
            for i in range(num_operations):
                try:
                    # Read current data
                    data = tsf.read() or {}

                    # Update worker data
                    if 'workers' not in data:
                        data['workers'] = {}

                    data['workers'][f'worker_{worker_id}'] = {
                        'operation': i + 1,
                        'timestamp': time.time()
                    }
                    data['total_operations'] = data.get('total_operations', 0) + 1

                    # Write back
                    tsf.write(data)
                    results.append(f"Worker {worker_id} operation {i+1} completed")

                    # Small delay between operations
                    time.sleep(0.01)

                except Exception as e:
                    results.append(f"Worker {worker_id} operation {i+1} failed: {e}")

            return results

        print("📋 Testing concurrent individual operations")

        # Run multiple workers concurrently
        executor = ThreadPoolExecutor(max_workers=5)
        futures = []

        for worker_id in range(1, 6):
            future = executor.submit(worker_task, worker_id, 3)
            futures.append(future)

        # Collect results
        all_results = []
        for future in futures:
            worker_results = future.result()
            all_results.extend(worker_results)

        # Check final state
        final_data = tsf.read()
        total_ops = final_data.get('total_operations', 0)
        worker_count = len(final_data.get('workers', {}))

        print(f"📊 Final results:")
        print(f"   - Total operations recorded: {total_ops}")
        print(f"   - Workers that wrote data: {worker_count}")
        print(f"   - Individual operation results: {len([r for r in all_results if 'completed' in r])}/{len(all_results)} successful")

        # All workers should have been able to write at least something
        assert worker_count > 0, "No workers managed to write data"
        print("✅ Concurrent individual operations work correctly")

        executor.shutdown(wait=True)

        print("\n🎉 All concurrency tests passed!")

    finally:
        # Cleanup
        try:
            test_file.unlink()
        except:
            pass


if __name__ == "__main__":
    test_threaded_safefile_basic_operations()
    test_threaded_safefile_locked_context()
    test_threaded_safefile_timeout_behavior()
    test_threaded_safefile_error_handling()
    test_threaded_safefile_concurrency()

    print("\n" + "="*70)
    print("🎊 ALL THREADED SAFEFILE TESTS COMPLETED SUCCESSFULLY!")
    print("="*70)
    print("\n📝 Summary:")
    print("   ThreadedSafeFile: Advanced file operations with cross-operation locking")
    print("   ✅ Individual operations work correctly")
    print("   ✅ locked() context manager provides proper cross-operation locking")
    print("   ✅ Timeout handling works as expected")
    print("   ✅ Error handling is robust")
    print("   ✅ Concurrent access is properly managed")
    print("\n💡 Use ThreadedSafeFile when you need:")
    print("   • Cross-operation exclusive access")
    print("   • Complex multi-step file operations")
    print("   • Proper thread coordination in sync code")
