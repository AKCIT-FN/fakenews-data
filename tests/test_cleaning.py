import pandas as pd

from fakenews_br_data.cleaning import (
    remove_outer_quotes,
    normalize_accents,
    normalize_spaces,
    clean_for_factcheck,
    DatasetCleaner,
)


def test_clean_for_factcheck_pipeline():
    """clean_for_factcheck should apply the expected normalization pipeline."""
    raw = '  "Olá, MúndO!!!"  '
    cleaned = clean_for_factcheck(raw)

    # No accents, lowercase, no duplicate spaces, no outer quotes
    assert "á" not in cleaned and "ú" not in cleaned
    assert cleaned == "Olá, Mundo!!!"


def test_remove_outer_quotes():
    """remove_outer_quotes deve remover aspas externas apenas, mantendo conteúdo interno."""
    assert remove_outer_quotes('"texto"') == "texto"
    assert remove_outer_quotes("'texto'") == "texto"
    # Without outer quotes, it should remain unchanged (except for trimming surrounding spaces)
    assert remove_outer_quotes("  texto  ") == "texto"


def test_normalize_accents_basic():
    """normalize_accents should remove accents, but keep other characters."""
    s = "Olá, ação, informação!"
    norm = normalize_accents(s)
    assert norm == "Ola, acao, informacao!"


def test_normalize_spaces():
    """normalize_spaces should collapse multiple spaces and line breaks."""
    s = "texto   com   espaços \n\n extras"
    norm = normalize_spaces(s)
    assert norm == "texto com espaços extras"


def test_dataset_cleaner_filters_and_generates_columns(tmp_path):
    """
    DatasetCleaner.clean_dataset should:
    - filter invalid labels;
    - remove null/short texts;
    - create text_no_url and text_clean columns;
    - preserve canonical columns when present.
    """
    input_csv = tmp_path / "merged.csv"

    df_in = pd.DataFrame(
        {
            "dataset_name": ["D1", "D1", "D1", "D1"],
            "source_type": ["news"] * 4,
            "source_description": ["Teste"] * 4,
            "orig_id": ["1", "2", "3", "4"],
            "text": [
                "Notícia falsa sobre algo http://exemplo.com/a",
                "Notícia verdadeira sobre algo http://exemplo.com/b",
                "Linha com label inválido",
                "Muito curta",
            ],
            "label": ["falso", "verdadeiro", "none", "fake"],
            "date_iso": ["2024-01-10"] * 4,
        }
    )
    df_in.to_csv(input_csv, index=False)

    cleaner = DatasetCleaner(min_tokens=2)
    out_csv = tmp_path / "clean.csv"
    out_parquet = tmp_path / "clean.parquet"

    df_clean = cleaner.clean_dataset(
        path=str(input_csv),
        save_csv=str(out_csv),
        save_parquet=str(out_parquet),
    )

    # Should save the files
    assert out_csv.exists()
    assert out_parquet.exists()

    # Should have filtered the row with invalid label ("none")
    assert set(df_clean["label"].unique()) <= {"fake", "true"}
    assert "none" not in df_clean["label"].astype(str).tolist()

    # Should have removed the short text ("Muito curta") given min_tokens=2
    assert not (df_clean["orig_id"] == "4").any()

    # Clean text columns should exist
    assert "text_no_url" in df_clean.columns
    assert "text_clean" in df_clean.columns

    # text_no_url should not contain the original URLs
    for t in df_clean["text_no_url"].astype(str):
        assert "http://" not in t and "https://" not in t
