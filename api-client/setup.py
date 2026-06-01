from setuptools import setup, find_packages

setup(
    name="gisele_ts",
    version="0.1.0",
    description="Cliente Python para extracao de serie temporal GISELE (CPTEC/INPE)",
    long_description=open("README.md", encoding="utf-8").read(),
    long_description_content_type="text/markdown",
    author="Jorge Luis Gomes",
    author_email="jorge.gomes@inpe.br",
    license="MIT",
    packages=find_packages(),
    python_requires=">=3.9",
    install_requires=[
        "requests>=2.28",
    ],
    extras_require={
        "pandas": ["pandas>=1.5"],
        "dev": ["pytest>=7.0", "ruff>=0.1"],
    },
    entry_points={
        "console_scripts": [
            "gisele-ts = gisele_ts.__main__:main",
        ],
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "License :: OSI Approved :: MIT License",
        "Topic :: Scientific/Engineering :: Atmospheric Science",
        "Operating System :: OS Independent",
    ],
)
