# Contributing to Lithic

Thank you for your interest in contributing to Lithic! This document provides guidelines and instructions for contributing.

## Code of Conduct

By participating in this project, you agree to abide by our Code of Conduct. Please be respectful and inclusive.

## How to Contribute

### Reporting Issues

- Check if the issue already exists in [GitHub Issues](https://github.com/DelwarOfficial/Lithic-CLI/issues)
- Provide a clear description of the problem
- Include steps to reproduce, expected behavior, and actual behavior
- Add your OS version, Python version, and relevant logs

### Feature Requests

- Describe the feature and its use case
- Explain how it fits into Lithic's goals (graph-first, compression, concise responses)
- Provide examples of how it would be used

### Pull Requests

1. **Fork the repository**
2. **Create a feature branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```
3. **Make your changes**
   - Follow the existing code style
   - Add tests for new functionality
   - Update documentation as needed
4. **Run tests**
   ```bash
   pytest tests/ -q
   ```
5. **Submit a pull request**
   - Provide a clear description of changes
   - Reference any related issues

## Development Setup

```bash
# 1. Install uv (if not already installed)
# On macOS (via Homebrew):
brew install uv

# On Windows (via winget):
winget install astral.uv

# On Linux or any platform (via pip):
pip install uv

# 2. Clone the repository
git clone https://github.com/DelwarOfficial/Lithic-CLI.git
cd Lithic-CLI

# 3. Install all dependencies (including dev tools)
uv sync --group dev

# 4. Install pre-commit hooks
uv run pre-commit install

# 5. Verify setup by running the test suite
uv run pytest tests/ -q

# 6. Run all checks
uv run ruff check src/lithic_cli/ tests/
uv run ruff format src/lithic_cli/ tests/
uv run mypy src/lithic_cli/
```

All commands use `uv run` - do not use `pip` or `python` directly.

## Code Style

- Follow [PEP 8](https://www.python.org/dev/peps/pep-0008/)
- Use type hints (Python 3.12+)
- Run ruff before committing:
  ```bash
  ruff check .
  ```

## Testing

- Write tests for all new functionality
- Run the test suite:
  ```bash
  pytest tests/ -v
  ```

## Documentation

- Update README.md for user-facing changes
- Add docstrings for new functions and classes
- Keep platform guidelines up to date

## Commit Messages

Follow [Conventional Commits](https://www.conventionalcommits.org/):

- `feat:` new feature
- `fix:` bug fix
- `docs:` documentation changes
- `style:` formatting changes
- `refactor:` code refactoring
- `test:` test changes
- `chore:` maintenance tasks

Example:
```
feat: add lithic ask command

Adds the ability to query the knowledge graph using natural language.
```

## Questions?

Open an issue or reach out via [GitHub Discussions](https://github.com/DelwarOfficial/Lithic-CLI/discussions).

Thank you for contributing!
