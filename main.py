#!/usr/bin/env python3
"""
CNS Raspador - Interface Principal de Linha de Comando

Interface de linha de comando para coletar resoluções do CNS (Conselho Nacional 
de Saúde) do site oficial do governo brasileiro.

Este script oferece comandos para:
- Coletar metadados das resoluções do site do CNS
- Baixar os arquivos PDF das resoluções
- Extrair texto dos PDFs para análise
- Executar todo o pipeline completo
- Verificar o status atual dos dados

Uso:
    python main.py scrape                    # Coleta dados das resoluções
    python main.py download [ARQUIVO_CSV]    # Baixa PDFs das resoluções
    python main.py extract [ARQUIVO_CSV]     # Extrai texto dos PDFs
    python main.py full                      # Pipeline completo (coletar + baixar + extrair)
    python main.py status                    # Mostra status do projeto

Exemplos:
    python main.py scrape                    # Inicia coleta de resoluções
    python main.py download resolucoes.csv   # Baixa PDFs do arquivo especificado
    python main.py full                      # Executa processo completo
"""

import argparse
import sys
import os
from pathlib import Path

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.scraper import main as scraper_main, baixar_todos_pdfs
from src.text_extractor import criar_base_completa_com_textos
import glob


def encontrar_csv_mais_recente(padrao="cns_resolucoes_*.csv", padroes_exclusao=None):
    """
    Encontra o arquivo CSV mais recente que corresponde ao padrão especificado.
    
    Esta função é útil para automaticamente usar o arquivo CSV mais recente
    quando o usuário não especifica um arquivo específico.
    
    Args:
        padrao (str): Padrão glob para buscar arquivos CSV
        padroes_exclusao (list): Lista de padrões a excluir da busca
        
    Returns:
        str: Caminho para o arquivo CSV mais recente, ou None se nenhum for encontrado
    """
    if padroes_exclusao is None:
        padroes_exclusao = ['teste', 'com_textos', 'temp']
    
    arquivos_csv = glob.glob(padrao)
    arquivos_csv = [f for f in arquivos_csv if not any(excl in f for excl in padroes_exclusao)]
    
    if not arquivos_csv:
        return None
    
    return max(arquivos_csv, key=os.path.getctime)


def cmd_coletar(_args):
    """
    Executa o comando de coleta de dados das resoluções.
    
    Este comando acessa o site oficial do CNS e coleta todos os metadados
    das resoluções disponíveis, salvando em um arquivo CSV.
    
    Args:
        _args: Argumentos da linha de comando (não utilizados neste comando)
        
    Returns:
        bool: True se a coleta foi bem-sucedida, False caso contrário
    """
    del _args  # Suprime aviso de variável não utilizada
    print("🕷️ Iniciando coleta de metadados das resoluções CNS...")
    df_resultado = scraper_main()
    if df_resultado is not None:
        print("✅ Coleta concluída com sucesso!")
        return True
    else:
        print("❌ Coleta falhou!")
        return False


def cmd_baixar(args):
    """
    Executa o comando de download dos arquivos PDF das resoluções.
    
    Este comando lê um arquivo CSV com dados das resoluções e baixa
    os arquivos PDF correspondentes, organizando-os por ano.
    
    Args:
        args: Argumentos da linha de comando contendo:
              - csv_file: Caminho para arquivo CSV (opcional)
              
    Returns:
        bool: True se o download foi bem-sucedido, False caso contrário
    """
    arquivo_csv = args.csv_file
    
    if not arquivo_csv:
        arquivo_csv = encontrar_csv_mais_recente()
        if not arquivo_csv:
            print("❌ Nenhum arquivo CSV encontrado!")
            print("   Dica: Execute 'python main.py scrape' primeiro ou especifique um arquivo CSV.")
            return False
        print(f"📁 Usando o arquivo CSV mais recente: {arquivo_csv}")
    
    if not os.path.exists(arquivo_csv):
        print(f"❌ Arquivo CSV não encontrado: {arquivo_csv}")
        return False
    
    print(f"📥 Iniciando download de PDFs de: {arquivo_csv}")
    resultado = baixar_todos_pdfs(arquivo_csv, pular_existentes=True)
    
    # A etapa é considerada um sucesso se não houver erros.
    # Não importa se os arquivos foram baixados agora ou já existiam.
    if resultado and isinstance(resultado, dict) and resultado.get('erros', 0) == 0:
        print("✅ Etapa de download concluída (nenhum erro encontrado).")
        return True
    else:
        # Mostra o número de erros, se disponível
        num_erros = resultado.get('erros', 'desconhecido') if isinstance(resultado, dict) else 'desconhecido'
        print(f"❌ Download de PDFs falhou! Erros reportados: {num_erros}")
        return False


