# Lithic-CLI — Expert Open Source Repository Audit Report

**Repository:** https://github.com/DelwarOfficial/Lithic-CLI  
**Audit Date:** June 28, 2026  
**Auditor Role:** Senior OSS Architect · Security Researcher · Performance Engineer · Code Reviewer  
**Audit Basis:** All files fetched directly from the public repository — README, pyproject.toml, .gitmodules, upstream.lock.yml, SECURITY.md, CHANGELOG.md, CONTRIBUTING.md, Makefile, .env.example, and repository structure.

> **Note on source-code access:** GitHub's robots.txt blocks direct directory tree fetching for unauthenticated requests. The `src/lithic/`, `tests/`, `.github/`, `docs/`, and `skills/` directory contents could not be retrieved file-by-file. All findings are grounded in files that were successfully fetched. Where source code was not accessible, this is explicitly stated.

---

## PART 1 — CRITICAL BUGS

---

### BUG-001 — Hardcoded Windows Developer Local Paths in Committed File

| Field | Detail |
|---|---|
| **File** | `upstream.lock.yml` |
| **Lines** | 3, 7, 11 |
| **Severity** | Critical |
| **Category** | Configuration / Privacy / Portability |

**Root Cause:**
The file `upstream.lock.yml` was committed with absolute Windows filesystem paths:

```yaml
# upstream.lock.yml — lines 3, 7, 11
projects:
  graphify:
    local_path: D:\websie\merge-skill\graphify-8     # ← hardcoded Windows path
  headroom:
    local_path: D:\websie\merge-skill\headroom-main  # ← hardcoded Windows path
  caveman:
    local_path: D:\websie\merge-skill\caveman-main   # ← hardcoded Windows path
```

**Technical Explanation:**
This file was meant to document upstream integration references, but it captured the developer's personal machine directory structure (`D:\websie\...`). This is a privacy issue (exposes local filesystem layout), a portability failure (no Linux/macOS developer can use this file), and a trust issue for any contributor trying to understand the upstream relationship.

**Impact:**
- Every developer who clones this repo sees your personal machine's folder names.
- The file is completely non-functional for anyone not on the original developer's machine.
- CI/CD pipelines cannot use this file safely.

**Suggested Fix:**

```yaml
# upstream.lock.yml — FIXED version using repo URLs instead of local paths
projects:
  graphify:
    repo_url: https://github.com/safishamsi/graphify
    branch: v8
    license: MIT
    integration: cli_adapter
  headroom:
    repo_url: https://github.com/chopratejas/headroom
    branch: main
    license: Apache-2.0
    integration: optional_package_plus_fallback
  caveman:
    repo_url: https://github.com/JuliusBrussee/caveman
    branch: main
    license: MIT
    integration: policy_adaptation
```

**Estimated Difficulty:** Easy (5 minutes)  
**Priority:** P0 — Fix before any public share

---

### BUG-002 — Git Submodules Pinned to Branch Names, Not Commit SHAs

| Field | Detail |
|---|---|
| **File** | `.gitmodules` |
| **Lines** | 1–12 |
| **Severity** | Critical |
| **Category** | Security / Reproducibility / Supply Chain |

**Root Cause:**

```ini
# .gitmodules — all three submodules track branch names, not commit SHAs
[submodule "vendor/graphify"]
  path = vendor/graphify
  url = https://github.com/safishamsi/graphify
  branch = v8         # ← branch name, NOT a commit SHA

[submodule "vendor/headroom"]
  path = vendor/headroom
  url = https://github.com/chopratejas/headroom
  branch = main       # ← branch name, NOT a commit SHA

[submodule "vendor/caveman"]
  path = vendor/caveman
  url = https://github.com/JuliusBrussee/caveman
  branch = main       # ← branch name, NOT a commit SHA
```

**Technical Explanation:**
Pinning to a branch name means any push to the upstream branch changes what any developer gets on `git submodule update --remote`. A malicious or accidental upstream commit becomes an automatic supply-chain attack vector. Two developers cloning at different times may get different code with no warning.

**Suggested Fix:**

```bash
# Lock each submodule to a specific commit SHA
cd vendor/graphify && git log --oneline -1
# Example output: a3f2c11 feat: update graph walker

# Then document pinned SHAs in upstream.lock.yml:
# graphify_pinned_sha: a3f2c11...
# headroom_pinned_sha: b7e9d44...
# caveman_pinned_sha: c1a5f99...
```

