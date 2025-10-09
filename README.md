# fakenews-br-data

Brazilian fake news dataset collection, processing, and analysis toolkit.

This package provides tools for collecting, normalizing, cleaning, and analyzing Brazilian Portuguese fake news datasets from multiple sources including HuggingFace, Zenodo, and local files.

## Features

- Download datasets from multiple sources (HuggingFace, Zenodo, GitHub, local files)
- Normalize schemas across different dataset formats
- Clean and preprocess text data (remove URLs, emojis, normalize accents)
- Detect near-duplicate content using MinHash LSH
- Integrate with Google Fact Check API for verification
- Both library API and command-line interface

## Installation

```bash
# Using pip
pip install fakenews-br-data

# Using uv (recommended)
uv pip install fakenews-br-data
```

For development with HuggingFace support:

```bash
# Using pip
pip install fakenews-br-data[huggingface]

# Using uv
uv pip install fakenews-br-data[huggingface]
```

## Quick Start

### Library Usage

```python
from fakenews_br_data import Pipeline, DatasetCleaner

# Full pipeline
pipeline = Pipeline(config_path="config.json")
pipeline.download()
pipeline.process()
df_clean = pipeline.clean()

# Or use individual components
from fakenews_br_data import DatasetCleaner, DuplicateDetector, FactChecker

cleaner = DatasetCleaner(min_tokens=5)
df_clean = cleaner.clean_dataset("input.csv", "output_clean.csv")

detector = DuplicateDetector(threshold=0.7)
duplicates = detector.find_near_duplicates(texts)

checker = FactChecker(api_key="YOUR_KEY")
results = checker.check_claims(df)
```

### CLI Usage

```bash
# Run full pipeline
fakenews-br-data pipeline --config config.json --output ./data

# Individual commands
fakenews-br-data clean --input merged.csv --output clean.csv
fakenews-br-data factcheck --input clean.csv --config config.json
```

## Configuration

Create a `config.json` file with your settings:

```json
{
  "factcheck_api_key": "YOUR_GOOGLE_FACTCHECK_API_KEY",
  "out_dir": "data",
  "max_workers": 31,
  "factcheck_sleep": 1
}
```

See `config.example.json` for a template.

## Dataset Sources

This toolkit supports multiple Brazilian Portuguese fake news datasets:

- **MuMiN-PT**: Portuguese subset of MuMiN (Multimodal Misinformation)
- **COVID19.BR**: COVID-19 fact-checks and news
- **Fake.br**: Processed Fake.br dataset
- **FakeTweetBr**: Labeled Portuguese tweets
- **FakeWhatsAppBR**: WhatsApp messages from 2018
- **Kaggle datasets**: True and fake news collections
- **LLM4BR**: 300 filtered news articles

## Development

### Using uv (recommended)

```bash
git clone https://github.com/kauandivino/fakenews-data.git
cd fakenews-data

# Install uv if you haven't already
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install in development mode
uv pip install -e .[dev]

# Build the package
uv build

# Publish to PyPI (requires PyPI token)
uv publish
```

### Using pip

```bash
git clone https://github.com/kauandivino/fakenews-data.git
cd fakenews-data
pip install -e .[dev]
```

## License

MIT License - see LICENSE file for details.

## Citation

If you use this toolkit in your research, please cite:

```
@software{fakenews_br_data,
  title = {fakenews-br-data: Brazilian Fake News Dataset Toolkit},
  author = {Victor Emanuel},
  year = {2025},
  url = {https://github.com/kauandivino/fakenews-data}
}
```

## Acknowledgments

This toolkit aggregates and processes datasets from multiple sources. Please cite the original dataset authors when using their data.
