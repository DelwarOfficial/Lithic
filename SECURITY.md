# Security Policy

## Supported Versions

| Version | Supported |
|---------|-----------|
| 0.1.x   | Yes       |
| < 0.1   | No        |

## Reporting a Vulnerability

**Do not open a public GitHub issue for security vulnerabilities.**

Report security issues via GitHub's private vulnerability reporting, or email the maintainer directly at delwarnetwork@gmail.com. Please include:

- Description of the vulnerability
- Steps to reproduce
- Potential impact
- Suggested fix (if any)

We will acknowledge receipt within 48 hours and aim to release a fix within 7 days for critical issues.

## Security Model

Lithic is a **local development CLI tool** that combines graph indexing, compression, and response policies. It runs as a CLI and optionally as a local MCP stdio server.

### Actual Defenses

| Vector | Mitigation | File |
|--------|------------|------|
| **Path traversal** | `resolve_path_within_root()` resolves paths and rejects those outside project root. `_safe_target()` duplicates this check. | `src/lithic/tools/fs.py:8`, `src/lithic/graph/graphify_adapter.py:90` |
| **Destructive commands** | `_is_destructive()` checks command + args against a blocklist (rm -rf, del /s, git reset --hard, drop table, etc.). Raises `ValueError` before execution. | `src/lithic/tools/shell.py:29` |
| **Shell injection** | All subprocess calls use list form (no `shell=True`). `_sanitize_input()` blocks shell metacharacters and flag injection (`--` prefix). | `src/lithic/graph/graphify_adapter.py:104` |
| **Symlink traversal** | `_rmtree_safe()` refuses to follow symlinks during directory removal. | `src/lithic/graph/graphify_adapter.py:135` |
| **Input size limits** | Graph queries capped at 2000 chars. MCP inputs capped at 100K chars. Compression inputs capped at 500K chars. File compression capped at 100MB. | `src/lithic/graph/graphify_adapter.py:113`, `src/lithic/mcp/server.py:17-21` |
| **Rate limiting** | MCP server enforces 60 calls per 60s window (configurable via `LITHIC_MCP_*` env vars). | `src/lithic/mcp/server.py:25` |
| **Audit logging** | All subprocess calls, tool calls, rejected inputs, auth failures, and rate limit hits are logged to JSON. | `src/lithic/tools/audit.py` |
| **Response mode validation** | Unknown response modes are rejected with a clear error. | `src/lithic/config.py:60` |
| **Branch name validation** | Git branch names validated against allowed charset before `git checkout -b`. | `src/lithic/updater/branch_manager.py:17` |

### What Lithic Does NOT Do

- Does not run a network listener (MCP server communicates over stdio only)
- Does not use `shell=True` in any subprocess call
- Does not store credentials or API keys — all secrets read from environment variables
- Does not execute arbitrary code from source files
- Does not follow symlinks during recursive directory operations

## Best Practices for Users

1. **Keep Lithic updated** — Use the latest version for security fixes
2. **Use virtual environments** — Isolate dependencies to reduce supply chain risks
3. **Review graph output** — Generated HTML/JSON may reflect project internals; review before sharing
4. **Do not commit `.env`** — API keys in `.env` are excluded by `.gitignore`; verify before committing
5. **Pin dependencies** — Use `uv.lock` (committed) for reproducible, auditable builds

## Security Contact

For security concerns, email delwarnetwork@gmail.com or use GitHub's private vulnerability reporting.
