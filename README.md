# fakenews-br-data

_Framework_ para coleta, processamento e análise de _datasets_ de desinformação com enfoque no contexto brasileiro:


- Interface de biblioteca e linha de comando
- Limpeza e pré-processamento de dados de texto (remover URLs, emojis, normalizar acentos)
- Detecção de conteúdo quase-duplicado usando MinHash LSH
- Integração com Google Fact Check API para verificação

## Instalação

```bash
pip install git+https://github.com/Vrt-sources/fakenews-data
```

**Funcionalidades extras**
- `fakenews-br-data[huggingface]`: <mark>Explicar o que é </mark>
- - `fakenews-br-data[dev]`: <mark>Explicar o que é </mark>


## Estrutura

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
```

```bash
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

```bash
# Caso queira passar os parâmetros do config por tags
fakenews-br-data pipeline  --tag out_dir=data  --tag max_workers=31  --tag factcheck_sleep=1   --tag factcheck_api_key= <API_KEY> 
```

## Fontes de Datasets

Este framework suporta os seguintes conjuntos de dados em português brasileiro:

<mark> Melhorar descrição dos datasets e incluir link </mark>

- [**MuMiN-PT**](https://huggingface.co/datasets/ju-resplande/portuguese-fact-checking): Subconjunto português do MuMiN, foi montado por abordagem top-down: começando de alegações já verificadas por agências de fact-checking e, então, mapeando os posts do X/Twitter (2020–2022).
  
  Tarefa e rótulos
  - Tarefa: classificação de veracidade/misinformation em texto curto (tweets).
  - Distribuição de classes: ~1.404 instâncias (≈ 1.339 vs 65 na tabela do card), com forte desbalanceamento — a classe minoritária são as verdadeiras após o filtro para PT, o que motivou inclusive a exclusão do MuMiN-PT de alguns experimentos no estudo.

  Esquema (versão “clean” do MuMiN-PT)
  - Campos visíveis no viewer do dataset específico ju-resplande/MuMiN-PT (1.4k linhas, split único “train” + máscaras):
    - id (int64)
    - claim (string, PT)
    - claim_en (string, EN – tradução do enunciado)
    - verdict (string, 2 classes)
    - train_mask, val_mask, test_mask (booleanos) – máscaras para reconstruir partições. 

  Estatísticas pós limpeza
  - Tamanho médio do texto (palavras): ~18.9 (misinfo) / 16.9 (verdadeiro).
  - Presença de URL: ~0.3% (misinfo) / 0.0% (verdadeiro).
  - Período: 2020–2022.

- [**COVID19.BR**](https://huggingface.co/datasets/ju-resplande/portuguese-fact-checking): Fact-checks e notícias sobre COVID-19: Corpus de mensagens de WhatsApp sobre Covid-19 em PT-BR, coletado em 236 grupos públicos entre abril–junho/2020. Abordagem bottom-up.

  Tarefa e rótulos
  - Classificação binária (label: fake/true). 1.99k linhas no split “train” do viewer. Distribuição após limpeza: 848 falsas / 1.139 verdadeiras.

  Esquema
  - Texto: text_no_url.
  - Rótulos e splits: label, new_split (3 valores; use para reconstruir train/val/test).
  - Evidências externas: initial_query, claim_query, google_search_results (lista), google_fact_check_results (dict).
  - Qualidade/duplicatas: near_duplicates (lista), text_urls (lista), metadata (dict).

  Estatísticas úteis (pós-limpeza, do card)
  - % com URL: 28,9% nas falsas / 56,9% nas verdadeiras.
  - Comprimento médio (palavras): 167,7 falsas / 111,1 verdadeiras.
  - Ano: 2020. Domínio: Saúde.

- [**Fake.br**](https://huggingface.co/datasets/ju-resplande/portuguese-fact-checking): Corpus de notícias brasileiras com pares alinhados de textos falsos e verdadeiros, coletados na web e pareados por similaridade lexical. Período alvo: jan/2016–jan/2018.

  Tarefa e rótulos:
  - Tarefa: classificação binária de veracidade em notícias longas. 
  - Balanceamento: equilibrado 50/50 no “clean” (3.580/3.580).

  Esquema no pacote combinado (clean)
  - Colunas expostas no viewer do dataset combinado incluem, entre outras: text_no_url, label (fake/true), old_split, new_split, text_urls, near_duplicates, google_search_results, google_fact_check_results, metadata. Algumas podem estar vazias dependendo da instância.
  - Estatísticas agregadas para Fake.Br: média de palavras ~181,4 (falsas) / 183,1 (verdadeiras).


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

## Citação

Se você usar este framework em sua pesquisa, por favor cite:

```
@software{fakenews_br_data,
  title = {fakenews-br-data: Brazilian Fake News Dataset Framework},
  authors = {Fabrycio Leite Nakano Almada, Kauan Divino Pouso Mariano, Maykon Adriell Dutra,  Victor Emanuel da Silva Monteiro, Juliana Resplande Sant'Anna Gomes},
  year = {2025},
  url = {https://github.com/Vrt-sources/fakenews-data}
}
```

## Agradecimentos

This work has been fully funded by the project "Computational Techniques for Multimodal Data Security and Privacy" supported by the Advanced Knowledge Center in Immersive Technologies (AKCIT), with financial resources from the PPI IoT/Manufatura 4.0 / PPI HardwareBR of the MCTI grant number 057/2023, signed with EMBRAPII.

