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

O `fakenews-br-data` define alguns *extras* de instalação no `pyproject.toml`.  
Eles permitem instalar conjuntos opcionais de dependências usando a sintaxe:
```bash
pip install "fakenews-br-data[extra]"
```
Atualmente existem dois extras principais: `huggingface` e `dev`.

- `fakenews-br-data[huggingface]`: Adiciona dependências usadas em fluxos de trabalho de download/integração com datasets hospedados na stack do Hugging Face.
    - Instalação a partir do PyPI:
        ```bash
        pip install "fakenews-br-data[huggingface]"
        ```
    - Instalação em modo desenvolvimento (a partir do repositório clonado):
        ```bash
        pip install -e ".[huggingface]"
        ```
  
- `fakenews-br-data[dev]`: Agrupa dependências voltadas para desenvolvimento do projeto, como ferramentas de testes e formatação de código.
    - Instalação a partir do PyPI:
        ```bash
        pip install "fakenews-br-data[dev]"
        ```
    - Instalação em modo desenvolvimento (a partir do repositório clonado):
        ```bash
        pip install -e ".[dev]"
        ```


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

## Esquema de colunas e fluxo de transformação

O `fakenews-br-data` organiza os dados em três grandes etapas:

1. **Normalização de esquema** (`schema.ensure_schema` + `Pipeline.normalize_and_merge`)
2. **Limpeza de texto e filtragem** (`DatasetCleaner.clean_dataset`)
3. **Enriquecimento com fact-checking** (`FactChecker.process_dataset`)

Abaixo descrevemos as colunas de entrada e saída em cada etapa.

### 1.1. Esquema padrão (saída de `ensure_schema` / `Pipeline.normalize_and_merge`)

A função `ensure_schema` recebe um `DataFrame` bruto (com nomes de colunas variados, dependendo do dataset) e o converte para um esquema canônico. Após a etapa de normalização e merge, o `DataFrame` resultante (por exemplo, `FakenewsBR_merged.csv`) contém, no mínimo, as colunas:

- **dataset_name** (`str`)  
  Nome canônico do dataset de origem (ex.: `Fake.br`, `COVID19.BR`, `MuMiN-PT`, `FakeWhatsApp.BR_2018`, `LLM4BR_300`, `fake`, `true`).

- **source_type** (`str`)  
  Tipo de fonte, utilizado para caracterizar a origem do conteúdo (ex.: `"news"`, `"whatsapp messages"`, `"tweets"` etc.).

- **source_description** (`str`)  
  Descrição textual do dataset/fonte, normalmente obtida a partir do dicionário `DATASET_DESCRIPTIONS`, com um resumo do que aquele conjunto representa.

- **orig_id** (`str`)  
  Identificador original da instância no dataset de origem (por exemplo, ID de notícia, ID de mensagem, ID interno do corpus). É mantido como referência para rastreabilidade.

- **text** (`str`)  
  Texto principal da instância já unificado. Dependendo do dataset, pode ser:
  - o próprio campo de texto original, ou  
  - a concatenação de título + corpo (quando separados em colunas diferentes).

- **label** (`str`)  
  Rótulo de veracidade conforme o dataset de origem (tipicamente algo mapeado para valores como `"fake"` e `"true"`; outros rótulos podem existir conforme o corpus original).

- **url_claim** (`str` ou nulo)  
  URL associada à notícia, tweet ou mensagem original (a “fonte” da alegação). Nem todos os datasets possuem esse campo.

- **url_review** (`str` ou nulo)  
  URL para a checagem de fatos associada (quando o dataset já inclui links de fact-check). Pode estar completamente ausente em alguns datasets.

- **date_iso** (`str` no formato `YYYY-MM-DD` ou nulo)  
  Data da instância normalizada para um formato ISO amigável. A função tenta extrair e normalizar datas a partir de diferentes colunas/formatos no dataset original.

Além dessas, após a chamada de `assign_uids` dentro do `Pipeline`:

- **uid** (`int`)  
  Identificador sequencial global criado pelo `assign_uids`, garantindo um ID único por linha ao longo de todos os datasets mesclados.

Em casos específicos, o pipeline também pode adicionar:

- **tweet_id** (`str` ou nulo)  
  Para datasets oriundos de X/Twitter, pode ser extraído a partir de `url_claim` usando `extract_tweet_id`. Fica vazio para instâncias sem URL de tweet.

Outras colunas específicas de cada dataset podem ser mantidas “como vieram” e são preservadas, ainda que não sejam obrigatórias para o fluxo principal.

### 1.2. Saída do `DatasetCleaner.clean_dataset`

A etapa de limpeza trabalha, em geral, sobre o arquivo mesclado (`FakenewsBR_merged.csv`) gerado pelo `Pipeline`, e produz um arquivo limpo (`FakenewsBR_clean.csv` / `FakenewsBR_clean.parquet`).

**Entrada esperada:**

- As colunas padrão descritas em 1.1 (**dataset_name**, **source_type**, **source_description**, **orig_id**, **text**, **label**, **url_claim**, **url_review**, **date_iso**, **uid**, opcionalmente **tweet_id**).
- Colunas específicas de cada dataset podem estar presentes, mas não são obrigatórias.
- Uma coluna opcional **language** pode aparecer em alguns datasets; ela é descartada durante a limpeza.

**Colunas novas e colunas transformadas na saída:**

- **text_no_url** (`str`)  
  Versão de `text` com URLs removidas, preservando apenas o conteúdo textual.

