import sys
import json
import argparse
from pathlib import Path

def main():
    # atomicio CLI
    # -------------
    # Herramienta de línea de comandos para operaciones atómicas y seguras sobre archivos con soporte de plugins de formato.
    #
    # Comandos:
    #     read <file> [--as-bytes]     Lee y muestra el archivo (auto-detecta formato)
    #     write <file> <data> [--as-bytes]  Escribe datos en el archivo (JSON para estructurados)
    #     formats                      Lista los formatos soportados
    #
    # Ejemplos:
    #     python -m atomicio read config.yaml
    #     python -m atomicio write config.json '{"foo": 1}'
    from .core import SafeFile


# atomicio CLI
# -------------
# Herramienta de línea de comandos para operaciones atómicas y seguras sobre archivos con soporte de plugins de formato.
#
# Comandos:
#     read <file> [--as-bytes]     Lee y muestra el archivo (auto-detecta formato)
#     write <file> <data> [--as-bytes]  Escribe datos en el archivo (JSON para estructurados)
#     formats                      Lista los formatos soportados
#
# Ejemplos:
#     python -m atomicio read config.yaml
#     python -m atomicio write config.json '{"foo": 1}'
def main():
    """
    Entry point for the atomicio CLI. (English)
    Punto de entrada para el CLI de atomicio. (Español)
    Uses argparse to expose reading, writing, and listing supported formats. (English)
    Usa argparse para exponer lectura, escritura y listado de formatos soportados. (Español)
    """
    examples = [
        "python -m atomicio read config.yaml",
        "python -m atomicio write config.json '{\"foo\": 1}'",
        "python -m atomicio formats"
    ]
    parser = argparse.ArgumentParser(
        description="""
        atomicio: Atomic, locked file operations with plugin-based format support.\n
        atomicio: Operaciones atómicas y seguras sobre archivos con soporte de plugins de formato.\n
        Examples / Ejemplos:\n  """ + "\n  ".join(examples),
        epilog="For more info, see the documentation. / Para más información, consulte la documentación."
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    # Read command
    read_parser = subparsers.add_parser(
        "read",
        help="Read and print a file (auto-detect format) / Lee y muestra un archivo (auto-detecta formato)"
    )
    read_parser.add_argument("file", type=str, help="Path to the file to read / Ruta del archivo a leer")
    read_parser.add_argument("--as-bytes", action="store_true", help="Read as raw bytes (output to stdout) / Leer como bytes crudos (salida a stdout)")

    # Write command
    write_parser = subparsers.add_parser(
        "write",
        help="Write data to a file (auto-detect format) / Escribe datos en un archivo (auto-detecta formato)"
    )
    write_parser.add_argument("file", type=str, help="Path to the file to write / Ruta del archivo a escribir")
    write_parser.add_argument("data", type=str, help="Data to write (JSON string for structured formats) / Datos a escribir (cadena JSON para formatos estructurados)")
    write_parser.add_argument("--as-bytes", action="store_true", help="Write as raw bytes (input as utf-8 string) / Escribir como bytes crudos (entrada como cadena utf-8)")

    # List formats
    formats_parser = subparsers.add_parser(
        "formats",
        help="List supported formats / Lista los formatos soportados"
    )

    args = parser.parse_args()

    if args.command == "read":
        if not Path(args.file).exists():
            print(f"Error: File not found: {args.file}\nError: Archivo no encontrado: {args.file}", file=sys.stderr)
            sys.exit(1)
        sf = SafeFile(args.file)
        try:
            if args.as_bytes:
                data = sf.read_bytes()
                sys.stdout.buffer.write(data or b"")
            else:
                data = sf.read()
                if isinstance(data, (dict, list)):
                    print(json.dumps(data, indent=2, ensure_ascii=False))
                else:
                    print(data if data is not None else "")
        except Exception as e:
            print(f"Read error: {e}\nError de lectura: {e}", file=sys.stderr)
            sys.exit(2)
    elif args.command == "write":
        # Validate file path
        parent = Path(args.file).parent
        if not parent.exists():
            print(f"Error: Directory does not exist: {parent}\nError: El directorio no existe: {parent}", file=sys.stderr)
            sys.exit(1)
        sf = SafeFile(args.file)
        try:
            if args.as_bytes:
                # Validate input is string
                if not isinstance(args.data, str):
                    print("Input must be a string for --as-bytes. / La entrada debe ser una cadena para --as-bytes.", file=sys.stderr)
                    sys.exit(1)
                sf.write_bytes(args.data.encode("utf-8"))
            else:
                # Try to parse as JSON, fallback to string
                try:
                    val = json.loads(args.data)
                except Exception:
                    val = args.data
                sf.write(val)
        except Exception as e:
            print(f"Write error: {e}\nError de escritura: {e}", file=sys.stderr)
            sys.exit(2)
    elif args.command == "formats":
        from .core import SafeFile
        print("Supported formats / Formatos soportados:", ", ".join(SafeFile.supported_formats()))
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
