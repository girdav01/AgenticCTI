"""
Setup configuration for AgenticCTI.
"""

from setuptools import setup, find_packages
from pathlib import Path

# Read README
readme_file = Path(__file__).parent / "README.md"
long_description = readme_file.read_text(encoding="utf-8") if readme_file.exists() else ""

# Read requirements
requirements_file = Path(__file__).parent / "requirements.txt"
requirements = []
if requirements_file.exists():
    with open(requirements_file, 'r') as f:
        requirements = [
            line.strip()
            for line in f
            if line.strip() and not line.startswith('#')
        ]

setup(
    name="agentic-cti",
    version="1.0.0",
    author="AgenticCTI Team",
    author_email="contact@example.com",
    description="Autonomous Cyber Threat Intelligence Platform with LLM autonomy",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/AgenticCTI",
    packages=find_packages(exclude=["tests", "tests.*"]),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Information Technology",
        "Intended Audience :: System Administrators",
        "Topic :: Security",
        "Topic :: Internet :: WWW/HTTP :: Indexing/Search",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
    python_requires=">=3.9",
    install_requires=requirements,
    extras_require={
        "dev": [
            "pytest>=7.4.0",
            "pytest-cov>=4.1.0",
            "mypy>=1.7.0",
            "black>=23.0.0",
            "flake8>=6.0.0",
        ],
        "openai": ["openai>=1.0.0"],
        "anthropic": ["anthropic>=0.18.0"],
    },
    entry_points={
        "console_scripts": [
            "agentic-cti=main:main",
        ],
    },
    include_package_data=True,
    package_data={
        "": ["*.yaml", "*.yml", "*.json"],
    },
    keywords=[
        "cybersecurity",
        "threat-intelligence",
        "cti",
        "security",
        "stix",
        "automation",
        "llm",
        "ai",
    ],
)
