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

- [**MuMiN-PT**](https://huggingface.co/datasets/ju-resplande/portuguese-fact-checking): Subconjunto em português do MuMiN, construído de forma top-down a partir de alegações já verificadas por agências de fact-checking, com posterior mapeamento de posts do X/Twitter (2020–2022).
  
  Tarefa e rótulos
  - Tarefa: classificação de veracidade/misinformation em texto curto (tweets).
  - Tamanho: 1.404 instâncias (1.339 falsas / 65 verdadeiras)
  - Período: 2020–2022

  Colunas
    - `id` (*int64*)
    - `claim` (*string*, PT)
    - `claim_en` (*string*, EN — tradução do enunciado)
    - `verdict` (*string*, 2 classes)
    - `train_mask`, `val_mask`, `test_mask` (*booleanos*, partições)
  
  Estatísticas pós limpeza
  - Média de palavras: ~18.9 (misinfo) / 16.9 (verdadeiro).
  - Presença de URL: ~0.3% (misinfo) / 0.0% (verdadeiro).

- [**COVID19.BR**](https://huggingface.co/datasets/ju-resplande/portuguese-fact-checking): Corpus de mensagens de WhatsApp em português brasileiro sobre COVID-19, coletado em 236 grupos entre abril e junho de 2020, construído por abordagem bottom-up a partir de conteúdos verificados por agências de fact-checking.

  Tarefa e rótulos
  - Classificação binária de veracidade (fake/true)
  - Tamanho: 1.987 mensagens (848 falsas / 1.139 verdadeiras)
  - Período: 2020 

  Colunas
  - `text_no_url` (*string*) — texto limpo da mensagem
  - `label` (*string*, fake/true)
  - `new_split` (*string*, indica partição train/val/test)
  - `initial_query`, `claim_query` (*string*) — termos de busca usados na coleta
  - `google_search_results` (*list*), `google_fact_check_results` (*dict*) — evidências externas
  - `near_duplicates`, `text_urls` (*list*), `metadata` (*dict*) — controle de qualidade e duplicatas

  Estatísticas úteis (pós-limpeza, do card)
  - Média de palavras: 167,7 (falsas) / 111,1 (verdadeiras)
  - Presença de URLs: 28,9% (falsas) / 56,9% (verdadeiras)

- [**Fake.br**](https://huggingface.co/datasets/ju-resplande/portuguese-fact-checking): Corpus de notícias brasileiras com pares alinhados de textos falsos e verdadeiros, coletados na web entre janeiro de 2016 e janeiro de 2018. As amostras foram pareadas por similaridade lexical, garantindo correspondência temática entre versões fake e true.

  Tarefa e rótulos:
  - Tarefa: Classificação binária de veracidade em notícias longas 
  - Tamanho: 7.160 textos (3.580 falsos / 3.580 verdadeiros)
  - Período: 2016–2018

  Colunas
  - `text_no_url` (*string*) — texto principal sem URLs
  - `label` (*string*, fake/true)
  - `old_split`, `new_split` (*string*, partições de treino/val/test)
  - `text_urls`, `near_duplicates` (*list*) — controle de duplicatas
  - `google_search_results` (*list*), `google_fact_check_results` (*dict*) — evidências externas
  - `metadata` (*dict*) — informações adicionais

  Estatísticas (pós-limpeza)
  - Média de palavras: 181,4 (falsas) / 183,1 (verdadeiras)

- [**FakeTweetBr**](https://github.com/prc992/FakeTweet.Br): Corpus de tweets em português brasileiro rotulados como falsos ou verdadeiros, criado para estudos de verificação automática de rumores e classificação de notícias falsas em redes sociais. O conjunto foi compilado a partir de publicações no Twitter, refletindo temas variados de interesse público.

  Tarefa e rótulos:
  - Tarefa: Classificação binária de veracidade em texto curto (tweets) 
  - Tamanho: 299 tweets (206 falsos / 93 verdadeiros)
  - Período: 2010-2019

  Colunas
  - `id` (*int64*) — identificador do tweet  
  - `subject` (*string*) — tema ou assunto do tweet  
  - `text` (*string*) — conteúdo textual do tweet  
  - `classificacao` (*string*, fake/true) — rótulo de veracidade  
  - `date` (*string*) — data de publicação  
  - `retweets` (*int64*) — número de retweets  
  - `favorites` (*int64*) — número de curtidas  
  - `permalink` (*string*) — URL do tweet original 

  Estatísticas
  - Média de palavras: 29,39 (falsas) / 29,71 (verdadeiras)

- [**FakeWhatsAppBR**](https://github.com/cabrau/FakeWhatsApp.Br): Corpus anotado e anonimizado de mensagens públicas de WhatsApp em português brasileiro, criado para estudos de detecção automática de desinformação textual e identificação de usuários maliciosos. O conjunto foi compilado durante as eleições presidenciais brasileiras de 2018, a partir de grupos públicos.

  Tarefa e rótulos:
  - Tarefa: Classificação binária de desinformação (misinformation / não misinformation) 
  - Tamanho: 282601 (11412 falsos / 9877 verdadeiros / sem rotulos 261312)
  - Período: 2018

  Colunas
  - `id` (*int64*) — identificador único do usuário  
  - `date` (*string*) — data de envio da mensagem  
  - `ddi`, `country`, `country_iso3`, `ddd`, `state` — metadados geográficos e telefônicos  
  - `midia` (*bool*) — indica se a mensagem contém mídia (1/0)  
  - `url` (*bool*) — presença de URLs (1/0)  
  - `characters`, `words` (*int64*) — comprimento do texto  
  - `viral` (*bool*) — mensagem viral (aparece ≥ 5 vezes no corpus)  
  - `shares` (*int64*) — número de ocorrências do mesmo texto  
  - `text` (*string*) — conteúdo textual da mensagem  
  - `misinformation` (*int*, 1 = contém desinformação, 0 = não, -1 = não rotulada)

  Estatísticas
  - Média de palavras: 121,72 (falsas) / 68,16 (verdadeiras)

- [**Fake news in Portuguese**](www.kaggle.com/datasets/fabioselau/fakes-news-portuguese): Corpus de notícias em português brasileiro rotuladas como falsas ou verdadeiras, publicado no Kaggle. O conjunto foi construído a partir de notícias coletadas na web entre 2005 e 2022, organizadas em dois arquivos (`fake.csv` e `true.csv`).

  Tarefa e rótulos:
  - Tarefa: Classificação binária de veracidade (fake/true) 
  - Tamanho: 23.198 notícias (20.478 falsas / 2.720 verdadeiras)
  - Período: 2005–2022

  Colunas
  - `title` (*string*) — título da notícia  
  - `text` (*string*) — corpo textual da notícia  
  - `origin` (*string*) — origem declarada ou categoria do conteúdo  
  - `url` (*string*) — link original da notícia  
  - `label` (*int*, 1 = fake, 0 = true) — rótulo de veracidade  
  - `publisher_name` (*string*) — nome do veículo de publicação  
  - `publisher_site` (*string*) — domínio ou site da fonte  
  - `date` (*string*) — data de publicação (AAAA-MM-DD)  
  - `word_count` (*int64*) — número de palavras no texto

  Estatísticas
  - Média de palavras: 18,72 (falsas) / 15,24 (verdadeiras)

- [**LLM4BrazilianFakeNews**](https://github.com/GoloMarcos/LLM4BrazilianFakeNews): Corpus de notícias políticas brasileiras criado para avaliar o desempenho de modelos de linguagem de larga escala (LLMs) — tanto open-source quanto proprietários — na detecção de desinformação textual. O conjunto foi proposto em um estudo que investiga a eficácia de LLMs na identificação de fake news sobre política nacional, destacando o potencial de modelos abertos como alternativa aos comerciais.

  Tarefa e rótulos:
  - Tarefa: Classificação binária de veracidade (fake/true) 
  - Tamanho: 300 notícias (148 falsas / 152 verdadeiras)
  - Período: Não especificado

  Colunas
  - `ID` (*int64*) — identificador único do artigo  
  - `Fonte` (*string*) — veículo ou origem da notícia  
  - `text` (*string*) — texto processado da notícia  
  - `Texto_Original` (*string*) — texto original sem pré-processamento  
  - `Tematica` (*string*) — tema principal do conteúdo (ex.: política, economia)  
  - `Rótulo` (*string*, fake/true) — rótulo de veracidade  
  - `Tipo_Dado` (*string*) — origem do dado (ex.: real ou gerado)  
  - `word_count` (*int64*) — número de palavras do texto  

  Estatísticas
  - Média de palavras: 427,9 (falsas) / 659,3 (verdadeiras)

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

