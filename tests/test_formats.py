import io
import pytest
from atomicio import formats

def test_register_and_use_format():
    dummy_loader_called = False
    dummy_dumper_called = False

    def dummy_loader(f):
        nonlocal dummy_loader_called
        dummy_loader_called = True
        return "loaded"

    def dummy_dumper(data, f):
        nonlocal dummy_dumper_called
        dummy_dumper_called = True

    formats.register_format(".dum", dummy_loader, dummy_dumper)

    # Simular archivo con io.StringIO
    fake_file = io.StringIO("data")
    result = formats.load_data(fake_file, ".dum")
    assert result == "loaded"
    assert dummy_loader_called

    dummy_dumper("data", fake_file)
    assert dummy_dumper_called

def test_get_handlers_error():
    with pytest.raises(ValueError):
        formats.load_data(io.StringIO(), ".noext")
