import json
from pathlib import Path
from typing import Any


def save_json(_file: Path, _data: Any) -> None:
    with open(_file, 'w', encoding='utf-8') as f:
        json.dump(_data, f, ensure_ascii=False, indent=4)


def load_json(_file: Path) -> Any:
    with open(_file, 'r', encoding='utf-8') as f:
        return json.load(f)