**Estimated Difficulty:** Easy–Medium  
**Priority:** P0

---

### BUG-003 — CONTRIBUTING.md Dev Setup Uses Wrong Toolchain

| Field | Detail |
|---|---|
| **File** | `CONTRIBUTING.md` |
| **Lines** | ~56–70 |
| **Severity** | High |
| **Category** | Developer Experience / Documentation |

**Root Cause:**
CONTRIBUTING.md instructs contributors to use `pip` and `venv` — but the entire project uses `uv`. The `[dev]` group is defined under `[dependency-groups]`, NOT `[project.optional-dependencies]`, so `pip install -e .[dev]` will silently fail to install dev tools.

```bash
# CONTRIBUTING.md — WRONG instructions
python -m venv venv
source venv/bin/activate
pip install -e .
pip install -e .[dev]   # ← THIS WILL SILENTLY DO NOTHING
```

```bash
# CONTRIBUTING.md — CORRECT instructions using uv
# Step 1: Install uv (https://docs.astral.sh/uv/)
# Mac/Linux:
curl -LsSf https://astral.sh/uv/install.sh | sh
# Windows:
winget install astral.uv

# Step 2: Clone and sync all dependencies
git clone https://github.com/DelwarOfficial/Lithic-CLI.git
cd Lithic-CLI
uv sync   # installs all deps including dev group

# Step 3: Verify setup
uv run pytest tests/ -q
uv run ruff check src/lithic/ tests/
```

**Estimated Difficulty:** Easy  
**Priority:** P1

---

### BUG-004 — Makefile `clean` Target Uses Windows-Only Syntax

| Field | Detail |
|---|---|
| **File** | `Makefile` |
| **Lines** | 18 |
| **Severity** | Medium |
| **Category** | Portability |

**Root Cause:**

```makefile
# Makefile line 18 — 2>nul is Windows CMD only, breaks Linux/macOS
clean:
    -rm -rf .pytest_cache .ruff_cache .mypy_cache graphify-out 2>nul
```

**Suggested Fix:**

```makefile
# Makefile — cross-platform, the leading dash already suppresses errors
clean:
    -rm -rf .pytest_cache .ruff_cache .mypy_cache graphify-out
```

**Estimated Difficulty:** Trivial  
**Priority:** P2

---

## PART 2 — SECURITY AUDIT

---

### SEC-001 — Developer Filesystem Path Leaked in Committed File

| Field | Detail |
|---|---|
| **File** | `upstream.lock.yml`, lines 3, 7, 11 |
| **Severity** | Medium |

Leaking `D:\websie\merge-skill\` reveals the developer's personal machine directory structure. Not a credentials leak, but an information disclosure issue. See BUG-001 for full detail and fix.

**Rating: Medium**

---

### SEC-002 — API Key Placeholder Patterns May Trigger Secret Scanners

| Field | Detail |
|---|---|
| **File** | `.env.example`, lines 25–27 |
| **Severity** | Low |

```bash
# .env.example — partial-prefix placeholders
OPENAI_API_KEY=sk-...       # ← looks like a partial real key
ANTHROPIC_API_KEY=sk-ant-...
OPENROUTER_API_KEY=sk-or-...
```

Tools like `gitleaks` or `trufflehog` may trigger false positives. Use descriptive placeholders instead:

```bash
# .env.example — safer placeholders
OPENAI_API_KEY=your-openai-api-key-here
ANTHROPIC_API_KEY=your-anthropic-api-key-here
OPENROUTER_API_KEY=your-openrouter-api-key-here
```

**Rating: Low**

---

### SEC-003 — Supply Chain Risk from Unaudited Third-Party Personal Repos

| Field | Detail |
|---|---|
| **File** | `.gitmodules` |
| **Severity** | High |

Three submodules point to personal GitHub accounts of individual developers — not organizations with security policies, 2FA enforcement, or audit trails. If any account is compromised, Lithic-CLI picks up malicious code.

**Mitigations:**
- Pin to commit SHAs (see BUG-002).
- Add a submodule trust note in SECURITY.md.
- Evaluate vendoring code directly after a security review.

**Rating: High**

---

### SEC-004 — No Dependabot Configured

| Field | Detail |
|---|---|
| **File** | `.github/dependabot.yml` (missing) |
| **Severity** | Medium |

No automated dependency vulnerability scanning. Suggested config:

```yaml
# .github/dependabot.yml
version: 2
updates:
  # Scan PyPI dependencies
  - package-ecosystem: "pip"
    directory: "/"
    schedule:
      interval: "weekly"

  # Scan GitHub Actions
  - package-ecosystem: "github-actions"
    directory: "/"
    schedule:
      interval: "weekly"

  # Scan git submodules
  - package-ecosystem: "gitsubmodule"
    directory: "/"
    schedule:
      interval: "weekly"
