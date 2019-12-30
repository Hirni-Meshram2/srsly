from typing import Union, Iterable, Sequence, Any, Optional
import sys
import json as _builtin_json
import gzip

from . import ujson
from .types import FilePath, StandardIO, JSONInput, JSONOutput
from .util import force_path, force_string


def json_dumps(
    data: JSONInput, indent: Optional[int] = 0, sort_keys: bool = False
) -> str:
    """Serialize an object to a JSON string.

    data: The JSON-serializable data.
    indent (int): Number of spaces used to indent JSON.
    sort_keys (bool): Sort dictionary keys. Falls back to json module for now.
    RETURNS (str): The serialized string.
    """
    if sort_keys:
        indent = None if indent == 0 else indent
        result = _builtin_json.dumps(
            data, indent=indent, separators=(",", ":"), sort_keys=sort_keys
        )
    else:
        result = ujson.dumps(data, indent=indent, escape_forward_slashes=False)
    return result


def json_loads(data: Union[str, bytes]) -> JSONOutput:
    """Deserialize unicode or bytes to a Python object.

    data (str / bytes): The data to deserialize.
    RETURNS: The deserialized Python object.
    """
    return ujson.loads(data)


def read_json(location: Union[FilePath, StandardIO]) -> JSONOutput:
    """Load JSON from file or standard input.

    location (unicode / Path): The file path. "-" for reading from stdin.
    RETURNS (dict / list): The loaded JSON content.
    """
    if location == "-":  # reading from sys.stdin
        data = sys.stdin.read()
        return ujson.loads(data)
    file_path = force_path(location)
    with file_path.open("r", encoding="utf8") as f:
        return ujson.load(f)


def read_gzip_json(location: FilePath) -> JSONOutput:
    """Load JSON from a gzipped file.

        location (unicode / Path): The file path.
        RETURNS (dict / list): The loaded JSON content.
    """
    file_path = force_string(location)
    with gzip.open(file_path, "r") as f:
        return ujson.load(f)


def write_json(
    location: Union[FilePath, StandardIO], data: JSONInput, indent: int = 2
) -> None:
    """Create a .json file and dump contents or write to standard
    output.

    location (unicode / Path): The file path. "-" for writing to stdout.
    data: The JSON-serializable data to output.
    indent (int): Number of spaces used to indent JSON.
    """
    json_data = json_dumps(data, indent=indent)
    if location == "-":  # writing to stdout
        print(json_data)
    else:
        file_path = force_path(location, require_exists=False)
        with file_path.open("w", encoding="utf8") as f:
            f.write(json_data)


def write_gzip_json(location: FilePath, data: JSONInput, indent: int = 2) -> None:
    """Create a .json.gz file and dump contents.

    location (unicode / Path): The file path.
    data: The JSON-serializable data to output.
    indent (int): Number of spaces used to indent JSON.
    """
    json_data = json_dumps(data, indent=indent)
    file_path = force_string(location)
    with gzip.open(file_path, "w") as f:
        f.write(json_data.encode("utf-8"))


def read_jsonl(location: FilePath, skip: bool = False) -> Iterable[JSONOutput]:
    """Read a .jsonl file or standard input and yield contents line by line.
    Blank lines will always be skipped.

    location (unicode / Path): The file path. "-" for reading from stdin.
    skip (bool): Skip broken lines and don't raise ValueError.
    YIELDS: The loaded JSON contents of each line.
    """
    if location == "-":  # reading from sys.stdin
        for line in _yield_json_lines(sys.stdin, skip=skip):
            yield line
    else:
        file_path = force_path(location)
        with file_path.open("r", encoding="utf8") as f:
            for line in _yield_json_lines(f, skip=skip):
                yield line


def write_jsonl(
    location: FilePath,
    lines: Sequence[JSONInput],
    append: bool = False,
    append_new_line: bool = True,
) -> None:
    """Create a .jsonl file and dump contents or write to standard output.

    location (unicode / Path): The file path. "-" for writing to stdout.
    lines (list): The JSON-serializable contents of each line.
    append (bool): Whether or not to append to the location.
    append_new_line (bool): Whether or not to write a new line before appending
        to the file.
    """
    if location == "-":  # writing to stdout
        for line in lines:
            print(json_dumps(line))
    else:
        mode = "a" if append else "w"
        file_path = force_path(location, require_exists=False)
        with file_path.open(mode, encoding="utf-8") as f:
            if append and append_new_line:
                f.write("\n")
            for line in lines:
                f.write(json_dumps(line) + "\n")


def is_json_serializable(obj: Any) -> bool:
    """Check if a Python object is JSON-serializable.

    obj: The object to check.
    RETURNS (bool): Whether the object is JSON-serializable.
    """
    if hasattr(obj, "__call__"):
        # Check this separately here to prevent infinite recursions
        return False
    try:
        ujson.dumps(obj)
        return True
    except (TypeError, OverflowError):
        return False


def _yield_json_lines(
    stream: Iterable[str], skip: bool = False
) -> Iterable[JSONOutput]:
    line_no = 1
    for line in stream:
        line = line.strip()
        if line == "":
            continue
        try:
            yield ujson.loads(line)
        except ValueError:
            if skip:
                continue
            raise ValueError(f"Invalid JSON on line {line_no}: {line}")
        line_no += 1
