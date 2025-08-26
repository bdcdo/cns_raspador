"""
Script de configuração para instalação do CNS Raspador.

Este arquivo define as configurações necessárias para instalar o CNS Raspador
como um pacote Python, incluindo dependências, metadados e scripts de linha de comando.
"""

from setuptools import setup, find_packages

# Lê a descrição longa do arquivo README.md
with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

# Lê as dependências do arquivo requirements.txt
with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = [line.strip() for line in fh if line.strip() and not line.startswith("#")]

setup(
    name="cns-raspador",
    version="1.0.0",
    author="Equipe CNS Raspador",
    author_email="contato@cns-raspador.com",
    description="Ferramenta completa para coleta, download e extração de texto das resoluções do Conselho Nacional de Saúde (CNS)",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/cns-raspador/cns-raspador",
    packages=find_packages(),
    classifiers=[
        # Estado de desenvolvimento
        "Development Status :: 4 - Beta",
        
        # Público-alvo
        "Intended Audience :: Researchers",
        "Intended Audience :: Developers",
        "Intended Audience :: Healthcare Industry",
        "Intended Audience :: Legal Industry",
        "Intended Audience :: Science/Research",
        
        # Tópicos
        "Topic :: Scientific/Engineering :: Information Analysis",
        "Topic :: Text Processing :: Markup :: HTML",
        "Topic :: Office/Business :: Office Suites",
        "Topic :: Database",
        
        # Licença
        "License :: OSI Approved :: MIT License",
        
        # Versões do Python suportadas
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        
        # Sistema operacional
        "Operating System :: OS Independent",
        "Operating System :: POSIX :: Linux",
        "Operating System :: Microsoft :: Windows",
        "Operating System :: MacOS",
        
        # Idioma natural
        "Natural Language :: Portuguese (Brazilian)",
    ],
    python_requires=">=3.7",
    install_requires=requirements,
    entry_points={
        "console_scripts": [
            "cns-raspador=main:main",
        ],
    },
    keywords="cns, conselho-nacional-saude, web-scraping, pdf-extraction, health-council, brazil, government-data, resolucoes, saude-publica, dados-governamentais",
    project_urls={
        "Código Fonte": "https://github.com/cns-raspador/cns-raspador",
        "Relatório de Bugs": "https://github.com/cns-raspador/cns-raspador/issues",
        "Documentação": "https://github.com/cns-raspador/cns-raspador/wiki",
        "Changelog": "https://github.com/cns-raspador/cns-raspador/releases",
    },
)