# MCP Tools Reference

Lithic exposes its core capabilities through the Model Context Protocol (MCP) server. This document describes each tool, its input schema, and example outputs.

## Server Setup

Start the MCP server:

```bash
uv run lithic mcp serve
```

## Tools

### `lithic_graph_query`

Query the project architecture graph.

**Input:**
```json
{
  "question": "string (max 2000 chars)"
}
```

**Output:** Text response with architecture context.

### `lithic_graph_explain`

Explain a symbol, module, or concept from the graph.

**Input:**
```json
{
  "concept": "string (max 2000 chars)"
}
```

**Output:** Text explanation of the concept.

### `lithic_graph_path`

Find a relationship path between two graph concepts.

**Input:**
```json
{
  "source": "string (max 2000 chars)",
  "target": "string (max 2000 chars)"
}
```

**Output:** Graph path description.

### `lithic_compress`

Compress text safely to reduce token usage.

**Input:**
```json
{
  "text": "string (max 500000 chars)"
}
```

**Output:** Compressed text.

### `lithic_review`

Review the current working-tree diff.

**Input:** None

**Output:** Concise review findings.

### `lithic_commit`

Generate a Conventional Commit message from staged/working changes.

**Input:** None

**Output:** Commit message.

### `lithic_stats`

Return runtime statistics.

**Input:** None

**Output:** JSON with graph stats, compression stats, and event history.
