import pandas as pd

from fakenews_br_data.factcheck import FactChecker


def test_check_claim_empty_text_returns_nones():
    """check_claim deve retornar campos None quando o texto é vazio ou inválido."""
    fc = FactChecker(
        api_key="DUMMY",
        max_workers=1,
        max_inflight=1,
        show_progress_bar=False,
    )

    res = fc.check_claim("")
    assert res["factcheck_rating"] is None
    assert res["factcheck_claimant"] is None
    assert res["factcheck_url"] is None

    res_none = fc.check_claim(None)
    assert res_none["factcheck_rating"] is None
    assert res_none["factcheck_claimant"] is None
    assert res_none["factcheck_url"] is None


def test_run_factcheck_and_join_with_sqlite(monkeypatch, tmp_path):
    """
    Testa o fluxo run_factcheck_streaming + join_with_sqlite usando um stub
    de check_claim, sem chamadas reais à API externa.
    """
    input_csv = tmp_path / "input.csv"
    df_in = pd.DataFrame(
        {
            "orig_id": ["1", "2"],
            "text": ["Texto 1 de teste", "Texto 2 de teste"],
        }
    )
    df_in.to_csv(input_csv, index=False)

    fc = FactChecker(
        api_key="DUMMY",
        max_workers=2,
        max_inflight=2,
        show_progress_bar=False,
    )

    # Stub de check_claim para evitar chamada HTTP real
    def fake_check_claim(self, text):
        suffix = text.split()[-1]  # "teste"
        return {
            "factcheck_rating": f"rating_{suffix}",
            "factcheck_claimant": "claimant_stub",
            "factcheck_url": f"http://example.org/{suffix}",
        }

    monkeypatch.setattr(FactChecker, "check_claim", fake_check_claim, raising=True)

    tmp_dir = tmp_path / "tmp"
    tmp_dir.mkdir()

    # 1) Streaming: gera factcheck_tmp.csv
    tmp_csv = fc.run_factcheck_streaming(str(input_csv), str(tmp_dir))
    tmp_df = pd.read_csv(tmp_csv)

    # Verifica colunas e número de linhas
    assert set(tmp_df.columns) == {
        "rid",
        "orig_id",
        "factcheck_rating",
        "factcheck_claimant",
        "factcheck_url",
    }
    assert len(tmp_df) == 2

    # 2) JOIN com o dataset original via SQLite
    output_csv = tmp_path / "output.csv"
    fc.join_with_sqlite(str(input_csv), tmp_csv, str(output_csv), str(tmp_dir))

    out_df = pd.read_csv(output_csv)

    # Deve preservar as colunas originais
    for col in ["orig_id", "text"]:
        assert col in out_df.columns

    # Deve adicionar colunas de fact-check
    for col in ["factcheck_rating", "factcheck_claimant", "factcheck_url"]:
        assert col in out_df.columns
        assert out_df[col].notna().all()

    # Ordem dos orig_id deve ser preservada
    assert out_df["orig_id"].astype(str).tolist() == ["1", "2"]
