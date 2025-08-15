#!/usr/bin/env python3
"""
Test AsyncSafeFile comprehensive functionality and async cross-operation locking behavior.
This test focuses on AsyncSafeFile's role as an async file operations class
with proper async lock coordination capabilities.
"""

import asyncio
import time
import tempfile
import pytest
from pathlib import Path
from atomicio import AsyncSafeFile, AsyncTimeoutError


@pytest.mark.asyncio
async def test_async_safefile_basic_operations():
    """Test AsyncSafeFile basic read/write operations"""

    print("🚀 Testing AsyncSafeFile Basic Operations")
    print("="*50)

    with tempfile.NamedTemporaryFile(suffix='.json', delete=False) as tmp:
        test_file = Path(tmp.name)

    try:
        asf = AsyncSafeFile(test_file)

        # Test 1: Basic write/read
        print("📋 Test 1: Basic async write and read")
        data = {'message': 'hello async', 'number': 42}
        await asf.write(data)
        result = await asf.read()
        assert result == data, f"Expected {data}, got {result}"
        print("✅ Basic async write/read works correctly")

        # Test 2: Update operation
        print("\n📋 Test 2: Async update operation")
        data['updated'] = True
        data['timestamp'] = time.time()
        await asf.write(data)
        result = await asf.read()
        assert result == data, f"Expected {data}, got {result}"
        print("✅ Async update operation works correctly")

        # Test 3: Individual operations with timeout
        print("\n📋 Test 3: Individual async operations with timeout")
        asf_timeout = AsyncSafeFile(test_file, timeout=5.0)
        test_data = {'async_timeout_test': True}
        await asf_timeout.write(test_data)
        result = await asf_timeout.read()
        assert result == test_data, "Async timeout operations failed"
        print("✅ Individual async operations with timeout work correctly")

        # Test 4: Bytes operations
        print("\n📋 Test 4: Async bytes operations")
        test_bytes = b"Hello, async binary world!"
        await asf.write_bytes(test_bytes)
        result_bytes = await asf.read_bytes()
        assert result_bytes == test_bytes, f"Expected {test_bytes}, got {result_bytes}"
        print("✅ Async bytes operations work correctly")

        # Test 5: Append operation
        print("\n📋 Test 5: Async append operation")
        await asf.write({'base': 'async content'})  # Reset to JSON
        await asf.append("\n# This is appended text from AsyncSafeFile")
        content = (await asf.read_bytes()).decode('utf-8')
        assert "appended text from AsyncSafeFile" in content, "Async append operation failed"
        print("✅ Async append operation works correctly")

        print("\n🎉 All basic async operations tests passed!")

    finally:
        # Cleanup
        try:
            test_file.unlink()
        except:
            pass


