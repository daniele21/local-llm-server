# Incrementa automaticamente la versione patch in pyproject.toml
python3 -c '
import re
from pathlib import Path
p = Path("pyproject.toml")
c = p.read_text(encoding="utf-8")
m = re.search(r"version\s*=\s*\"([^\"]+)\"", c)
if m:
    v = m.group(1)
    parts = v.split(".")
    parts[-1] = str(int(parts[-1]) + 1)
    nv = ".".join(parts)
    c = c.replace(f"version = \"{v}\"", f"version = \"{nv}\"")
    p.write_text(c, encoding="utf-8")
    print(f"[*] Version bumped: {v} -> {nv}")
'

uv pip install build
uv run python -m build