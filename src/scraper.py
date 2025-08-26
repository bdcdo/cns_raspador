"""
Módulo de Raspagem do CNS

Este módulo realiza a raspagem web das resoluções do CNS (Conselho Nacional de Saúde)
do site do governo, incluindo extração de dados e download de PDFs.
"""

import requests
from bs4 import BeautifulSoup, Tag
import pandas as pd
import time
from datetime import datetime
import os
import urllib.request
import shutil
from pathlib import Path
from typing import Any


def gerar_urls_paginas() -> list[str]:
    """
    Gera lista de páginas de resoluções do CNS por ano (2025 a 1988).
    
    Esta função cria URLs para todas as páginas de resoluções do CNS,
    começando do ano mais recente (2025) até 1988. O site do governo
    organiza as resoluções por ano em URLs específicas.
    
    Returns:
        list[str]: Lista de URLs das páginas de resoluções por ano
    """
    return [f'https://www.gov.br/conselho-nacional-de-saude/pt-br/atos-normativos/resolucoes/{ano}' 
            for ano in range(2025, 1987, -1)]


def extrair_dados_artigo(artigo: Any) -> dict[str, str]:
    """
    Extrai dados de um elemento article específico da página.
    
    Esta função processa cada elemento <article> encontrado na página
    do CNS e extrai as informações principais de uma resolução:
    título, link, descrição, tags e dados de publicação.
    
    Args:
        artigo (Any): Elemento BeautifulSoup representando um artigo/resolução
        
    Returns:
        dict[str, str]: Dados extraídos incluindo título, link, descrição, tags e informações de publicação
    """
    # Inicializa dicionário para armazenar os dados da resolução
    dados = {}
    
    try:
        # Extração do título da resolução
        # O título está dentro de um elemento h2 com classe 'tileHeadline'
        title_elem = artigo.find('h2', class_='tileHeadline')
        if title_elem:
            # Verifica se há um link dentro do título
            link_elem = title_elem.find('a')
            if link_elem:
                dados['titulo'] = link_elem.text.strip()
                dados['link'] = link_elem.get('href', '')
            else:
                # Se não há link, pega apenas o texto
                dados['titulo'] = title_elem.text.strip()
                dados['link'] = ''
        else:
            # Se não encontra o elemento título, define valores vazios
            dados['titulo'] = ''
            dados['link'] = ''
        
        # Extração da descrição/resumo da resolução
        # A descrição está em um span com classe 'description'
        desc_elem = artigo.find('span', class_='description')
        dados['descricao'] = desc_elem.text.strip() if desc_elem else ''
        
        # Extração de tags/categorias
        # As tags estão em links dentro de uma div com classe 'keywords'
        tags_elem = artigo.find('div', class_='keywords')
        if tags_elem:
            tag_links = tags_elem.find_all('a', class_='link-category')
            tags = [tag.text.strip() for tag in tag_links]
            dados['tags'] = ', '.join(tags)  # Une as tags em uma string separada por vírgulas
        else:
            dados['tags'] = ''
        
        # Extração de data e hora de publicação
        # Estas informações estão na linha de informações do documento
        byline = artigo.find('span', class_='documentByLine')
        dados['data_publicacao'] = ''
        dados['hora_publicacao'] = ''
        
        if byline:
            # Procura por ícones que indicam data e hora
            date_icons = byline.find_all('span', class_='summary-view-icon')
            for icon_span in date_icons:
                icon = icon_span.find('i')
                # Ícone de dia (calendário) indica data de publicação
                if icon and 'icon-day' in icon.get('class', []):
                    dados['data_publicacao'] = icon_span.get_text().strip()
                # Ícone de relógio indica hora de publicação
                elif icon and 'icon-hour' in icon.get('class', []):
                    dados['hora_publicacao'] = icon_span.get_text().strip()
        
        return dados
        
    except Exception as e:
        print(f"Erro ao processar artigo: {e}")
        # Em caso de erro, retorna estrutura padrão com valores vazios
        return {
            'titulo': '',
            'link': '',
            'descricao': '',
            'tags': '',
            'data_publicacao': '',
            'hora_publicacao': ''
        }


