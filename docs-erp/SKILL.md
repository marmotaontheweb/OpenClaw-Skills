---
name: docs-erp
description: Consulta, busca e extrai informações de arquivos XML e PDF em um diretório específico. Use esta skill sempre que o usuário perguntar sobre documentos, notas fiscais, relatórios, contratos ou dados contidos em arquivos XML/PDF.
version: 1.0.0
metadata:
  openclaw:
    emoji: "📄"
    requires:
      bins:
        - python3
      env:
        - DOCS_DIR
---

# Consulta de Documentos (XML e PDF)

Esta skill permite listar, buscar por palavras-chave e extrair dados de arquivos `.xml` e `.pdf` armazenados no diretório configurado em `$DOCS_DIR`.

## Quando Usar
- O usuário pede para buscar informações em um documento, PDF ou XML (ex: "Qual o valor da nota X?", "O que diz o PDF sobre tal cláusula?", "Quais arquivos XML temos hoje?").

## Fluxo de Trabalho (Passo a Passo)
Para evitar estourar o limite de tokens, **NUNCA** tente ler arquivos PDF ou XML brutos diretamente com `cat`. Use sempre o script `scripts/query_docs.py`:

### 1. Listar arquivos disponíveis (se você não souber o nome exato)
```bash
python3 {baseDir}/scripts/query_docs.py list
```
### 2. Buscar um termo em todos os arquivos (XML e PDF)
Use quando o usuário procurar por um nome, número de documento, CNPJ, produto ou palavra-chave:

```bash
python3 {baseDir}/scripts/query_docs.py search --query "TERMO_DE_BUSCA"
```

### 3. Ler o conteúdo resumido/estruturado de um arquivo específico
Depois de identificar o arquivo correto, extraia os dados dele:

```bash
python3 {baseDir}/scripts/query_docs.py read --file "nome_do_arquivo.xml"
```

---

### 4. O Script de Extração (`scripts/query_docs.py`)

Este script em Python faz o trabalho pesado no servidor do OpenClaw: remove namespaces chatos de XML (muito comuns em NF-e/XMLs corporativos), extrai texto de PDFs usando `pypdf` (ou `pymupdf`) e limita o tamanho do retorno para não sobrecarregar o Qwen 2.5.

Instale a dependência no servidor do OpenClaw:
```bash
pip install pypdf
