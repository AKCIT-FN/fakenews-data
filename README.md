# fakenews-br-data

_Framework_ for collecting, processing, and analyzing disinformation datasets with a focus on the Brazilian context:

- Library and command-line interface
- Text data cleaning and preprocessing (remove URLs, emojis, normalize accents)
- Near-duplicate content detection using MinHash LSH
- Integration with Google Fact Check API for verification

## Installation

```bash
pip install git+https://github.com/Vrt-sources/fakenews-data
```

**Installation Extras**

`fakenews-br-data` defines some installation *extras* in `pyproject.toml`.  
These allow installing optional sets of dependencies using the following syntax:
```bash
pip install "fakenews-br-data[extra]"
```
Currently, there are two main extras: `huggingface` and `dev`.

- `fakenews-br-data[huggingface]`: Adds dependencies used in download/integration workflows with datasets hosted on the Hugging Face stack.
    - Installation from PyPI:
        ```bash
        pip install "fakenews-br-data[huggingface]"
        ```
    - Development mode installation (from a cloned repository):
        ```bash
        pip install -e ".[huggingface]"
        ```
  
- `fakenews-br-data[dev]`: Groups dependencies focused on project development, such as testing tools and code formatting.
    - Installation from PyPI:
        ```bash
        pip install "fakenews-br-data[dev]"
        ```
    - Development mode installation (from a cloned repository):
        ```bash
        pip install -e ".[dev]"
        ```

## Structure

```
fakenews-data/
├── 📄 README.md                    # This file - main documentation
├── 📄 LICENSE                      # MIT License
├── ⚙️ pyproject.toml               # Python package configuration
├── ⚙️ config.example.json          # Configuration template
├── 📦 src/fakenews_br_data/        # Main source code
│   ├── __init__.py                 # Package public API
│   ├── pipeline.py                 # Main processing pipeline
│   ├── cleaning.py                 # Text cleaning and preprocessing
│   ├── deduplication.py            # Duplicate detection (MinHash LSH)
│   ├── factcheck.py                # Google Fact Check API integration
│   ├── downloaders.py              # Downloaders (HF, Zenodo, URL, Local)
│   ├── schema.py                   # Schema normalization
│   ├── config.py                   # Configuration management
│   ├── utils.py                    # Utility functions
│   └── cli.py                      # Command-line interface
├── 🧪 tests/                       # Tests (basic structure)
│   └── __init__.py
├── 📊 Dataset_combinado_adicionado_(Semana_15_09).ipynb  # Original notebook
└── 📦 dist/                        # Distribution files (generated)
    ├── fakenews_br_data-0.1.3-py3-none-any.whl
    └── fakenews_br_data-0.1.3.tar.gz
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

### CLI (Command Line Interface) Usage

```bash
# Run full pipeline
fakenews-br-data pipeline --config config.json --output ./data
```

```bash
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

See `config.example.json` for a complete template.

```bash
# If you want to pass config parameters via tags
fakenews-br-data pipeline  --tag out_dir=data  --tag max_workers=31  --tag factcheck_sleep=1   --tag factcheck_api_key=<API_KEY> 
```

## Column Schema and Transformation Flow

`fakenews-br-data` organizes data into three major stages:

1. **Schema Normalization** (`schema.ensure_schema` + `Pipeline.normalize_and_merge`)
2. **Text Cleaning and Filtering** (`DatasetCleaner.clean_dataset`)
3. **Fact-checking Enrichment** (`FactChecker.process_dataset`)

Below we describe the input and output columns for each stage.

### 1.1. Standard Schema (output of `ensure_schema` / `Pipeline.normalize_and_merge`)

The `ensure_schema` function receives a raw `DataFrame` (with varying column names depending on the dataset) and converts it to a canonical schema. After the normalization and merge stage, the resulting `DataFrame` (e.g., `FakenewsBR_merged.csv`) contains, at a minimum, the following columns:

- **dataset_name** (`str`)  
  Canonical name of the source dataset (e.g., `Fake.br`, `COVID19.BR`, `MuMiN-PT`, `FakeWhatsApp.BR_2018`, `LLM4BR_300`, `fake`, `true`).

