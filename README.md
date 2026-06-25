# fakenews-br-data

A *framework* for collecting, processing, and analyzing misinformation *datasets* focused on the Brazilian context:

* Library and command-line interface
* Text data cleaning and preprocessing (URL removal, emoji removal, accent normalization)
* Near-duplicate content detection using MinHash LSH
* Integration with the Google Fact Check API for verification

## Installation

```bash
pip install git+https://github.com/Vrt-sources/fakenews-data
```

**Optional features**

`fakenews-br-data` defines a few installation *extras* in `pyproject.toml`.
They allow you to install optional dependency groups using the following syntax:

```bash
pip install "fakenews-br-data[extra]"
```

There are currently two main extras: `huggingface` and `dev`.

* `fakenews-br-data[huggingface]`: Adds dependencies used in workflows for downloading and integrating datasets hosted on the Hugging Face ecosystem.

  * Installation from PyPI:

    ```bash
    pip install "fakenews-br-data[huggingface]"
    ```
  * Development installation (from a cloned repository):

    ```bash
    pip install -e ".[huggingface]"
    ```

* `fakenews-br-data[dev]`: Includes dependencies intended for project development, such as testing and code-formatting tools.

  * Installation from PyPI:

    ```bash
    pip install "fakenews-br-data[dev]"
    ```
  * Development installation (from a cloned repository):

    ```bash
    pip install -e ".[dev]"
    ```

## Structure

```text
fakenews-data/
├──  README.md                    # This file - main documentation
├──  LICENSE                      # MIT License
├──  pyproject.toml               # Python package configuration
├──  config.example.json          # Configuration template
├──  src/fakenews_br_data/        # Main source code
│   ├── __init__.py                 # Public package API
│   ├── pipeline.py                 # Main processing pipeline
│   ├── cleaning.py                 # Text cleaning and preprocessing
│   ├── deduplication.py            # Duplicate detection (MinHash LSH)
│   ├── factcheck.py                # Google Fact Check API integration
│   ├── downloaders.py              # Downloaders (HF, Zenodo, URL, Local)
│   ├── schema.py                   # Schema normalization
│   ├── config.py                   # Configuration management
│   ├── utils.py                    # Utility functions
│   └── cli.py                      # Command-line interface
├──  tests/                       # Tests (basic structure)
│   └── __init__.py
├──  Dataset_combinado_adicionado_(Semana_15_09).ipynb  # Original notebook
└──  dist/                        # Distribution files (generated)
    ├── fakenews_br_data-0.1.3-py3-none-any.whl
    └── fakenews_br_data-0.1.3.tar.gz
```

## Quick Start

### Library Usage

```python
from fakenews_br_data import Pipeline, DatasetCleaner

# Complete pipeline
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
# Run the complete pipeline
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
# You can also pass configuration parameters through tags
fakenews-br-data pipeline --tag out_dir=data --tag max_workers=31 --tag factcheck_sleep=1 --tag factcheck_api_key=<API_KEY>
```

## Column Schema and Transformation Flow

`fakenews-br-data` organizes data into three major stages:

1. **Schema normalization** (`schema.ensure_schema` + `Pipeline.normalize_and_merge`)
2. **Text cleaning and filtering** (`DatasetCleaner.clean_dataset`)
3. **Fact-checking enrichment** (`FactChecker.process_dataset`)

The input and output columns for each stage are described below.

### 1.1. Standard Schema (`ensure_schema` / `Pipeline.normalize_and_merge` output)

The `ensure_schema` function receives a raw `DataFrame`, which may contain different column names depending on the dataset, and converts it into a canonical schema. After the normalization and merge stage, the resulting `DataFrame` (for example, `FakenewsBR_merged.csv`) contains at least the following columns:

* **dataset_name** (`str`)
  Canonical name of the source dataset (e.g., `Fake.br`, `COVID19.BR`, `MuMiN-PT`, `FakeWhatsApp.BR_2018`, `LLM4BR_300`, `fake`, `true`).

