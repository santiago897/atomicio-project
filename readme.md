

# atomicio

## Atomic, locked file operations with plugin-based format support

### Features
- Atomic and thread-safe file operations
- Inter-process locking (FileLock)
- Plugin system for custom file formats (via entry points)
- CLI for reading, writing, and listing supported formats

### CLI Usage

```
python -m atomicio read <file> [--as-bytes]
python -m atomicio write <file> <data> [--as-bytes]
python -m atomicio formats
```

#### Examples

```
python -m atomicio read config.yaml
python -m atomicio write config.json '{"foo": 1}'
python -m atomicio formats
```

### Plugin Support: Registering New Formats

atomicio supports external plugins for file formats using Python entry points. To add support for a new format from another package:

1. In your package's `setup.py` or `pyproject.toml`, declare an entry point under `atomicio.formats`:

   ```toml
   [project.entry-points."atomicio.formats"]
   myformat = "myplugin.module:MyFormatHandler"
   ```
   or in `setup.py`:
   ```python
   entry_points={
       'atomicio.formats': [
           'myformat = myplugin.module:MyFormatHandler',
       ],
   },
   ```
2. Implement the required interface in your handler (see `atomicio/formats.py` for examples).
3. Install your package. atomicio will auto-detect and use your format.

---

# atomicio (Español)

## Operaciones atómicas y seguras sobre archivos con soporte de plugins de formato

### Características
- Operaciones de archivo atómicas y seguras para hilos
- Bloqueo entre procesos (FileLock)
- Sistema de plugins para formatos personalizados (via entry points)
- CLI para leer, escribir y listar formatos soportados

### Uso del CLI

```
python -m atomicio read <archivo> [--as-bytes]
python -m atomicio write <archivo> <datos> [--as-bytes]
python -m atomicio formats
```

#### Ejemplos

```
python -m atomicio read config.yaml
python -m atomicio write config.json '{"foo": 1}'
python -m atomicio formats
```

### Soporte de Plugins: Registrar Nuevos Formatos

atomicio soporta plugins externos para formatos de archivo usando entry points de Python. Para agregar soporte a un nuevo formato desde otro paquete:

1. En el `setup.py` o `pyproject.toml` de tu paquete, declara un entry point bajo `atomicio.formats`:

   ```toml
   [project.entry-points."atomicio.formats"]
   miformato = "miplugin.modulo:MiHandlerFormato"
   ```
   o en `setup.py`:
   ```python
   entry_points={
       'atomicio.formats': [
           'miformato = miplugin.modulo:MiHandlerFormato',
       ],
   },
   ```
2. Implementa la interfaz requerida en tu handler (ver ejemplos en `atomicio/formats.py`).
3. Instala tu paquete. atomicio detectará y usará tu formato automáticamente.

Atomic, locked file operations with plugin-based format support.

## Features
- Cross-process file locking (.lock)
- Thread-safe locks in memory
- Atomic writes to avoid file corruption
- Plugin system to add support for new file formats
- Supports YAML, JSON, TOML, TXT out of the box

## Installation

```bash
pip install atomicio
```

## Usage example
```python
from atomicio import SafeFile

sf = SafeFile("config.yaml")

with sf.locked() as f:
    data = f.read() or {}
    data["counter"] = data.get("counter", 0) + 1
    f.write(data)
```

## List supported formats
```python
from atomicio import SafeFile
print(SafeFile.supported_formats())
# Output: ['.json', '.toml', '.txt', '.yaml', '.yml']
```

## Extending with plugins (custom formats)
You can add support for new file formats by registering a loader and dumper:

```python
from atomicio import register_format, SafeFile

def csv_loader(f):
    import csv
    return list(csv.reader(f))

def csv_dumper(data, f):
    import csv
    writer = csv.writer(f)
    writer.writerows(data)

register_format('.csv', csv_loader, csv_dumper)

sf = SafeFile('data.csv')
sf.write([[1,2,3],[4,5,6]])
print(sf.read())
```


## Command Line Interface (CLI)

atomicio incluye un CLI para usuarios avanzados:

```bash
# Leer y mostrar un archivo (auto-detecta formato)
python -m atomicio read config.yaml

# Escribir datos (JSON para estructurados)
python -m atomicio write config.json '{"foo": 1}'

# Leer/escribir como bytes
python -m atomicio read archivo.bin --as-bytes > out.bin
python -m atomicio write archivo.txt "hola" --as-bytes

# Listar formatos soportados
python -m atomicio formats
```

Puedes ver ayuda y ejemplos con:
```bash
python -m atomicio --help
```

## License
MIT

