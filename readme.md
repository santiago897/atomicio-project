


# atomicio

## Atomic, locked file operations with plugin-based format support

### Features
- Atomic and thread-safe file operations
- Inter-process locking (FileLock)
- Plugin system for custom file formats (via entry points)
- CLI for reading, writing, and listing supported formats
- Utility functions for safe file and path management

---

## API Reference (Python)

### resolve_path
```python
resolve_path(path: str = None, dirpath: str = None, filename: str = None) -> Path
```
Resolves an absolute path from a string path or a combination of directory and filename.

### create_file
```python
create_file(path: str = None, dirpath: str = None, filename: str = None, content: str = "", overwrite: bool = False) -> Path
```
Creates a file at the given path. Raises if it exists and `overwrite` is False.

### delete_file
```python
delete_file(path: str = None, dirpath: str = None, filename: str = None, missing_ok: bool = True) -> None
```
Deletes a file. If `missing_ok` is False and the file does not exist, raises an exception.

### find_project_root
```python
find_project_root(start_path=None, git=False) -> Path | None
```
Searches upwards from a path (or cwd) for a project root (by .git, .venv, etc). Returns Path or None.

### find_project_files
```python
find_project_files(pattern: str, dirpath: str = None, recursive: bool = True, ignore_dirs=None, verbose: bool = False) -> list[Path] | False
```
Searches for files matching a regex pattern in the project or a directory. If `verbose=True`, prints a pretty summary of the results (number of files found and a numbered list with filename and path).

#### Example (verbose):
```python
files = find_project_files(r"test.*\\.py$", verbose=True)
# Output:
# Found 2 files:
#   1) filename: test_core.py | path: /path/to/test_core.py
#   2) filename: test_utils.py | path: /path/to/test_utils.py
```

---

### SafeFile class
Provides atomic, thread-safe, and process-safe file operations with format support.

#### Methods:
- `read()` – Reads and deserializes the file (by extension). Returns None if not found.
- `write(data)` – Serializes and writes data atomically.
- `append(text)` – Appends text to the file (not atomic).
- `read_bytes()` – Reads file as bytes.
- `write_bytes(data)` – Writes bytes atomically.
- `locked()` – Context manager for manual locking (thread + process).
- `supported_formats()` – Lists supported file extensions.

#### Example:
```python
from atomicio import SafeFile

sf = SafeFile("config.yaml")
with sf.locked() as f:
    data = f.read() or {}
    data["counter"] = data.get("counter", 0) + 1
    f.write(data)
```

---

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

## Command Line Interface (CLI)

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

---

# atomicio (Español)

## Operaciones atómicas y seguras sobre archivos con soporte de plugins de formato

### Características
- Operaciones de archivo atómicas y seguras para hilos
- Bloqueo entre procesos (FileLock)
- Sistema de plugins para formatos personalizados (via entry points)
- CLI para leer, escribir y listar formatos soportados
- Funciones utilitarias para manejo seguro de archivos y rutas

---

## Referencia de la API (Python)

### resolve_path
```python
resolve_path(path: str = None, dirpath: str = None, filename: str = None) -> Path
```
Resuelve una ruta absoluta a partir de un string o combinación de directorio y nombre de archivo.

### create_file
```python
create_file(path: str = None, dirpath: str = None, filename: str = None, content: str = "", overwrite: bool = False) -> Path
```
Crea un archivo en la ruta indicada. Lanza excepción si existe y `overwrite` es False.

### delete_file
```python
delete_file(path: str = None, dirpath: str = None, filename: str = None, missing_ok: bool = True) -> None
```
Elimina un archivo. Si `missing_ok` es False y el archivo no existe, lanza excepción.

### find_project_root
```python
find_project_root(start_path=None, git=False) -> Path | None
```
Busca hacia arriba desde una ruta (o cwd) el root del proyecto (por .git, .venv, etc). Devuelve Path o None.

### find_project_files
```python
find_project_files(pattern: str, dirpath: str = None, recursive: bool = True, ignore_dirs=None, verbose: bool = False) -> list[Path] | False
```
Busca archivos por regex en el proyecto o un directorio. Si `verbose=True`, imprime un resumen bonito (cantidad de archivos y lista numerada con nombre y ruta).

#### Ejemplo (verbose):
```python
files = find_project_files(r"test.*\\.py$", verbose=True)
# Salida:
# Found 2 files:
#   1) filename: test_core.py | path: /ruta/a/test_core.py
#   2) filename: test_utils.py | path: /ruta/a/test_utils.py
```

---

### Clase SafeFile
Provee operaciones atómicas, seguras para hilos y procesos, y soporte de formatos.

#### Métodos:
- `read()` – Lee y deserializa el archivo (por extensión). Devuelve None si no existe.
- `write(data)` – Serializa y escribe datos atómicamente.
- `append(text)` – Agrega texto al final (no atómico).
- `read_bytes()` – Lee el archivo como bytes.
- `write_bytes(data)` – Escribe bytes atómicamente.
- `locked()` – Context manager para bloqueo manual (hilos + proceso).
- `supported_formats()` – Lista las extensiones soportadas.

#### Ejemplo:
```python
from atomicio import SafeFile

sf = SafeFile("config.yaml")
with sf.locked() as f:
    data = f.read() or {}
    data["counter"] = data.get("counter", 0) + 1
    f.write(data)
```

---

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

---

## Uso del CLI

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

---

## License
MIT

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

