import os
import time
import threading
import multiprocessing
import pytest
from atomicio import SafeFile

TEST_FILE = "test_concurrency.yaml"

def worker(id, iterations):
    sf = SafeFile(TEST_FILE)
    for _ in range(iterations):
        with sf.locked() as f:
            data = f.read() or {"counter": 0, "writes": {}, "last_access": {}}

            # Incrementar contador global
            data["counter"] = data.get("counter", 0) + 1

            # Contar escrituras por worker
            writes = data.get("writes", {})
            writes[str(id)] = writes.get(str(id), 0) + 1
            data["writes"] = writes

            # Guardar último timestamp de acceso
            last_access = data.get("last_access", {})
            last_access[str(id)] = time.time()
            data["last_access"] = last_access

            f.write(data)

        time.sleep(0.005)  # simular trabajo

def test_heavy_concurrent_modifications():
    if os.path.exists(TEST_FILE):
        os.remove(TEST_FILE)

    thread_count = 5
    process_count = 3
    iterations = 50

    threads = [threading.Thread(target=worker, args=(f"thread-{i}", iterations)) for i in range(thread_count)]
    processes = [multiprocessing.Process(target=worker, args=(f"proc-{i}", iterations)) for i in range(process_count)]

    for p in processes:
        p.start()
    for t in threads:
        t.start()

    for t in threads:
        t.join()
    for p in processes:
        p.join()

    sf = SafeFile(TEST_FILE)
    data = sf.read()

    assert data is not None, "Archivo vacío"
    expected_count = (thread_count + process_count) * iterations
    assert data.get("counter") == expected_count, f"Contador incorrecto: {data.get('counter')} != {expected_count}"

    writes = data.get("writes", {})
    for i in range(thread_count):
        key = f"thread-{i}"
        assert writes.get(key) == iterations, f"Escrituras incorrectas para {key}"

    for i in range(process_count):
        key = f"proc-{i}"
        assert writes.get(key) == iterations, f"Escrituras incorrectas para {key}"

    last_access = data.get("last_access", {})
    for i in range(thread_count):
        key = f"thread-{i}"
        assert key in last_access, f"Falta timestamp para {key}"

    for i in range(process_count):
        key = f"proc-{i}"
        assert key in last_access, f"Falta timestamp para {key}"
