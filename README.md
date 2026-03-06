GUMP Local Light — zero LLM, zero API

Objetivo:
- Ler documentos (pdf/docx/txt/html/eml/rtf/odt) localmente
- Extrair texto de forma robusta
- Normalizar/limpar caracteres inválidos
- Gerar JSONL (1 documento por linha)

Rodar:
  python main.py --input ./documentos --output ./gump_output

Saída:
  ./gump_output/documento.jsonl

Dependências:
  - pdfplumber
  - python-docx
  - beautifulsoup4 (opcional, mas recomendado pra HTML)
