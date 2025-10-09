# Índice da Documentação

Este projeto possui documentação completa para uso com `uv` e ferramentas tradicionais.

## Arquivos Principais

### 📖 README.md
- Visão geral do projeto
- Instalação (pip e uv)
- Quick start com exemplos
- Fontes de dados
- Licença e citação

### 📦 PACKAGE_INFO.md
- Guia completo de empacotamento
- Estrutura do projeto
- Instalação detalhada
- Build e publicação (pip/twine e uv)
- Comandos de desenvolvimento
- Metadados do pacote

### ⚡ UV_GUIDE.md
- Guia dedicado ao uso do uv
- Por que usar uv
- Instalação e configuração
- Build e publicação
- Gerenciamento de versões
- Trusted Publisher no GitHub Actions
- Troubleshooting
- Comparação de performance

### 🔄 COMMANDS_COMPARISON.md
- Tabela comparativa lado a lado
- uv vs pip/build/twine
- Todos os comandos comuns
- Workflows completos
- Performance benchmarks
- Recomendações de uso

### ✅ UV_MIGRATION_COMPLETE.md
- Status da migração para uv
- O que foi implementado
- Testes realizados
- Comandos rápidos
- Próximos passos
- Benefícios do uv

## Configuração

### pyproject.toml
- Metadados do pacote
- Dependências
- Build backend (Hatchling)
- Entry points (CLI)
- Compatível com pip e uv

### config.example.json
- Template de configuração
- API keys e parâmetros
- Configurações do pipeline

## GitHub Actions (Exemplos)

### .github/workflows/publish-pypi.yml.example
- Workflow para publicação no PyPI
- Usa uv e Trusted Publisher
- Sem necessidade de tokens
- Build e upload automático

### .github/workflows/test-build.yml.example
- Workflow para testar builds
- Matriz de Python 3.9-3.12
- Teste em Linux, macOS, Windows
- Linter e testes

## Arquivos de Suporte

### LICENSE
- Licença MIT completa
- Copyright 2025

### .gitignore
- Padrões Python
- Ambiente virtual
- Cache do uv
- Dados e builds
- Configurações sensíveis

## Como Navegar

### Novo no projeto?
1. Leia `README.md` primeiro
2. Depois `PACKAGE_INFO.md` para detalhes

### Quer usar uv?
1. `UV_GUIDE.md` - Guia completo
2. `COMMANDS_COMPARISON.md` - Referência rápida
3. `UV_MIGRATION_COMPLETE.md` - Status e próximos passos

### Quer publicar no PyPI?
1. `PACKAGE_INFO.md` - Seção "Next Steps for Distribution"
2. `.github/workflows/publish-pypi.yml.example` - Automação

### Quer desenvolver?
1. `README.md` - Seção "Development"
2. `COMMANDS_COMPARISON.md` - Comandos de dev
3. `.github/workflows/test-build.yml.example` - CI/CD

## Estrutura de Diretórios

```
package-python/
│
├── 📄 Documentação Principal
│   ├── README.md
│   ├── PACKAGE_INFO.md
│   ├── UV_GUIDE.md
│   ├── COMMANDS_COMPARISON.md
│   ├── UV_MIGRATION_COMPLETE.md
│   └── DOCUMENTATION_INDEX.md (este arquivo)
│
├── ⚙️ Configuração
│   ├── pyproject.toml
│   ├── config.example.json
│   ├── LICENSE
│   └── .gitignore
│
├── 🤖 Automação (Exemplos)
│   └── .github/workflows/
│       ├── publish-pypi.yml.example
│       └── test-build.yml.example
│
├── 📦 Código Fonte
│   └── src/fakenews_br_data/
│       ├── __init__.py
│       ├── pipeline.py
│       ├── cleaning.py
│       ├── deduplication.py
│       ├── factcheck.py
│       ├── downloaders.py
│       ├── schema.py
│       ├── config.py
│       ├── utils.py
│       └── cli.py
│
├── 🧪 Testes
│   └── tests/
│       └── __init__.py
│
└── 📦 Distribuição (gerado)
    └── dist/
        ├── fakenews_br_data-0.1.0-py3-none-any.whl
        └── fakenews_br_data-0.1.0.tar.gz
```

## Links Úteis

### Documentação Externa
- [uv Docs](https://docs.astral.sh/uv/)
- [Python Packaging Guide](https://packaging.python.org/)
- [PyPI](https://pypi.org/)
- [TestPyPI](https://test.pypi.org/)

### Repositórios
- [uv GitHub](https://github.com/astral-sh/uv)
- [Hatchling Docs](https://hatch.pypa.io/latest/)

## Suporte

Para dúvidas ou problemas:
1. Verifique a documentação relevante acima
2. Veja a seção "Troubleshooting" em `UV_GUIDE.md`
3. Abra uma issue no GitHub

---

**Última atualização**: Outubro 2025  
**Versão do pacote**: 0.1.0  
**Compatibilidade**: Python 3.9+, uv 0.9.0+, pip 23.0+

