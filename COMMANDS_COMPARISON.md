# Comparação de Comandos: uv vs pip/twine

Este guia mostra os comandos equivalentes entre uv e as ferramentas tradicionais (pip/build/twine).

## Instalação do Gerenciador

### uv

```bash
# Instalar uv
curl -LsSf https://astral.sh/uv/install.sh | sh
source $HOME/.local/bin/env
```

### pip

```bash
# pip já vem com Python
python3 --version
pip --version
```

## Instalar o Pacote

| Ação | uv | pip |
|------|-----|-----|
| Instalar de PyPI | `uv pip install fakenews-br-data` | `pip install fakenews-br-data` |
| Instalar com extras | `uv pip install fakenews-br-data[dev]` | `pip install fakenews-br-data[dev]` |
| Instalar modo editable | `uv pip install -e .` | `pip install -e .` |
| Instalar de arquivo | `uv pip install dist/*.whl` | `pip install dist/*.whl` |
| Desinstalar | `uv pip uninstall fakenews-br-data` | `pip uninstall fakenews-br-data` |

## Build do Pacote

| Ação | uv | pip/build |
|------|-----|-----------|
| Build básico | `uv build` | `python -m build` |
| Build sem sources | `uv build --no-sources` | N/A |
| Build apenas wheel | `uv build --wheel` | `python -m build --wheel` |
| Build apenas sdist | `uv build --sdist` | `python -m build --sdist` |
| **Tempo médio** | **~2 segundos ⚡** | **~15 segundos** |

## Gerenciamento de Versão

| Ação | uv | Manual |
|------|-----|--------|
| Ver versão atual | `uv version` | Ler `pyproject.toml` |
| Setar versão exata | `uv version 1.0.0` | Editar `pyproject.toml` |
| Preview de bump | `uv version --bump patch --dry-run` | N/A |
| Bump patch | `uv version --bump patch` | Editar manualmente |
| Bump minor | `uv version --bump minor` | Editar manualmente |
| Bump major | `uv version --bump major` | Editar manualmente |

## Publicação

### Para TestPyPI

| Ação | uv | twine |
|------|-----|-------|
| Publicar com token | `uv publish --index testpypi --token TOKEN` | `twine upload --repository testpypi dist/* -u __token__ -p TOKEN` |
| Com var ambiente | `UV_PUBLISH_TOKEN=TOKEN uv publish --index testpypi` | `TWINE_PASSWORD=TOKEN twine upload --repository testpypi dist/* -u __token__` |

### Para PyPI

| Ação | uv | twine |
|------|-----|-------|
| Publicar com token | `uv publish --token TOKEN` | `twine upload dist/* -u __token__ -p TOKEN` |
| Com var ambiente | `UV_PUBLISH_TOKEN=TOKEN uv publish` | `TWINE_PASSWORD=TOKEN twine upload dist/* -u __token__` |
| Trusted Publisher (CI) | `uv publish` | `twine upload dist/* --skip-existing` |

## Workflow Completo

### Com uv ⚡

```bash
# 1. Instalar dependências
uv pip install -e .[dev]

# 2. Fazer mudanças no código...

# 3. Bump versão
uv version --bump patch

# 4. Build
uv build

# 5. Publicar
uv publish
```

**Tempo total: ~10 segundos**

### Com pip/build/twine

```bash
# 1. Criar ambiente virtual
python -m venv venv
source venv/bin/activate

# 2. Instalar dependências
pip install -e .[dev]
pip install build twine

# 3. Fazer mudanças no código...

# 4. Editar versão manualmente
vim pyproject.toml  # Alterar version = "0.1.1"

# 5. Build
python -m build

# 6. Publicar
twine upload dist/*
```

**Tempo total: ~60+ segundos**

## Comandos de Desenvolvimento

| Ação | uv | pip/venv |
|------|-----|----------|
| Rodar script | `uv run python script.py` | `python script.py` |
| Rodar pytest | `uv run pytest` | `pytest` |
| Rodar CLI | `uv run fakenews-br-data --help` | `fakenews-br-data --help` |
| Rodar ruff | `uv run ruff check src/` | `ruff check src/` |
| Rodar black | `uv run black src/` | `black src/` |

## GitHub Actions

### Com uv

```yaml
- name: Install uv
  uses: astral-sh/setup-uv@v1

- name: Build and publish
  run: |
    uv build
    uv publish
```

### Com pip/twine

```yaml
- name: Set up Python
  uses: actions/setup-python@v5

- name: Install dependencies
  run: |
    pip install build twine
    
- name: Build and publish
  run: |
    python -m build
    twine upload dist/*
```

## Resumo de Performance

| Operação | pip/build/twine | uv | Melhoria |
|----------|-----------------|-----|----------|
| Instalar deps | ~45s | ~5s | **9x mais rápido** ⚡ |
| Build pacote | ~15s | ~2s | **7.5x mais rápido** ⚡ |
| Workflow completo | ~60s | ~10s | **6x mais rápido** ⚡ |

## Compatibilidade

Ambos os métodos são **100% compatíveis**:

✅ Mesmo `pyproject.toml`
✅ Mesmo formato de distribuição (wheel + sdist)
✅ Mesmo PyPI
✅ Mesmas convenções PEP

Você pode usar uv em um projeto e pip em outro, ou misturar ambos no mesmo projeto!

## Recomendação

**Use uv se você quer:**
- Velocidade máxima
- Comandos simplificados
- Gerenciamento de versão integrado
- Menos ferramentas para instalar

**Use pip/build/twine se você:**
- Prefere ferramentas tradicionais
- Trabalha em ambiente com restrições
- Precisa de máxima estabilidade garantida

## Documentação

- **uv**: https://docs.astral.sh/uv/
- **pip**: https://pip.pypa.io/
- **build**: https://build.pypa.io/
- **twine**: https://twine.readthedocs.io/

---

**Conclusão**: O uv é significativamente mais rápido e simples, mantendo 100% de compatibilidade com o ecossistema Python.

