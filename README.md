# fakenews-br-data

Framework para coleta, processamento e análise de datasets de fake news.

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

## Estrutura do Projeto

```
fakenews-data/
├── 📄 README.md                    # Este arquivo - documentação principal
├── 📄 LICENSE                      # Licença MIT
├── ⚙️ pyproject.toml               # Configuração do pacote Python
├── ⚙️ config.example.json          # Template de configuração
├── 📦 src/fakenews_br_data/        # Código fonte principal
│   ├── __init__.py                 # API pública do pacote
│   ├── pipeline.py                 # Pipeline principal de processamento
│   ├── cleaning.py                 # Limpeza e pré-processamento de texto
│   ├── deduplication.py            # Detecção de duplicatas (MinHash LSH)
│   ├── factcheck.py                # Integração com Google Fact Check API
│   ├── downloaders.py              # Downloaders (HF, Zenodo, URL, Local)
│   ├── schema.py                   # Normalização de esquemas
│   ├── config.py                   # Gerenciamento de configuração
│   ├── utils.py                    # Funções utilitárias
│   └── cli.py                      # Interface de linha de comando
├── 🧪 tests/                       # Testes (estrutura básica)
│   └── __init__.py
├── 📊 Dataset_combinado_adicionado_(Semana_15_09).ipynb  # Notebook original
└── 📦 dist/                        # Arquivos de distribuição (gerados)
    ├── fakenews_br_data-0.1.1-py3-none-any.whl
    └── fakenews_br_data-0.1.1.tar.gz
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

Veja `config.example.json` para um template completo.

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

## API Pública

O pacote exporta as seguintes classes e funções principais:

### Classes Principais
- `Pipeline` - Orquestração principal do pipeline completo
- `DatasetCleaner` - Limpeza e pré-processamento de texto
- `DuplicateDetector` - Detecção de conteúdo quase-duplicado
- `FactChecker` - Integração com Google Fact Check API

### Downloaders
- `HuggingFaceDownloader` - Download de datasets do HuggingFace
- `ZenodoDownloader` - Download de datasets do Zenodo
- `URLDownloader` - Download de arquivos via URL
- `LocalFileLoader` - Carregamento de arquivos locais

### Utilitários
- `load_config`, `save_config` - Gerenciamento de configuração
- `ensure_schema`, `normalize_date` - Utilitários de esquema
- `sha256`, `download_to` - Funções utilitárias gerais

## Licença

Licença MIT - veja arquivo LICENSE para detalhes.

## Citação

Se você usar este framework em sua pesquisa, por favor cite:

```
@software{fakenews_br_data,
  title = {fakenews-br-data: Brazilian Fake News Dataset Framework},
  author = {Kauan Divino Pouso Mariano, Fabrycio Leite Nakano Almada, Maykon Adriell Dutra,  Victor Emanuel da Silva Monteiro, Juliana Resplande Sant'Anna Gomes},
  year = {2025},
  url = {https://github.com/kauandivino/fakenews-data}
}
```

<<<<<<< HEAD
## Agradecimentos

Este kit de ferramentas agrega e processa datasets de múltiplas fontes. Por favor, cite os autores originais dos datasets ao usar seus dados.

## Links Úteis

- **GitHub:** https://github.com/kauandivino/fakenews-data
- **TestPyPI:** https://test.pypi.org/project/fakenews-br-data/
- **PyPI:** https://pypi.org/project/fakenews-br-data/ (quando publicado)
=======
>>>>>>> efe32677c8f22344fdf9b37acf9de46e701801a9
