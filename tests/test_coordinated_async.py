import time
import asyncio
import sys
import os

# Add the current directory to the path so we can import atomicio
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from atomicio.core import AsyncSafeFile
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

async def timer_display():
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
        await asyncio.sleep(0.5)

    print(f"\r⏱️  [{'█' * bar_length}] 100.0% - COMPLETADO" + " " * 20)

async def worker(ct, elapsed, timeout, simulate_long_write=False):
    try:
        new_data = {
            "current_time": ct,
            "time_elapsed": elapsed
        }

        asf = AsyncSafeFile('coordinated_test.yaml', timeout=timeout)

        if simulate_long_write:
            # Use locked context to hold the lock during the entire operation
            async with asf.locked() as locked_file:
                # Read and write operations using the locked context
                prev_data = await locked_file.read() or {}
                updated_data = prev_data.copy()
                updated_data.update(new_data)
                await locked_file.write(updated_data)

                print(f"-📝  Worker wrote at time: {ct}")
                print(f"Previous data read from file: {prev_data}")
                print(f"Updated data to be written to file: {updated_data}")

                # Simulate 3-second block WHILE HOLDING the lock
                print(f"💤 Simulating 3-second write block WHILE HOLDING LOCK...")
                await asyncio.sleep(3)
                print(f"✅ 3-second write block completed")
        else:
            # For normal operations, use direct methods
            prev_data = await asf.read() or {}
            updated_data = prev_data.copy()
            updated_data.update(new_data)
            await asf.write(updated_data)

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

async def main():
    global IS_BLOCKED
    start_time = time.time()
    last_validation_time = 0
    prev_elapsed = -1

    # Create tasks for timer and worker logic
    timer_task = asyncio.create_task(timer_display())

    try:
        while time.time() - start_time < TEST_TIME_DURATION:
            current_time = time.time()
            elapsed = current_time - start_time

            # Check if 5 seconds have passed since last validation (simulate 3-second block)
            if elapsed - last_validation_time >= 5.0:
                print(f"\n[{elapsed:.1f}s] Running LONG WRITE (3-second block)...")

                # Start the long write operation as a background task
                long_write_task = asyncio.create_task(
                    worker(current_time, elapsed, timeout=10.0, simulate_long_write=True)
                )

                # Give the long write a moment to acquire the lock
                await asyncio.sleep(0.1)

                # Now try multiple concurrent short operations while the long write is holding the lock
                concurrent_attempts = []
                for i in range(3):  # Try 3 concurrent operations during the long write
                    attempt_task = asyncio.create_task(
                        worker(current_time + 0.1 * i, elapsed + 0.1 * i, timeout=1, simulate_long_write=False)
                    )
                    concurrent_attempts.append(attempt_task)
                    await asyncio.sleep(0.2)  # Small delay between starting attempts

                # Wait for all concurrent attempts to complete and check results
                timeout_count = 0
                for i, attempt_task in enumerate(concurrent_attempts):
                    try:
                        result = await attempt_task
                        if result == ({}, {}):  # Empty result indicates timeout was caught
                            timeout_count += 1
                            print(f"  ✅ Concurrent attempt {i+1} timed out correctly (returned empty result)")
                        else:
                            print(f"  ❌ Concurrent attempt {i+1} unexpectedly succeeded with result: {result}")
                    except Exception as e:
                        print(f"  ⚠️  Concurrent attempt {i+1} failed with unexpected error: {e}")

                # Wait for the long write to complete
                prev_data, data = await long_write_task
                last_validation_time = elapsed

                print(f"✅ Long write completed. File now contains time: {elapsed:.1f}")
                print(f"🎯 Timeout count: {timeout_count}/3 concurrent attempts timed out correctly")

            # Run worker with short timeout for regular updates (every 1 second)
            if elapsed - prev_elapsed >= 1.0:
                print(f"\n[{elapsed:.1f}s] Attempting regular 1-second update...")
                try:
                    prev_data, updated_data = await worker(current_time, elapsed, timeout=1, simulate_long_write=False)
                    print(prev_data, updated_data)
                except AsyncTimeoutError as e:
                    print(f"⚠️ TIMEOUT: Regular update timed out at {elapsed:.1f}s")
                    print(f"⚠️ Timeout details: {e}")
                    print(f"⚠️ Timeout duration: {e.timeout}s, Path: {e.path}")
                except FileOperationError as e:
                    print(f"📁 FILE ERROR: Regular update failed at {elapsed:.1f}s")
                    print(f"📁 Error details: {e}")

                prev_elapsed = elapsed

            # Small delay to prevent busy waiting
            await asyncio.sleep(0.1)

    finally:
        # Cancel timer task
        timer_task.cancel()
        try:
            await timer_task
        except asyncio.CancelledError:
            pass

    print(f"\n⏱️  Test completed successfully!")

    # Cleanup: Delete the test file
    try:
        asf = AsyncSafeFile('coordinated_test.yaml')
        data = await asf.read() or {}

        print(f"-📝  Test file final content:\n{data}")

        if os.path.exists('coordinated_test.yaml'):
            os.remove('coordinated_test.yaml')
            print("🗑️  Test file cleaned up")
    except Exception as e:
        print(f"Warning: Could not clean up test file: {e}")

    return

if __name__ == "__main__":
    asyncio.run(main())
