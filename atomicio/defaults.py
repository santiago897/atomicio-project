import json
import yaml
import tomli_w
import tomli
from typing import IO

from .formats import register_format

# YAML
def yaml_loader(f: IO):
    return yaml.safe_load(f)

def yaml_dumper(data, f: IO):
    yaml.safe_dump(data, f, default_flow_style=False, allow_unicode=True, indent=4)

register_format(".yaml", yaml_loader, yaml_dumper)
register_format(".yml", yaml_loader, yaml_dumper)

# JSON
def json_loader(f: IO):
    return json.load(f)

def json_dumper(data, f: IO):
    json.dump(data, f, indent=4)

register_format(".json", json_loader, json_dumper)

# TOML
def toml_loader(f: IO):
    return tomli.load(f)

def toml_dumper(data, f: IO):
    b = tomli_w.dumps(data)
    f.write(b)

register_format(".toml", toml_loader, toml_dumper)

# TXT (texto plano)
def txt_loader(f: IO):
    return f.read()

def txt_dumper(data, f: IO):
    if not isinstance(data, str):
        data = str(data)
    f.write(data)

register_format(".txt", txt_loader, txt_dumper)
