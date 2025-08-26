"""
Módulo de Extração de Texto

Este módulo é responsável por:
1. Extrair texto de arquivos PDF das resoluções do CNS baixadas usando múltiplas estratégias
2. Combinar o texto extraído com os metadados coletados
3. Criar uma base de dados completa com resoluções e seus respectivos textos

Fluxo de trabalho:
- Processa todos os PDFs em pastas organizadas por ano
- Tenta extrair texto de cada PDF com a seguinte ordem de preferência:
  1. PyMuPDF (fitz): Rápido e robusto para a maioria dos PDFs.
  2. pdfplumber: Bom para PDFs com layouts complexos.
  3. PyPDF2: Fallback para casos mais simples.
  4. OCR (Tesseract): Último recurso para PDFs baseados em imagem (escaneados).
- Faz a correspondência entre os PDFs e os dados das resoluções
- Gera um arquivo CSV final com todos os dados unificados
"""

import pandas as pd
import time
from datetime import datetime
import unicodedata
from pathlib import Path
import glob
import os
import warnings
import shutil

# Variável global para verificar a disponibilidade do Tesseract
TESSERACT_DISPONIVEL = False

def _check_tesseract():
    """Verifica se o executável do Tesseract está disponível no PATH."""
    global TESSERACT_DISPONIVEL
    if shutil.which("tesseract"):
        TESSERACT_DISPONIVEL = True
        return True
    else:
        TESSERACT_DISPONIVEL = False
        print("--------------------------------------------------------------------")
        print("AVISO: Tesseract OCR não encontrado no seu sistema.")
        print("A extração de texto de PDFs baseados em imagem (escaneados) será pulada.")
        print("Para habilitar o OCR, instale o Tesseract:")
        print("  - No Ubuntu/Debian: sudo apt-get install tesseract-ocr tesseract-ocr-por")
        print("  - No Windows: baixe em https://github.com/UB-Mannheim/tesseract/wiki")
        print("  - No macOS: brew install tesseract")
        print("--------------------------------------------------------------------")
        time.sleep(3) # Pausa para o usuário ler o aviso
        return False

def instalar_bibliotecas_pdf():
    """
    Instala as bibliotecas necessárias para extração de texto PDF.
    """
    import subprocess
    import sys
    
    bibliotecas = {
        "PyMuPDF": "fitz",
        "pdfplumber": "pdfplumber",
        "PyPDF2": "PyPDF2",
        "Pillow": "PIL",
        "pytesseract": "pytesseract"
    }
    
    bibliotecas_instaladas = []
    
    for lib_install, lib_import in bibliotecas.items():
        try:
            __import__(lib_import)
            print(f"{lib_install} já instalado ✓")
            bibliotecas_instaladas.append(lib_install)
        except ImportError:
            print(f"Instalando {lib_install}...")
            try:
                # Usando uv, se disponível, para acelerar a instalação
                pip_command = "uv pip install" if shutil.which("uv") else f"{sys.executable} -m pip install"
                subprocess.check_call(f"{pip_command} {lib_install}", shell=True)
                __import__(lib_import)
                print(f"{lib_install} instalado com sucesso ✓")
                bibliotecas_instaladas.append(lib_install)
            except Exception as e:
                print(f"❌ Erro ao instalar {lib_install}: {e}")

    _check_tesseract()

    if "PyMuPDF" in bibliotecas_instaladas or "pdfplumber" in bibliotecas_instaladas:
        print(f"Bibliotecas PDF disponíveis: {', '.join(bibliotecas_instaladas)}")
        return True
    else:
        print("❌ Nenhuma biblioteca PDF principal (PyMuPDF ou pdfplumber) pôde ser instalada!")
        return False

# Chamar a instalação no início para garantir que tudo está pronto
instalar_bibliotecas_pdf()

# Importações que dependem da instalação
try:
    import fitz  # PyMuPDF
except ImportError:
    fitz = None

try:
    import pdfplumber
except ImportError:
    pdfplumber = None

try:
    import PyPDF2
except ImportError:
    PyPDF2 = None

try:
    from PIL import Image
    import pytesseract
except ImportError:
    Image = None
    pytesseract = None


def verificar_integridade_pdf(caminho_pdf):
    """Verifica se um arquivo PDF está íntegro e pode ser processado."""
    try:
        if not os.path.exists(caminho_pdf) or os.path.getsize(caminho_pdf) < 100:
            return False, "Arquivo não existe ou é muito pequeno"
        
        if fitz:
            with fitz.open(caminho_pdf) as doc:
                if not doc.page_count:
                    return False, "PDF sem páginas (verificado com PyMuPDF)"
        else: # Fallback se PyMuPDF não estiver instalado
             with pdfplumber.open(caminho_pdf) as pdf:
                if not pdf.pages:
                    return False, "PDF sem páginas (verificado com pdfplumber)"

        return True, "PDF válido"
        
    except Exception as e:
        error_msg = str(e).lower()
        if "no /root object" in error_msg:
            return False, "Arquivo corrompido (sem objeto /Root)"
        elif "not a pdf" in error_msg:
            return False, "Arquivo não é um PDF válido"
        else:
            return False, f"Erro de verificação: {str(e)[:100]}"