* **source_type** (`str`)
  Source type used to characterize the origin of the content (e.g., `"news"`, `"whatsapp messages"`, `"tweets"`, etc.).

* **source_description** (`str`)
  Textual description of the dataset or source, usually obtained from the `DATASET_DESCRIPTIONS` dictionary, summarizing what the dataset represents.

* **orig_id** (`str`)
  Original instance identifier in the source dataset, such as a news ID, message ID, or internal corpus ID. It is retained for traceability.

* **text** (`str`)
  Unified main text of the instance. Depending on the dataset, it may be:

  * the original text field itself, or
  * the concatenation of title and body when they are stored in separate columns.

* **label** (`str`)
  Veracity label defined by the source dataset, typically mapped to values such as `"fake"` and `"true"`. Other labels may exist depending on the original corpus.

* **url_claim** (`str` or null)
  URL associated with the original news article, tweet, or message—the source of the claim. Not all datasets provide this field.

* **url_review** (`str` or null)
  URL pointing to the associated fact-checking result, when the dataset already includes fact-check links. It may be completely absent in some datasets.

* **date_iso** (`str` in `YYYY-MM-DD` format or null)
  Instance date normalized into an ISO-friendly format. The function attempts to extract and normalize dates from different columns and formats in the original dataset.

In addition, after `assign_uids` is called within the `Pipeline`:

* **uid** (`int`)
  Global sequential identifier created by `assign_uids`, ensuring a unique ID for each row across all merged datasets.

In specific cases, the pipeline may also add:

* **tweet_id** (`str` or null)
  For datasets originating from X/Twitter, this value may be extracted from `url_claim` using `extract_tweet_id`. It remains empty for instances without a tweet URL.

Other dataset-specific columns may remain unchanged and are preserved even when they are not required by the main workflow.

### 1.2. `DatasetCleaner.clean_dataset` Output

The cleaning stage generally operates on the merged file (`FakenewsBR_merged.csv`) generated by the `Pipeline` and produces a cleaned file (`FakenewsBR_clean.csv` / `FakenewsBR_clean.parquet`).

**Expected input:**

* The standard columns described in section 1.1 (**dataset_name**, **source_type**, **source_description**, **orig_id**, **text**, **label**, **url_claim**, **url_review**, **date_iso**, **uid**, and optionally **tweet_id**).
* Dataset-specific columns may also be present, but they are not required.
* An optional **language** column may appear in some datasets; it is removed during cleaning.

**New and transformed output columns:**

* **text_no_url** (`str`)
  Version of `text` with URLs removed, retaining only the textual content.

* **extracted_urls** (serialized list or `str`)
  URLs extracted from the original text. Useful for later analysis or context reconstruction.

* **text_clean** (`str`)
  Standardized text for fact-checking and NLP models. It includes:

  * URL removal through `text_no_url`,
  * accent normalization,
  * emoji removal,
  * removal of surrounding quotation marks and redundant whitespace.

* **is_duplicated** (`bool`)
  Indicates duplicate textual content, computed from `text_clean`:

  * by `dataset_name`, when that column is available, or
  * globally, when `dataset_name` is unavailable.

* **is_null** (`bool`)
  Flags instances where `text_clean` is missing or null.

* **too_short** (`bool`)
  Flags instances where `text_clean` has fewer tokens than the configured minimum (`min_tokens`), which defaults to 3.

The filtered output (**clean DataFrame**) contains only rows where:

* `is_null == False`
* `is_duplicated == False`
* `too_short == False`

It retains the canonical columns:

* **dataset_name**, **source_type**, **source_description**
* **label**, **date_iso**, **orig_id**, **tweet_id** (when available)
* **url_claim**, **url_review**, **text**, **text_clean**

as well as any additional columns present in the dataset, such as `uid`, auxiliary flags, and others.

### 1.3. `FactChecker.process_dataset` Output

The fact-checking stage generally receives the cleaned file (`FakenewsBR_clean.csv`) and produces an enriched file (`FakenewsBR_factchecked.csv`).

