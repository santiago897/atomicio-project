#!/usr/bin/env python3
"""
Test to verify all atomicio imports and basic functionality work correctly.
This test ensures our refactoring didn't break any imports or basic operations.
"""

import tempfile
import time
import asyncio
import pytest
from pathlib import Path


def test_imports():
    """Test that all classes and functions can be imported correctly"""

    print("🚀 Testing Atomicio Imports")
    print("="*40)

    # Test main classes import
    from atomicio import SafeFile, ThreadedSafeFile, AsyncSafeFile
    print("✅ Main classes imported successfully")

    # Test utility functions import
    from atomicio import resolve_path, create_file, delete_file, find_project_files
    print("✅ Utility functions imported successfully")

    # Test format registration
    from atomicio import register_format
    print("✅ Format registration imported successfully")

    # Test exceptions
    from atomicio import (
        AtomicIOError, FileOperationError, FileReadError,
        FileWriteError, FileAppendError, AsyncTimeoutError, AsyncLockError
    )
    print("✅ All exceptions imported successfully")

    # Test version
    from atomicio import __version__
    print(f"✅ Version imported successfully: {__version__}")

    print("\n🎉 All imports successful!")


def test_safefile_basic():
    """Test SafeFile basic functionality"""

    print("\n🚀 Testing SafeFile Basic Functionality")
    print("="*45)

    from atomicio import SafeFile

    with tempfile.NamedTemporaryFile(suffix='.json', delete=False) as tmp:
        test_file = Path(tmp.name)

    try:
        sf = SafeFile(test_file, timeout=5)

        # Test basic write/read
        test_data = {'test': 'safefile', 'number': 123}
        sf.write(test_data)
        result = sf.read()

        assert result == test_data, f"Expected {test_data}, got {result}"
        print("✅ SafeFile write/read works")

        # Test context manager
        with sf:
            data = sf.read()
            data['context'] = True
            sf.write(data)

        final_data = sf.read()
        assert 'context' in final_data, "Context manager failed"
        print("✅ SafeFile context manager works")

    finally:
        test_file.unlink(missing_ok=True)
        Path(str(test_file) + ".lock").unlink(missing_ok=True)


def test_threaded_safefile_basic():
    """Test ThreadedSafeFile basic functionality"""

    print("\n🚀 Testing ThreadedSafeFile Basic Functionality")
    print("="*50)

    from atomicio import ThreadedSafeFile

    with tempfile.NamedTemporaryFile(suffix='.json', delete=False) as tmp:
        test_file = Path(tmp.name)

    try:
        tsf = ThreadedSafeFile(test_file, timeout=5)

        # Test basic operations
        test_data = {'test': 'threaded_safefile', 'number': 456}
        tsf.write(test_data)
        result = tsf.read()

        assert result == test_data, f"Expected {test_data}, got {result}"
        print("✅ ThreadedSafeFile write/read works")

        # Test locked context manager
        with tsf.locked() as f:
            data = f.read()
            data['locked'] = True
            f.write(data)
            # Sleep briefly while holding lock
            time.sleep(0.1)

        final_data = tsf.read()
        assert 'locked' in final_data, "Locked context manager failed"
        print("✅ ThreadedSafeFile locked() context manager works")

    finally:
        test_file.unlink(missing_ok=True)


@pytest.mark.asyncio
async def test_async_safefile_basic():
    """Test AsyncSafeFile basic functionality"""

    print("\n🚀 Testing AsyncSafeFile Basic Functionality")
    print("="*45)

    from atomicio import AsyncSafeFile

    with tempfile.NamedTemporaryFile(suffix='.json', delete=False) as tmp:
        test_file = Path(tmp.name)

    try:
        asf = AsyncSafeFile(test_file, timeout=5)

        # Test basic operations
        test_data = {'test': 'async_safefile', 'number': 789}
        await asf.write(test_data)
        result = await asf.read()

        assert result == test_data, f"Expected {test_data}, got {result}"
        print("✅ AsyncSafeFile write/read works")

        # Test locked context manager
        async with asf.locked() as f:
            data = await f.read()
            data['async_locked'] = True
            await f.write(data)
            # Sleep briefly while holding lock
            await asyncio.sleep(0.1)

        final_data = await asf.read()
        assert 'async_locked' in final_data, "Async locked context manager failed"
        print("✅ AsyncSafeFile locked() context manager works")

    finally:
        test_file.unlink(missing_ok=True)


def test_utility_functions():
    """Test utility functions"""

    print("\n🚀 Testing Utility Functions")
    print("="*35)

    from atomicio import resolve_path, create_file, delete_file

    # Test resolve_path
    test_path = resolve_path(path="test.txt")
    assert isinstance(test_path, Path), "resolve_path should return Path object"
    print("✅ resolve_path works")

    # Test create_file and delete_file
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_dir_path = Path(temp_dir)
        test_file = create_file(dirpath=str(temp_dir_path), filename="test.txt", content="Hello World")

        assert test_file.exists(), "create_file should create file"
        assert test_file.read_text() == "Hello World", "File content should match"
        print("✅ create_file works")

        delete_file(path=str(test_file))
        assert not test_file.exists(), "delete_file should remove file"
        print("✅ delete_file works")


def test_supported_formats():
    """Test that supported formats work"""

    print("\n🚀 Testing Supported Formats")
    print("="*35)

    from atomicio import SafeFile

    formats = SafeFile.supported_formats()
    assert isinstance(formats, list), "supported_formats should return list"
    assert len(formats) > 0, "Should have some supported formats"

    expected_formats = ['.json', '.yaml', '.yml', '.toml', '.txt']
    for fmt in expected_formats:
        if fmt in formats:
            print(f"✅ {fmt} format supported")
        else:
            print(f"⚠️  {fmt} format not found (might be optional)")

    print(f"📋 Total supported formats: {len(formats)}")


async def run_async_tests():
    """Run async tests"""
    return await test_async_safefile_basic()


def main():
    """Run all tests"""

    print("🧪 ATOMICIO IMPORT AND FUNCTIONALITY TEST")
    print("="*60)

    results = []

    # Run sync tests
    results.append(("Imports", test_imports()))
    results.append(("SafeFile Basic", test_safefile_basic()))
    results.append(("ThreadedSafeFile Basic", test_threaded_safefile_basic()))
    results.append(("Utility Functions", test_utility_functions()))
    results.append(("Supported Formats", test_supported_formats()))

    # Run async tests
    try:
        async_result = asyncio.run(run_async_tests())
        results.append(("AsyncSafeFile Basic", async_result))
    except Exception as e:
        print(f"❌ Async tests failed: {e}")
        results.append(("AsyncSafeFile Basic", False))

    # Summary
    print("\n" + "="*60)
    print("📊 TEST RESULTS SUMMARY")
    print("="*60)

    passed = 0
    total = len(results)

    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{test_name:25} {status}")
        if result:
            passed += 1

    print("-" * 60)
    print(f"TOTAL: {passed}/{total} tests passed")

    if passed == total:
        print("\n🎊 ALL TESTS PASSED! Atomicio is working correctly!")
        print("\n📝 Summary of available classes:")
        print("   • SafeFile: Simple atomic operations with FileLock")
        print("   • ThreadedSafeFile: Cross-operation locking with thread locks")
        print("   • AsyncSafeFile: Async operations with async locks")
        print("\n💡 Use SafeFile for basic atomic operations in sync code")
        print("💡 Use ThreadedSafeFile when you need cross-operation locking")
        print("💡 Use AsyncSafeFile for proper async coordination")
        return True
    else:
        print(f"\n❌ {total - passed} tests failed!")
        return False


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