def _tentar_pymupdf(caminho_pdf, max_paginas=None):
    """Tenta extrair texto usando PyMuPDF (fitz)."""
    if not fitz:
        return None

    try:
        doc = fitz.open(caminho_pdf)
        texto_completo = []
        
        paginas_para_processar = range(doc.page_count)
        if max_paginas:
            paginas_para_processar = range(min(doc.page_count, max_paginas))

        for i in paginas_para_processar:
            pagina = doc.load_page(i)
            texto_pagina = pagina.get_text("text")
            if texto_pagina and texto_pagina.strip():
                texto_completo.append(texto_pagina.strip())
        
        doc.close()
        
        if texto_completo:
            return f"SUCCESS_PYMUPDF: {' '.join(texto_completo)}"
        return None
    except Exception as e:
        print(f"    - PyMuPDF falhou: {e}")
        return None


def _tentar_pdfplumber(caminho_pdf, max_paginas=None):
    """Tenta extrair texto usando pdfplumber com múltiplas estratégias."""
    if not pdfplumber:
        return None

    try:
        with pdfplumber.open(caminho_pdf) as pdf:
            texto_completo = []
            paginas_para_processar = pdf.pages
            if max_paginas:
                paginas_para_processar = pdf.pages[:max_paginas]

            for pagina in paginas_para_processar:
                # Estratégia 1: Padrão
                texto_pagina = pagina.extract_text()
                
                # Estratégia 2: Layout
                if not texto_pagina or len(texto_pagina.strip()) < 10:
                    texto_pagina = pagina.extract_text(
                        x_tolerance=3, y_tolerance=3, layout=True, 
                        x_density=7.25, y_density=13
                    )

                if texto_pagina and texto_pagina.strip():
                    texto_completo.append(texto_pagina.strip())
            
            if texto_completo:
                return f"SUCCESS_PDFPLUMBER: {' '.join(texto_completo)}"
        return None
    except Exception as e:
        print(f"    - pdfplumber falhou: {e}")
        return None


def _tentar_pypdf2(caminho_pdf, max_paginas=None):
    """Tenta extrair texto usando PyPDF2 como fallback."""
    if not PyPDF2:
        return None

    try:
        with open(caminho_pdf, 'rb') as arquivo:
            leitor = PyPDF2.PdfReader(arquivo)
            texto_completo = []
            
            num_paginas = len(leitor.pages)
            if max_paginas:
                num_paginas = min(num_paginas, max_paginas)
            
            for i in range(num_paginas):
                pagina = leitor.pages[i]
                texto_pagina = pagina.extract_text()
                if texto_pagina and texto_pagina.strip():
                    texto_completo.append(texto_pagina.strip())
            
            if texto_completo:
                return f"SUCCESS_PYPDF2: {' '.join(texto_completo)}"
        return None
    except Exception as e:
        print(f"    - PyPDF2 falhou: {e}")
        return None

def _tentar_ocr(caminho_pdf, max_paginas=None):
    """Tenta extrair texto usando OCR (Tesseract) como último recurso."""
    if not TESSERACT_DISPONIVEL or not fitz or not Image or not pytesseract:
        return None

    try:
        print("    - Tentando OCR (pode ser lento)...")
        doc = fitz.open(caminho_pdf)
        texto_completo = []
        
        paginas_para_processar = range(doc.page_count)
        if max_paginas:
            paginas_para_processar = range(min(doc.page_count, max_paginas))

        for i in paginas_para_processar:
            pagina = doc.load_page(i)
            # Renderiza a página como imagem
            pix = pagina.get_pixmap(dpi=300)
            img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
            
            # Extrai texto da imagem usando Tesseract
            texto_pagina = pytesseract.image_to_string(img, lang='por')
            if texto_pagina and texto_pagina.strip():
                texto_completo.append(texto_pagina.strip())
        
        doc.close()

        if texto_completo:
            return f"SUCCESS_OCR: {' '.join(texto_completo)}"
        return None
    except Exception as e:
        print(f"    - OCR falhou: {e}")
        return None


