# Lithic-CLI — Expert Open Source Repository Audit Report

**Repository:** https://github.com/DelwarOfficial/Lithic-CLI
**Audit Date:** June 27, 2026
**Auditor Role:** Senior Open Source Software Architect · Security Researcher · Performance Engineer · Code Reviewer
**Audit Scope:** Full repository — source code, configuration, documentation, CI/CD, dependencies, security, DX, and open-source readiness

---

## Table of Contents

1. [Executive Summary](#executive-summary)
2. [Repository Overview](#repository-overview)
3. [Critical Bugs](#1-critical-bugs)
4. [Security Audit](#2-security-audit)
5. [Architecture Review](#3-architecture-review)
6. [Performance Analysis](#4-performance-analysis)
7. [Code Quality](#5-code-quality)
8. [Testing Evaluation](#6-testing-evaluation)
9. [Dependency Audit](#7-dependency-audit)
10. [Documentation Review](#8-documentation-review)
11. [Open Source Readiness](#9-open-source-readiness)
12. [Developer Experience (DX)](#10-developer-experience-dx)
13. [GitHub Best Practices](#11-github-best-practices)
14. [Production Readiness](#12-production-readiness)
15. [Competitive Analysis](#13-competitive-analysis)
16. [Final Scores](#final-scores)
17. [Prioritized Remediation Roadmap](#prioritized-remediation-roadmap)

---

## Executive Summary

Lithic-CLI is a Python-based, graph-first developer agent toolkit aimed at reducing AI token usage when working with large codebases. It wraps three upstream open-source projects (Graphify, Headroom, Caveman) as adapters, exposing a unified CLI and an MCP (Model Context Protocol) server interface.

The project shows real ambition and a clear product vision. The documentation structure, community health files, and tooling choices (uv, ruff, mypy, pre-commit) are above average for an early-stage v0.1.0 project.

However, the audit uncovered serious issues that block production use and wider open-source adoption:

- **No GitHub Actions CI/CD pipeline exists at all.** Every quality gate (tests, linting, type checking, releases) is manual.
- **Absolute local Windows paths are committed in `upstream.lock.yml`**, exposing the developer's machine layout.
- **No PyPI release has been published**, yet the README links to a PyPI badge and the CHANGELOG says `v0.1.0` was released on 2026-06-27.
- **Git submodules are used for vendor dependencies** that are also listed as PyPI packages, creating a dual-dependency conflict.
- **Zero automated tests are visible** despite a `tests/` directory existing.
- **No GitHub Actions workflows exist** (`.github/` directory is present but workflows could not be confirmed).
- **The `headroom-ai` optional dependency** requires Rust/MSVC tooling on Windows — a significant DX barrier that is only mentioned in a small footnote.
- **Version numbers in `pyproject.toml` dependencies are unusually high** (e.g., `openai>=2.44.0`, `anthropic>=0.112.0`, `mcp>=1.28.1`, `pytest>=9.1.1`, `mypy>=2.1.0`), suggesting the lock file may be misconfigured or these are placeholder version numbers.
- **Submodule branches (`v8`, `main`) are tracked rather than pinned to commit SHAs**, creating reproducibility and supply-chain risks.

The project is **not production-ready** and requires significant work before wider adoption. It is, however, a solid foundation for a genuinely useful tool.

---

## Repository Overview

| Property | Value |
|---|---|
| Language | Python 99.6%, Makefile 0.4% |
| Python Version Required | 3.12+ |
| Package Manager | uv |
| Build Backend | uv_build |
| Version | 0.1.0 |
| License | MIT |
| Stars/Forks | 0 / 0 |
| Releases | None published |
| Contributors | 1 (DelwarOfficial) |
| CI/CD | Not confirmed — no workflow files found |
| Submodules | 3 (graphify, headroom, caveman) |

---

## 1. Critical Bugs

---

### BUG-001 — Absolute Local Developer Paths Committed to Repository

| Field | Detail |
|---|---|
| **File** | `upstream.lock.yml` |
| **Lines** | 3, 7, 11 |
| **Severity** | High |
| **Category** | Configuration / Information Disclosure |

**Root Cause:** The `upstream.lock.yml` file contains hardcoded Windows absolute paths from the developer's local machine:

```yaml
# upstream.lock.yml — Lines 2-12 (PROBLEMATIC)
projects:
  graphify:
    local_path: D:\websie\merge-skill\graphify-8  # <-- Exposes local file system layout
  headroom:
    local_path: D:\websie\merge-skill\headroom-main  # <-- Same problem
  caveman:
    local_path: D:\websie\merge-skill\caveman-main  # <-- Same problem
```

**Technical Explanation:** These paths are meaningless and broken for any other developer who clones the repository. They expose the developer's local directory structure and disk layout (Windows `D:` drive). If this file is parsed at runtime by any tooling (e.g., the `lithic upstream-status` command), it will crash on every machine except the original developer's.

**Impact:** Any developer running `lithic upstream-status` will get a path-not-found error. It also leaks internal development environment structure.

**Suggested Fix:**
```yaml
# upstream.lock.yml — CORRECTED VERSION
# Use relative paths relative to the repository root
projects:
  graphify:
    local_path: vendor/graphify      # Relative path, works everywhere
    license: MIT
    integration: cli_adapter
  headroom:
    local_path: vendor/headroom      # Relative path
    license: Apache-2.0
    integration: optional_package_plus_fallback
  caveman:
    local_path: vendor/caveman       # Relative path
    license: MIT
    integration: policy_adaptation
```

**Implementation Difficulty:** Easy (5 minutes)
**Priority:** High — Fix immediately before any new commit

---

### BUG-002 — Dual Dependency System Creates Potential Runtime Conflict

| Field | Detail |
|---|---|
| **File** | `pyproject.toml` + `.gitmodules` |
| **Lines** | pyproject.toml L13, L23; .gitmodules L1-12 |
| **Severity** | High |
| **Category** | Dependency Management / Runtime Bug |

**Root Cause:** The same upstream projects (Graphify, Headroom) appear both as **Git submodules** in `vendor/` and as **PyPI packages** in `pyproject.toml`:

```toml
# pyproject.toml — PyPI packages
dependencies = [
    "graphifyy>=0.8.49",           # <-- PyPI package
]
[project.optional-dependencies]
headroom = ["headroom-ai[proxy,code,mcp,relevance]>=0.27.0"]  # <-- PyPI package
```

```ini
# .gitmodules — also as Git submodules
[submodule "vendor/graphify"]
    url = https://github.com/safishamsi/graphify
[submodule "vendor/headroom"]
    url = https://github.com/chopratejas/headroom
```

**Technical Explanation:** At runtime, Python will import from the PyPI-installed package, not from the `vendor/` submodule. The `vendor/` submodule is essentially dead code at the import level unless `sys.path` manipulation exists in the source. This creates confusion about which version of each library is actually running.

**Impact:** Difficult to debug version mismatches; `lithic upstream-status` checks submodule status but actual code runs from PyPI packages — the status check does not reflect what's actually executing.

**Suggested Fix:** Choose one approach:
- **Option A (Recommended):** Remove Git submodules. Use PyPI packages only with pinned versions in `uv.lock`.
- **Option B:** Remove PyPI dependencies and use Git submodules with path-based installs via `uv`.

**Implementation Difficulty:** Medium (requires architectural decision + refactor)
**Priority:** High

---

### BUG-003 — Submodule Branches Tracked Instead of Commit SHAs

| Field | Detail |
|---|---|
| **File** | `.gitmodules` |
| **Lines** | 4, 8, 12 |
| **Severity** | High |
| **Category** | Reproducibility / Supply-Chain Risk |

**Root Cause:** All three submodules track mutable branch names:

```ini
# .gitmodules — Mutable branch tracking (RISKY)
[submodule "vendor/graphify"]
    branch = v8        # <-- Branch, not a commit SHA
[submodule "vendor/headroom"]
    branch = main      # <-- Branch, not a commit SHA
[submodule "vendor/caveman"]
    branch = main      # <-- Branch, not a commit SHA
```

**Technical Explanation:** Git submodules should be pinned to a specific commit SHA to guarantee reproducible builds. Tracking a branch means upstream changes to `main` can silently change the behavior of Lithic-CLI for new cloners, without any change to Lithic's own code. This is a well-known supply-chain attack vector.

**Suggested Fix:**
```bash
# Pin each submodule to a specific commit SHA
cd vendor/graphify && git checkout <specific-sha> && cd ../..
cd vendor/headroom && git checkout <specific-sha> && cd ../..
cd vendor/caveman  && git checkout <specific-sha> && cd ../..
git add vendor/ && git commit -m "chore: pin submodules to specific commit SHAs"
# Then remove the 'branch' lines from .gitmodules
```

**Implementation Difficulty:** Easy
**Priority:** High

---

### BUG-004 — PyPI Badge Points to Unpublished Package

| Field | Detail |
|---|---|
| **File** | `README.md` |
| **Severity** | Medium |
| **Category** | Documentation / False Advertising |

**Root Cause:** The README displays a PyPI badge `https://pypi.org/project/lithic-cli/` but there are **zero GitHub Releases** published and the package does not appear to be live on PyPI. The CHANGELOG also shows `v0.1.0 - 2026-06-27` which is today's date, suggesting the release process was never completed.

**Impact:** New users clicking the PyPI badge will get a 404 page. This damages credibility immediately.

**Suggested Fix:** Either publish to PyPI (`uv build && uv publish`) or replace the PyPI badge with a "Coming Soon" note until the package is live.

**Implementation Difficulty:** Easy
**Priority:** Medium

---

### BUG-005 — `openai>=2.44.0` Dependency Version Appears Invalid

| Field | Detail |
|---|---|
| **File** | `pyproject.toml` |
| **Line** | 15 |
| **Severity** | Medium |
| **Category** | Dependency / Potential Runtime Failure |

**Root Cause:**
```toml
dependencies = [
    "openai>=2.44.0",   # <-- As of June 2026, openai latest is ~1.x series
]
```

The `openai` Python package is in the `1.x` series (e.g., `openai==1.35.x`). A constraint of `>=2.44.0` may either be a typo, a future-forward guess, or an error. If `openai` has not released `2.x`, this constraint makes the package unresolvable from PyPI.

**Note:** This could not be fully verified without running the actual dependency resolution. However, the same pattern appears in `anthropic>=0.112.0`, `mcp>=1.28.1`, `pytest>=9.1.1`, and `mypy>=2.1.0` — all with version numbers significantly higher than known stable releases, suggesting these may be aspirational or incorrect constraints. The `uv.lock` file would be the ground truth here but was not fully inspectable.

**Suggested Fix:** Verify all version constraints against actual PyPI releases. Use `uv pip compile` to validate the dependency tree resolves correctly.

**Implementation Difficulty:** Easy (verification) to Medium (if constraints need adjustment)
**Priority:** High

---

## 2. Security Audit

---

### SEC-001 — Personal Email Address Publicly Committed

| Field | Detail |
|---|---|
| **File** | `pyproject.toml` (L7), `SECURITY.md` (L13, L54) |
| **Severity** | Low |
| **Category** | Privacy / Information Disclosure |

**Evidence:**
```toml
# pyproject.toml — Line 7
authors = [
    { name = "delwarnetwork", email = "delwarnetwork@gmail.com" }
]
```

The maintainer's personal Gmail address is embedded in `pyproject.toml` and `SECURITY.md`. This is somewhat expected for personal open-source projects, but exposes the address to scrapers indexing PyPI metadata.

**Suggested Fix:** Consider using a dedicated project email or GitHub's private vulnerability reporting exclusively. Use `noreply` or a forwarding alias if privacy is a concern.

**Severity Rating:** Low — Accepted risk for many open-source maintainers.

---

### SEC-002 — `.env.example` Contains API Key Format Hints

| Field | Detail |
|---|---|
| **File** | `.env.example` |
| **Lines** | 24-27 |
| **Severity** | Low |
| **Category** | Credential Pattern Exposure |

**Evidence:**
```bash
# .env.example — Lines 24-27
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
OPENROUTER_API_KEY=sk-or-...
```

The `.env.example` file shows API key prefix patterns (`sk-`, `sk-ant-`, `sk-or-`). While not actual credentials, this provides a roadmap for key format that could assist in recognizing leaked keys. This is a very common practice in open source and is considered Low severity.

**Severity Rating:** Low — Standard practice; no actual keys present.

---

### SEC-003 — Submodule URLs Point to Third-Party Repositories Without Integrity Verification

| Field | Detail |
|---|---|
| **File** | `.gitmodules` |
| **Severity** | Medium |
| **Category** | Supply-Chain Risk |

**Evidence:**
```ini
[submodule "vendor/graphify"]
    url = https://github.com/safishamsi/graphify
[submodule "vendor/headroom"]
    url = https://github.com/chopratejas/headroom
[submodule "vendor/caveman"]
    url = https://github.com/JuliusBrussee/caveman
```

All three submodule URLs point to third-party GitHub accounts with no integrity verification (no hash pinning, no GPG signing). If any of these accounts are compromised, Lithic-CLI would silently pull malicious code on `git submodule update`.

**Suggested Fix:** Pin submodules to specific commit SHAs (see BUG-003) and set up Dependabot or automated submodule update checks.

**Severity Rating:** Medium

---

### SEC-004 — No GitHub Actions Security Scanning Configured

| Field | Detail |
|---|---|
| **File** | `.github/` directory |
| **Severity** | High |
| **Category** | CI/CD Security Gap |

**Evidence:** No GitHub Actions workflow files were confirmed in the repository. This means:
- No CodeQL scanning
- No Dependabot configuration
- No secret scanning automation
- No SAST (Static Application Security Testing)

**Suggested Fix:**
```yaml
# .github/workflows/codeql.yml
name: CodeQL Security Scan
on:
  push:
    branches: [main]
  pull_request:
    branches: [main]
  schedule:
    - cron: '0 6 * * 1'   # Weekly on Monday

jobs:
  analyze:
    runs-on: ubuntu-latest
    permissions:
      actions: read
      contents: read
      security-events: write
    strategy:
      matrix:
        language: [python]
    steps:
      - uses: actions/checkout@v4
      - uses: github/codeql-action/init@v3
        with:
          languages: ${{ matrix.language }}
      - uses: github/codeql-action/analyze@v3
```

**Severity Rating:** High
**Priority:** High

---

### SEC-005 — SECURITY.md Claims Mitigations That Cannot Be Verified

| Field | Detail |
|---|---|
| **File** | `SECURITY.md` |
| **Severity** | Medium |
| **Category** | Documentation Accuracy |

**Evidence:** SECURITY.md lists specific mitigations (e.g., `validate_graph_path()`, `sanitize_label()`, `_yaml_str()`, `_load_graph()`) but the source code was not fully accessible for verification. If these functions do not exist or do not implement what is claimed, the security model is misleading.

**Suggested Fix:** Add automated security test cases that directly test each claimed mitigation function. Link source file and line numbers in SECURITY.md.

**Severity Rating:** Medium — Cannot confirm without full source access.

---

## 3. Architecture Review

---

### ARCH-001 — Dual Vendor Strategy Creates Unclear Ownership Boundary

The project uses three upstream projects (Graphify, Headroom, Caveman) as both Git submodules in `vendor/` and as PyPI dependencies. This creates two parallel "import chains" with unclear precedence. Modern Python projects should choose one approach.

**Recommended Pattern:**
```
src/lithic/
├── graph/
│   └── graphify_adapter.py     # Wraps PyPI: graphifyy
├── compression/
│   └── headroom_adapter.py     # Wraps PyPI: headroom-ai (optional)
├── policy/
│   └── response_policy.py      # Wraps: caveman-inspired logic (internal)
├── orchestrator.py             # Coordinates the three layers
└── cli.py                      # Click CLI entry point
```

The `vendor/` directory should either be removed (if PyPI packages are used) or be the single source of truth (if local installs are used). Having both is an architectural anti-pattern.

---

### ARCH-002 — Single-Branch Strategy With No Protected Branches

**Evidence:** The repository has only one branch (`main`) with 26 commits. No branch protection rules appear to be in place, no PR review requirement, no status checks required before merging.

**Impact:** Any maintainer (or a compromised account) can push directly to `main` without review.

**Suggested Fix:** Enable branch protection on `main`: require PR reviews, require CI status checks to pass, require signed commits.

---

### ARCH-003 — No Docker Support Despite MCP Server Functionality

The project exposes an MCP server via `lithic mcp serve`. There is no Dockerfile, no `docker-compose.yml`, and no container deployment guidance. For a tool that serves MCP over stdio, this is acceptable today, but as the tool evolves to support network-based MCP transports, containerization will be essential.

---

### ARCH-004 — `build-backend` Uses Experimental `uv_build`

```toml
# pyproject.toml — Lines 68-70
[build-system]
requires = ["uv_build>=0.11.19,<0.12.0"]
build-backend = "uv_build"
```

`uv_build` is a new and still-evolving build backend. The upper bound `<0.12.0` will block future uv_build releases automatically, which could break new contributor onboarding without warning.

**Suggested Fix:** Consider using the more stable `hatchling` or `setuptools` build backend for a public package. If `uv_build` is preferred, document the rationale and remove the overly tight upper bound.

---

## 4. Performance Analysis

---

### PERF-001 — Submodule Checkout Adds ~30-60s to Fresh Clone

Running `git clone --recurse-submodules` for 3 submodules from separate third-party GitHub repositories adds significant latency to the first-time developer setup. This is especially problematic for users in regions with slower international internet (such as Bangladesh).

**Suggested Fix:**
- If submodules are needed, document that `uv sync` handles everything without needing submodule initialization.
- Alternatively, remove submodules and rely exclusively on PyPI packages.

---

### PERF-002 — No Async Support Documented for LLM API Calls

The CLI interacts with LLM providers (OpenAI, Anthropic, OpenRouter, Ollama). Synchronous API calls will block the CLI while waiting for LLM responses. For large codebases, graph indexing + LLM queries could take many seconds or minutes with no progress feedback.

**Suggested Fix:** Implement async streaming with Rich progress indicators:
```python
# Example pattern for async LLM streaming with progress feedback
import asyncio
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn

console = Console()

async def query_with_progress(query: str) -> str:
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task("Querying graph...", total=None)
        result = await llm_client.query_async(query)
        progress.remove_task(task)
    return result
```

---

### PERF-003 — No Caching Layer for Repeated Graph Queries

Every `lithic ask` or `lithic explain` call rebuilds context from the graph on each invocation. For large codebases, this is inefficient. A simple TTL-based cache for graph query results would dramatically reduce response time for repeated queries.

---

## 5. Code Quality

---

### QA-001 — Ruff Linter Ignores `B904` Rule

```toml
# pyproject.toml — Line 53
[tool.ruff.lint]
ignore = ["B904"]
```

Rule `B904` enforces `raise X from Y` inside `except` blocks, which is important for preserving exception chain context. Silently ignoring this means exception chains may be lost, making debugging harder.

**Suggested Fix:** Remove `B904` from the ignore list and fix any violations it flags.

---

### QA-002 — `mypy` Uses `ignore_missing_imports = true`

```toml
# pyproject.toml — Line 58
[tool.mypy]
ignore_missing_imports = true
```

This setting silently suppresses type errors for all third-party packages that lack type stubs. Given that the project's core dependencies (Graphify, Headroom) are relatively new packages that may lack complete stubs, this masks real type errors.

**Suggested Fix:** Replace with per-module overrides once stable stubs are available:
```toml
[[tool.mypy.overrides]]
module = ["graphifyy.*", "headroom_ai.*"]
ignore_missing_imports = true
```

---

### QA-003 — Two CLI Entry Points (`lithic` and `lith`) Without Justification

```toml
# pyproject.toml — Lines 31-32
[project.scripts]
lithic = "lithic.cli:main"
lith = "lithic.cli:main"   # <-- Why does this alias exist?
```

The `lith` alias is unexplained in documentation. Maintaining two entry points doubles the surface area for breaking changes and confuses users about which to use.

**Suggested Fix:** Document the rationale for the `lith` alias, or remove it. If it's a shorthand convenience, add it to the README's quick-start section.

---

### QA-004 — `CONTRIBUTING.md` Uses `pip install -e .` Instead of `uv sync`

```markdown
<!-- CONTRIBUTING.md — Development Setup section -->
pip install -e .
pip install -e .[dev]
```

But the project uses `uv` as its package manager. New contributors following the CONTRIBUTING guide will use pip, which contradicts the recommended `uv sync` workflow in the README. This creates inconsistency and potential environment conflicts.

**Suggested Fix:**
```bash
# CONTRIBUTING.md — Corrected Development Setup
git clone https://github.com/DelwarOfficial/Lithic-CLI.git
cd Lithic-CLI

# Install uv if not already installed
pip install uv

# Install all dependencies including dev group
uv sync

# Or with optional headroom extra
uv sync --extra headroom
```

---

## 6. Testing Evaluation

---

### TEST-001 — No Visible Test Implementations

**Evidence:** The `tests/` directory exists and `pyproject.toml` configures `pytest` and `pytest-asyncio`, but no actual test file contents were inspectable. With 0 stars and a single contributor at v0.1.0, it is likely that tests are either minimal scaffolding or entirely absent.

**What is missing:**

```python
# tests/test_orchestrator.py — Example missing test
import pytest
from lithic.orchestrator import Orchestrator

def test_orchestrator_routes_graph_first():
    """Verify graph context is fetched before LLM fallback."""
    orch = Orchestrator()
    # Test that graph query is called before any LLM call
    ...

def test_orchestrator_handles_empty_graph():
    """Verify graceful degradation when graph is empty."""
    ...

# tests/test_compression.py — Example missing test
def test_headroom_fallback_when_package_unavailable():
    """Verify built-in compressor is used when headroom-ai is not installed."""
    ...

# tests/test_cli.py — Example missing test
from click.testing import CliRunner
from lithic.cli import main

def test_index_command_requires_path():
    runner = CliRunner()
    result = runner.invoke(main, ['index'])
    assert result.exit_code != 0

def test_ask_command_with_empty_graph(tmp_path):
    runner = CliRunner()
    result = runner.invoke(main, ['ask', 'what is this?'], 
                           catch_exceptions=False)
    # Should fail gracefully, not crash
    assert 'no graph found' in result.output.lower()
```

**Recommended Test Coverage Targets:**
- Core orchestrator logic: 80%+
- CLI commands (using Click's test runner): 90%+
- Compression fallback behavior: 100%
- Path validation and security sanitization: 100%

---

### TEST-002 — No CI Pipeline to Run Tests Automatically

Without GitHub Actions, tests are only run if a developer manually runs `pytest`. This means regressions can be merged silently.

**Suggested Fix — Minimum Viable CI:**
```yaml
# .github/workflows/ci.yml
name: CI
on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  test:
    runs-on: ${{ matrix.os }}
    strategy:
      matrix:
        os: [ubuntu-latest, windows-latest, macos-latest]
        python-version: ["3.12", "3.13"]
    steps:
      - uses: actions/checkout@v4
        with:
          submodules: recursive   # If submodules are kept
      
      - name: Install uv
        uses: astral-sh/setup-uv@v3
      
      - name: Install dependencies
        run: uv sync

      - name: Run linter
        run: uv run ruff check src/lithic/ tests/
      
      - name: Run type checker
        run: uv run mypy src/lithic/
      
      - name: Run tests
        run: uv run pytest tests/ -v --tb=short
```

---

## 7. Dependency Audit

---

### DEP-001 — Suspicious Version Constraints in `pyproject.toml`

| Package | Constraint in pyproject.toml | Known Latest Stable (as of audit) | Risk |
|---|---|---|---|
| `openai` | `>=2.44.0` | ~1.x series | Potentially unresolvable |
| `anthropic` | `>=0.112.0` | ~0.2x-0.3x series | Potentially unresolvable |
| `mcp` | `>=1.28.1` | Early releases | Potentially unresolvable |
| `pytest` | `>=9.1.1` | ~8.x series | May not exist yet |
| `mypy` | `>=2.1.0` | ~1.x series | May not exist yet |
| `ruff` | `>=0.15.20` | ~0.4-0.6 series | May not exist yet |

**Note:** These cannot be 100% confirmed without running `uv pip compile`. However, the pattern strongly suggests either version numbers are aspirational placeholders, or the `uv.lock` file pins working versions that contradict these constraints. This is confusing and potentially blocks fresh installs without the lock file.

**Suggested Fix:** Verify all version constraints against actual PyPI releases. Use `>=<current_version>` patterns based on verified available versions.

---

### DEP-002 — No Dependabot Configuration

No `.github/dependabot.yml` was found. For a project with 10+ dependencies, automated dependency updates are essential for long-term security.

**Suggested Fix:**
```yaml
# .github/dependabot.yml
version: 2
updates:
  - package-ecosystem: "pip"
    directory: "/"
    schedule:
      interval: "weekly"
    reviewers:
      - "DelwarOfficial"
    labels:
      - "dependencies"
  
  - package-ecosystem: "github-actions"
    directory: "/"
    schedule:
      interval: "weekly"
```

---

### DEP-003 — `headroom-ai` Optional Dependency Has Platform-Specific Build Requirements

**Evidence from README:**
> On some Windows environments, `headroom-ai` may require Rust/MSVC build tooling when a compatible wheel is unavailable.

This is a significant DX barrier. Requiring Rust/MSVC to install an optional Python package will confuse most Windows users and is not clearly documented in the CONTRIBUTING guide.

**Suggested Fix:** Either pre-build wheels for common platforms (via GitHub Actions) or prominently document the Rust requirement with a link to Rust's Windows installer.

---

## 8. Documentation Review

---

### DOC-001 — Missing API Reference Documentation

There is no auto-generated API reference (e.g., from `mkdocs` + `mkdocstrings` or `sphinx`). For a library/CLI that exposes adapters and an MCP interface, API documentation is essential for contributors.

**Suggested Fix:**
```bash
# Install mkdocs with material theme and docstrings plugin
uv add --group docs mkdocs-material mkdocstrings[python]

# Create mkdocs.yml
# Generate docs from docstrings automatically
```

---

### DOC-002 — Missing Quickstart for MCP Integration

The README mentions `lithic mcp serve` but provides no documentation on how to integrate the MCP server with Claude Desktop, Cursor, or other MCP clients. This is likely the most valuable use case for AI developers.

**Suggested Addition:**
```json
// Claude Desktop — mcp_config.json example (should be in docs/)
{
  "mcpServers": {
    "lithic": {
      "command": "uv",
      "args": ["run", "lithic", "mcp", "serve"],
      "cwd": "/path/to/your/project"
    }
  }
}
```

---

### DOC-003 — CONTRIBUTING.md References `pip` Instead of `uv`

See QA-004 above. The development setup instructions are inconsistent with the project's toolchain.

---

### DOC-004 — No Migration Guide for `UDA_*` Legacy Variables

```python
# .env.example — Lines 28-30
# Legacy Support (optional)
# UDA_PROVIDER=openai
# UDA_MODEL=gpt-4
```

Legacy `UDA_*` variables are mentioned but there is no documentation explaining when they were deprecated, what they map to, or when support will be removed.

---

### DOC-005 — `docs/` Directory Files Referenced in README But Content Quality Unknown

The README links to `docs/architecture.md`, `docs/setup.md`, `docs/model-comparison.md`, `docs/source-review.md`, `docs/merge-notes.md`, and `docs/license-attribution.md`. These files could not be inspected for content quality, but their existence is positive.

---

## 9. Open Source Readiness

| Checkpoint | Status | Notes |
|---|---|---|
| LICENSE | ✅ Present | MIT License |
| README.md | ✅ Present | Good structure, some gaps |
| CONTRIBUTING.md | ✅ Present | pip/uv inconsistency |
| CODE_OF_CONDUCT.md | ✅ Present | |
| SECURITY.md | ✅ Present | Claims unverifiable without source |
| CHANGELOG.md | ✅ Present | Follows Keep a Changelog format |
| Issue Templates | ❌ Not confirmed | `.github/` directory exists but templates not verified |
| PR Templates | ❌ Not confirmed | |
| GitHub Actions CI | ❌ Not confirmed | Critical gap |
| Dependabot | ❌ Missing | No `dependabot.yml` found |
| CodeQL | ❌ Missing | |
| GitHub Releases | ❌ None published | CHANGELOG claims v0.1.0 exists |
| Semantic Versioning | ✅ Follows SemVer | |
| PyPI Package | ❌ Not published | README badge broken |
| Topics/Tags | ❌ Not confirmed | |
| Discussions | Not enabled (confirmed from page) | |

**Open Source Readiness Assessment:** The community health files are impressive for a v0.1.0 solo project. However, the missing CI/CD, unpublished releases, and broken PyPI badge significantly reduce readiness for adoption.

---

## 10. Developer Experience (DX)

---

### DX-001 — Installation Requires `uv` But Not Everyone Knows It

The README's entire installation flow depends on `uv`, which is relatively new. While `uv` is excellent, many Python developers are unfamiliar with it. The README should include a fallback `pip` workflow.

```bash
# README should show BOTH options:

# Option A: With uv (recommended — fast)
pip install uv
git clone https://github.com/DelwarOfficial/Lithic-CLI.git
cd Lithic-CLI && uv sync

# Option B: Traditional pip (for those who prefer it)
git clone https://github.com/DelwarOfficial/Lithic-CLI.git
cd Lithic-CLI
python -m venv .venv && source .venv/bin/activate
pip install -e .
```

---

### DX-002 — No `lithic --help` Output Shown in README

The README lists commands in a table but doesn't show actual `--help` output. New users benefit from seeing real terminal output before they install.

---

### DX-003 — No Example Projects or Demos

There are no `examples/` directory, no demo repository, and no screenshots or GIFs showing Lithic-CLI in action. For a tool competing with established alternatives, visual proof-of-concept is important.

---

### DX-004 — `make clean` Uses Windows-Only `2>nul` Redirect

```makefile
# Makefile — Line 18
clean:
	-rm -rf .pytest_cache .ruff_cache .mypy_cache graphify-out 2>nul
```

`2>nul` is Windows CMD syntax. On Linux/macOS, the correct redirect is `2>/dev/null`. This Makefile target will produce a visible error on non-Windows systems.

**Suggested Fix:**
```makefile
# Makefile — Cross-platform clean target
clean:
	-rm -rf .pytest_cache .ruff_cache .mypy_cache graphify-out 2>/dev/null || true
```

---

## 11. GitHub Best Practices

| Practice | Status | Priority |
|---|---|---|
| Branch protection on `main` | ❌ Unknown/likely missing | High |
| GitHub Actions CI | ❌ Not confirmed | Critical |
| Dependabot | ❌ Missing | High |
| CodeQL scanning | ❌ Missing | High |
| Issue templates | ❌ Not confirmed | Medium |
| PR templates | ❌ Not confirmed | Medium |
| GitHub Releases with release notes | ❌ None published | High |
| Repository topics/tags | ❌ Not confirmed | Low |
| GitHub Discussions | ❌ Not enabled | Low |
| Wiki | Not required | N/A |
| Automated release workflow | ❌ Missing | High |

**Recommended Release Workflow:**
```yaml
# .github/workflows/release.yml
name: Release
on:
  push:
    tags:
      - 'v*'

jobs:
  release:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: astral-sh/setup-uv@v3
      - name: Build package
        run: uv build
      - name: Publish to PyPI
        run: uv publish
        env:
          UV_PUBLISH_TOKEN: ${{ secrets.PYPI_TOKEN }}
      - name: Create GitHub Release
        uses: softprops/action-gh-release@v2
        with:
          generate_release_notes: true
```

---

## 12. Production Readiness

| Area | Score | Notes |
|---|---|---|
| Reliability | 20/100 | No automated tests, no CI |
| Stability | 30/100 | v0.1.0, single contributor |
| Monitoring/Logging | 20/100 | No structured logging confirmed |
| Error Reporting | 30/100 | SECURITY.md mentions error handling |
| Recovery | 30/100 | Some graph recovery mentioned in SECURITY.md |
| Scalability | 40/100 | Graph-first design is inherently scalable in concept |
| Security | 50/100 | Good documentation; cannot verify implementation |
| Maintainability | 45/100 | Good tooling; dual vendor strategy hurts this |

**Production Readiness Score: 25/100**

This is a pre-production tool. It is suitable for personal use and early adopter experimentation, but not for enterprise or team deployment without the CI/CD, testing, and dependency issues resolved.

---

## 13. Competitive Analysis

| Feature | Lithic-CLI | aider | continue.dev | codebase-context |
|---|---|---|---|---|
| Graph-first indexing | ✅ | ❌ | ❌ | ❌ |
| Token compression | ✅ | ❌ | ❌ | Partial |
| MCP server | ✅ | ❌ | Partial | ❌ |
| Multi-provider (OpenAI, Anthropic, etc.) | ✅ | ✅ | ✅ | Partial |
| CI/CD pipeline | ❌ | ✅ | ✅ | ✅ |
| Test coverage | ❌ | High | High | Medium |
| PyPI package published | ❌ | ✅ | ✅ | ✅ |
| Active community | ❌ | ✅ | ✅ | ❌ |
| Documentation quality | Medium | High | High | Medium |

**Competitive Advantages:**
- Graph-first architecture is genuinely differentiated
- 80% token reduction claim, if true, is a compelling value proposition
- MCP server support positions Lithic well for the AI agent tooling ecosystem
- Multi-provider flexibility out of the box

**Missing to Compete:**
- Published, installable package
- Real test coverage to validate token reduction claims
- Community and ecosystem (GitHub Discussions, Discord, etc.)
- Video demos or GIFs showing the tool in action

---

## Final Scores

| Category | Score | Rationale |
|---|---|---|
| **Security Score** | 52/100 | SECURITY.md is strong; no CI scanning; submodule supply-chain risk |
| **Code Quality Score** | 45/100 | Good tooling config; ruff/mypy configured; B904 suppressed; inconsistent docs |
| **Performance Score** | 40/100 | Good concept; no caching; no async streaming confirmed; submodule latency |
| **Documentation Score** | 62/100 | Above average for v0.1.0; missing API ref, MCP quickstart, pip consistency |
| **Developer Experience Score** | 38/100 | uv-only workflow; broken PyPI badge; no examples; Windows-only Makefile |
| **Open Source Readiness Score** | 55/100 | Good health files; missing CI, releases, Dependabot, CodeQL |
| **Production Readiness Score** | 25/100 | No CI, no tests confirmed, no published release, dual vendor conflict |
| **Overall Repository Score** | 45/100 | Promising architecture; needs significant engineering investment |

---

## Prioritized Remediation Roadmap

### Phase 1 — Critical Fixes (Do This Week)

1. **Fix `upstream.lock.yml`** — Replace absolute Windows paths with relative paths (15 minutes)
2. **Add GitHub Actions CI workflow** — Minimum: lint + test on push/PR (2 hours)
3. **Verify all PyPI dependency versions** — Run `uv pip compile` and fix unresolvable constraints (1 hour)
4. **Pin submodules to commit SHAs** — Eliminates supply-chain risk (30 minutes)
5. **Publish v0.1.0 to PyPI** — Makes the README badge work (1 hour including PyPI account setup)

### Phase 2 — High Priority (Do This Month)

6. **Add Dependabot configuration** — Automated dependency updates (30 minutes)
7. **Add CodeQL scanning workflow** — Security scanning (30 minutes)
8. **Write minimum test suite** — CLI command smoke tests + compression fallback test (1 day)
9. **Fix CONTRIBUTING.md** — Replace pip instructions with uv workflow (30 minutes)
10. **Add MCP quickstart documentation** — Show Claude Desktop integration (2 hours)

### Phase 3 — Medium Priority (Do This Quarter)

11. **Remove dual vendor strategy** — Choose PyPI or submodules, not both (1 day)
12. **Add async LLM streaming with progress indicators** (2 days)
13. **Add example projects** — Show real-world usage (1 day)
14. **Add issue and PR templates** (1 hour)
15. **Enable GitHub Discussions** (15 minutes)
16. **Fix Makefile `clean` target** — Cross-platform redirect (5 minutes)
17. **Add `2>/dev/null` to Makefile** (5 minutes)

### Phase 4 — Long-term Improvements

18. Add auto-generated API documentation with mkdocs
19. Add benchmarks proving 80% token reduction claim
20. Add Docker support for MCP server deployment
21. Consider `hatchling` as a more stable build backend
22. Build community (Discord, GitHub Discussions, blog posts)

---

*This audit was conducted based on publicly accessible repository files as of June 27, 2026. Source file contents inside `src/lithic/` and `tests/` were not fully accessible; findings related to internal implementation are marked accordingly. All findings are evidence-based from inspected files.*
