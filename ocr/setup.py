"""Setup script for OCR Extractor."""

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="ocr-extractor",
    version="0.1.0",
    author="Your Name",
    author_email="your.email@example.com",
    description="PDF to text extraction pipeline using OCR",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/ocr-extractor",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
    python_requires=">=3.8",
    install_requires=[
        "pdf2image>=1.17.0",
        "Pillow>=10.0.0",
        "openai>=1.0.0",
        "click>=8.1.0",
        "pydantic>=2.0.0",
        "pydantic-settings>=2.0.0",
        "python-dotenv>=1.0.0",
        "python-docx>=0.8.11",
    ],
    extras_require={
        "dev": [
            "pytest>=7.4.0",
            "black>=23.0.0",
            "isort>=5.12.0",
            "flake8>=6.0.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "ocr-extract=ocr_extractor.cli:main",
        ],
    },
)