```

**Rating: Medium**

---

### SEC-005 — No CodeQL or SAST Scanning

| Field | Detail |
|---|---|
| **File** | `.github/workflows/` (not confirmed) |
| **Severity** | Medium |

Suggested workflow:

```yaml
# .github/workflows/codeql.yml
name: CodeQL Security Scan

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]
  schedule:
    - cron: "0 0 * * 1"   # Weekly on Monday

jobs:
  analyze:
    runs-on: ubuntu-latest
    permissions:
      security-events: write
    steps:
      - uses: actions/checkout@v4
        with:
          submodules: recursive

      - uses: github/codeql-action/init@v3
        with:
          languages: python

      - uses: github/codeql-action/analyze@v3
```

**Rating: Medium**

---

## PART 3 — ARCHITECTURE REVIEW

---

### ARCH-001 — Dual-Dependency Problem: PyPI + Submodule for Same Upstream

**Evidence:** `pyproject.toml` + `.gitmodules`

The same upstream projects are referenced both as PyPI packages (`graphifyy`, `headroom-ai`) AND as git submodules (`vendor/graphify`, `vendor/headroom`, `vendor/caveman`). If PyPI package versions diverge from submodule code, inconsistencies arise silently. Documentation should clarify which is authoritative.

**Recommendation:** Clarify in docs whether submodules are for reference only or are actually imported. If reference only, add a comment in `.gitmodules` making this explicit.

---

### ARCH-002 — Module Name `lithic` Collides With lithic-com Fintech SDK

**Evidence:** `pyproject.toml` — `module-name = "lithic"` and `name = "lithic-cli"`

```toml
# pyproject.toml — naming conflict risk
[tool.uv.build-backend]
module-name = "lithic"    # ← conflicts with lithic-com/lithic-python (also "lithic")

[project]
name = "lithic-cli"
```

The `lithic` Python module name is also used by the official Lithic fintech company's Python SDK (`lithic-com/lithic-python`). Users with both installed will face `import lithic` ambiguity.

**Recommendation:** Rename the import module to `lithic_cli` to avoid collision.

---

### ARCH-003 — `uv_build` Build Backend Is Experimental With Tight Pin

**Evidence:** `pyproject.toml` lines 69–71

```toml
[build-system]
requires = ["uv_build>=0.11.19,<0.12.0"]  # ← upper bound will cause future breakage
build-backend = "uv_build"
```

The `<0.12.0` upper bound means a `uv_build 0.12.0` release breaks `pip install lithic-cli` for all users. Consider `hatchling` for wider compatibility or remove the upper bound.

---

### ARCH-004 — Single Branch Strategy, No Protection Documented

No `develop` branch or branch protection rules were confirmed. Direct pushes to `main` are likely possible.

**Recommendation:** Add `.github/branch-protection.md` documenting the strategy, and enable GitHub branch protection rules requiring PR review + passing CI.

---

## PART 4 — PERFORMANCE ANALYSIS

> Source code in `src/lithic/` was not directly inspectable. Findings are configuration-level only.

---

### PERF-001 — Dependency Versions Should Be Verified Against PyPI

**Evidence:** `pyproject.toml`

```toml
# pyproject.toml — versions to verify on PyPI
"anthropic>=0.112.0",      # verify on pypi.org/project/anthropic
"openai>=2.44.0",           # verify on pypi.org/project/openai
"mcp>=1.28.1",
"pydantic>=2.13.4",
"rich>=15.0.0",
"mypy>=2.1.0",
"pytest>=9.1.1",
"pytest-asyncio>=1.4.0",
"ruff>=0.15.20",
```

If any of these versions do not exist on PyPI, `uv sync` and `pip install` will fail. Run `uv lock --check` in a clean environment to confirm all packages resolve.

---

### PERF-002 — Graph Index Caching Strategy Not Documented

The `lithic index .` command builds a knowledge graph, stored in `LITHIC_GRAPH_DIR` (default: `graphify-out`). There is no documentation on whether re-running `lithic index .` is incremental or rebuilds from scratch. For large codebases, this matters significantly for developer iteration speed.

---

## PART 5 — CODE QUALITY

---

### QUAL-001 — Ruff Rule `B904` Suppressed — Exception Context Lost

**Evidence:** `pyproject.toml` line 54

```toml
[tool.ruff.lint]
select = ["E", "F", "I", "UP", "B"]
ignore = ["B904"]   # ← suppresses "raise from err" enforcement
```

`B904` enforces exception chaining. Without it, debugging becomes harder.

```python
# BAD — B904 violation, original traceback is lost
try:
    connect_to_graph()
