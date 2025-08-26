"""Setup script for CNS Raspador."""

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = [line.strip() for line in fh if line.strip() and not line.startswith("#")]

setup(
    name="cns-raspador",
    version="1.0.0",
    author="Your Name",
    author_email="your.email@example.com",
    description="Raspador completo para resoluções do Conselho Nacional de Saúde (CNS)",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/cns-raspador",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Researchers",
        "Intended Audience :: Developers",
        "Topic :: Scientific/Engineering :: Information Analysis",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.7",
    install_requires=requirements,
    entry_points={
        "console_scripts": [
            "cns-raspador=main:main",
        ],
    },
    keywords="cns, web-scraping, pdf-extraction, health-council, brazil, government-data",
    project_urls={
        "Bug Reports": "https://github.com/yourusername/cns-raspador/issues",
        "Source": "https://github.com/yourusername/cns-raspador",
    },
)