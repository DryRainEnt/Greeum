from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = fh.read().splitlines()

setup(
    name="greeum",
    version="0.1.0",
    author="Greeum Team",
    author_email="playtart@play-t.art",
    description="LLM-Independent Memory System",
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
    install_requires=requirements,
    entry_points={
        "console_scripts": [
            "greeum=greeum.cli:main",
        ],
    },
) 