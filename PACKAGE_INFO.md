# fakenews-br-data Package - Installation Guide

## Package Successfully Created! ✅

The Jupyter notebook has been transformed into a fully functional Python package following PyPA guidelines.

## Package Structure

```
package-python/
├── LICENSE                  # MIT License
├── README.md               # Complete documentation
├── pyproject.toml          # Package configuration (hatchling backend)
├── config.example.json     # Example configuration file
├── .gitignore             # Git ignore rules
├── src/
│   └── fakenews_br_data/
│       ├── __init__.py         # Public API exports
│       ├── utils.py            # Utility functions (sha256, download_to, etc.)
│       ├── config.py           # Configuration management
│       ├── schema.py           # Schema normalization functions
│       ├── cleaning.py         # Text cleaning and preprocessing
│       ├── deduplication.py    # Near-duplicate detection (MinHash LSH)
│       ├── downloaders.py      # Dataset downloaders (HF, Zenodo, URL, Local)
│       ├── factcheck.py        # Google Fact Check API integration
│       ├── pipeline.py         # Main orchestration pipeline
│       └── cli.py              # Command-line interface
├── tests/
│   └── __init__.py        # Test placeholder
├── dist/                  # Distribution files (wheel + tar.gz)
│   ├── fakenews_br_data-0.1.0-py3-none-any.whl
│   └── fakenews_br_data-0.1.0.tar.gz
└── venv/                  # Virtual environment (not in repo)
```

## Installation

### Using uv (recommended)

```bash
# Install uv if you haven't already
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install in development mode (uv manages its own virtual environment)
uv pip install -e .

# Or install with optional dependencies
uv pip install -e .[huggingface,dev]
```

### Using pip (traditional)

```bash
# Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install in editable mode
pip install -e .

# Or install with optional dependencies
pip install -e .[huggingface,dev]
```

### From Built Package

```bash
# Using uv
uv pip install dist/fakenews_br_data-0.1.0-py3-none-any.whl

# Using pip
pip install dist/fakenews_br_data-0.1.0-py3-none-any.whl
```

### From PyPI (when published)

```bash
# Using uv
uv pip install fakenews-br-data

# Using pip
pip install fakenews-br-data
```

## Quick Start

### 1. Library Usage

```python
from fakenews_br_data import Pipeline, DatasetCleaner, FactChecker

# Full pipeline with configuration
pipeline = Pipeline(config_path="config.json")
results = pipeline.run_full_pipeline()

# Individual components
cleaner = DatasetCleaner(min_tokens=5)
df_clean = cleaner.clean_dataset("input.csv", "output_clean.csv")

# Fact checking
checker = FactChecker(api_key="YOUR_API_KEY")
checker.process_dataset("clean.csv", "factchecked.csv")
```

### 2. Command-Line Interface

```bash
# Full pipeline
fakenews-br-data pipeline --config config.json

# Individual steps
fakenews-br-data download --config config.json
fakenews-br-data process --config config.json
fakenews-br-data clean --input merged.csv --output clean.csv
fakenews-br-data factcheck --input clean.csv --output checked.csv --config config.json
```

## Configuration

Create a `config.json` file (use `config.example.json` as template):

```json
{
  "factcheck_api_key": "YOUR_GOOGLE_FACTCHECK_API_KEY",
  "out_dir": "data",
  "max_workers": 31,
  "factcheck_sleep": 1,
  "max_inflight": 200,
  "min_tokens": 5,
  "deduplication": {
    "threshold": 0.7,
    "ngram": 5,
    "seed": 3,
    "num_perm": 128,
    "bands": 50
  }
}
```

## Testing the Installation

```bash
# Activate virtual environment
source venv/bin/activate  # or: ./venv/bin/python for direct execution

# Test import
python -c "import fakenews_br_data; print('Version:', fakenews_br_data.__version__)"

# Test CLI
fakenews-br-data --help
```

## Next Steps for Distribution

### Using uv (recommended)

#### 1. Build the package

```bash
# Build with uv (creates wheel and sdist)
uv build

# Preview version update before publishing
uv version --dry-run

# Update version (e.g., bump to 0.2.0)
uv version 0.2.0

# Or bump semantically
uv version --bump minor  # 0.1.0 -> 0.2.0
uv version --bump patch  # 0.1.0 -> 0.1.1
```

#### 2. Test on TestPyPI

First, configure TestPyPI in pyproject.toml (add this section):

```toml
[[tool.uv.index]]
name = "testpypi"
url = "https://test.pypi.org/simple/"
publish-url = "https://test.pypi.org/legacy/"
explicit = true
```

Then publish:

```bash
# Publish to TestPyPI (requires TestPyPI API token)
uv publish --index testpypi

# Or set token via environment variable
UV_PUBLISH_TOKEN=your_testpypi_token uv publish --index testpypi
```

#### 3. Install from TestPyPI to test

```bash
uv pip install --index-url https://test.pypi.org/simple/ fakenews-br-data
```

#### 4. Publish to PyPI (when ready)

```bash
# Publish to PyPI (requires PyPI API token)
uv publish

# Or set token via environment variable  
UV_PUBLISH_TOKEN=your_pypi_token uv publish

# For GitHub Actions with Trusted Publisher, no token needed
# Just add trusted publisher to PyPI project settings
```

### Using pip/twine (traditional)

#### 1. Build and test on TestPyPI

```bash
# Build package
python -m build

# Install twine
pip install twine

# Upload to TestPyPI
python -m twine upload --repository testpypi dist/*
```

#### 2. Install from TestPyPI to test

```bash
pip install --index-url https://test.pypi.org/simple/ fakenews-br-data
```

#### 3. Upload to PyPI (when ready)

```bash
python -m twine upload dist/*
```

## Key Features Implemented

✅ Standard PyPA src/ layout
✅ Hatchling build backend
✅ Both library API and CLI
✅ Configuration via JSON files
✅ All notebook functionality refactored into modules:
  - Dataset downloading (HuggingFace, Zenodo, URLs, Local)
  - Schema normalization
  - Text cleaning and preprocessing
  - Near-duplicate detection (MinHash LSH)
  - Google Fact Check API integration
  - Complete pipeline orchestration

✅ Type hints throughout
✅ Proper documentation
✅ MIT License
✅ Built and ready for distribution

## Development Commands

### Using uv

```bash
# Rebuild package after changes
uv build

# Check that build works without tool.uv.sources (recommended before publishing)
uv build --no-sources

# Run linter (if configured)
uv run ruff check src/

# Format code (if configured)
uv run black src/

# Run tests
uv run pytest

# Update version
uv version --bump patch
```

### Using traditional tools

```bash
# Rebuild package after changes
python -m build

# Run linter (if configured)
ruff check src/

# Format code (if configured)
black src/

# Run tests
pytest
```

## Package Metadata

- Name: `fakenews-br-data`
- Version: `0.1.0`
- Python: `>=3.9`
- License: MIT
- Entry Point: `fakenews-br-data` (CLI command)

## Public API

The following are exported from `fakenews_br_data`:

- `Pipeline` - Main orchestration class
- `DatasetCleaner` - Text cleaning and preprocessing
- `DuplicateDetector` - Near-duplicate detection
- `FactChecker` - Google Fact Check integration
- `load_config`, `save_config` - Configuration management
- `ensure_schema`, `normalize_date` - Schema utilities
- `HuggingFaceDownloader`, `ZenodoDownloader`, `URLDownloader`, `LocalFileLoader` - Downloaders

## Support

For issues and questions, see the repository README or create an issue on GitHub.

