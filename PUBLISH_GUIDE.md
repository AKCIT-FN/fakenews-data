# Guia Rápido: Como Publicar no PyPI

## Status Atual

✅ **Seu pacote está pronto localmente**  
⏳ **Ainda não foi publicado no PyPI**

Por enquanto, usuários podem instalar diretamente do GitHub:
```bash
pip install git+https://github.com/kauandivino/fakenews-data.git
```

## Como Publicar no PyPI

### Opção 1: Publicar no TestPyPI (Recomendado para Teste)

#### 1. Criar conta no TestPyPI
- Acesse: https://test.pypi.org/account/register/
- Crie sua conta

#### 2. Gerar um API Token
- Acesse: https://test.pypi.org/manage/account/token/
- Clique em "Add API token"
- Nome: "fakenews-br-data-test"
- Escopo: "Entire account" (por enquanto)
- **Copie o token** (começa com `pypi-...`) - você só verá uma vez!

#### 3. Build do pacote
```bash
cd /Users/victoremanuel/CURSOR/package-python

# Usando uv (mais rápido)
uv build

# Ou usando pip/build tradicional
python -m build
```

#### 4. Publicar no TestPyPI
```bash
# Usando uv (recomendado)
uv publish --index testpypi --token pypi-SEU_TOKEN_AQUI

# Ou configure o token como variável de ambiente
export UV_PUBLISH_TOKEN="pypi-SEU_TOKEN_AQUI"
uv publish --index testpypi
```

#### 5. Testar a instalação
```bash
# Instalar do TestPyPI
pip install --index-url https://test.pypi.org/simple/ fakenews-br-data

# Ou com uv
uv pip install --index-url https://test.pypi.org/simple/ fakenews-br-data

# Testar
python -c "import fakenews_br_data; print(fakenews_br_data.__version__)"
fakenews-br-data --help
```

---

### Opção 2: Publicar no PyPI Real (Produção)

⚠️ **Atenção**: Depois de publicado, você **não pode deletar** uma versão do PyPI!

#### 1. Criar conta no PyPI
- Acesse: https://pypi.org/account/register/
- Crie sua conta
- **Configure 2FA** (obrigatório para publicar)

#### 2. Gerar um API Token
- Acesse: https://pypi.org/manage/account/token/
- Clique em "Add API token"
- Nome: "fakenews-br-data"
- Escopo: "Entire account" (depois pode criar um específico para o projeto)
- **Copie o token** (começa com `pypi-...`)

#### 3. Build do pacote
```bash
cd /Users/victoremanuel/CURSOR/package-python
uv build
```

#### 4. Publicar no PyPI
```bash
# Usando uv
uv publish --token pypi-SEU_TOKEN_AQUI

# Ou com variável de ambiente
export UV_PUBLISH_TOKEN="pypi-SEU_TOKEN_AQUI"
uv publish
```

#### 5. Verificar publicação
- Acesse: https://pypi.org/project/fakenews-br-data/
- Teste instalação:
```bash
pip install fakenews-br-data
```

---

## Checklist Antes de Publicar

- [ ] Email atualizado no `pyproject.toml` (atualmente: `author@example.com`)
- [ ] Versão correta (atualmente: `0.1.0`)
- [ ] README bem escrito e sem erros
- [ ] LICENSE incluída
- [ ] Código testado e funcionando
- [ ] Dependências corretas no `pyproject.toml`
- [ ] URLs do GitHub corretas no `pyproject.toml`

### Itens que você precisa ajustar:

```toml
# Em pyproject.toml, linha 9:
authors = [
  { name="Victor Emanuel", email="SEU_EMAIL_REAL@example.com" },
]
```

---

## Atualizando uma Versão

Quando quiser publicar uma atualização:

### 1. Atualizar versão
```bash
# Usando uv (automático)
uv version --bump patch  # 0.1.0 -> 0.1.1
uv version --bump minor  # 0.1.0 -> 0.2.0
uv version --bump major  # 0.1.0 -> 1.0.0

# Ou editar manualmente pyproject.toml
# version = "0.1.1"
```

### 2. Fazer commit
```bash
git add pyproject.toml
git commit -m "Bump version to 0.1.1"
git tag v0.1.1
git push origin main --tags
```

### 3. Build e publicar
```bash
uv build
uv publish
```

---

## Instalação Atual (Enquanto não está no PyPI)

Por enquanto, as pessoas podem instalar direto do GitHub:

```bash
# Instalação básica
pip install git+https://github.com/kauandivino/fakenews-data.git

# Com opcional dependencies
pip install "git+https://github.com/kauandivino/fakenews-data.git#egg=fakenews-br-data[huggingface]"

# Para desenvolvimento
git clone git@github.com:kauandivino/fakenews-data.git
cd fakenews-data
pip install -e .[dev]
```

---

## Comandos Úteis

```bash
# Ver versão atual
uv version

# Preview de bump sem alterar
uv version --bump patch --dry-run

# Limpar builds antigos
rm -rf dist/

# Rebuild
uv build

# Verificar o que está no pacote
tar -tzf dist/fakenews_br_data-0.1.0.tar.gz
unzip -l dist/fakenews_br_data-0.1.0-py3-none-any.whl
```

---

## Próximos Passos Recomendados

1. **Testar no TestPyPI primeiro**
   - Garante que tudo funciona
   - Você pode experimentar sem riscos

2. **Configurar Trusted Publisher no GitHub Actions** (opcional mas recomendado)
   - Publicação automática sem token
   - Mais seguro
   - Ver: `.github/workflows/publish-pypi.yml.example`

3. **Adicionar testes**
   - Criar testes em `tests/`
   - Configurar CI/CD

4. **Documentação**
   - Considere adicionar exemplos em notebooks
   - Documentação mais detalhada com Sphinx

---

## Links Úteis

- **TestPyPI**: https://test.pypi.org/
- **PyPI**: https://pypi.org/
- **Guia oficial**: https://packaging.python.org/tutorials/packaging-projects/
- **uv Docs**: https://docs.astral.sh/uv/guides/publish/
- **Seu repositório**: https://github.com/kauandivino/fakenews-data

---

## Dúvidas Comuns

**Q: Posso publicar de novo com a mesma versão?**  
A: Não! Cada versão é única. Você precisa fazer bump da versão.

**Q: Posso deletar uma versão do PyPI?**  
A: Não. Você pode "yank" (marcar como quebrada), mas não deletar.

**Q: TestPyPI é obrigatório?**  
A: Não, mas é muito recomendado para testar antes.

**Q: Preciso do 2FA?**  
A: Sim, PyPI exige 2FA para publicar pacotes.

**Q: Quanto custa?**  
A: PyPI é 100% gratuito! 🎉

