"""Detect a changed lockfile, frontend source or build config across pulls."""

import hashlib
from pathlib import Path

root = Path(__file__).resolve().parents[1] / "frontend"
files = [
    *root.glob("*.json"),
    *root.glob("*.ts"),
    root / "index.html",
    *(root / "src").rglob("*"),
    *(root / "public").rglob("*"),
]
digest = hashlib.sha256()
for path in sorted(p for p in files if p.is_file()):
    digest.update(str(path.relative_to(root)).encode())
    digest.update(path.read_bytes())
print(digest.hexdigest())
