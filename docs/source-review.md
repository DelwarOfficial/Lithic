# Source Code Review Guide

This document provides guidance for reviewing contributions to Lithic-CLI. As a graph-first agent tool, code reviews must ensure both correctness and safety.

## Code Review Checklist

### Security & Safety (Always Required)

- [ ] No `shell=True` in any subprocess call — must use list-form arguments
- [ ] No hardcoded API keys, tokens, or secrets in code
- [ ] File operations use `resolve_path_within_root()` and respect project boundary
- [ ] Destructive operations (delete, overwrite) protected by safety guards
- [ ] Subprocess commands have timeout set (120s default for large repos)
- [ ] Secret redaction in audit logs covers all provider key formats
- [ ] No path traversal vulnerabilities — verify `_safe_target()` usage
- [ ] No symlink following without `is_symlink()` check before operations

### Code Quality (Always Required)

- [ ] `ruff check` passes (run: `uv run ruff check src/lithic_cli/ tests/`)
- [ ] `ruff format` applied (run: `uv run ruff format src/lithic_cli/ tests/`)
- [ ] `mypy src/lithic_cli/` passes with no errors (run: `uv run mypy src/lithic_cli/`)
- [ ] Exception chaining present (B904 — use `raise NewError(...) from e`)
- [ ] Type hints complete on all new functions and parameters
- [ ] Docstrings include examples for public APIs

### Testing (Required for Features)

- [ ] New features include corresponding tests in `tests/`
- [ ] Tests pass locally: `uv run pytest tests/ -q`
- [ ] Edge cases covered (empty input, large input, special chars)
- [ ] Error paths tested (invalid graph, missing files, API failures)
- [ ] Cross-platform tested (Windows, macOS, Linux if possible)

### Documentation (Required for User-Facing Changes)

- [ ] README.md updated if command or behavior changed
- [ ] CONTRIBUTING.md updated if dev process changed
- [ ] docs/architecture.md updated if module structure or flow changed
- [ ] Commit message follows Conventional Commits format
- [ ] CHANGELOG.md entry added (if applicable)

### Performance (If Performance-Sensitive)

- [ ] No new blocking operations in hot paths
- [ ] LRU cache used for expensive computations
- [ ] Subprocess calls minimized (batch when possible)
- [ ] No unbounded loops or recursive calls without limits

## Review Process

### 1. Initial Check

Before deep review, verify:
- PR has clear title and description
- Code is against `main` branch (not another feature branch)
- CI checks pass (ruff, mypy, pytest, extras)

### 2. Security Pass

Review for the security checklist first. If any security concern is found, request changes before proceeding further.

### 3. Functionality Pass

Read the code change and verify:
- Logic is correct and handles edge cases
- Matches the described intent in PR description
- No performance regressions
- Integrates cleanly with existing code

### 4. Testing Pass

Verify tests are complete and meaningful. Run locally if unsure:
```bash
uv run pytest tests/ -q -k "your_test_name"
```

### 5. Documentation Pass

Check that user-facing changes are documented:
- For new CLI commands: add to README.md under "What It Does" table
- For new modules: add to docs/architecture.md module map
- For breaking changes: highlight in CHANGELOG.md

## Using `lithic review` During Review

Reviewers can use `lithic review` to get a concise diff summary:

```bash
# From feature branch, review your own changes
lithic review

# Use in supervised mode for careful audits
lithic review --mode careful
```

The output includes:
- Summary of changed files
- High-level changes per file
- Risk assessment (security, performance, compatibility)
- Recommendations for improvement

## Example Review Comment

```
Good catch on the graph validation logic. However, I noticed:

1. **Security**: The subprocess call to graphify doesn't have a timeout. 
   Can you add `timeout=120` to prevent hangs on large repos?
   
2. **Error handling**: What happens if graphify crashes? 
   The error message should include stderr for debugging.
   
3. **Tests**: Can you add a test for the "graphify not installed" case?

Everything else looks great! Ready to merge once these three are addressed.
```

## When to Request Changes vs Approve

### Request Changes if:
- Security issue found (shells, secrets, path traversal, symlinks)
- Tests don't cover new logic
- Type hints missing
- Code fails `ruff check` or `mypy`

### Approve (with suggestion) if:
- Minor documentation improvement (doesn't block functionality)
- Performance optimization for future (not a regression)
- Nice-to-have refactoring (doesn't change behavior)

### Approve (ready to merge) if:
- All checklist items passed
- Code is tested and documented
- No security or quality concerns
- CI passes

## References

- [Security model](./architecture.md#safety-model) — subprocess, filesystem, and MCP safety
- [Architecture](./architecture.md) — data flow and module boundaries
- [Contributing guide](../CONTRIBUTING.md) — how to set up dev environment
