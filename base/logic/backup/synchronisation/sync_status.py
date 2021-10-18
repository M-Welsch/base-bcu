from pathlib import Path


class SyncStatus:
    def __init__(self, path: Path = Path(), progress: float = 0.0) -> None:
        self.path: Path = path
        self.progress: float = progress
        self.finished: bool = False
        self.error: bool = False

    def __str__(self) -> str:
        return f"Status(path={self.path}, progress={self.progress}, finished={self.finished})"