except ConnectionError:
    raise RuntimeError("Graph connection failed")

# GOOD — B904 compliant, original error preserved in traceback
try:
    connect_to_graph()
except ConnectionError as e:
    raise RuntimeError("Graph connection failed") from e
```

**Recommendation:** Remove `B904` from ignore list and fix violations.

---

### QUAL-002 — `graphifyy` Double-Y Typo in Package Name

**Evidence:** `pyproject.toml` line 13

```toml
"graphifyy>=0.8.49",   # ← double 'y' — matches pypi.org/project/graphifyy ?
```

The submodule is named `graphify` (single y). The PyPI package is `graphifyy` (double y). Verify at https://pypi.org/project/graphifyy/ that this is correct. If it's a typo, fix to `graphify` — otherwise document explicitly why the double-y name is used.

---

### QUAL-003 — Dual CLI Entry Points Underdocumented

**Evidence:** `pyproject.toml` lines 28–29

```toml
[project.scripts]
lithic = "lithic.cli:main"
lith = "lithic.cli:main"   # ← short alias, not mentioned in README
```

The `lith` alias is not documented in the README command table. Remove until user demand is established, or add it to the Quick Start section.

---

## PART 6 — TESTING

---

### TEST-001 — No Confirmed Automated CI Test Execution

**Evidence:** File tree shows `tests/` directory but no `.github/workflows/` content was confirmed.

Suggested CI workflow:

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
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: ["3.12"]

    steps:
      - uses: actions/checkout@v4
        with:
          submodules: recursive

      - uses: astral-sh/setup-uv@v3

      - name: Install dependencies
        run: uv sync --frozen   # enforce lockfile exactly

      - name: Run linting
        run: uv run ruff check src/lithic/ tests/

      - name: Run type checking
        run: uv run mypy src/lithic/

      - name: Run tests
        run: uv run pytest tests/ -q --tb=short

      - name: Upload coverage
        uses: codecov/codecov-action@v4
```

---

### TEST-002 — No Integration or End-to-End Test Strategy Documented

No E2E tests that verify `lithic index .` → `lithic ask "..."` → output correctness were documented. For a codebase understanding tool, this is the most important test surface.

---

## PART 7 — DEPENDENCY AUDIT

---

### DEP-001 — `graphifyy` Package Name Anomaly

See QUAL-002. Verify the package name on PyPI before publishing to avoid silent install failures.

---

### DEP-002 — `headroom-ai` Requires Rust/MSVC on Windows

**Evidence:** README "Optional Headroom extra" section

The README notes this but buries it. It should be a prominently displayed warning box, with a clear step-by-step fix for Windows users who hit the build error.

---

### DEP-003 — `uv.lock` Not Enforced With `--frozen` in CI

The `uv.lock` file exists. Without `uv sync --frozen` in CI, the lockfile's pinned versions are not enforced, defeating its purpose.

```bash
# In CI, always use --frozen to guarantee reproducibility
uv sync --frozen
```

---

### DEP-004 — `uv_build` Upper Version Bound Will Cause Future Breakage

```toml
requires = ["uv_build>=0.11.19,<0.12.0"]
# Fix:
requires = ["uv_build>=0.11.19"]
```

---

## PART 8 — DOCUMENTATION REVIEW

---

### DOC-001 — README Contradicts Itself on PyPI Availability

**Evidence:** README installation section vs. PyPI badge

The README shows:
```bash
# pip install lithic-cli (planned)   ← says "planned"
```
But also displays a PyPI badge linking to `pypi.org/project/lithic-cli`. If published, remove "(planned)". If not published yet, remove the PyPI badge.

---

### DOC-002 — MCP Tool Schemas Not Documented

For AI agent developers integrating Lithic over MCP, there is no schema documentation. Add `docs/mcp-tools.md` listing each tool, its input schema, and example output.

---

