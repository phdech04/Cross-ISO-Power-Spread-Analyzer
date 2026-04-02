from setuptools import setup, find_packages

setup(
    name="power-spread-analyzer",
    version="0.1.0",
    description="Cross-ISO Power Spread Analyzer for North American electricity markets",
    author="Phemo",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    python_requires=">=3.10",
    install_requires=[
        "pandas>=2.0",
        "numpy>=1.24",
        "requests>=2.31",
        "pyarrow>=14.0",
        "pyyaml>=6.0",
        "duckdb>=0.9",
        "plotly>=5.18",
        "streamlit>=1.29",
        "scikit-learn>=1.3",
        "hmmlearn>=0.3",
        "statsmodels>=0.14",
        "scipy>=1.11",
        "fastapi>=0.104",
        "uvicorn>=0.24",
    ],
    extras_require={
        "dev": ["pytest>=7.4"],
    },
)