- **source_type** (`str`)  
  Source type, used to characterize the origin of the content (e.g., `"news"`, `"whatsapp messages"`, `"tweets"`, etc.).

- **source_description** (`str`)  
  Textual description of the dataset/source, usually obtained from the `DATASET_DESCRIPTIONS` dictionary, providing a summary of what that set represents.

- **orig_id** (`str`)  
  Original identifier of the instance in the source dataset (e.g., news ID, message ID, internal corpus ID). It is kept as a reference for traceability.

- **text** (`str`)  
  Main text of the unified instance. Depending on the dataset, it may be:
  - the original text field itself, or  
  - the concatenation of title + body (when separated into different columns).

- **label** (`str`)  
  Veracity label as per the source dataset (typically mapped to values like `"fake"` and `"true"`; other labels may exist depending on the original corpus).

- **url_claim** (`str` or null)  
  URL associated with the original news, tweet, or message (the "source" of the claim). Not all datasets have this field.

- **url_review** (`str` or null)  
  URL for the associated fact-check (when the dataset already includes fact-check links). It may be completely absent in some datasets.

- **date_iso** (`str` in `YYYY-MM-DD` format or null)  
  Normalized instance date in a user-friendly ISO format. The function attempts to extract and normalize dates from different columns/formats in the original dataset.

In addition to these, after calling `assign_uids` within the `Pipeline`:

- **uid** (`int`)  
  Global sequential identifier created by `assign_uids`, ensuring a unique ID per row across all merged datasets.

In specific cases, the pipeline may also add:

- **tweet_id** (`str` or null)  
  For datasets originating from X/Twitter, this can be extracted from `url_claim` using `extract_tweet_id`. It remains empty for instances without a tweet URL.

Other specific columns from each dataset may be kept "as they were" and are preserved, even if they are not mandatory for the main flow.

### 1.2. Output of `DatasetCleaner.clean_dataset`

The cleaning stage generally works on the merged file (`FakenewsBR_merged.csv`) generated by the `Pipeline` and produces a clean file (`FakenewsBR_clean.csv` / `FakenewsBR_clean.parquet`).

**Expected Input:**

- The standard columns described in 1.1 (**dataset_name**, **source_type**, **source_description**, **orig_id**, **text**, **label**, **url_claim**, **url_review**, **date_iso**, **uid**, and optionally **tweet_id**).
- Dataset-specific columns may be present but are not mandatory.
- An optional **language** column may appear in some datasets; it is discarded during cleaning.

**New and Transformed Columns in the Output:**

- **text_no_url** (`str`)  
  Version of `text` with URLs removed, preserving only the textual content.

- **extracted_urls** (serialized list or `str`)  
  URLs extracted from the original text. Useful for further analysis or context reconstruction.

- **text_clean** (`str`)  
  Standardized text for use in fact-checking and NLP models. Includes:
  - URL removal (from `text_no_url`),  
  - accent normalization,  
  - emoji removal,  
  - cleaning of outer quotes and redundant spaces.

- **is_duplicated** (`bool`)  
  Textual content duplicate indicator, computed over `text_clean`:
  - by `dataset_name`, when this column is present, or  
  - globally, when there is no `dataset_name`.

- **is_null** (`bool`)  
  Marks instances where `text_clean` is missing or null.

- **too_short** (`bool`)  
  Marks instances where `text_clean` has fewer tokens than the configured minimum (`min_tokens`), default is 3.

The filtered output (**Clean DataFrame**) contains only the rows where:

- `is_null == False`  
- `is_duplicated == False`  
- `too_short == False`  

and maintains the canonical columns:

- **dataset_name**, **source_type**, **source_description**  
- **label**, **date_iso**, **orig_id**, **tweet_id** (when available)  
- **url_claim**, **url_review**, **text**, **text_clean**

as well as any additional columns the user had in the dataset (e.g., `uid`, auxiliary flags, etc.).

### 1.3. Output of `FactChecker.process_dataset`

