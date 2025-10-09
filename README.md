# fakenews-br-data

Kit de ferramentas para coleta, processamento e análise de datasets de fake news brasileiras.

Este pacote fornece ferramentas para coletar, normalizar, limpar e analisar datasets de fake news em português brasileiro de múltiplas fontes, incluindo HuggingFace, Zenodo e arquivos locais.

## Características

- Download de datasets de múltiplas fontes (HuggingFace, Zenodo, GitHub, arquivos locais)
- Normalização de esquemas entre diferentes formatos de dataset
- Limpeza e pré-processamento de dados de texto (remover URLs, emojis, normalizar acentos)
- Detecção de conteúdo quase-duplicado usando MinHash LSH
- Integração com Google Fact Check API para verificação
- Interface de biblioteca e linha de comando

## Instalação

### Do TestPyPI (atual)

```bash
# Usando pip
pip install --index-url https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple/ fakenews-br-data

# Usando uv (recomendado)
uv pip install --index-url https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple/ fakenews-br-data
```

### Do PyPI (quando publicado)

```bash
# Usando pip
pip install fakenews-br-data

# Usando uv (recomendado)
uv pip install fakenews-br-data
```

### Do GitHub (método atual)

```bash
# Usando pip
pip install git+https://github.com/kauandivino/fakenews-data.git

# Usando uv (recomendado)
uv pip install git+https://github.com/kauandivino/fakenews-data.git
```

### Para desenvolvimento com suporte ao HuggingFace:

```bash
# Do TestPyPI (atual)
pip install --index-url https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple/ "fakenews-br-data[huggingface]"
uv pip install --index-url https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple/ "fakenews-br-data[huggingface]"

# Do PyPI (quando publicado)
pip install fakenews-br-data[huggingface]
uv pip install fakenews-br-data[huggingface]

# Do GitHub (atual)
pip install "git+https://github.com/kauandivino/fakenews-data.git#egg=fakenews-br-data[huggingface]"
uv pip install "git+https://github.com/kauandivino/fakenews-data.git#egg=fakenews-br-data[huggingface]"
```

## Início Rápido

### Uso da Biblioteca

```python
from fakenews_br_data import Pipeline, DatasetCleaner

# Pipeline completo
pipeline = Pipeline(config_path="config.json")
pipeline.download()
pipeline.process()
df_clean = pipeline.clean()

# Ou usar componentes individuais
from fakenews_br_data import DatasetCleaner, DuplicateDetector, FactChecker

cleaner = DatasetCleaner(min_tokens=5)
df_clean = cleaner.clean_dataset("input.csv", "output_clean.csv")

detector = DuplicateDetector(threshold=0.7)
duplicates = detector.find_near_duplicates(texts)

checker = FactChecker(api_key="SUA_CHAVE")
results = checker.check_claims(df)
```

### Uso da CLI

```bash
# Executar pipeline completo
fakenews-br-data pipeline --config config.json --output ./data

# Comandos individuais
fakenews-br-data clean --input merged.csv --output clean.csv
fakenews-br-data factcheck --input clean.csv --config config.json
```

## Configuração

Crie um arquivo `config.json` com suas configurações:

```json
{
  "factcheck_api_key": "SUA_CHAVE_API_GOOGLE_FACTCHECK",
  "out_dir": "data",
  "max_workers": 31,
  "factcheck_sleep": 1
}
```

Veja `config.example.json` para um template.

## Fontes de Datasets

Este kit de ferramentas suporta múltiplos datasets de fake news em português brasileiro:

- **MuMiN-PT**: Subconjunto português do MuMiN (Multimodal Misinformation)
- **COVID19.BR**: Fact-checks e notícias sobre COVID-19
- **Fake.br**: Dataset Fake.br processado
- **FakeTweetBr**: Tweets em português rotulados
- **FakeWhatsAppBR**: Mensagens do WhatsApp de 2018
- **Datasets do Kaggle**: Coleções de notícias verdadeiras e falsas
- **LLM4BR**: 300 artigos de notícias filtrados

## Desenvolvimento

### Usando uv (recomendado)

```bash
git clone https://github.com/kauandivino/fakenews-data.git
cd fakenews-data

# Instalar uv se ainda não tiver
curl -LsSf https://astral.sh/uv/install.sh | sh

# Instalar em modo de desenvolvimento
uv pip install -e .[dev]

# Build do pacote
uv build

# Publicar no PyPI (requer token do PyPI)
uv publish
```

### Usando pip

```bash
git clone https://github.com/kauandivino/fakenews-data.git
cd fakenews-data
pip install -e .[dev]
```

## Licença

Licença MIT - veja arquivo LICENSE para detalhes.

## Citação

Se você usar este kit de ferramentas em sua pesquisa, por favor cite:

```
@software{fakenews_br_data,
  title = {fakenews-br-data: Brazilian Fake News Dataset Toolkit},
  author = {Victor Emanuel},
  year = {2025},
  url = {https://github.com/kauandivino/fakenews-data}
}
```

## Agradecimentos

Este kit de ferramentas agrega e processa datasets de múltiplas fontes. Por favor, cite os autores originais dos datasets ao usar seus dados.
