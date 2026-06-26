# Lithic

Lithic is a graph-first developer agent toolkit for understanding codebases, compressing context, and producing concise engineering output.

[GitHub Repository](https://github.com/DelwarOfficial/Lithic)

Lithic brings together three complementary ideas in a clean adapter-based architecture:

- **Graphify-inspired graph intelligence** for codebase indexing, architecture mapping, and graph-guided exploration
- **Headroom-inspired compression** for large tool output, logs, JSON, and file reads
- **Caveman-inspired response policy** for concise review, commit, and coding-agent communication

Rather than merging upstream projects into one tangled codebase, Lithic keeps each capability behind a dedicated layer. That makes the system easier to understand, safer to evolve, and better suited for real repository work.

## Why Lithic

Coding-agent workflows usually break down in three places:

- they lose architectural context in large repositories
- they spend too many tokens on noisy tool output
- they answer too verbosely when short, actionable feedback is better

Lithic is designed to improve all three:

- **Graph-first orientation** before broad file scanning
- **Deterministic compression** before model-facing calls
- **Mode-aware response shaping** for review, commit, and concise workflows

## Features

- Build and refresh a project knowledge graph
- Ask architecture and codebase questions through Graphify-backed queries
- Explain symbols, files, modules, and relationships
- Find graph paths between concepts
- Compress large file, shell, log, and diff output safely
- Generate concise review output
- Generate Conventional Commit-style commit messages
- Expose core capabilities over MCP
- Support optional provider integrations for OpenAI, Anthropic, OpenRouter, and Ollama

## Architecture

Lithic is organized into three primary runtime layers:

- **Graph layer**: `lithic.graph.graphify_adapter`
- **Compression layer**: `lithic.compression.headroom_adapter`
- **Policy layer**: `lithic.policy.response_policy`

These layers are coordinated by `lithic.orchestrator`, which is intentionally **graph-first**. Broad codebase questions are routed through graph context before narrower reads or downstream actions.

More architecture details are available in [`docs/architecture.md`](docs/architecture.md).

## Installation

### Requirements

- Python 3.12
- [uv](https://github.com/astral-sh/uv)
- A shell environment such as PowerShell, Terminal, or Bash

### Install

```powershell
git clone https://github.com/DelwarOfficial/Lithic.git
cd Lithic
uv sync
```

### Optional Headroom extra

```powershell
uv sync --extra headroom
```

On some Windows environments, `headroom-ai` may require Rust/MSVC build tooling when a compatible wheel is unavailable. Lithic still works without that extra by falling back to its built-in deterministic compressor.

## Quick Start

Index the repository:

```powershell
uv run lithic index .
```

Ask an architecture question:

```powershell
uv run lithic ask "explain this project architecture"
```

Explain a symbol:

```powershell
uv run lithic explain "GraphifyAdapter"
```

Find a relationship path:

```powershell
uv run lithic path "GraphifyAdapter" "HeadroomAdapter"
```

Compress a large file:

```powershell
uv run lithic compress-file README.md
```

Review current changes:

```powershell
uv run lithic review
```

Generate a commit message:

```powershell
uv run lithic commit
```

Start the MCP server:

```powershell
uv run lithic mcp
```

## CLI Commands

| Command | Purpose |
| --- | --- |
| `lithic index .` | Build or refresh the project graph |
| `lithic ask "..."` | Ask a graph-guided codebase question |
| `lithic explain "..."` | Explain a symbol, file, module, or concept |
| `lithic path "A" "B"` | Find a graph relationship path |
| `lithic edit "..."` | Orient an edit task without mutating files |
| `lithic review` | Produce concise review findings from the current diff |
| `lithic commit` | Generate a Conventional Commit-style subject |
| `lithic compress-file <file>` | Compress large text output safely |
| `lithic stats` | Show graph and compression runtime stats |
| `lithic mcp` | Serve Lithic MCP tools over stdio |

## Configuration

Lithic reads configuration from environment variables and supports a local `.env` file.

Primary variables:

- `LITHIC_PROVIDER`
- `LITHIC_MODEL`
- `LITHIC_GRAPH_DIR`
- `LITHIC_RESPONSE_MODE`
- `LITHIC_VERBOSE`
- `OPENAI_API_KEY`
- `ANTHROPIC_API_KEY`
- `OPENROUTER_API_KEY`

Legacy `UDA_*` variables are still accepted as a compatibility fallback.

More setup details are available in [`docs/setup.md`](docs/setup.md).

## Safety

Lithic is designed to stay concise without becoming careless.

- Destructive shell patterns are refused unless explicitly approved
- Risky actions are shifted into clearer language instead of aggressive compression
- Code blocks, commands, file paths, and error strings are preserved exactly during response shaping and compression
- Original upstream repositories are not modified by Lithic itself

## Current Scope

Lithic is currently strongest as a **codebase understanding, compression, review, and commit-assist tool**.

Implemented today:

- graph-backed indexing and querying
- deterministic or Headroom-backed compression
- concise policy modes
- CLI and MCP surfaces
- optional provider wrappers

Not yet implemented:

- autonomous file-edit execution
- reversible decompression APIs
- full IDE/plugin packaging workflows

## Documentation

- [`docs/architecture.md`](docs/architecture.md)
- [`docs/setup.md`](docs/setup.md)
- [`docs/source-review.md`](docs/source-review.md)
- [`docs/merge-notes.md`](docs/merge-notes.md)
- [`docs/license-attribution.md`](docs/license-attribution.md)

## License and Attribution

Lithic includes adapter work and behavioral inspiration from:

- Graphify - MIT
- Headroom - Apache-2.0
- Caveman - MIT

See [`THIRD_PARTY_NOTICES.md`](THIRD_PARTY_NOTICES.md) and the [`LICENSES`](LICENSES) directory for details.