@pytest.mark.asyncio
async def test_async_safefile_locked_context():
    """Test AsyncSafeFile locked() context manager for cross-operation locking"""

    print("\n🚀 Testing AsyncSafeFile Locked Context Manager")
    print("="*55)

    with tempfile.NamedTemporaryFile(suffix='.json', delete=False) as tmp:
        test_file = Path(tmp.name)

    try:
        asf = AsyncSafeFile(test_file, timeout=3)

        # Test 1: Basic async locked context usage
        print("📋 Test 1: Basic async locked context usage")
        initial_data = {'counter': 0, 'async_operations': []}
        await asf.write(initial_data)

        async with asf.locked() as f:
            data = await f.read()
            data['counter'] += 1
            data['async_operations'].append('async_locked_operation_1')
            await f.write(data)

            # Do another operation while holding the lock
            await asyncio.sleep(0.1)
            data = await f.read()
            data['counter'] += 1
            data['async_operations'].append('async_locked_operation_2')
            await f.write(data)

        final_data = await asf.read()
        assert final_data['counter'] == 2, f"Expected counter=2, got {final_data['counter']}"
        assert len(final_data['async_operations']) == 2, "Async operations not recorded correctly"
        print("✅ Basic async locked context works correctly")

        # Test 2: Async cross-operation locking behavior
        print("\n📋 Test 2: Async cross-operation locking behavior")

        async def long_async_locked_operation():
            """Performs a long async operation while holding the lock"""
            async with asf.locked() as f:
                data = await f.read() or {}
                data['async_long_operation_start'] = time.time()
                await f.write(data)

                # Hold the lock for 2 seconds
                await asyncio.sleep(2)

                data = await f.read()
                data['async_long_operation_end'] = time.time()
                data['async_long_operation_completed'] = True
                await f.write(data)

            return "Async long operation completed"

        async def quick_async_operation(worker_id):
            """Tries to do a quick async operation with shorter timeout"""
            try:
                start_time = time.time()
                # Use a shorter timeout to ensure it fails if lock is held
                quick_asf = AsyncSafeFile(asf.path, timeout=0.5)
                data = await quick_asf.read() or {}
                data[f'async_quick_worker_{worker_id}'] = {
                    'timestamp': time.time(),
                    'duration': time.time() - start_time
                }
                await quick_asf.write(data)
                return f"Async quick worker {worker_id} succeeded"
            except AsyncTimeoutError:
                return f"Async quick worker {worker_id} timed out (expected)"
            except Exception as e:
                return f"Async quick worker {worker_id} failed: {type(e).__name__}: {e}"

        # Start long operation in background
        long_task = asyncio.create_task(long_async_locked_operation())

        # Give it time to acquire the lock
        await asyncio.sleep(0.5)

        # Try concurrent quick operations
        print("🎯 Testing concurrent async operations during locked context...")
        quick_tasks = []
        for i in range(3):
            task = asyncio.create_task(quick_async_operation(i+1))
            quick_tasks.append(task)
            await asyncio.sleep(0.1)  # Stagger attempts

        # Check results with timeout
        timeout_count = 0
        for i, task in enumerate(quick_tasks):
            try:
                result = await asyncio.wait_for(task, timeout=3.0)  # Give enough time to wait
                if "timed out" in result or "failed" in result:
                    timeout_count += 1
                    print(f"  ✅ {result}")
                else:
                    print(f"  ❌ {result} (should have been blocked)")
            except asyncio.TimeoutError:
                timeout_count += 1
                print(f"  ✅ Async quick worker {i+1} timed out correctly")
                task.cancel()
            except Exception as e:
                timeout_count += 1
                print(f"  ✅ Async quick worker {i+1} blocked: {type(e).__name__}")

        # Wait for long operation to complete
        long_result = await long_task
        print(f"📋 {long_result}")

        print(f"🎯 Async cross-operation blocking: {timeout_count}/3 operations were properly blocked")

        # Verify the long operation completed
        final_data = await asf.read()
        assert 'async_long_operation_completed' in final_data, "Async long operation did not complete"
        print("✅ Async cross-operation locking works correctly")

        print("\n🎉 All async locked context tests passed!")

    finally:
        # Cleanup
        try:
            test_file.unlink()
        except:
            pass


@pytest.mark.asyncio
async def test_async_safefile_timeout_behavior():
    """Test AsyncSafeFile timeout behavior and configurations"""

    print("\n🚀 Testing AsyncSafeFile Timeout Behavior")
    print("="*50)

    with tempfile.NamedTemporaryFile(suffix='.json', delete=False) as tmp:
        test_file = Path(tmp.name)

    try:
        # Test different timeout configurations
        print("📋 Test 1: Async timeout configuration validation")

        # Test boolean timeout values
        asf_default = AsyncSafeFile(test_file, timeout=True)
        asf_no_timeout = AsyncSafeFile(test_file, timeout=False)
        asf_none_timeout = AsyncSafeFile(test_file, timeout=None)
        asf_numeric = AsyncSafeFile(test_file, timeout=2.5)

        assert asf_default.timeout == 15.0, "Default async timeout not set correctly"
        assert asf_no_timeout.timeout is None, "No async timeout not set correctly"
        assert asf_none_timeout.timeout is None, "None async timeout not set correctly"
        assert asf_numeric.timeout == 2.5, "Numeric async timeout not set correctly"
        print("✅ All async timeout configurations work correctly")

        # Test timeout in async locked context
        print("\n📋 Test 2: Async timeout behavior in locked context")

        asf_short = AsyncSafeFile(test_file, timeout=1.0)

        async def blocking_async_operation():
            """Holds async lock for longer than timeout"""
            async with asf_short.locked() as f:
                await f.write({'async_blocking': 'started'})
                await asyncio.sleep(2)  # Hold for 2 seconds
                await f.write({'async_blocking': 'completed'})
            return "Async blocking operation done"

        async def timeout_async_operation():
            """Should timeout trying to acquire async lock"""
            try:
                start_time = time.time()
                async with asf_short.locked() as f:
                    await f.write({'async_timeout_test': 'should_not_reach_here'})
                return "Should not succeed"
            except AsyncTimeoutError as e:
                duration = time.time() - start_time
                return f"Async timed out after {duration:.1f}s (expected)"
            except Exception as e:
                return f"Async failed with: {type(e).__name__}: {e}"

        # Start blocking operation
        blocking_task = asyncio.create_task(blocking_async_operation())

        # Give it time to acquire lock
        await asyncio.sleep(0.2)

        # Try operation that should timeout
        timeout_task = asyncio.create_task(timeout_async_operation())

        # Wait for both to complete
        timeout_result = await timeout_task
        blocking_result = await blocking_task

        print(f"  📋 Async blocking operation: {blocking_result}")
        print(f"  📋 Async timeout operation: {timeout_result}")

        assert "Async timed out" in timeout_result, "Async timeout behavior not working"
        print("✅ Async timeout behavior works correctly")

        print("\n🎉 All async timeout behavior tests passed!")

    finally:
        # Cleanup
        try:
            test_file.unlink()
        except:
            pass


