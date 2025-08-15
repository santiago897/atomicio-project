import time
import threading
import sys
import os
from concurrent.futures import ThreadPoolExecutor, as_completed

# Add the current directory to the path so we can import atomicio
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from atomicio.core import ThreadedSafeFile
from atomicio import AsyncTimeoutError, FileOperationError

TEST_TIME_DURATION = 30  # Full test duration
TEST_DURATION = TEST_TIME_DURATION  # Fix undefined variable
FINAL_PHASE_START = TEST_TIME_DURATION * 0.8  # Last 20% of the test
IS_BLOCKED = False

def check(name, condition, ok_message, error_message):
    try:
        assert condition, f"❌ Test '{error_message}' failed:"
        print(ok_message)
    except AssertionError as e:
        print(e)

def timer_display():
    """Muestra el progreso del test."""
    start_time = time.time()

    while time.time() - start_time < TEST_DURATION:
        elapsed = time.time() - start_time
        remaining = TEST_DURATION - elapsed
        progress = elapsed / TEST_DURATION * 100

        # Barra de progreso
        bar_length = 30
        filled_length = int(bar_length * elapsed / TEST_DURATION)
        bar = "█" * filled_length + "░" * (bar_length - filled_length)

        # Indicar fase
        if elapsed < FINAL_PHASE_START:
            phase = "CRONÓMETRO + VALIDACIÓN"
        else:
            phase = "FASE FINAL"

        print(f"\r⏱️  [{bar}] {progress:.1f}% - {remaining:.1f}s - {phase}", end="", flush=True)
        time.sleep(0.5)

    print(f"\r⏱️  [{'█' * bar_length}] 100.0% - COMPLETADO" + " " * 20)

def worker(ct, elapsed, timeout, simulate_long_write=False):
    try:
        new_data = {
            "current_time": ct,
            "time_elapsed": elapsed
        }

        tsf = ThreadedSafeFile('coordinated_test_threaded.yaml', timeout=timeout)

        if simulate_long_write:
            # Use locked context to hold the lock during the entire operation
            with tsf.locked() as f:
                # Read and write operations using the locked context
                prev_data = f.read() or {}
                updated_data = prev_data.copy()
                updated_data.update(new_data)
                f.write(updated_data)

                print(f"-📝  Worker wrote at time: {ct}")
                print(f"Previous data read from file: {prev_data}")
                print(f"Updated data to be written to file: {updated_data}")

                # Simulate 3-second block WHILE HOLDING the lock
                print(f"💤 Simulating 3-second write block WHILE HOLDING LOCK...")
                time.sleep(3)
                print(f"✅ 3-second write block completed")
        else:
            # For normal operations, use direct methods
            prev_data = tsf.read() or {}
            updated_data = prev_data.copy()
            updated_data.update(new_data)
            tsf.write(updated_data)

            print(f"-📝  Worker wrote at time: {ct}")
            print(f"Previous data read from file: {prev_data}")
            print(f"Updated data to be written to file: {updated_data}")

        return prev_data, updated_data
    except AsyncTimeoutError as e:
        print(f"⚠️  Worker timed out waiting for file lock at time: {ct}")
        print(f"⚠️  Timeout details: {e}")
        print(f"⚠️  Timeout duration: {e.timeout}s, Path: {e.path}")
        return {}, {}
    except FileOperationError as e:
        print(f"📁  File operation error at time: {ct}")
        print(f"📁  Error details: {e}")
        return {}, {}
    except Exception as e:
        import traceback
        print(f"Worker couldn't write file at time: {ct}")
        print(f"Error type: {type(e).__name__}")
        print(f"Error message: {str(e)}")
        print(f"Traceback: {traceback.format_exc()}")
        return {}, {}

