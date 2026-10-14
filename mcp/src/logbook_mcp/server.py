"""logbook MCP server. Env:
  VAULT_PATH        vault root (required)
  WRITE_DIRS        top-level dirs where AI may create/append notes (default: inbox,retro,meetings,troubleshooting,career,study)
  APPEND_ONLY_DIRS  top-level dirs where AI may only append (default: journal)
  MCP_TRANSPORT     stdio | streamable-http (default: stdio)
  MCP_HOST/MCP_PORT for streamable-http (default: 127.0.0.1:8000)
"""
from __future__ import annotations

import os
from pathlib import Path

from mcp.server.mcpserver import MCPServer
from mcp.server.mcpserver.exceptions import ToolError
from mcp.types import ToolAnnotations

from .vault import Vault, VaultError


def _build() -> MCPServer:
    def _dirs(env: str, default: str) -> tuple[str, ...]:
        return tuple(d.strip() for d in os.environ.get(env, default).split(",") if d.strip())

    vault = Vault(
        Path(os.environ["VAULT_PATH"]),
        _dirs("WRITE_DIRS", "inbox,retro,meetings,troubleshooting,career,study"),
        _dirs("APPEND_ONLY_DIRS", "journal"),
    )
    readme = vault.root / "README.md"
    rules = readme.read_text(encoding="utf-8") if readme.is_file() else ""
    instructions = (
        "Personal work-log vault (markdown). Read the rules below before writing.\n"
        f"Create/append dirs: {', '.join(vault.write_dirs)}. Append-only dirs: {', '.join(vault.append_only_dirs) or '-'}. "
        "Notes are never overwritten; use append_note.\n\n"
        + rules
    )

    mcp = MCPServer("logbook", instructions=instructions)
    ro = ToolAnnotations(readOnlyHint=True)
    rw = ToolAnnotations(readOnlyHint=False, destructiveHint=False)

    def _guard(fn, *args):
        try:
            return fn(*args)
        except VaultError as e:
            raise ToolError(str(e)) from None

    @mcp.tool(annotations=ro)
    def list_notes(directory: str = "") -> list[str]:
        """List markdown notes (relative paths) under a directory, e.g. 'retro/daily'. Empty = whole vault."""
        return _guard(vault.list, directory)

    @mcp.tool(annotations=ro)
    def read_note(path: str) -> str:
        """Read a note by relative path, e.g. 'retro/daily/2026-10-14.md'."""
        return _guard(vault.read, path)

    @mcp.tool(annotations=ro)
    def search_notes(query: str, directory: str = "", limit: int = 20) -> list[dict]:
        """Case-insensitive substring search over note paths and contents. Returns matching lines per note."""
        return _guard(vault.search, query, directory, limit)

    @mcp.tool(annotations=rw)
    def write_note(path: str, content: str) -> str:
        """Create a NEW note (fails if it exists). Only allowed under the writable dirs."""
        return _guard(vault.write, path, content)

    @mcp.tool(annotations=rw)
    def append_note(path: str, content: str) -> str:
        """Append content to the end of an existing note under the writable dirs."""
        return _guard(vault.append, path, content)

    @mcp.tool(annotations=ro)
    def vault_guide() -> str:
        """Return the vault README (folder layout, naming and frontmatter rules). Call before writing."""
        return rules or "No README.md in vault."

    return mcp


def main() -> None:
    mcp = _build()
    transport = os.environ.get("MCP_TRANSPORT", "stdio")
    if transport == "streamable-http":
        mcp.run(
            transport,
            host=os.environ.get("MCP_HOST", "127.0.0.1"),
            port=int(os.environ.get("MCP_PORT", "8000")),
        )
    else:
        mcp.run(transport)


if __name__ == "__main__":
    main()
