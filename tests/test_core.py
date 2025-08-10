import os
import pytest
from atomicio import SafeFile

TEST_FILE = "test_core.txt"

def teardown_function():
    if os.path.exists(TEST_FILE):
        os.remove(TEST_FILE)

def test_write_and_read():
    sf = SafeFile(TEST_FILE)
    sf.write("Hola Mundo")
    contenido = sf.read()
    assert contenido == "Hola Mundo"

def test_append():
    sf = SafeFile(TEST_FILE)
    sf.write("Linea1\n")
    sf.append("Linea2\n")
    contenido = sf.read()
    assert contenido == "Linea1\nLinea2\n"

def test_locked_context():
    sf = SafeFile(TEST_FILE)
    with sf.locked() as f:
        f.write("Dentro de locked")
        contenido = f.read()
        assert contenido == "Dentro de locked"


def test_read_file_not_found():
    sf = SafeFile("no_such_file_123456.txt")
    assert sf.read() is None

def test_write_permission_error(tmp_path):
    # Create a read-only file
    file_path = tmp_path / "readonly.txt"
    file_path.write_text("data")
    file_path.chmod(0o444)  # read-only
    sf = SafeFile(str(file_path))
    with pytest.raises(Exception):
        sf.write("fail")

def test_unsupported_format(tmp_path):
    file_path = tmp_path / "file.unsupported"
    sf = SafeFile(str(file_path))
    with pytest.raises(Exception):
        sf.write({"a": 1})