- **extracted_urls** (lista serializada ou `str`)  
  URLs extraídas do texto original. Útil para análise posterior ou reconstrução do contexto.

- **text_clean** (`str`)  
  Texto padronizado para uso em fact-checking e modelos de NLP. Inclui:
  - remoção de URLs (a partir de `text_no_url`),  
  - normalização de acentos,  
  - remoção de emojis,  
  - limpeza de aspas externas e espaços redundantes.

- **is_duplicated** (`bool`)  
  Indicador de duplicatas de conteúdo textual, computado sobre `text_clean`:
  - por `dataset_name`, quando essa coluna está presente, ou  
  - globalmente, quando não há `dataset_name`.

- **is_null** (`bool`)  
  Marca instâncias cujo `text_clean` está ausente ou nulo.

- **too_short** (`bool`)  
  Marca instâncias cujo `text_clean` tem menos tokens do que o mínimo configurado (`min_tokens`), por padrão 3.

A saída filtrada (**DataFrame limpo**) contém apenas as linhas onde:

- `is_null == False`  
- `is_duplicated == False`  
- `too_short == False`  

e mantém as colunas canônicas:

- **dataset_name**, **source_type**, **source_description**  
- **label**, **date_iso**, **orig_id**, **tweet_id** (quando existir)  
- **url_claim**, **url_review**, **text**, **text_clean**

bem como quaisquer colunas adicionais que o usuário tenha no dataset (por exemplo, `uid`, flags auxiliares, etc.).

### 1.3. Saída do `FactChecker.process_dataset`

A etapa de fact-checking recebe, em geral, o arquivo limpo (`FakenewsBR_clean.csv`) e produz um arquivo enriquecido (`FakenewsBR_factchecked.csv`).

**Entrada esperada:**

- Deve conter, no mínimo:
  - **orig_id** (`str`): para rastreio da instância original.
  - **text** (`str`): texto da alegação a ser enviado para a API de Fact Check.
- Idealmente, é o mesmo esquema produzido por `DatasetCleaner.clean_dataset`, mantendo todas as colunas padrão (dataset, rótulo, datas, etc.).

**Colunas adicionadas na saída:**

Para cada linha, é feita uma consulta à Google Fact Check Tools API usando o conteúdo de `text`. O resultado é anexado como novas colunas:

- **factcheck_rating** (`str` ou nulo)  
  Avaliação textual retornada pela API (por exemplo, termos equivalentes a “True”, “False”, “Misleading”, dependendo do provedor de checagem).

- **factcheck_claimant** (`str` ou nulo)  
  Nome da entidade ou pessoa associada à alegação (claimant) na base de fact-check.

- **factcheck_url** (`str` ou nulo)  
  URL da página de checagem de fatos utilizada como referência para aquela instância.

Todas as demais colunas da entrada são preservadas.  
Quando não há resultado de fact-check para um determinado texto, as colunas `factcheck_*` vêm como `None`/vazias para aquela linha.

---

## Fontes de Datasets

Este framework suporta os seguintes conjuntos de dados em português brasileiro:

- [**MuMiN-PT**](https://huggingface.co/datasets/ju-resplande/portuguese-fact-checking): Subconjunto em português do MuMiN, construído de forma top-down a partir de alegações já verificadas por agências de fact-checking, com posterior mapeamento de posts do X/Twitter (2020–2022).
  
- [**COVID19.BR**](https://huggingface.co/datasets/ju-resplande/portuguese-fact-checking): Corpus de mensagens de WhatsApp em português brasileiro sobre COVID-19, coletado em 236 grupos entre abril e junho de 2020, construído por abordagem bottom-up a partir de conteúdos verificados por agências de fact-checking.

- [**Fake.br**](https://huggingface.co/datasets/ju-resplande/portuguese-fact-checking): Corpus de notícias brasileiras com pares alinhados de textos falsos e verdadeiros, coletados na web entre janeiro de 2016 e janeiro de 2018. As amostras foram pareadas por similaridade lexical, garantindo correspondência temática entre versões fake e true.

- [**FakeTweetBr**](https://github.com/prc992/FakeTweet.Br): Corpus de tweets em português brasileiro rotulados como falsos ou verdadeiros, criado para estudos de verificação automática de rumores e classificação de notícias falsas em redes sociais. O conjunto foi compilado a partir de publicações no Twitter, refletindo temas variados de interesse público.

- [**FakeWhatsAppBR**](https://github.com/cabrau/FakeWhatsApp.Br): Corpus anotado e anonimizado de mensagens públicas de WhatsApp em português brasileiro, criado para estudos de detecção automática de desinformação textual e identificação de usuários maliciosos. O conjunto foi compilado durante as eleições presidenciais brasileiras de 2018, a partir de grupos públicos.

- [**Fake news in Portuguese**](https://www.kaggle.com/datasets/fabioselau/fakes-news-portuguese): Corpus de notícias em português brasileiro rotuladas como falsas ou verdadeiras, publicado no Kaggle. O conjunto foi construído a partir de notícias coletadas na web entre 2005 e 2022, organizadas em dois arquivos (`fake.csv` e `true.csv`).

- [**LLM4BrazilianFakeNews**](https://github.com/GoloMarcos/LLM4BrazilianFakeNews): Corpus de notícias políticas brasileiras criado para avaliar o desempenho de modelos de linguagem de larga escala (LLMs) — tanto open-source quanto proprietários — na detecção de desinformação textual. O conjunto foi proposto em um estudo que investiga a eficácia de LLMs na identificação de fake news sobre política nacional, destacando o potencial de modelos abertos como alternativa aos comerciais.


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

