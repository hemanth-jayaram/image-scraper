"""
Setup script for Article Image Scraper Pipeline
"""

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = [line.strip() for line in fh if line.strip() and not line.startswith("#")]

setup(
    name="article-image-scraper",
    version="2.0.0",
    author="Article Image Scraper Team",
    author_email="contact@example.com",
    description="A production-ready Python pipeline for extracting the single most relevant image from article URLs",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/article-image-scraper",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: Internet :: WWW/HTTP :: Indexing/Search",
        "Topic :: Multimedia :: Graphics",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
    python_requires=">=3.7",
    install_requires=requirements,
    entry_points={
        "console_scripts": [
            "article-image-scraper=image_scraper_pipeline:main",
        ],
    },
    keywords="web-scraping, image-extraction, article-processing, opengraph, schema.org, trafilatura",
    project_urls={
        "Bug Reports": "https://github.com/yourusername/article-image-scraper/issues",
        "Source": "https://github.com/yourusername/article-image-scraper",
        "Documentation": "https://github.com/yourusername/article-image-scraper#readme",
    },
)
