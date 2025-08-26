"""
CNS Raspador - Raspador de Resoluções do Conselho Nacional de Saúde

Um toolkit completo para coleta, download e extração de texto das
resoluções do Conselho Nacional de Saúde (CNS) do Brasil.

Este pacote oferece:
- Coleta automatizada de dados das resoluções do site oficial do CNS
- Download de arquivos PDF das resoluções
- Extração de texto dos PDFs usando técnicas de OCR
- Interface de linha de comando simples para uso
- Funcionalidades programáticas para integração em outros projetos
"""

__version__ = "1.0.0"
__author__ = "Equipe CNS Raspador"
__email__ = "contato@cns-raspador.com"
__description__ = "Raspador completo para resoluções do Conselho Nacional de Saúde"
__license__ = "MIT"

from .scraper import (
    gerar_anos,
    gerar_url_pagina,
    extrair_dados_artigo,
    coletar_dados_pagina_unica,
    coletar_dados_ano_completo,
    coletar_todos_dados,
    baixar_todos_pdfs,
    main as scraper_main
)

from .text_extractor import (
    extrair_texto_do_pdf,
    processar_todos_pdfs_para_texto,
    combinar_csv_com_textos_pdf,
    criar_base_completa_com_textos,
    main as extractor_main
)

__all__ = [
    'gerar_anos',
    'gerar_url_pagina',
    'extrair_dados_artigo',
    'coletar_dados_pagina_unica',
    'coletar_dados_ano_completo',
    'coletar_todos_dados',
    'baixar_todos_pdfs',
    'scraper_main',
    'extrair_texto_do_pdf',
    'processar_todos_pdfs_para_texto',
    'combinar_csv_com_textos_pdf',
    'criar_base_completa_com_textos',
    'extractor_main'
]