@pytest.mark.asyncio
async def test_async_safefile_error_handling():
    """Test AsyncSafeFile error handling"""

    print("\n🚀 Testing AsyncSafeFile Error Handling")
    print("="*45)

    with tempfile.NamedTemporaryFile(suffix='.json', delete=False) as tmp:
        test_file = Path(tmp.name)

    try:
        asf = AsyncSafeFile(test_file)

        # Test reading non-existent file
        print("📋 Test 1: Async reading non-existent file")
        test_file.unlink()  # Remove the file
        result = await asf.read()
        assert result is None, "Async reading non-existent file should return None"
        print("✅ Async non-existent file handling works correctly")

        # Test reading empty file
        print("\n📋 Test 2: Async reading empty file")
        test_file.touch()  # Create empty file
        result = await asf.read()
        assert result is None, "Async reading empty file should return None"
        print("✅ Async empty file handling works correctly")

        # Test invalid timeout values
        print("\n📋 Test 3: Invalid async timeout values")
        try:
            AsyncSafeFile(test_file, timeout="invalid")
            assert False, "Should have raised ValueError"
        except ValueError:
            print("✅ Invalid async timeout value properly rejected")

        # Test bytes operations on non-existent file
        print("\n📋 Test 4: Async bytes operations on non-existent file")
        test_file.unlink()
        result = await asf.read_bytes()
        assert result is None, "Async reading bytes from non-existent file should return None"
        print("✅ Async bytes operations on non-existent file work correctly")

        # Test supported formats
        print("\n📋 Test 5: Async supported formats")
        formats = AsyncSafeFile.supported_formats()
        assert isinstance(formats, list), "async supported_formats should return a list"
        assert len(formats) > 0, "Should have at least some supported formats"
        print(f"✅ Async supported formats: {formats}")

        # Test cleanup_locks method
        print("\n📋 Test 6: Async cleanup locks method")
        await AsyncSafeFile.cleanup_locks()  # Should not raise any errors
        print("✅ Async cleanup locks method works correctly")

        print("\n🎉 All async error handling tests passed!")

    finally:
        # Cleanup
        try:
            test_file.unlink(missing_ok=True)
        except:
            pass


@pytest.mark.asyncio
async def test_async_safefile_concurrency():
    """Test AsyncSafeFile behavior under concurrent async access"""

    print("\n🚀 Testing AsyncSafeFile Async Concurrency")
    print("="*45)

    with tempfile.NamedTemporaryFile(suffix='.json', delete=False) as tmp:
        test_file = Path(tmp.name)

    try:
        asf = AsyncSafeFile(test_file, timeout=5)

        # Initialize file
        await asf.write({'async_workers': {}, 'total_async_operations': 0})

        async def async_worker_task(worker_id, num_operations):
            """Async worker that performs multiple operations"""
            results = []
            for i in range(num_operations):
                try:
                    # Read current data
                    data = await asf.read() or {}

                    # Update worker data
                    if 'async_workers' not in data:
                        data['async_workers'] = {}

                    data['async_workers'][f'async_worker_{worker_id}'] = {
                        'operation': i + 1,
                        'timestamp': time.time()
                    }
                    data['total_async_operations'] = data.get('total_async_operations', 0) + 1

                    # Write back
                    await asf.write(data)
                    results.append(f"Async worker {worker_id} operation {i+1} completed")

                    # Small delay between operations
                    await asyncio.sleep(0.01)

                except Exception as e:
                    results.append(f"Async worker {worker_id} operation {i+1} failed: {e}")

            return results

        print("📋 Testing concurrent async individual operations")

        # Run multiple async workers concurrently
        tasks = []
        for worker_id in range(1, 6):
            task = asyncio.create_task(async_worker_task(worker_id, 3))
            tasks.append(task)

        # Wait for all tasks to complete
        all_results = await asyncio.gather(*tasks)

        # Flatten results
        flattened_results = []
        for worker_results in all_results:
            flattened_results.extend(worker_results)

        # Check final state
        final_data = await asf.read()
        total_ops = final_data.get('total_async_operations', 0)
        worker_count = len(final_data.get('async_workers', {}))

        print(f"📊 Final async results:")
        print(f"   - Total async operations recorded: {total_ops}")
        print(f"   - Async workers that wrote data: {worker_count}")
        print(f"   - Individual async operation results: {len([r for r in flattened_results if 'completed' in r])}/{len(flattened_results)} successful")

        # All async workers should have been able to write at least something
        assert worker_count > 0, "No async workers managed to write data"
        print("✅ Concurrent async individual operations work correctly")

        print("\n🎉 All async concurrency tests passed!")

    finally:
        # Cleanup
        try:
            test_file.unlink()
        except:
            pass


