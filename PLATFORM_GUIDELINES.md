# Platform-Specific Guidelines

## 🍏 Mac Users

### Installation (single command)

```bash
uv tool install git+https://github.com/DelwarOfficial/Lithic-CLI.git
# or
pip install git+https://github.com/DelwarOfficial/Lithic-CLI.git
```

See main README 📦 Installation for details. Dev: clone + uv sync.

### Keyboard Shortcuts

| Action | Shortcut |
|--------|----------|
| Open terminal | `Cmd + Space` → type "Terminal" |
| Clear screen | `Cmd + K` |
| Cancel running command | `Ctrl + C` |
| Path autocomplete | `Tab` key |
| Command history | `↑` / `↓` arrow keys |

### Common Issues & Fixes

- **Python version**: Ensure Python 3.12+ is installed (`python3 --version`)
- **Permission denied**: Use `sudo` with caution, or install with `--user` flag
- **Headroom (opt)**: May need Rust build tools. Falls back to built-in compressor.

---

## 🪟 Windows Users

### Installation (single command)

```powershell
uv tool install git+https://github.com/DelwarOfficial/Lithic-CLI.git
# or
pip install git+https://github.com/DelwarOfficial/Lithic-CLI.git
```

See main README for dev clone path.

### Keyboard Shortcuts

| Action | Shortcut |
|--------|----------|
| Open terminal | `Win + R` → type "cmd" or "powershell" |
| Clear screen | `cls` (CMD) or `Clear-Host` (PowerShell) |
| Cancel running command | `Ctrl + C` |
| Path autocomplete | `Tab` key |
| Command history | `↑` / `↓` arrow keys |

### Common Issues & Fixes

- **Python path**: Ensure Python is in your PATH environment variable
- **Long paths**: Enable long path support in Windows
- **Headroom (opt)**: Rust/MSVC may be needed for full build. Built-in fallback always available.

---

## 🔧 Universal Guidelines

### Pre-Installation Checklist

- [ ] Python 3.12+
- [ ] uv or pip
- [ ] Internet for first install

### Troubleshooting

1. **Command not found**: Add uv/pip user bin to PATH
2. **Permission errors**: Use `--user` or uv tool
3. **Graph fails**: Run from writable project dir. Use `lithic stats`

### Resources

- [README](README.md)
- [docs/setup.md](docs/setup.md)
- [GitHub Issues](https://github.com/DelwarOfficial/Lithic-CLI/issues)

**Need help?** Provide your OS version and the exact error message for faster support.
