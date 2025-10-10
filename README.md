# fakenews-br-data

Framework para coleta, processamento e análise de datasets de fake news brasileiras.

Este pacote fornece ferramentas para coletar, normalizar, limpar e analisar datasets de fake news em português brasileiro de múltiplas fontes, incluindo HuggingFace, Zenodo e arquivos locais.

## Características

- Download de datasets de múltiplas fontes (HuggingFace, Zenodo, GitHub, arquivos locais)
- Normalização de esquemas entre diferentes formatos de dataset
- Limpeza e pré-processamento de dados de texto (remover URLs, emojis, normalizar acentos)
- Detecção de conteúdo quase-duplicado usando MinHash LSH
- Integração com Google Fact Check API para verificação
- Interface de biblioteca e linha de comando

## Instalação

### Instalação básica (recomendada)
```bash
pip install --index-url https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple/ fakenews-br-data
```

### Instalação com funcionalidades extras
```bash
# Com suporte ao Google Drive
pip install --index-url https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple/ "fakenews-br-data[huggingface]"

# Para desenvolvimento (testes, formatação de código)
pip install --index-url https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple/ "fakenews-br-data[dev]"
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
    ├── fakenews_br_data-0.1.3-py3-none-any.whl
    └── fakenews_br_data-0.1.3.tar.gz
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

### Uso da CLI (linha de comando)

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

Este framework suporta múltiplos datasets de fake news em português brasileiro:

- **MuMiN-PT**: Subconjunto português do MuMiN (Multimodal Misinformation)
- **COVID19.BR**: Fact-checks e notícias sobre COVID-19
- **Fake.br**: Dataset Fake.br processado
- **FakeTweetBr**: Tweets em português rotulados
- **FakeWhatsAppBR**: Mensagens do WhatsApp de 2018
- **Datasets do Kaggle**: Coleções de notícias verdadeiras e falsas
- **LLM4BR**: 300 artigos de notícias filtrados

## API Pública

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

## Desenvolvimento

```bash
git clone https://github.com/kauandivino/fakenews-data.git
cd fakenews-data

# Instalar em modo de desenvolvimento
pip install -e .[dev]

# Build do pacote
uv build

# Publicar no PyPI (requer token do PyPI)
uv publish
```

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

## Agradecimentos

Este framework agrega e processa datasets de múltiplas fontes. Por favor, cite os autores originais dos datasets ao usar seus dados.

## Links Úteis

- **GitHub:** https://github.com/kauandivino/fakenews-data
- **TestPyPI:** https://test.pypi.org/project/fakenews-br-data/
- **PyPI:** https://pypi.org/project/fakenews-br-data/ (quando publicado)
