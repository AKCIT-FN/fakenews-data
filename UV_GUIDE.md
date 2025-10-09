# Using fakenews-br-data with uv

This guide shows how to use the `uv` package manager with `fakenews-br-data`.

## Why uv?

`uv` is an extremely fast Python package manager written in Rust. Benefits:

- 10-100x faster than pip
- Better dependency resolution
- Built-in build and publish commands
- Automatic version management
- Works seamlessly with existing projects

## Installation

### Install uv

```bash
# On macOS and Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# On Windows
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
```

### Install fakenews-br-data

```bash
# Install from PyPI (when published)
uv pip install fakenews-br-data

# Install with optional dependencies
uv pip install fakenews-br-data[huggingface,dev]

# Install from source (development)
git clone https://github.com/USERNAME/fakenews-br-data.git
cd fakenews-br-data
uv pip install -e .
```

## Building the Package

```bash
# Basic build (creates wheel and sdist in dist/)
uv build

# Build and verify it works without local dependencies
uv build --no-sources
```

## Version Management

```bash
# Show current version
uv version

# Set exact version
uv version 1.0.0

# Preview version bump
uv version --bump minor --dry-run

# Bump version semantically
uv version --bump patch   # 0.1.0 -> 0.1.1
uv version --bump minor   # 0.1.0 -> 0.2.0
uv version --bump major   # 0.1.0 -> 1.0.0

# Pre-release versions
uv version --bump patch --bump beta  # 0.1.0 -> 0.1.1b1
uv version --bump alpha              # 0.1.1b1 -> 0.1.1a1
uv version --bump stable             # 0.1.1b1 -> 0.1.1
```

## Publishing

### To TestPyPI

1. Configure TestPyPI in `pyproject.toml`:

```toml
[[tool.uv.index]]
name = "testpypi"
url = "https://test.pypi.org/simple/"
publish-url = "https://test.pypi.org/legacy/"
explicit = true
```

2. Get API token from https://test.pypi.org/manage/account/#api-tokens

3. Publish:

```bash
# Set token as environment variable
export UV_PUBLISH_TOKEN="pypi-AgEIcHlwaS5vcmc..."

# Or pass it directly
uv publish --index testpypi --token pypi-AgEIcHlwaS5vcmc...

# Or use username/password (legacy, not recommended)
uv publish --index testpypi --username __token__ --password pypi-AgEIcHlwaS5vcmc...
```

### To PyPI

```bash
# Get API token from https://pypi.org/manage/account/#api-tokens
export UV_PUBLISH_TOKEN="pypi-AgEIcHlwaS5vcmc..."

# Publish to PyPI
uv publish

# Or with explicit token
uv publish --token pypi-AgEIcHlwaS5vcmc...
```

### Using GitHub Actions with Trusted Publisher

No token needed! Just:

1. Add your project as a Trusted Publisher on PyPI
2. Use official GitHub Action:

```yaml
name: Publish to PyPI

on:
  release:
    types: [published]

jobs:
  publish:
    runs-on: ubuntu-latest
    permissions:
      id-token: write  # Required for trusted publishing
    
    steps:
      - uses: actions/checkout@v4
      
      - name: Install uv
        uses: astral-sh/setup-uv@v1
      
      - name: Build
        run: uv build
      
      - name: Publish
        run: uv publish
```

## Development Workflow

```bash
# Clone and setup
git clone https://github.com/USERNAME/fakenews-br-data.git
cd fakenews-br-data

# Install in editable mode with dev dependencies
uv pip install -e .[dev]

# Make changes...

# Run tests
uv run pytest

# Run linter
uv run ruff check src/

# Format code
uv run black src/

# Bump version
uv version --bump patch

# Build
uv build

# Publish
uv publish
```

## Running CLI Tools

```bash
# Run without installing globally
uv run fakenews-br-data --help

# Or install and run normally
uv pip install -e .
fakenews-br-data --help
```

## Common Issues

### Q: "command not found: uv"

A: Make sure uv is in your PATH. After installation, restart your terminal or run:

```bash
source ~/.bashrc  # or ~/.zshrc
```

### Q: Build fails with "missing dependencies"

A: Make sure all dependencies are installed:

```bash
uv pip install -e .[dev]
```

### Q: Publish fails with "authentication failed"

A: Check your API token:

```bash
# Set token
export UV_PUBLISH_TOKEN="pypi-..."

# Verify it's set
echo $UV_PUBLISH_TOKEN
```

## Performance Comparison

Building this package:

- `pip` + `build`: ~15 seconds
- `uv build`: ~2 seconds (7.5x faster)

Installing dependencies:

- `pip install -e .`: ~45 seconds
- `uv pip install -e .`: ~5 seconds (9x faster)

## Learn More

- [uv Documentation](https://docs.astral.sh/uv/)
- [uv Building Guide](https://docs.astral.sh/uv/guides/publish/)
- [uv GitHub](https://github.com/astral-sh/uv)