def coletar_dados_pagina(url: str, ano: str) -> list[dict[str, str]]:
    """
    Coleta dados de todos os artigos em uma página específica.
    
    Esta função acessa uma página do CNS de um ano específico e extrai
    todas as resoluções listadas nessa página. Cada resolução é processada
    pela função extrair_dados_artigo().
    
    Args:
        url (str): URL da página a ser processada
        ano (str): Ano de referência para identificação
        
    Returns:
        list[dict[str, str]]: Lista de dicionários contendo os dados dos artigos/resoluções
    """
    try:
        print(f"Coletando dados de {ano}: {url}")
        
        # Faz a requisição HTTP para obter o conteúdo da página
        response = requests.get(url)
        response.raise_for_status()  # Levanta exceção se houver erro HTTP
        
        # Parse do HTML usando BeautifulSoup
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Localiza a div principal que contém os artigos
        # O site do CNS usa uma div com id 'content-core' como container principal
        content_core = soup.find('div', id='content-core')
        if not content_core:
            print(f"Aviso: content-core não encontrado para {ano}")
            return []
        
        # Encontra todos os elementos article que representam as resoluções
        # Cada resolução é um elemento <article> com classe 'tileItem'
        articles = []
        if isinstance(content_core, Tag):
            articles = content_core.find_all('article', class_='tileItem')
        
        # Processa cada artigo encontrado
        dados_artigos = []
        for artigo in articles:
            dados = extrair_dados_artigo(artigo)
            dados['ano'] = ano  # Adiciona o ano aos dados da resolução
            dados_artigos.append(dados)
            
        print(f"Coletados {len(dados_artigos)} artigos de {ano}")
        return dados_artigos
        
    except Exception as e:
        print(f"Erro ao coletar dados de {ano}: {e}")
        return []  # Retorna lista vazia em caso de erro


def coletar_todos_dados() -> list[dict[str, str]]:
    """
    Função principal para coletar dados de todas as páginas do CNS.
    
    Esta função orquestra o processo completo de coleta, processando
    todas as páginas de resoluções do CNS desde 2025 até 1988.
    Inclui salvamento progressivo para evitar perda de dados.
    
    Returns:
        list[dict[str, str]]: Todos os dados coletados de todas as páginas
    """
    # Gera lista de URLs de todas as páginas a serem processadas
    urls_paginas = gerar_urls_paginas()  # Função corrigida: era generate_page_urls
    todos_dados = []
    total_paginas = len(urls_paginas)
    
    print(f"Iniciando coleta de {total_paginas} páginas...")
    
    # Processa cada página (ano) individualmente
    for i, url in enumerate(urls_paginas, 1):
        # Extrai o ano da URL para identificação
        ano = url.split('/')[-1]
        print(f"Progresso: {i}/{total_paginas} - Processando ano {ano}")
        
        # Coleta dados da página atual
        dados_pagina = coletar_dados_pagina(url, ano)
        todos_dados.extend(dados_pagina)  # Adiciona os dados à lista geral
        
        # Pausa respeitosa entre requisições para não sobrecarregar o servidor
        # Isso é uma boa prática em web scraping
        time.sleep(1)
        
        # Salvamento progressivo a cada 5 páginas para evitar perda de dados
        # Em caso de erro ou interrupção, os dados não são perdidos
        if i % 5 == 0:
            df_temp = pd.DataFrame(todos_dados)
            df_temp.to_csv(f'cns_resolucoes_temp_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv', 
                          index=False, encoding='utf-8')
            print(f"Salvamento temporário realizado após {i} páginas")
    
    return todos_dados


def converter_link_visualizacao_para_download(link_visualizacao: str) -> str:
    """
    Converte link de visualização para link de download direto do PDF.
    
    O site do CNS fornece links de visualização no formato '/view',
    mas para download direto precisamos converter para '/@@download/file'.
    
    Args:
        link_visualizacao (str): Link original de visualização
        
    Returns:
        str: Link modificado para download direto
    """
    if link_visualizacao and '/view' in link_visualizacao:
        return link_visualizacao.replace('/view', '/@@download/file')
    return link_visualizacao