def extrair_texto_do_pdf(caminho_pdf, max_paginas=None):
    """
    Extrai texto de um PDF usando uma cadeia de estratégias.
    
    Ordem das tentativas:
    1. PyMuPDF (fitz)
    2. pdfplumber
    3. PyPDF2
    4. OCR (Tesseract)
    
    Returns:
        str: Texto extraído com um prefixo de sucesso (e.g., "SUCCESS_PYMUPDF: ")
             ou uma mensagem de erro (e.g., "ERROR_ALL_METHODS_FAILED").
    """
    warnings.filterwarnings('ignore', category=UserWarning)
    warnings.filterwarnings('ignore', message='.*invalid.*color.*')

    # Estratégia 1: PyMuPDF
    texto = _tentar_pymupdf(caminho_pdf, max_paginas)
    if texto:
        return texto

    # Estratégia 2: pdfplumber
    texto = _tentar_pdfplumber(caminho_pdf, max_paginas)
    if texto:
        return texto

    # Estratégia 3: PyPDF2
    texto = _tentar_pypdf2(caminho_pdf, max_paginas)
    if texto:
        return texto

    # Estratégia 4: OCR
    texto = _tentar_ocr(caminho_pdf, max_paginas)
    if texto:
        return texto

    return "ERROR_ALL_METHODS_FAILED: Nenhuma biblioteca conseguiu extrair texto."


def limpar_texto_extraido(texto):
    """Limpa e normaliza o texto extraído dos PDFs."""
    if not texto or texto.startswith("ERROR_"):
        return texto
    
    # Remove o prefixo de sucesso (e.g., "SUCCESS_PYMUPDF: ")
    if ": " in texto:
        texto = texto.split(": ", 1)[1]

    texto = unicodedata.normalize('NFKD', texto)
    texto = ' '.join(texto.split())
    
    if len(texto) > 50000:
        texto = texto[:50000] + "... [TEXTO_TRUNCADO]"
    
    return texto


def processar_todos_pdfs_para_texto(pasta_pdfs="pdfs_cns_resolucoes", max_paginas_por_pdf=None):
    """Processa todos os PDFs encontrados na pasta e extrai seus textos."""
    pasta_base = Path(pasta_pdfs)
    if not pasta_base.exists():
        print(f"Pasta {pasta_pdfs} não encontrada!")
        return {}
    
    todos_pdfs = list(pasta_base.glob('**/*.pdf'))
    print(f"Encontrados {len(todos_pdfs)} PDFs para processar...")
    
    if not todos_pdfs:
        return {}
    
    textos_extraidos = {}
    sucessos = 0
    erros = 0
    
    print("\nIniciando extração de texto dos PDFs...")
    print("=" * 60)
    
    for i, caminho_pdf in enumerate(todos_pdfs, 1):
        nome_arquivo = caminho_pdf.stem
        ano = caminho_pdf.parent.name
        
        print(f"{i}/{len(todos_pdfs)} - Processando: {ano}/{nome_arquivo}")
        
        pdf_valido, msg_verificacao = verificar_integridade_pdf(caminho_pdf)
        
        if not pdf_valido:
            print(f"  ✗ PDF inválido: {msg_verificacao}")
            texto_bruto = f"ERROR_INVALID_PDF: {msg_verificacao}"
            erros += 1
        else:
            texto_bruto = extrair_texto_do_pdf(caminho_pdf, max_paginas_por_pdf)
            
            if texto_bruto.startswith("ERROR_"):
                print(f"  ✗ Erro de extração: {texto_bruto}")
                erros += 1
            else:
                metodo = texto_bruto.split(':', 1)[0].replace('SUCCESS_', '')
                tamanho = len(limpar_texto_extraido(texto_bruto))
                print(f"  ✓ Texto extraído com {metodo}: {tamanho} caracteres")
                sucessos += 1
        
        chave = f"{ano}_{nome_arquivo}"
        texto_limpo = limpar_texto_extraido(texto_bruto)
        textos_extraidos[chave] = {
            'ano': ano,
            'nome_arquivo': nome_arquivo,
            'caminho_completo': str(caminho_pdf),
            'texto': texto_limpo,
            'tamanho_texto': len(texto_limpo) if not texto_limpo.startswith("ERROR_") else 0,
            'tem_erro': texto_limpo.startswith("ERROR_"),
            'metodo_extracao': texto_bruto.split(':', 1)[0]
        }
        
        if i % 10 == 0:
            print(f"  Progresso: {i}/{len(todos_pdfs)} - Sucessos: {sucessos}, Erros: {erros}")
            time.sleep(0.1)
            
    print("=" * 60)
    print(f"Extração concluída! Sucessos: {sucessos}, Erros: {erros}")
    
    # Salva resultado intermediário
    df_textos = pd.DataFrame.from_dict(textos_extraidos, orient='index')
    if not df_textos.empty:
        nome_arquivo_textos = f'textos_pdfs_extraidos_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
        df_textos.to_csv(nome_arquivo_textos, index_label='chave', encoding='utf-8')
        print(f"\nArquivo de backup salvo: {nome_arquivo_textos}")
    
    return textos_extraidos