The fact-checking stage generally receives the clean file (`FakenewsBR_clean.csv`) and produces an enriched file (`FakenewsBR_factchecked.csv`).

**Expected Input:**

- Must contain at least:
  - **orig_id** (`str`): for tracking the original instance.
  - **text** (`str`): the claim text to be sent to the Fact Check API.
- Ideally, it is the same schema produced by `DatasetCleaner.clean_dataset`, maintaining all standard columns (dataset, label, dates, etc.).

**Columns Added to the Output:**

For each row, a query is made to the Google Fact Check Tools API using the content of `text`. The result is appended as new columns:

- **factcheck_rating** (`str` or null)  
  Textual rating returned by the API (e.g., terms equivalent to "True", "False", "Misleading", depending on the checking provider).

- **factcheck_claimant** (`str` or null)  
  Name of the entity or person associated with the claim (claimant) in the fact-check database.

- **factcheck_url** (`str` or null)  
  URL of the fact-check page used as a reference for that instance.

All other input columns are preserved.  
When there is no fact-check result for a given text, the `factcheck_*` columns will be `None`/empty for that row.

---

## Dataset Sources

This framework supports the following datasets in Brazilian Portuguese:

- [**MuMiN-PT**](https://huggingface.co/datasets/ju-resplande/portuguese-fact-checking): A Portuguese subset of MuMiN, built top-down from claims already verified by fact-checking agencies, with subsequent mapping of X/Twitter posts (2020–2022).
  
- [**COVID19.BR**](https://huggingface.co/datasets/ju-resplande/portuguese-fact-checking): A corpus of WhatsApp messages in Brazilian Portuguese about COVID-19, collected from 236 groups between April and June 2020, built using a bottom-up approach from content verified by fact-checking agencies.

- [**Fake.br**](https://huggingface.co/datasets/ju-resplande/portuguese-fact-checking): A corpus of Brazilian news with aligned pairs of fake and true texts, collected from the web between January 2016 and January 2018. Samples were paired by lexical similarity, ensuring thematic correspondence between fake and true versions.

- [**FakeTweetBr**](https://github.com/prc992/FakeTweet.Br): A corpus of Brazilian Portuguese tweets labeled as fake or true, created for studies on automatic rumor verification and fake news classification on social media. The set was compiled from Twitter posts, reflecting various topics of public interest.

- [**FakeWhatsAppBR**](https://github.com/cabrau/FakeWhatsApp.Br): An annotated and anonymized corpus of public WhatsApp messages in Brazilian Portuguese, created for studies on automatic textual disinformation detection and malicious user identification. The set was compiled during the 2018 Brazilian presidential elections from public groups.

- [**Fake news in Portuguese**](www.kaggle.com/datasets/fabioselau/fakes-news-portuguese): A corpus of news in Brazilian Portuguese labeled as fake or true, published on Kaggle. The set was built from news collected on the web between 2005 and 2022, organized into two files (`fake.csv` and `true.csv`).

- [**LLM4BrazilianFakeNews**](https://github.com/GoloMarcos/LLM4BrazilianFakeNews): A corpus of Brazilian political news created to evaluate the performance of Large Language Models (LLMs)—both open-source and proprietary—in detecting textual disinformation. The set was proposed in a study investigating the effectiveness of LLMs in identifying fake news about national politics, highlighting the potential of open models as an alternative to commercial ones.

## Public API

### Main Classes
- `Pipeline` - Main orchestration of the full pipeline
- `DatasetCleaner` - Text cleaning and preprocessing
- `DuplicateDetector` - Near-duplicate content detection
- `FactChecker` - Google Fact Check API integration

### Downloaders
- `HuggingFaceDownloader` - Download datasets from Hugging Face
- `ZenodoDownloader` - Download datasets from Zenodo
- `URLDownloader` - Download files via URL
- `LocalFileLoader` - Load local files

### Utilities
- `load_config`, `save_config` - Configuration management
- `ensure_schema`, `normalize_date` - Schema utilities
- `sha256`, `download_to` - General utility functions
