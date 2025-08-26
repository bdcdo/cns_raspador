# CNS Raspador

[![Python 3.7+](https://img.shields.io/badge/python-3.7+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

Um raspador completo para coleta, download e extração de texto das resoluções do **Conselho Nacional de Saúde (CNS)** do Brasil.

## 📋 Funcionalidades

- **🕷️ Web Scraping**: Coleta metadados de todas as resoluções CNS por ano (1988-2025)
- **📥 Download de PDFs**: Download automático dos documentos PDF das resoluções
- **📄 Extração de Texto**: Extração de texto completo dos PDFs utilizando OCR
- **🔗 Matching Inteligente**: Combinação automática entre metadados e textos extraídos
- **📊 Relatórios Detalhados**: Estatísticas completas do processo de coleta
- **💾 Formato CSV**: Exportação em formato estruturado para análise posterior

## 🚀 Instalação

### 1. Clone o repositório
```bash
git clone https://github.com/seu-usuario/cns-raspador.git
cd cns-raspador
```

### 2. Crie um ambiente virtual (recomendado)
```bash
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
# ou
venv\Scripts\activate  # Windows
```

### 3. Instale as dependências
```bash
pip install -r requirements.txt
```

## 📖 Como Usar

### Interface de Linha de Comando

O projeto oferece uma interface CLI completa através do arquivo `main.py`:

```bash
# Exibir ajuda
python main.py -h

# Verificar status do projeto
python main.py status

# Executar pipeline completo (recomendado)
python main.py full

# Ou executar etapas individuais:
python main.py scrape                    # 1. Coletar metadados
python main.py download [arquivo.csv]    # 2. Baixar PDFs
python main.py extract [arquivo.csv]     # 3. Extrair textos
```

### Uso Programático

```python
from src.scraper import collect_all_data, download_all_pdfs
from src.text_extractor import create_complete_database_with_texts

# 1. Coletar dados das resoluções
resolution_data = collect_all_data()

# 2. Baixar PDFs (opcional)
download_all_pdfs('cns_resolucoes_completo_20241225_120000.csv')

# 3. Criar base completa com textos
complete_db = create_complete_database_with_texts()
```

## 📁 Estrutura do Projeto

```
cns-raspador/
├── src/                          # Código fonte
│   ├── __init__.py              # Inicialização do módulo
│   ├── scraper.py               # Web scraping e download de PDFs
│   └── text_extractor.py        # Extração de texto dos PDFs
├── main.py                      # Interface CLI principal
├── requirements.txt             # Dependências Python
├── README.md                    # Este arquivo
├── .gitignore                   # Arquivos ignorados pelo Git
└── outputs/                     # Arquivos de saída (criado automaticamente)
    ├── cns_resolucoes_*.csv     # Metadados das resoluções
    ├── cns_resolucoes_com_textos_*.csv  # Base completa com textos
    └── pdfs_cns_resolucoes/     # PDFs baixados organizados por ano
```

## 📊 Dados Coletados

### Metadados (scraper.py)
- **titulo**: Título da resolução
- **link**: URL para o documento PDF
- **descricao**: Descrição/resumo da resolução
- **tags**: Tags/categorias separadas por vírgula
- **data_publicacao**: Data de publicação
- **hora_publicacao**: Hora de publicação
- **ano**: Ano da resolução

### Textos Extraídos (text_extractor.py)
- **pdf_text**: Texto completo extraído do PDF
- **pdf_text_size**: Número de caracteres do texto
- **pdf_extraction_error**: Indica se houve erro na extração

## ⚙️ Configuração

### Parâmetros Importantes

- **Anos de coleta**: Por padrão coleta de 2025 a 1988 (configurável em `generate_page_urls()`)
- **Timeout de download**: 30 segundos por PDF (configurável em `download_pdf()`)
- **Limite de páginas**: Sem limite por padrão (configurável em `extract_text_from_pdf()`)
- **Pausa entre requisições**: 1 segundo para scraping, 0.5s para downloads

### Personalização

Para modificar os anos de coleta, edite a função `generate_page_urls()` em `src/scraper.py`:

```python
def generate_page_urls():
    return [f'https://www.gov.br/conselho-nacional-de-saude/pt-br/atos-normativos/resolucoes/{ano}' 
            for ano in range(2025, 2000, -1)]  # Apenas de 2025 a 2000
```

## 📈 Performance

- **Coleta de metadados**: ~1-2 segundos por ano
- **Download de PDFs**: ~1-5 segundos por arquivo (varia com tamanho)
- **Extração de texto**: ~0.5-2 segundos por PDF
- **Total estimado**: 2-4 horas para coleta completa (1988-2025)

### Otimizações Implementadas

- ✅ Salvamentos progressivos a cada 5 anos
- ✅ Verificação de arquivos existentes (pula downloads duplicados)
- ✅ Tratamento robusto de erros com logs detalhados
- ✅ Pausas respeitosas entre requisições
- ✅ Matching inteligente entre metadados e PDFs

## 🛠️ Dependências

- **requests**: Para requisições HTTP
- **beautifulsoup4**: Para parsing HTML
- **pandas**: Para manipulação de dados
- **pdfplumber**: Para extração de texto de PDFs

## 📝 Exemplos de Uso

### 1. Coleta Rápida (últimos 5 anos)
```python
from src.scraper import generate_page_urls, collect_page_data

# Modificar temporariamente para apenas anos recentes
urls = [f'https://www.gov.br/conselho-nacional-de-saude/pt-br/atos-normativos/resolucoes/{ano}' 
        for ano in range(2025, 2020, -1)]

data = []
for url in urls:
    year = url.split('/')[-1]
    data.extend(collect_page_data(url, year))
```

### 2. Extração de Texto Limitada
```python
from src.text_extractor import create_complete_database_with_texts

# Limitar a 3 páginas por PDF para processamento mais rápido
df = create_complete_database_with_texts(max_pages_per_pdf=3)
```

### 3. Análise dos Dados Coletados
```python
import pandas as pd

# Carregar dados completos
df = pd.read_csv('cns_resolucoes_com_textos_20241225_120000.csv')

# Estatísticas básicas
print(f"Total de resoluções: {len(df)}")
print(f"Anos disponíveis: {sorted(df['ano'].unique())}")
print(f"Resoluções com texto: {df['pdf_text_size'].gt(0).sum()}")

# Resoluções por ano
print(df['ano'].value_counts().sort_index())

# Buscar por termo específico
covid_resolutions = df[df['pdf_text'].str.contains('COVID', case=False, na=False)]
print(f"Resoluções sobre COVID: {len(covid_resolutions)}")
```

## 🤝 Contribuição

Contribuições são bem-vindas! Por favor:

1. Faça um Fork do projeto
2. Crie uma branch para sua feature (`git checkout -b feature/nova-funcionalidade`)
3. Commit suas mudanças (`git commit -am 'Adiciona nova funcionalidade'`)
4. Push para a branch (`git push origin feature/nova-funcionalidade`)
5. Abra um Pull Request

## 📄 Licença

Este projeto está licenciado sob a Licença MIT - veja o arquivo [LICENSE](LICENSE) para detalhes.

## ⚠️ Aviso Legal

Este projeto foi desenvolvido para fins educacionais e de pesquisa. Os dados coletados são públicos e disponibilizados pelo governo brasileiro. Use de forma responsável e respeitando os termos de uso do site do CNS.

## 📞 Suporte

- **Issues**: [GitHub Issues](https://github.com/seu-usuario/cns-raspador/issues)
- **Documentação**: Este README e comentários no código
- **Email**: seu.email@exemplo.com

## 🏆 Reconhecimentos

- **CNS**: Conselho Nacional de Saúde pela disponibilização dos dados
- **Governo Federal**: Portal gov.br pela transparência dos dados públicos
- **Comunidade Python**: Pelas excelentes bibliotecas utilizadas

---

**Desenvolvido com ❤️ para facilitar o acesso às resoluções do CNS**