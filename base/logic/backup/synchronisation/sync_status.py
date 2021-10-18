from pathlib import Path
from dataclasses import dataclass


@dataclass
class SyncStatus:
    path: Path = Path()
    progress: float = 0.0
    finished: bool = False
    error: bool = False
