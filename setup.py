from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="greeum",
    version="0.5.2",
    author="Greeum Team",
    author_email="playtart@play-t.art",
    description="LLM-Independent Memory System with Multilingual Support",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/DryRainEnt/Greeum",
    packages=find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.7",
    install_requires=[
        "numpy>=1.20.0",
        "flask>=2.0.0",
        "sqlalchemy>=1.4.0",
        "requests>=2.25.0",
        "python-dotenv>=0.19.0",
        "flask-restx>=0.5.1",
        "flask-cors>=3.0.10",
        "click>=8.0.0",
        "rich>=10.0.0",
        "typer>=0.4.0",
        "python-dateutil>=2.8.2",
    ],
    extras_require={
        "embedding": ["sentence-transformers>=2.2.0", "openai>=0.27.0"],
        "nlp": ["spacy>=3.5.0"],
        "all": [
            "sentence-transformers>=2.2.0", 
            "openai>=0.27.0",
            "spacy>=3.5.0",
            "gunicorn>=20.1.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "greeum=greeum.cli:main",
        ],
    },
) 