def limpar_nome_arquivo(titulo: str, tamanho_maximo: int = 100) -> str:
    """
    Limpa o título para criar um nome de arquivo válido.
    
    Remove caracteres especiais que podem causar problemas no sistema
    de arquivos e limita o tamanho do nome do arquivo.
    
    Args:
        titulo (str): Título original da resolução
        tamanho_maximo (int): Comprimento máximo do nome do arquivo
        
    Returns:
        str: Nome de arquivo limpo e válido
    """
    if not titulo:
        return "resolucao_sem_titulo"
    
    import string
    # Define caracteres válidos para nomes de arquivo
    # Inclui letras, números, espaços e alguns símbolos básicos
    valid_chars = "-_.() %s%s" % (string.ascii_letters, string.digits)
    titulo_limpo = ''.join(c for c in titulo if c in valid_chars)
    
    # Remove espaços duplos e limita o tamanho
    titulo_limpo = ' '.join(titulo_limpo.split())
    if len(titulo_limpo) > tamanho_maximo:
        titulo_limpo = titulo_limpo[:tamanho_maximo]
    
    return titulo_limpo


def baixar_pdf(url: str, caminho_arquivo: str | Path, timeout: int = 30) -> tuple[bool, str]:
    """
    Baixa um PDF de uma URL e salva no caminho especificado.
    
    Esta função faz o download de um arquivo PDF usando urllib e salva
    no sistema de arquivos local. Inclui headers de User-Agent para
    evitar bloqueios por parte do servidor.
    
    Args:
        url (str): URL do arquivo PDF a ser baixado
        caminho_arquivo (str | Path): Caminho de destino onde salvar o arquivo
        timeout (int): Tempo limite para a requisição em segundos
        
    Returns:
        tuple[bool, str]: (sucesso: bool, mensagem: str) indicando resultado da operação
    """
    try:
        # Headers para simular um navegador real e evitar bloqueios
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        # Cria requisição com headers personalizados
        req = urllib.request.Request(url, headers=headers)
        
        # Abre a conexão e faz o download
        with urllib.request.urlopen(req, timeout=timeout) as response:
            # Verifica se o conteúdo é realmente um PDF
            content_type = response.headers.get('Content-Type', '')
            if 'pdf' not in content_type.lower() and response.headers.get('Content-Disposition'):
                print(f"Aviso: Content-Type não é PDF: {content_type}")
            
            # Salva o arquivo no disco
            with open(str(caminho_arquivo), 'wb') as f:
                shutil.copyfileobj(response, f)
            
            return True, "Download concluído"
            
    except Exception as e:
        return False, str(e)


