from __future__ import annotations

import json
from pathlib import Path
from threading import Lock
from typing import Dict, List

from .models import Classroom, Room


class DataStore:
    """Simple JSON-backed storage for rooms and classrooms."""

    def __init__(self, file_path: Path):
        self.file_path = file_path
        self._lock = Lock()
        self._data = {"rooms": [], "classes": []}
        self.file_path.parent.mkdir(parents=True, exist_ok=True)
        self._load()

    def _load(self) -> None:
        if self.file_path.exists():
            raw = json.loads(self.file_path.read_text())
            self._data["rooms"] = raw.get("rooms", [])
            self._data["classes"] = raw.get("classes", [])
        else:
            self._persist()

    def _persist(self) -> None:
        with self.file_path.open("w", encoding="utf-8") as fp:
            json.dump(self._data, fp, ensure_ascii=False, indent=2)

    # Helper conversions -------------------------------------------------
    def _rooms(self) -> List[Room]:
        return [Room.parse_obj(room) for room in self._data["rooms"]]

    def _classes(self) -> List[Classroom]:
        return [Classroom.parse_obj(cls) for cls in self._data["classes"]]

    def load(self) -> Dict[str, List]:
        with self._lock:
            return {"rooms": self._rooms(), "classes": self._classes()}

    def save(self, rooms: List[Room], classes: List[Classroom]) -> None:
        with self._lock:
            self._data["rooms"] = [room.dict() for room in rooms]
            self._data["classes"] = [cls.dict() for cls in classes]
            self._persist()


_store: DataStore | None = None


def get_store() -> DataStore:
    global _store
    if _store is None:
        data_path = Path("data/store.json")
        _store = DataStore(data_path)
    return _store