def cmd_extrair(args):
    """
    Executa o comando de extração de texto dos PDFs baixados.
    
    Este comando processa todos os arquivos PDF baixados, extrai o texto
    de cada um e combina com os metadados das resoluções, gerando uma
    base de dados completa.
    
    Args:
        args: Argumentos da linha de comando contendo:
              - csv_file: Caminho para arquivo CSV (opcional)
              
    Returns:
        bool: True se a extração foi bem-sucedida, False caso contrário
    """
    arquivo_csv = args.csv_file
    
    if not arquivo_csv:
        arquivo_csv = encontrar_csv_mais_recente()
        if not arquivo_csv:
            print("❌ Nenhum arquivo CSV encontrado!")
            print("   Dica: Execute 'python main.py scrape' primeiro ou especifique um arquivo CSV.")
            return False
        print(f"📁 Usando o arquivo CSV mais recente: {arquivo_csv}")
    
    if not os.path.exists(arquivo_csv):
        print(f"❌ Arquivo CSV não encontrado: {arquivo_csv}")
        return False
    
    print(f"📄 Iniciando extração de texto de: {arquivo_csv}")
    df_resultado = criar_base_completa_com_textos(arquivo_csv)
    
    if df_resultado is not None:
        print("✅ Extração de texto concluída com sucesso!")
        return True
    else:
        print("❌ Extração de texto falhou!")
        return False


def cmd_completo(args):
    """
    Executa o pipeline completo de processamento das resoluções CNS.
    
    Este comando executa sequencialmente:
    1. Coleta de dados das resoluções do site oficial
    2. Download dos arquivos PDF das resoluções
    3. Extração de texto dos PDFs e combinação com metadados
    
    É a forma mais conveniente de obter uma base completa de dados.
    
    Args:
        args: Argumentos da linha de comando
        
    Returns:
        bool: True se todo o pipeline foi executado com sucesso, False caso contrário
    """
    print("🚀 Iniciando pipeline completo de processamento de resoluções CNS...")
    print("=" * 60)
    
    # PASSO 1: Coleta de metadados
    print("📊 PASSO 1: Coletando metadados das resoluções...")
    if not cmd_coletar(args):
        return False
    
    # Encontra o arquivo CSV criado pela coleta
    arquivo_csv = encontrar_csv_mais_recente()
    if not arquivo_csv:
        print("❌ Não foi possível encontrar o arquivo CSV recém coletado!")
        print("   Verifique se a coleta foi concluída com sucesso.")
        return False
    
    # PASSO 2: Download dos arquivos PDF
    print(f"\n📥 PASSO 2: Baixando arquivos PDF das resoluções...")
    args.csv_file = arquivo_csv  # Define arquivo CSV para as etapas seguintes
    if not cmd_baixar(args):
        return False
    
    # PASSO 3: Extração de texto dos PDFs
    print(f"\n📄 PASSO 3: Extraindo texto dos PDFs e criando base completa...")
    if not cmd_extrair(args):
        return False
    
    print("\n🎉 Pipeline completo concluído com sucesso!")
    print("📊 Sua base completa de resoluções CNS está pronta para uso!")
    print("📁 Verifique os arquivos gerados no diretório atual.")
    return True


def cmd_status(_args):
    """
    Mostra o status atual do projeto CNS Raspador.
    
    Este comando examina o diretório atual e mostra informações sobre:
    - Arquivos CSV de resoluções coletadas
    - Arquivos PDF baixados (total e distribuição por ano)
    - Arquivos de extração de texto processados
    
    Útil para verificar o progresso e entender o estado atual dos dados.
    
    Args:
        _args: Argumentos da linha de comando (não utilizados neste comando)
    """
    del _args  # Suprime aviso de variável não utilizada
    print("📊 Status do Projeto CNS Raspador")
    print("=" * 40)
    
    # Verificar arquivos CSV
    arquivos_csv = glob.glob("cns_resolucoes_*.csv")
    if arquivos_csv:
        print(f"📄 Arquivos CSV encontrados: {len(arquivos_csv)}")
        mais_recente = encontrar_csv_mais_recente()
        if mais_recente:
            print(f"   Mais recente: {mais_recente}")
    else:
        print("📄 Nenhum arquivo CSV de resoluções encontrado")
        print("   Execute 'python main.py scrape' para coletar os dados")
    
    # Verificar PDFs
    pasta_pdfs = Path("pdfs_cns_resolucoes")
    if pasta_pdfs.exists():
        total_pdfs = len(list(pasta_pdfs.glob("**/*.pdf")))
        print(f"📁 PDFs baixados: {total_pdfs}")
        
        # Contar por ano
        pastas_ano = [f for f in pasta_pdfs.iterdir() if f.is_dir()]
        if pastas_ano:
            print("   Distribuição por ano:")
            for pasta_ano in sorted(pastas_ano):
                quantidade = len(list(pasta_ano.glob("*.pdf")))
                print(f"     {pasta_ano.name}: {quantidade} PDFs")
    else:
        print("📁 Nenhuma pasta de PDFs encontrada")
        print("   Execute 'python main.py download' para baixar os PDFs")
    
    # Verificar resultados de extração de texto
    arquivos_texto = glob.glob("cns_resolucoes_com_textos_*.csv")
    if arquivos_texto:
        print(f"📝 Arquivos de extração de texto: {len(arquivos_texto)}")
        texto_mais_recente = max(arquivos_texto, key=os.path.getctime)
        print(f"   Mais recente: {texto_mais_recente}")
    else:
        print("📝 Nenhum arquivo com texto extraído encontrado")
        print("   Execute 'python main.py extract' para processar os PDFs")


