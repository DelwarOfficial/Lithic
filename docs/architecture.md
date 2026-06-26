# Architecture

Lithic has three independent layers:

- Graph layer: `GraphifyAdapter` shells out to the Graphify CLI and stores output under `graphify-out/graph.json`.
- Compression layer: `HeadroomAdapter` uses Headroom when installed and otherwise uses deterministic compression that preserves errors, paths, commands, stack traces, and code blocks.
- Response policy layer: `ResponsePolicy` shapes output into normal, concise, caveman-lite/full/ultra, review, commit, and safety-clear modes.

`Orchestrator` is graph-first. Broad codebase questions call Graphify before raw file access. Edit workflows currently orient through Graphify and report likely context; future versions can add patch application.

The CLI is in `lithic.cli`; MCP tools are in `lithic.mcp.server`; provider wrappers are optional and read API keys from environment variables or a local `.env`.

Implemented providers: OpenAI, Anthropic, OpenRouter, Ollama.

Not implemented in this repo yet: reversible decompress API, IDE plugin packaging, autonomous edit execution.