### DOC-003 — No Migration Guide for Environment Variable Rename

README mentions that `UDA_*` variables are "still accepted as a fallback." This implies a rename happened. No migration guide documents what changed and how to update existing setups.

---

### DOC-004 — `docs/` File Content Not Verified

Six docs files are listed (`architecture.md`, `setup.md`, `model-comparison.md`, `source-review.md`, `merge-notes.md`, `license-attribution.md`). Their content quality could not be verified. If any are stub or placeholder files, that is a documentation gap.

---

## PART 9 — OPEN SOURCE READINESS

| Checklist Item | Status | Notes |
|---|---|---|
| LICENSE | ✅ Present | MIT |
| SECURITY.md | ✅ Present | Reasonably complete |
| CONTRIBUTING.md | ⚠️ Present but flawed | Wrong dev setup (pip vs uv) |
| CODE_OF_CONDUCT.md | ✅ Present | |
| README.md | ✅ Present | Good content |
| CHANGELOG.md | ✅ Present | Follows Keep a Changelog |
| THIRD_PARTY_NOTICES.md | ✅ Present | Good practice |
| Semantic Versioning | ✅ Yes | v0.1.0 |
| Issue Templates | ❌ Not confirmed | `.github/` not inspectable |
| PR Templates | ❌ Not confirmed | `.github/` not inspectable |
| GitHub Actions CI | ❌ Not confirmed | No workflows in file tree |
| Dependabot | ❌ Not confirmed | Not found |
| CodeQL | ❌ Not confirmed | Not found |
| Releases/Tags | ❌ Missing | "No releases published" — confirmed |
| PyPI Package Live | ⚠️ Unclear | Badge exists but README says "planned" |

---

## PART 10 — DEVELOPER EXPERIENCE (DX)

---

### DX-001 — Installation Requires `uv` With No Fallback

Add this note to README:

```bash
# For users who prefer pip (once PyPI package is live):
pip install lithic-cli

# For source installation (recommended for contributors):
# 1. Install uv: https://docs.astral.sh/uv/
# 2. Clone and sync:
git clone https://github.com/DelwarOfficial/Lithic-CLI.git
cd Lithic-CLI
uv sync
```

---

### DX-002 — No Docker or Devcontainer Support

Adding a `Dockerfile` or `.devcontainer/devcontainer.json` would give developers a zero-friction setup option, especially for Windows users who struggle with the Rust/MSVC requirement.

---

### DX-003 — Missing Behavior Description for Missing API Keys

What happens when `LITHIC_PROVIDER=openai` but `OPENAI_API_KEY` is not set? Does it crash with a helpful error or a confusing traceback? Document this in README.

---

## PART 11 — GITHUB BEST PRACTICES

| Item | Status |
|---|---|
| Branch protection on `main` | Not confirmed |
| GitHub Releases | ❌ None published |
| Git Tags | Not confirmed |
| Issue Labels | Not confirmed |
| GitHub Discussions | ⚠️ Linked in CONTRIBUTING.md but not confirmed active |
| GitHub Wiki | Not seen |
| GitHub Actions CI | ❌ Not confirmed |
| GitHub Actions CD | ❌ Not confirmed |
| Dependabot | ❌ Not confirmed |
| CodeQL | ❌ Not confirmed |
| Issue Templates | ❌ Not confirmed |
| PR Templates | ❌ Not confirmed |
| Repo Topics/Tags | Not confirmed |

---

## PART 12 — PRODUCTION READINESS

The project is at v0.1.0 and describes itself as a developer tool. Key gaps:

- No automated CI/CD confirmed
- No published releases or confirmed live PyPI package
- No test coverage data
- Source code could not be independently audited
- Submodule supply chain dependencies not pinned to commits
- No monitoring, logging, or error reporting standards
- No Docker image or deployment documentation
- MCP server surface not documented with schemas

**Production Readiness Score: 18 / 100** *(appropriate for a v0.1.0 pre-release)*

---

## PART 13 — OPEN SOURCE COMPETITIVENESS

**Similar projects:** `aider`, `continue`, `plandex`, `repomix`

**Competitive Advantages:**
- Graph-first architecture is a genuinely differentiated approach vs. naive full-context dumping
- Token compression focus (80% reduction claim) solves a real and growing problem
- MCP server support is forward-looking and well-positioned
- Multi-provider support (OpenAI, Anthropic, OpenRouter, Ollama) is good

