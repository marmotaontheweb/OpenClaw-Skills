#!/usr/bin/env python3
import os
import sys
import json
import argparse
import xml.etree.ElementTree as ET
from pathlib import Path
from pypdf import PdfReader

# Pega o diretório da variável de ambiente ou usa um caminho padrão
DOCS_DIR = Path(os.environ.get("DOCS_DIR", "/caminho/padrao/dos/arquivos"))
MAX_CHARS = 4000  # Limite seguro para não sobrecarregar o contexto do Qwen 2.5

def strip_ns(tag: str) -> str:
    """Remove o namespace XML (ex: {http://www.portalfiscal.inf.br/nfe}vNF -> vNF)"""
    return tag.split("}", 1)[-1] if "}" in tag else tag

def xml_to_dict(element):
    """Converte XML em uma estrutura enxuta de dicionário/texto"""
    result = {}
    for child in element:
        tag = strip_ns(child.tag)
        if len(child) > 0:
            val = xml_to_dict(child)
        else:
            val = (child.text or "").strip()
        if val:
            if tag in result:
                if not isinstance(result[tag], list):
                    result[tag] = [result[tag]]
                result[tag].append(val)
            else:
                result[tag] = val
    return result

def extract_xml_text(filepath: Path) -> str:
    try:
        tree = ET.parse(filepath)
        root = tree.getroot()
        data = {strip_ns(root.tag): xml_to_dict(root)}
        return json.dumps(data, ensure_ascii=False, indent=2)
    except Exception as e:
        return f"Erro ao ler XML {filepath.name}: {e}"

def extract_pdf_text(filepath: Path) -> str:
    try:
        reader = PdfReader(str(filepath))
        pages_text = []
        for i, page in enumerate(reader.pages):
            txt = page.extract_text() or ""
            if txt.strip():
                pages_text.append(f"--- Página {i+1} ---\n{txt.strip()}")
        return "\n\n".join(pages_text)
    except Exception as e:
        return f"Erro ao ler PDF {filepath.name}: {e}"

def list_files():
    if not DOCS_DIR.exists():
        print(f"Erro: Diretório {DOCS_DIR} não encontrado.")
        return
    files = [
        f.name for f in sorted(DOCS_DIR.iterdir())
        if f.is_file() and f.suffix.lower() in (".xml", ".pdf")
    ]
    print(json.dumps({"diretorio": str(DOCS_DIR), "total": len(files), "arquivos": files}, ensure_ascii=False, indent=2))

def read_file(filename: str):
    # Proteção contra Path Traversal (garante que só leia dentro de DOCS_DIR)
    filepath = (DOCS_DIR / Path(filename).name).resolve()
    if not filepath.exists():
        print(f"Erro: Arquivo '{filename}' não encontrado em {DOCS_DIR}.")
        return

    ext = filepath.suffix.lower()
    if ext == ".xml":
        content = extract_xml_text(filepath)
    elif ext == ".pdf":
        content = extract_pdf_text(filepath)
    else:
        print("Formato não suportado. Use apenas .xml ou .pdf")
        return

    if len(content) > MAX_CHARS:
        content = content[:MAX_CHARS] + "\n... [CONTEÚDO TRUNCADO PELO LIMITE DE TOKENS]"
    print(content)

def search_files(query: str):
    if not DOCS_DIR.exists():
        print(f"Erro: Diretório {DOCS_DIR} não encontrado.")
        return

    query_lower = query.lower()
    matches = []

    for f in sorted(DOCS_DIR.iterdir()):
        if not f.is_file() or f.suffix.lower() not in (".xml", ".pdf"):
            continue

        content = extract_xml_text(f) if f.suffix.lower() == ".xml" else extract_pdf_text(f)
        idx = content.lower().find(query_lower)
        if idx != -1:
            start = max(0, idx - 150)
            end = min(len(content), idx + 250)
            snippet = content[start:end].replace("\n", " ")
            matches.append({
                "arquivo": f.name,
                "trecho_encontrado": f"...{snippet}..."
            })

    print(json.dumps({"termo": query, "resultados": matches[:10]}, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Consulta arquivos XML e PDF")
    subparsers = parser.add_subparsers(dest="cmd", required=True)

    subparsers.add_parser("list")

    search_p = subparsers.add_parser("search")
    search_p.add_argument("--query", required=True, help="Termo para buscar")

    read_p = subparsers.add_parser("read")
    read_p.add_argument("--file", required=True, help="Nome do arquivo")

    args = parser.parse_args()
    if args.cmd == "list":
        list_files()
    elif args.cmd == "search":
        search_files(args.query)
    elif args.cmd == "read":
        read_file(args.file)
