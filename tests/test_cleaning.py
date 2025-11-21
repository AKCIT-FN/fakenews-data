import pandas as pd

from fakenews_br_data.cleaning import (
    remove_outer_quotes,
    normalize_accents,
    normalize_spaces,
    clean_for_factcheck,
    DatasetCleaner,
)


def test_clean_for_factcheck_pipeline():
    """clean_for_factcheck deve aplicar a sequência de normalização esperada."""
    raw = '  "Olá, MúndO!!!"  '
    cleaned = clean_for_factcheck(raw)

    # Sem acentos, minúsculas, sem espaços duplicados, sem aspas externas
    assert "á" not in cleaned and "ú" not in cleaned
    assert cleaned == "ola, mundo!!!"


def test_remove_outer_quotes():
    """remove_outer_quotes deve remover aspas externas apenas, mantendo conteúdo interno."""
    assert remove_outer_quotes('"texto"') == "texto"
    assert remove_outer_quotes("'texto'") == "texto"
    # Sem aspas externas, deve permanecer igual (tirando espaços extremos)
    assert remove_outer_quotes("  texto  ") == "texto"


def test_normalize_accents_basic():
    """normalize_accents deve remover acentos, mas manter demais caracteres."""
    s = "Olá, ação, informação!"
    norm = normalize_accents(s)
    assert norm == "Ola, acao, informacao!"


def test_normalize_spaces():
    """normalize_spaces deve colapsar múltiplos espaços e quebras de linha."""
    s = "texto   com   espaços \n\n extras"
    norm = normalize_spaces(s)
    assert norm == "texto com espaços extras"


def test_dataset_cleaner_filters_and_generates_columns(tmp_path):
    """
    DatasetCleaner.clean_dataset deve:
    - filtrar labels inválidos;
    - remover textos nulos/curtos;
    - criar colunas text_no_url e text_clean;
    - preservar as colunas canônicas quando presentes.
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

    # Deve salvar os arquivos
    assert out_csv.exists()
    assert out_parquet.exists()

    # Deve ter filtrado a linha com label inválido ("none")
    assert set(df_clean["label"].unique()) <= {"fake", "true"}
    assert "none" not in df_clean["label"].astype(str).tolist()

    # Deve ter removido texto muito curto ("Muito curta") dado min_tokens=2
    assert not (df_clean["orig_id"] == "4").any()

    # Colunas de texto limpo devem existir
    assert "text_no_url" in df_clean.columns
    assert "text_clean" in df_clean.columns

    # text_no_url não deve conter as URLs originais
    for t in df_clean["text_no_url"].astype(str):
        assert "http://" not in t and "https://" not in t
