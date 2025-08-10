import os
import tempfile
import pytest
from atomicio import SafeFile

def test_yaml_roundtrip():
    data = {"a": 1, "b": [1, 2, 3]}
    with tempfile.NamedTemporaryFile(suffix=".yaml", delete=False) as tf:
        path = tf.name
    sf = SafeFile(path)
    sf.write(data)
    loaded = sf.read()
    assert loaded == data
    os.remove(path)

def test_json_roundtrip():
    data = {"foo": "bar", "baz": 123}
    with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as tf:
        path = tf.name
    sf = SafeFile(path)
    sf.write(data)
    loaded = sf.read()
    assert loaded == data
    os.remove(path)

def test_toml_roundtrip():
    data = {"key": "value", "list": [1, 2, 3]}
    with tempfile.NamedTemporaryFile(suffix=".toml", delete=False) as tf:
        path = tf.name
    sf = SafeFile(path)
    sf.write(data)
    loaded = sf.read()
    assert loaded == data
    os.remove(path)

def test_txt_roundtrip():
    data = "Hola texto plano"
    with tempfile.NamedTemporaryFile(suffix=".txt", delete=False) as tf:
        path = tf.name
    sf = SafeFile(path)
    sf.write(data)
    loaded = sf.read()
    assert loaded == data
    os.remove(path)
