"""Vault file access with path-safety and write-scope rules. No MCP dependency here."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


class VaultError(Exception):
    pass


@dataclass(frozen=True)
class Vault:
    root: Path
    write_dirs: tuple[str, ...] = ("inbox", "retro")
    append_only_dirs: tuple[str, ...] = ()

    def __post_init__(self):
        object.__setattr__(self, "root", self.root.expanduser().resolve())
        if not self.root.is_dir():
            raise VaultError(f"vault not found: {self.root}")

    # --- path helpers -------------------------------------------------
    def _resolve(self, rel: str, *, must_be_md: bool = True) -> Path:
        rel = (rel or "").strip().lstrip("/")
        p = (self.root / rel).resolve()
        if p != self.root and self.root not in p.parents:
            raise VaultError("path escapes vault")
        parts = p.relative_to(self.root).parts
        if any(part.startswith(".") for part in parts):
            raise VaultError("hidden paths are not allowed")
        if must_be_md and p.suffix != ".md":
            raise VaultError("only .md files are allowed")
        return p

    def _rel(self, p: Path) -> str:
        return p.relative_to(self.root).as_posix()

    def _top(self, p: Path) -> str:
        parts = p.relative_to(self.root).parts
        return parts[0] if len(parts) > 1 else ""

    def _check_creatable(self, p: Path) -> None:
        if self._top(p) not in self.write_dirs:
            raise VaultError(f"new notes allowed only under: {', '.join(self.write_dirs)}")

    def _check_appendable(self, p: Path) -> None:
        if self._top(p) not in self.write_dirs + self.append_only_dirs:
            allowed = self.write_dirs + self.append_only_dirs
            raise VaultError(f"append allowed only under: {', '.join(allowed)}")

    def _iter_md(self, base: Path):
        for p in sorted(base.rglob("*.md")):
            if not any(part.startswith(".") for part in p.relative_to(self.root).parts):
                yield p

    # --- operations ---------------------------------------------------
    def list(self, directory: str = "") -> list[str]:
        base = self._resolve(directory, must_be_md=False)
        if not base.is_dir():
            raise VaultError(f"not a directory: {directory}")
        return [self._rel(p) for p in self._iter_md(base)]

    def read(self, path: str) -> str:
        p = self._resolve(path)
        if not p.is_file():
            raise VaultError(f"not found: {path}")
        return p.read_text(encoding="utf-8")

    def search(self, query: str, directory: str = "", limit: int = 20) -> list[dict]:
        q = query.strip().lower()
        if not q:
            raise VaultError("empty query")
        base = self._resolve(directory, must_be_md=False)
        results = []
        for p in self._iter_md(base):
            rel = self._rel(p)
            lines = p.read_text(encoding="utf-8", errors="ignore").splitlines()
            hits = [(i + 1, ln.strip()) for i, ln in enumerate(lines) if q in ln.lower()]
            if q in rel.lower() or hits:
                results.append({
                    "path": rel,
                    "matches": [{"line": n, "text": t[:200]} for n, t in hits[:5]],
                    "match_count": len(hits),
                })
            if len(results) >= limit:
                break
        return results

    def write(self, path: str, content: str) -> str:
        """Create a new note. Never overwrites."""
        p = self._resolve(path)
        self._check_creatable(p)
        if p.exists():
            raise VaultError(f"already exists (use append_note): {path}")
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content if content.endswith("\n") else content + "\n", encoding="utf-8")
        return self._rel(p)

    def append(self, path: str, content: str) -> str:
        p = self._resolve(path)
        self._check_appendable(p)
        if not p.is_file():
            raise VaultError(f"not found: {path}")
        existing = p.read_text(encoding="utf-8")
        sep = "" if existing.endswith("\n") else "\n"
        p.write_text(existing + sep + "\n" + content.rstrip("\n") + "\n", encoding="utf-8")
        return self._rel(p)
