from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = fh.read().splitlines()

setup(
    name="memory_engine",
    version="0.1.0",
    author="MemoryBlockEngine Team",
    author_email="example@example.com",
    description="LLM 독립적 메모리 시스템",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/username/MemoryBlockEngine",
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
            "memory-engine=memory_engine.cli:main",
        ],
    },
) 