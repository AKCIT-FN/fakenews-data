import pandas as pd

from fakenews_br_data.schema import ensure_schema, assign_uids


def test_ensure_schema_basic_mapping():
    """ensure_schema deve mapear colunas básicas e normalizar label/data."""
    df_raw = pd.DataFrame(
        {
            "id": [1, 2],
            "texto": ["Notícia falsa", "Notícia verdadeira"],
            "classificacao": ["falso", "verdadeiro"],
            "data": ["2024-01-10", "10/01/2024"],
            "url": ["http://exemplo.com/a", "http://exemplo.com/b"],
        }
    )

    out = ensure_schema(
        df_raw,
        dataset_name="Fake.br",
        source_type="news",
        source_description="Teste unitário Fake.br",
    )

    # Colunas obrigatórias
    for col in [
        "orig_id",
        "text",
        "label",
        "url_claim",
        "url_review",
        "date_iso",
        "dataset_name",
        "source_type",
        "source_description",
    ]:
        assert col in out.columns, f"Coluna obrigatória ausente: {col}"

    # Dataset metadata
    assert (out["dataset_name"] == "Fake.br").all()
    assert (out["source_type"] == "news").all()
    assert (out["source_description"] == "Teste unitário Fake.br").all()

    # Mapeamento de texto e label
    assert out.loc[0, "text"] == "Notícia falsa"
    assert out.loc[1, "text"] == "Notícia verdadeira"
    assert set(out["label"].unique()) == {"fake", "true"}

    # Normalização de data -> ISO
    assert out.loc[0, "date_iso"] == "2024-01-10"
    assert out.loc[1, "date_iso"] == "2024-01-10"


def test_assign_uids_sequential():
    """assign_uids deve criar uids sequenciais e únicos entre múltiplos DataFrames."""
    df1 = pd.DataFrame({"orig_id": ["a", "b"], "text": ["t1", "t2"]})
    df2 = pd.DataFrame({"orig_id": ["c"], "text": ["t3"]})

    dfs_with_uid = assign_uids([df1, df2])

    assert len(dfs_with_uid) == 2
    uids = pd.concat(dfs_with_uid)["uid"].tolist()

    # Deve começar em 1 e ser sequencial
    assert uids == [1, 2, 3]
    assert len(set(uids)) == 3