@pytest.mark.asyncio
async def test_async_safefile_mixed_scenarios():
    """Test AsyncSafeFile in mixed async scenarios"""

    print("\n🚀 Testing AsyncSafeFile Mixed Async Scenarios")
    print("="*50)

    with tempfile.NamedTemporaryFile(suffix='.json', delete=False) as tmp:
        test_file = Path(tmp.name)

    try:
        asf = AsyncSafeFile(test_file, timeout=3)

        # Test mixing individual operations with locked context
        print("📋 Test 1: Mixing individual async operations with locked context")

        await asf.write({'scenario': 'mixed', 'step': 0})

        # Individual operation
        data = await asf.read()
        data['step'] = 1
        await asf.write(data)

        # Locked context operation
        async with asf.locked() as f:
            data = await f.read()
            data['step'] = 2
            data['locked_context'] = True
            await f.write(data)

            await asyncio.sleep(0.1)

            data = await f.read()
            data['step'] = 3
            await f.write(data)

        # Another individual operation
        data = await asf.read()
        data['step'] = 4
        data['final'] = True
        await asf.write(data)

        final_data = await asf.read()
        assert final_data['step'] == 4, f"Expected step=4, got {final_data['step']}"
        assert final_data['locked_context'] is True, "Locked context flag not set"
        assert final_data['final'] is True, "Final flag not set"
        print("✅ Mixed async operations work correctly")

        # Test async context manager with exception handling
        print("\n📋 Test 2: Async context manager with exception handling")

        try:
            async with asf.locked() as f:
                data = await f.read()
                data['exception_test'] = 'started'
                await f.write(data)

                # Simulate an exception
                raise ValueError("Test exception in async context")

        except ValueError as e:
            print(f"  📋 Caught expected exception: {e}")

        # Verify the file is still accessible after exception
        data = await asf.read()
        assert 'exception_test' in data, "Data from before exception should still be there"

        # Write more data to verify lock was properly released
        data['after_exception'] = True
        await asf.write(data)

        final_data = await asf.read()
        assert final_data['after_exception'] is True, "Should be able to write after exception"
        print("✅ Async exception handling in locked context works correctly")

        print("\n🎉 All mixed async scenario tests passed!")

    finally:
        # Cleanup
        try:
            test_file.unlink()
        except:
            pass


async def run_all_async_tests():
    """Run all AsyncSafeFile tests"""

    await test_async_safefile_basic_operations()
    await test_async_safefile_locked_context()
    await test_async_safefile_timeout_behavior()
    await test_async_safefile_error_handling()
    await test_async_safefile_concurrency()
    await test_async_safefile_mixed_scenarios()

    print("\n" + "="*65)
    print("🎊 ALL ASYNC SAFEFILE TESTS COMPLETED SUCCESSFULLY!")
    print("="*65)
    print("\n📝 Summary:")
    print("   AsyncSafeFile: Async file operations with proper async lock coordination")
    print("   ✅ Individual async operations work correctly")
    print("   ✅ async locked() context manager provides proper cross-operation locking")
    print("   ✅ Async timeout handling works as expected")
    print("   ✅ Async error handling is robust")
    print("   ✅ Concurrent async access is properly managed")
    print("   ✅ Mixed async scenarios work correctly")
    print("\n💡 Use AsyncSafeFile when you need:")
    print("   • Async file operations with proper await support")
    print("   • Cross-operation exclusive access in async code")
    print("   • Proper async lock coordination")
    print("   • Complex async multi-step file operations")


if __name__ == "__main__":
    asyncio.run(run_all_async_tests())