def baixar_todos_pdfs(arquivo_csv: str, pasta_destino: str = "pdfs_cns_resolucoes", pular_existentes: bool = True) -> dict[str, int | str] | None:
    """
    Baixa todos os PDFs de resoluções listadas no CSV.
    
    Esta função lê um arquivo CSV contendo dados de resoluções do CNS
    e faz o download de todos os PDFs correspondentes, organizando-os
    em pastas por ano. Inclui controle de progresso e tratamento de erros.
    
    Args:
        arquivo_csv (str): Caminho para o arquivo CSV
        pasta_destino (str): Pasta de destino para os PDFs
        pular_existentes (bool): Pular arquivos já baixados
        
    Returns:
        dict[str, int | str] | None: Estatísticas do download incluindo sucessos, erros e arquivos pulados
    """
    if not os.path.exists(arquivo_csv):
        print(f"Erro: Arquivo {arquivo_csv} não encontrado!")
        return None
    
    df = pd.read_csv(arquivo_csv)
    print(f"Arquivo carregado com {len(df)} resoluções")
    
    # Cria pasta principal
    pasta_base = Path(pasta_destino)
    pasta_base.mkdir(exist_ok=True)
    
    # Contadores e listas de controle
    sucessos = 0
    erros = 0
    pulados = 0
    log_erros = []
    
    total = len(df)
    
    print(f"Iniciando download de {total} PDFs...")
    print(f"Pasta de destino: {pasta_base.absolute()}")
    print("=" * 60)
    
    contador = 0
    for _, linha in df.iterrows():
        contador += 1
        try:
            titulo = linha.get('titulo', '')
            link_visualizacao = linha.get('link', '')
            ano = linha.get('ano', 'sem_ano')
            
            if not link_visualizacao:
                print(f"{contador}/{total} - Pulando: sem link - {titulo[:50]}...")
                pulados += 1
                continue
            
            link_download = converter_link_visualizacao_para_download(link_visualizacao)
            
            # Cria pasta do ano
            pasta_ano = pasta_base / str(ano)
            pasta_ano.mkdir(exist_ok=True)
            
            # Cria nome do arquivo
            nome_limpo = limpar_nome_arquivo(titulo)
            nome_arquivo = f"{nome_limpo}.pdf"
            caminho_arquivo = pasta_ano / nome_arquivo
            
            # Verifica se já existe
            if pular_existentes and caminho_arquivo.exists():
                print(f"{contador}/{total} - Já existe: {nome_arquivo}")
                pulados += 1
                continue
            
            # Tenta fazer o download
            print(f"{contador}/{total} - Baixando: {nome_arquivo}")
            sucesso, mensagem = baixar_pdf(link_download, caminho_arquivo)
            
            if sucesso:
                print(f"  ✓ Sucesso: {caminho_arquivo.stat().st_size / 1024:.1f} KB")
                sucessos += 1
            else:
                print(f"  ✗ Erro: {mensagem}")
                erros += 1
                log_erros.append({
                    'titulo': titulo,
                    'link': link_visualizacao,
                    'erro': mensagem
                })
                
                if caminho_arquivo.exists():
                    caminho_arquivo.unlink()
            
            time.sleep(0.5)  # Respectful pause
            
            if contador % 10 == 0:
                print(f"  Progresso: {contador}/{total} - Sucessos: {sucessos}, Erros: {erros}, Pulados: {pulados}")
                
        except Exception as e:
            print(f"{contador}/{total} - Erro inesperado: {e}")
            erros += 1
            log_erros.append({
                'titulo': linha.get('titulo', ''),
                'link': linha.get('link', ''),
                'erro': str(e)
            })
    
    # Relatório final
    print("=" * 60)
    print("RELATÓRIO FINAL:")
    print(f"Total processado: {total}")
    print(f"Downloads bem-sucedidos: {sucessos}")
    print(f"Erros: {erros}")
    print(f"Pulados (já existem): {pulados}")
    print(f"Pasta de destino: {pasta_base.absolute()}")
    
    # Salva log de erros se houver algum
    if log_erros:
        nome_log = f"log_erros_download_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        df_erros = pd.DataFrame(log_erros)
        df_erros.to_csv(nome_log, index=False, encoding='utf-8')
        print(f"Log de erros salvo em: {nome_log}")
    
    return {
        'sucessos': sucessos,
        'erros': erros,
        'pulados': pulados,
        'pasta_destino': str(pasta_base.absolute())
    }


def main() -> Any:
    """
    Função principal de execução do scraper.
    
    Orquestra todo o processo de coleta de dados das resoluções do CNS,
    incluindo a extração de dados de todas as páginas, salvamento em CSV
    e apresentação de estatísticas finais.
    
    Returns:
        Any: DataFrame do pandas com todos os dados coletados
    """
    print("Iniciando coleta de Resoluções do CNS...")
    urls_paginas = gerar_urls_paginas()
    print(f"Processará {len(urls_paginas)} páginas (anos {urls_paginas[-1].split('/')[-1]} a {urls_paginas[0].split('/')[-1]})")
    print("=" * 60)
    
    # Coleta todos os dados
    dados_coletados = coletar_todos_dados()
    
    print("=" * 60)
    print(f"Coleta concluída! Total de resoluções coletadas: {len(dados_coletados)}")
    
    # Converte para DataFrame
    df_final = pd.DataFrame(dados_coletados)
    
    # Mostra informações sobre os dados coletados
    print("\nResumo dos dados coletados:")
    print(f"Total de registros: {len(df_final)}")
    print(f"Colunas: {list(df_final.columns)}")
    print(f"Anos com dados: {sorted(df_final['ano'].unique())}")
    
    # Salva arquivo final
    nome_arquivo_final = f'cns_resolucoes_completo_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
    df_final.to_csv(nome_arquivo_final, index=False, encoding='utf-8')
    
    print(f"\nArquivo final salvo como: {nome_arquivo_final}")
    print(f"Localização: {os.path.abspath(nome_arquivo_final)}")
    
    # Mostra amostra dos dados
    print("\nAmostra dos primeiros 3 registros:")
    print(df_final.head(3).to_string())
    
    return df_final


if __name__ == "__main__":
    main()