def main():
    global IS_BLOCKED
    start_time = time.time()
    last_validation_time = 0
    prev_elapsed = -1

    # Create timer thread
    timer_thread = threading.Thread(target=timer_display, daemon=True)
    timer_thread.start()

    # Use ThreadPoolExecutor for concurrent operations
    with ThreadPoolExecutor(max_workers=10) as executor:
        try:
            while time.time() - start_time < TEST_TIME_DURATION:
                current_time = time.time()
                elapsed = current_time - start_time

                # Check if 5 seconds have passed since last validation (simulate 3-second block)
                if elapsed - last_validation_time >= 5.0:
                    print(f"\n[{elapsed:.1f}s] Running LONG WRITE (3-second block with lock held)...")
                    print(f"📋 NOTE: ThreadedSafeFile CAN hold locks between operations like async version")

                    # Start the long write operation as a background task
                    long_write_future = executor.submit(
                        worker, current_time, elapsed, 10.0, True
                    )

                    # Give the long write a moment to acquire the lock
                    time.sleep(0.1)

                    # Now try multiple concurrent short operations while the long write is holding the lock
                    concurrent_futures = []
                    for i in range(3):  # Try 3 concurrent operations during the long write
                        future = executor.submit(
                            worker, current_time + 0.1 * i, elapsed + 0.1 * i, 1, False
                        )
                        concurrent_futures.append(future)
                        time.sleep(0.2)  # Small delay between starting attempts

                    # Wait for all concurrent attempts to complete and check results
                    timeout_count = 0
                    for i, future in enumerate(concurrent_futures):
                        try:
                            result = future.result(timeout=5)  # Give each task 5 seconds to complete
                            if result == ({}, {}):  # Empty result indicates timeout was caught
                                timeout_count += 1
                                print(f"  ✅ Concurrent attempt {i+1} timed out correctly (returned empty result)")
                            else:
                                print(f"  ❌ Concurrent attempt {i+1} unexpectedly succeeded with result: {result}")
                        except Exception as e:
                            print(f"  ⚠️  Concurrent attempt {i+1} failed with unexpected error: {e}")

                    # Wait for the long write to complete
                    try:
                        prev_data, data = long_write_future.result(timeout=15)  # Long write should complete within 15 seconds
                        last_validation_time = elapsed

                        print(f"✅ Long write completed. File now contains time: {elapsed:.1f}")
                        print(f"🎯 Timeout count: {timeout_count}/3 concurrent attempts timed out correctly")
                    except Exception as e:
                        print(f"❌ Long write failed: {e}")

                # Run worker with short timeout for regular updates (every 1 second)
                if elapsed - prev_elapsed >= 1.0:
                    print(f"\n[{elapsed:.1f}s] Attempting regular 1-second update...")
                    try:
                        future = executor.submit(worker, current_time, elapsed, 1, False)
                        prev_data, updated_data = future.result(timeout=2)  # Give 2 seconds for completion
                        print(prev_data, updated_data)
                    except AsyncTimeoutError as e:
                        print(f"⚠️ TIMEOUT: Regular update timed out at {elapsed:.1f}s")
                        print(f"⚠️ Timeout details: {e}")
                        print(f"⚠️ Timeout duration: {e.timeout}s, Path: {e.path}")
                    except FileOperationError as e:
                        print(f"📁 FILE ERROR: Regular update failed at {elapsed:.1f}s")
                        print(f"📁 Error details: {e}")
                    except Exception as e:
                        print(f"⚠️ THREAD ERROR: Regular update failed at {elapsed:.1f}s with error: {e}")

                    prev_elapsed = elapsed

                # Small delay to prevent busy waiting
                time.sleep(0.1)

        except KeyboardInterrupt:
            print("\n🛑 Test interrupted by user")
        finally:
            # Shutdown the executor
            executor.shutdown(wait=True)

    print(f"\n⏱️  Test completed successfully!")

    # Cleanup: Delete the test file
    try:
        tsf = ThreadedSafeFile('coordinated_test_threaded.yaml')
        data = tsf.read() or {}

        print(f"-📝  Test file final content:\n{data}")

        if os.path.exists('coordinated_test_threaded.yaml'):
            os.remove('coordinated_test_threaded.yaml')
            print("🗑️  Test file cleaned up")
    except Exception as e:
        print(f"Warning: Could not clean up test file: {e}")

    return

if __name__ == "__main__":
    main()
