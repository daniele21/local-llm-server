from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
import shutil
import socket
import tempfile
import uuid

PREFIX = "local-llm-e2e-"
OWNER_FILE = ".owner.json"


@dataclass(frozen=True)
class OwnedRunState:
    run_id: str
    root: Path

    @property
    def evaluation_root(self) -> Path:
        return self.root / "evaluation"

    @classmethod
    def create(cls) -> "OwnedRunState":
        run_id = uuid.uuid4().hex
        root = Path(tempfile.mkdtemp(prefix=f"{PREFIX}{run_id[:8]}-"))
        (root / OWNER_FILE).write_text(json.dumps({"run_id": run_id}) + "\n", encoding="utf-8")
        evaluation_root = root / "evaluation"
        evaluation_root.mkdir()
        return cls(run_id=run_id, root=root)

    def owns_root(self) -> bool:
        temp_root = Path(tempfile.gettempdir()).resolve()
        try:
            resolved = self.root.resolve()
            resolved.relative_to(temp_root)
        except (OSError, ValueError):
            return False
        if not resolved.name.startswith(PREFIX):
            return False
        marker = resolved / OWNER_FILE
        if not marker.is_file():
            return False
        try:
            payload = json.loads(marker.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return False
        return payload.get("run_id") == self.run_id

    def cleanup(self) -> None:
        if not self.root.exists():
            return
        if not self.owns_root():
            raise RuntimeError(f"refusing to delete unowned E2E root: {self.root}")
        shutil.rmtree(self.root)


def listener_open(host: str = "127.0.0.1", port: int = 8765, timeout: float = 0.2) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.settimeout(timeout)
        return sock.connect_ex((host, port)) == 0


def stale_owned_roots() -> list[Path]:
    temp_root = Path(tempfile.gettempdir())
    result: list[Path] = []
    for path in temp_root.glob(f"{PREFIX}*"):
        if path.is_dir() and (path / OWNER_FILE).is_file():
            result.append(path)
    return sorted(result)