def main():
    """
    Função principal da interface de linha de comando.
    
    Configura o parser de argumentos, define todos os subcomandos disponíveis
    e executa o comando solicitado pelo usuário.
    
    Os comandos disponíveis são:
    - scrape: Coleta dados das resoluções
    - download: Baixa arquivos PDF
    - extract: Extrai texto dos PDFs
    - full: Executa pipeline completo
    - status: Mostra status do projeto
    """
    parser = argparse.ArgumentParser(
        description="CNS Raspador - Ferramenta completa para coleta e processamento de resoluções do Conselho Nacional de Saúde",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemplos de uso:
  python main.py scrape                  # Coleta dados das resoluções
  python main.py download                # Baixa PDFs (usa CSV mais recente)
  python main.py extract resolucoes.csv # Extrai texto do arquivo especificado
  python main.py full                    # Executa processo completo
  python main.py status                  # Verifica status atual

Para mais informações sobre cada comando, use: python main.py <comando> --help
        """
    )
    
    subparsers = parser.add_subparsers(
        dest='command', 
        help='Comandos disponíveis',
        metavar='COMANDO',
        description='Use um dos comandos abaixo para executar ações específicas'
    )
    
    # Comando de coleta
    parser_scrape = subparsers.add_parser(
        'scrape', 
        help='Coleta metadados das resoluções do site oficial do CNS',
        description='Acessa o site oficial do CNS e coleta informações sobre todas as resoluções disponíveis'
    )
    
    # Comando de download
    parser_download = subparsers.add_parser(
        'download', 
        help='Baixa os arquivos PDF das resoluções',
        description='Baixa todos os arquivos PDF das resoluções listadas no arquivo CSV, organizando por ano'
    )
    parser_download.add_argument(
        'csv_file', 
        nargs='?', 
        help='Arquivo CSV com dados das resoluções (opcional - usa o mais recente se não especificado)',
        metavar='ARQUIVO_CSV'
    )
    
    # Comando de extração
    parser_extrair = subparsers.add_parser(
        'extract', 
        help='Extrai texto dos PDFs baixados e cria base completa',
        description='Processa todos os PDFs baixados, extrai o texto e combina com os metadados das resoluções'
    )
    parser_extrair.add_argument(
        'csv_file', 
        nargs='?', 
        help='Arquivo CSV com dados das resoluções (opcional - usa o mais recente se não especificado)',
        metavar='ARQUIVO_CSV'
    )
    
    # Comando de pipeline completo
    parser_full = subparsers.add_parser(
        'full', 
        help='Executa o pipeline completo (coletar + baixar + extrair)',
        description='Executa automaticamente todo o processo: coleta de dados, download de PDFs e extração de texto'
    )
    
    # Comando de status
    parser_status = subparsers.add_parser(
        'status', 
        help='Mostra o status atual do projeto',
        description='Examina os arquivos do projeto e mostra estatísticas sobre dados coletados, PDFs baixados e texto extraído'
    )
    
    # Processa os argumentos da linha de comando
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    # Mapeia comandos para suas respectivas funções
    comandos = {
        'scrape': cmd_coletar,      # Coleta de dados
        'download': cmd_baixar,     # Download de PDFs
        'extract': cmd_extrair,     # Extração de texto
        'full': cmd_completo,       # Pipeline completo
        'status': cmd_status        # Status do projeto
    }
    
    # Executa o comando selecionado
    try:
        sucesso = comandos[args.command](args)
        sys.exit(0 if sucesso else 1)
    except KeyboardInterrupt:
        print("\n\n❌ Operação interrompida pelo usuário")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Erro inesperado: {e}")
        print("Execute 'python main.py status' para verificar o estado atual")
        sys.exit(1)


if __name__ == "__main__":
    main()