def limpar_nome_arquivo_para_matching(titulo, tamanho_maximo=100):
    """Limpa o título da resolução para criar um nome de arquivo válido."""
    if not titulo:
        return "resolucao_sem_titulo"
    
    import string
    valid_chars = "-_.() %s%s" % (string.ascii_letters, string.digits)
    titulo_limpo = ''.join(c for c in titulo if c in valid_chars)
    
    titulo_limpo = ' '.join(titulo_limpo.split())
    return titulo_limpo[:tamanho_maximo]


def combinar_csv_com_textos_pdf(arquivo_csv, textos_extraidos, pasta_pdfs="pdfs_cns_resolucoes"):
    """Combina os dados das resoluções (CSV) com os textos extraídos dos PDFs."""
    if not os.path.exists(arquivo_csv):
        print(f"Arquivo CSV não encontrado: {arquivo_csv}")
        return None
    
    df_resolucoes = pd.read_csv(arquivo_csv)
    print(f"CSV carregado com {len(df_resolucoes)} resoluções")
    
    if not textos_extraidos:
        print("Dicionário de textos extraídos está vazio. Abortando combinação.")
        return df_resolucoes

    df_textos = pd.DataFrame.from_dict(textos_extraidos, orient='index')
    df_textos.index.name = 'chave_pdf'
    
    # Prepara as chaves no DataFrame de resoluções
    df_resolucoes['chave_pdf'] = df_resolucoes.apply(
        lambda row: f"{row['ano']}_{limpar_nome_arquivo_para_matching(row['titulo'])}",
        axis=1
    )

    # Merge exato
    df_completo = pd.merge(df_resolucoes, df_textos, on='chave_pdf', how='left')
    
    print("=" * 60)
    print("CORRESPONDÊNCIA CONCLUÍDA!")
    sucessos = df_completo['texto'].notna().sum()
    print(f"Correspondências diretas encontradas: {sucessos}/{len(df_completo)}")
    
    return df_completo


def criar_base_completa_com_textos(arquivo_csv=None, pasta_pdfs="pdfs_cns_resolucoes", max_paginas_por_pdf=None):
    """Função principal que cria a base de dados completa com textos dos PDFs."""
    if arquivo_csv is None:
        arquivos_csv = [f for f in glob.glob('cns_resolucoes_*.csv') if 'com_textos' not in f]
        if not arquivos_csv:
            print("Nenhum arquivo CSV de resoluções encontrado!")
            return None
        arquivo_csv = max(arquivos_csv, key=os.path.getctime)
        print(f"Usando arquivo CSV mais recente: {arquivo_csv}")
    
    print("=" * 60)
    print("CRIANDO BASE COMPLETA COM TEXTOS PDF")
    print("=" * 60)
    
    inicio_extracao = time.time()
    textos_extraidos = processar_todos_pdfs_para_texto(pasta_pdfs, max_paginas_por_pdf)
    
    if not textos_extraidos:
        print("❌ Nenhum texto extraído. Verifique a pasta de PDFs.")
        return None
    
    print(f"✅ Extração concluída em {time.time() - inicio_extracao:.2f} segundos")
    
    inicio_combinacao = time.time()
    df_completo = combinar_csv_com_textos_pdf(arquivo_csv, textos_extraidos)
    
    if df_completo is None:
        print("❌ Erro na combinação de dados.")
        return None
        
    print(f"✅ Combinação concluída em {time.time() - inicio_combinacao:.2f} segundos")

    nome_arquivo_final = f'cns_resolucoes_com_textos_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
    df_completo.to_csv(nome_arquivo_final, index=False, encoding='utf-8')
    
    print("=" * 60)
    print("🎉 BASE COMPLETA CRIADA COM SUCESSO!")
    print(f"📁 Arquivo salvo: {nome_arquivo_final}")
    
    # Estatísticas
    textos_validos = df_completo[df_completo['tem_erro'] == False]
    print(f"✅ Resoluções com texto extraído: {len(textos_validos)}/{len(df_completo)} ({len(textos_validos)/len(df_completo)*100:.1f}%)")
    
    if not textos_validos.empty:
        print("\n📊 Contagem por método de extração:")
        print(textos_validos['metodo_extracao'].value_counts())

    return df_completo


def main():
    """Função principal de execução do módulo."""
    print("Iniciando processo de extração de texto PDF...")
    df_resultado = criar_base_completa_com_textos()
    
    if df_resultado is not None:
        print("\n🎉 Processo concluído com sucesso!")
    else:
        print("\n❌ Processo falhou. Verifique os logs para detalhes.")

if __name__ == "__main__":
    main()