**Expected input:**

* It must contain at least:

  * **orig_id** (`str`): used to track the original instance.
  * **text** (`str`): claim text sent to the Fact Check API.
* Ideally, it uses the same schema produced by `DatasetCleaner.clean_dataset`, retaining all standard columns such as dataset information, labels, and dates.

**Output columns added:**

For each row, a request is made to the Google Fact Check Tools API using the content of `text`. The result is added as new columns:

* **factcheck_rating** (`str` or null)
  Textual rating returned by the API, such as terms equivalent to “True,” “False,” or “Misleading,” depending on the fact-checking provider.

* **factcheck_claimant** (`str` or null)
  Name of the entity or person associated with the claim in the fact-checking database.

* **factcheck_url** (`str` or null)
  URL of the fact-checking page used as a reference for that instance.

All other input columns are preserved.
When no fact-checking result is available for a given text, the `factcheck_*` columns are set to `None` or left empty for that row.

---

## Dataset Sources

This framework supports the following Brazilian Portuguese datasets:

* [**MuMiN-PT**](https://huggingface.co/datasets/ju-resplande/portuguese-fact-checking): Portuguese subset of MuMiN, built using a top-down approach from claims previously verified by fact-checking agencies, followed by the mapping of X/Twitter posts from 2020 to 2022.

* [**COVID19.BR**](https://huggingface.co/datasets/ju-resplande/portuguese-fact-checking): A corpus of Brazilian Portuguese WhatsApp messages about COVID-19, collected from 236 groups between April and June 2020. It was built using a bottom-up approach based on content verified by fact-checking agencies.

* [**Fake.br**](https://huggingface.co/datasets/ju-resplande/portuguese-fact-checking): A corpus of Brazilian news articles containing aligned pairs of fake and true texts, collected from the web between January 2016 and January 2018. Samples were paired through lexical similarity to ensure thematic alignment between fake and true versions.

* [**FakeTweetBr**](https://github.com/prc992/FakeTweet.Br): A corpus of Brazilian Portuguese tweets labeled as fake or true, created for studies on automated rumor verification and fake-news classification in social media. The dataset was compiled from Twitter posts covering a wide range of public-interest topics.

* [**FakeWhatsAppBR**](https://github.com/cabrau/FakeWhatsApp.Br): An annotated and anonymized corpus of public Brazilian Portuguese WhatsApp messages, created for studies on automated textual misinformation detection and malicious-user identification. The dataset was compiled from public groups during the 2018 Brazilian presidential election.

* [**Fake news in Portuguese**](https://www.kaggle.com/datasets/fabioselau/fakes-news-portuguese): A corpus of Brazilian Portuguese news articles labeled as fake or true, published on Kaggle. The dataset was built from news collected online between 2005 and 2022 and organized into two files: `fake.csv` and `true.csv`.

* [**LLM4BrazilianFakeNews**](https://github.com/GoloMarcos/LLM4BrazilianFakeNews): A corpus of Brazilian political news created to evaluate the performance of large language models (LLMs), both open-source and proprietary, in detecting textual misinformation. The dataset was proposed in a study investigating the effectiveness of LLMs in identifying fake news about national politics, highlighting the potential of open models as alternatives to commercial ones.

## Public API

### Main Classes

* `Pipeline` - Main orchestration for the complete pipeline
* `DatasetCleaner` - Text cleaning and preprocessing
* `DuplicateDetector` - Near-duplicate content detection
* `FactChecker` - Google Fact Check API integration

### Downloaders

* `HuggingFaceDownloader` - Downloads datasets from Hugging Face
* `ZenodoDownloader` - Downloads datasets from Zenodo
* `URLDownloader` - Downloads files through a URL
* `LocalFileLoader` - Loads local files

### Utilities

* `load_config`, `save_config` - Configuration management
* `ensure_schema`, `normalize_date` - Schema utilities
* `sha256`, `download_to` - General utility functions
