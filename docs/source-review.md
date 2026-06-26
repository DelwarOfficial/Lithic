# Source Review

Inspected local root: `D:\websie\merge-skill`.

Confirmed repositories:

- `D:\websie\merge-skill\graphify-8`
- `D:\websie\merge-skill\headroom-main`
- `D:\websie\merge-skill\caveman-main`

## Graphify

- Package: Python project `graphifyy`, version `0.8.49`.
- Manifest: `pyproject.toml`.
- License: MIT, copied to `LICENSES/MIT-Graphify.txt`.
- CLI entry points: `graphify = graphify.__main__:main`, `graphify-mcp = graphify.serve:_main`.
- Important modules: `graphify/__main__.py`, `graphify/extract.py`, `graphify/build.py`, `graphify/analyze.py`, `graphify/serve.py`, `graphify/watch.py`, `graphify/export.py`, `graphify/mcp_ingest.py`, `graphify/extractors/`.
- Output convention: `graphify-out/graph.json`, overrideable through `GRAPHIFY_OUT`.
- Graph commands found in CLI help/source: `query`, `explain`, `path`, `update`, `extract`, `watch`, `merge-graphs`, `global`, `tree-html`, `callflow-html`.
- MCP: `graphify/serve.py` exposes graph query tools over stdio and HTTP when the `mcp` extra is installed.
- Tests: 189 files under `tests`.
- Key dependencies: `networkx`, `numpy`, `rapidfuzz`, many `tree-sitter-*` language packages, `tree-sitter>=0.23.0,<0.26`.

## Headroom

- Package: Python/Rust project `headroom-ai`, version `0.27.0`.
- Manifest: `pyproject.toml` with `maturin` build backend.
- License: Apache-2.0, copied to `LICENSES/Apache-2.0-Headroom.txt`.
- CLI entry point: `headroom = headroom.cli:main`.
- Important modules: `headroom/compress.py`, `headroom/transforms/content_router.py`, `headroom/transforms/smart_crusher.py`, `headroom/compression/universal.py`, `headroom/ccr/mcp_server.py`, `headroom/proxy/server.py`, `headroom/cache/compression_store.py`, `headroom/memory/`.
- MCP: `headroom/ccr/mcp_server.py` and `headroom/integrations/mcp/server.py`.
- Tests: 674 files under `tests`.
- Key dependencies: `tiktoken`, `pydantic`, `litellm`, `click`, `rich`, `opentelemetry-api`, `ast-grep-cli`.
- Relevant extras: `proxy`, `code`, `mcp`, `relevance`.
- Dependency/build issue on this machine: `uv add "headroom-ai[proxy,code,mcp,relevance]"` resolved but failed while building the Rust extension because MSVC linker setup was unavailable. The package is therefore declared as optional; `HeadroomAdapter` falls back deterministically when `headroom` cannot import.

## Caveman

- Package: Node installer project `caveman-installer`, version `0.1.0`.
- Manifest: `package.json`.
- License: MIT, copied to `LICENSES/MIT-Caveman.txt`.
- Binary entry point: `caveman = ./bin/install.js`.
- Important directories: `skills/`, `commands/`, `src/hooks/`, `src/mcp-servers/`, `src/plugins/`, `src/rules/`, `src/tools/`.
- Skills: `caveman`, `caveman-commit`, `caveman-review`, `caveman-compress`, `caveman-stats`, `caveman-help`, `cavecrew`.
- Tests: 25 files under `tests`.
- Runtime style: installer and hooks are Node-based. Lithic adapts the policy guidance in Python rather than importing Caveman runtime files.

## Dependency Alignment

- Python target: 3.12.
- Graphify installs with `tree-sitter==0.25.2`, satisfying the preferred `>=0.25.2,<0.26` range.
- Headroom's `code` extra also prefers `tree-sitter>=0.25.2,<0.26`, but the Headroom package itself could not build in this environment due to native Rust/MSVC linking.
- No original repository files were modified.
