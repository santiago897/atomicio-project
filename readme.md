


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


### Imports
```python
from atomicio import resolve_path, create_file, delete_file, find_project_root, find_project_files, SafeFile
```

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

### What is `locked()`? When and why should you use it?

The `locked()` method of `SafeFile` provides a context manager that ensures **exclusive access** to a file, both at the thread and process level. This means that while your code is inside the `with sf.locked():` block, no other thread or process can read or write to the file, preventing race conditions and data corruption.

#### When should you use `locked()`?
- When you need to perform **multiple operations** on a file as a single atomic transaction (e.g., read, modify, write).
- When your code may run in **multi-threaded** or **multi-process** environments (e.g., web servers, background jobs, scripts running in parallel).
- When you want to ensure that **no other process or thread** can interfere with your file operations.

#### Example: Fetching data from an API and saving it atomically

Suppose you want to fetch data from an API and store the result in a JSON file, ensuring that no other process can read or write the file while you are updating it.

```python
from atomicio import SafeFile
import requests

# Create the file safely (if it doesn't exist)
sf = SafeFile.create(dirpath="results", filename="data.json")

# Fetch data from an API
response = requests.get("https://jsonplaceholder.typicode.com/todos/1")
api_data = response.json()

# Safely update the file with the new data
with sf.locked() as f:
    current = f.read() or {}
    current["api_result"] = api_data
    f.write(current)
```

#### Why is this beneficial?
- **Prevents race conditions:** If multiple scripts or threads try to update the file at the same time, only one will succeed at a time, ensuring data integrity.
- **Atomic updates:** The file is never left in a partially written or corrupted state.
- **Safe for concurrent environments:** Perfect for web servers, cron jobs, or any scenario where multiple processes may access the same file.
- **Easy to use:** The context manager pattern (`with ... as ...:`) is familiar and Pythonic.

#### Potential
This pattern allows you to safely:
- Aggregate results from multiple sources into a single file.
- Implement simple databases or caches using files.
- Share state between processes without risk of corruption.
- Build robust automation scripts that interact with external APIs or data sources.

---

### Plugin Support: Registering New Formats


atomicio allows you to extend its file format support by registering your own loader and dumper functions for any file extension using the `register_format` function.

#### Purpose
`register_format` lets you add support for custom file formats (e.g., CSV, XML, INI, etc.) so you can use all the atomic and safe file operations of atomicio with your own data types. This makes atomicio adaptable to any workflow or project, not just the built-in formats (YAML, JSON, TOML, TXT).

#### How it helps
- Integrate your own serialization/deserialization logic for any extension.
- Use the same SafeFile API for your custom formats.
- Share new formats as plugins or just register them at runtime.

#### Usage Example
Suppose you want to add support for CSV files:
```python
from atomicio import register_format, SafeFile
import csv

def csv_loader(f):
    return list(csv.reader(f))

def csv_dumper(data, f):
    writer = csv.writer(f)
    writer.writerows(data)

register_format('.csv', csv_loader, csv_dumper)

sf = SafeFile('data.csv')
sf.write([[1,2,3],[4,5,6]])
print(sf.read())  # Output: [[1, 2, 3], [4, 5, 6]]
```

#### Plugin System
You can also distribute your format as a plugin using entry points:

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


### Imports
```python
from atomicio import resolve_path, create_file, delete_file, find_project_root, find_project_files, SafeFile
```

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

### ¿Qué es `locked()`? ¿Cuándo usarlo y cuáles son sus beneficios?

El método `locked()` de `SafeFile` provee un context manager que asegura **acceso exclusivo** a un archivo, tanto a nivel de hilos como de procesos. Esto significa que, mientras tu código esté dentro del bloque `with sf.locked():`, ningún otro hilo o proceso podrá leer o escribir el archivo, evitando condiciones de carrera y corrupción de datos.

#### ¿Cuándo deberías usar `locked()`?
- Cuando necesitas realizar **varias operaciones** sobre un archivo como una transacción atómica (por ejemplo, leer, modificar y escribir).
- Cuando tu código puede ejecutarse en entornos **multihilo** o **multiproceso** (por ejemplo, servidores web, jobs en background, scripts en paralelo).
- Cuando quieres asegurar que **ningún otro proceso o hilo** interfiera con tus operaciones de archivo.

#### Ejemplo: Consultar una API y guardar el resultado de forma atómica

Supón que quieres consultar una API y guardar el resultado en un archivo JSON, asegurando que ningún otro proceso pueda leer o escribir el archivo mientras lo actualizas.

```python
from atomicio import SafeFile
import requests

# Crear el archivo de forma segura (si no existe)
sf = SafeFile.create(dirpath="results", filename="data.json")

# Consultar datos de una API
response = requests.get("https://jsonplaceholder.typicode.com/todos/1")
api_data = response.json()

# Actualizar el archivo de forma segura con los nuevos datos
with sf.locked() as f:
    actual = f.read() or {}
    actual["resultado_api"] = api_data
    f.write(actual)
```

#### ¿Por qué es beneficioso?
- **Evita condiciones de carrera:** Si varios scripts o hilos intentan actualizar el archivo al mismo tiempo, solo uno lo hará a la vez, asegurando la integridad de los datos.
- **Actualizaciones atómicas:** El archivo nunca queda en un estado parcialmente escrito o corrupto.
- **Seguro para entornos concurrentes:** Ideal para servidores web, cron jobs o cualquier escenario donde varios procesos acceden al mismo archivo.
- **Fácil de usar:** El patrón de context manager (`with ... as ...:`) es familiar y Pythonic.

#### Potencial
Este patrón te permite:
- Agregar resultados de múltiples fuentes en un solo archivo de forma segura.
- Implementar bases de datos o cachés simples usando archivos.
- Compartir estado entre procesos sin riesgo de corrupción.
- Construir scripts robustos de automatización que interactúan con APIs o fuentes de datos externas.

---

### Soporte de Plugins: Registrar Nuevos Formatos


atomicio te permite extender el soporte de formatos de archivo registrando tus propias funciones de carga y guardado para cualquier extensión usando la función `register_format`.

#### Objetivo
`register_format` te permite agregar soporte para formatos personalizados (por ejemplo, CSV, XML, INI, etc.) y así aprovechar todas las operaciones atómicas y seguras de atomicio con tus propios tipos de datos. Esto hace que atomicio sea adaptable a cualquier flujo de trabajo o proyecto, no solo a los formatos integrados (YAML, JSON, TOML, TXT).

#### ¿Cómo te ayuda?
- Integra tu propia lógica de serialización/deserialización para cualquier extensión.
- Usa la misma API de SafeFile para tus formatos personalizados.
- Puedes compartir nuevos formatos como plugins o simplemente registrarlos en tiempo de ejecución.

#### Ejemplo de uso
Supón que quieres agregar soporte para archivos CSV:
```python
from atomicio import register_format, SafeFile
import csv

def csv_loader(f):
    return list(csv.reader(f))

def csv_dumper(data, f):
    writer = csv.writer(f)
    writer.writerows(data)

register_format('.csv', csv_loader, csv_dumper)

sf = SafeFile('data.csv')
sf.write([[1,2,3],[4,5,6]])
print(sf.read())  # Salida: [[1, 2, 3], [4, 5, 6]]
```

#### Sistema de plugins
También puedes distribuir tu formato como plugin usando entry points:

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