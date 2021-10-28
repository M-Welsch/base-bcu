from dataclasses import dataclass
from pathlib import Path


@dataclass
class SyncStatus:
    path: Path = Path()
    progress: float = 0.0
    finished: bool = False
    error: bool = False