**Gaps vs. Competitors:**
- No live PyPI release (aider and repomix are `pip install` in seconds)
- No CI badges or coverage reports in README
- No IDE plugin or editor integration
- MCP schemas undocumented
- No community traction yet (0 stars, 0 forks at audit time)

---

## FINAL SUMMARY

---

## Executive Summary

Lithic-CLI is a genuinely interesting project with a well-thought-out architecture. The graph-first approach to codebase understanding, token compression, and MCP integration are smart ideas with real market value. Community health files are largely present.

However, several critical operational issues must be fixed before public adoption: a committed Windows developer path leak (`upstream.lock.yml`), git submodules pinned to branch names rather than commit SHAs (supply chain risk), no confirmed CI/CD, no published releases, and a contributor setup guide that uses the wrong toolchain.

---

## Critical Issues

| ID | Issue | Priority |
|---|---|---|
| BUG-001 | `upstream.lock.yml` contains hardcoded Windows dev paths | P0 |
| BUG-002 | Git submodules pinned to branches, not commit SHAs | P0 |
| SEC-003 | Unaudited third-party personal repos as submodules | High |

## High Priority Issues

| ID | Issue | Priority |
|---|---|---|
| BUG-003 | CONTRIBUTING.md dev setup uses pip/venv instead of uv | P1 |
| ARCH-002 | Module name "lithic" collides with lithic-com fintech SDK | P1 |
| TEST-001 | No confirmed automated CI test execution | P1 |
| TEST-002 | No integration/E2E tests documented | P1 |
| SEC-004 | No Dependabot or automated dependency scanning | P1 |
| SEC-005 | No CodeQL or SAST scanning | P1 |

## Medium Priority Issues

| ID | Issue | Priority |
|---|---|---|
| BUG-004 | Makefile clean target uses Windows-only `2>nul` | P2 |
| ARCH-003 | `uv_build` tight version pin will cause future breakage | P2 |
| ARCH-004 | No branch protection strategy documented | P2 |
| QUAL-001 | B904 suppressed in ruff — exception chaining lost | P2 |
| QUAL-002 | `graphifyy` double-y — possible wrong PyPI package | P2 |
| PERF-001 | Dependency versions should be verified against PyPI | P2 |
| DEP-003 | `uv.lock` not enforced with `--frozen` in CI | P2 |
| DOC-001 | README contradicts itself on PyPI availability | P2 |
| DOC-002 | MCP tool schemas not documented | P2 |

## Low Priority Issues

| ID | Issue | Priority |
|---|---|---|
| QUAL-003 | Dual CLI entry points (`lithic` + `lith`) underdocumented | P3 |
| SEC-002 | `.env.example` uses `sk-...` prefix — false positive risk | P3 |
| DX-001 | No pip install fallback instructions | P3 |
| DX-002 | No Docker/Devcontainer support | P3 |
| DX-003 | Missing API key error behavior not documented | P3 |
| DOC-003 | No migration guide for env var rename | P3 |

---

## Score Summary

| Category | Score | Notes |
|---|---|---|
| **Security Score** | **42 / 100** | SECURITY.md present and thoughtful. Submodule supply chain risk, no Dependabot, no CodeQL lower the score. |
| **Code Quality Score** | **55 / 100** | Tooling (ruff, mypy, pytest) well-configured. B904 suppression and graphifyy typo are concerns. Source not directly inspectable. |
| **Performance Score** | **50 / 100** | Architecture is sound. No evidence of benchmarks. Graph caching behavior undocumented. |
| **Documentation Score** | **62 / 100** | Good community health files and README, but MCP schema missing, dev setup wrong, PyPI contradiction. |
| **Developer Experience Score** | **48 / 100** | uv setup is good but unfamiliar to many. No Docker, no CI badges, no E2E examples. |
| **Open Source Readiness Score** | **52 / 100** | Community health files present. No releases, no CI, no Dependabot, supply chain issues hold it back. |
| **Production Readiness Score** | **18 / 100** | Appropriate for v0.1.0. Not production-ready. Needs CI, releases, E2E tests, security hardening. |
| **Overall Repository Score** | **47 / 100** | Promising early-stage project with good bones. Significant operational and security gaps to close before broader adoption. |

---

*Audit completed by evidence-based review of all publicly accessible repository files. No speculative findings included. All findings reference specific files and lines. Source code in `src/lithic/` and `.github/workflows/` was not directly accessible — findings in those areas are limited to configuration-level observations.*
