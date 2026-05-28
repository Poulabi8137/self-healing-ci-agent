import json
from pathlib import Path
from typing import Any, Dict, List, Union


def ensure_dir(path: Union[str, Path]) -> Path:
    path = Path(path)
    path.mkdir(parents=True, exist_ok=True)
    return path


def read_file(path: Union[str, Path]) -> str:
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def write_file(path: Union[str, Path], content: str) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)


def read_json(path: Union[str, Path]) -> Union[Dict[str, Any], List[Any]]:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def write_json(path: Union[str, Path], data: Any) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def list_files(directory: Union[str, Path], pattern: str = "*") -> List[Path]:
    return list(Path(directory).glob(pattern))


def file_exists(path: Union[str, Path]) -> bool:
    return Path(path).exists()
