# Changelog

All notable changes to the Article Image Scraper Pipeline will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [2.0.0] - 2025-01-15

### Added
- **OpenGraph support**: Extract images from `og:image` meta tags with +25 bonus points
- **Schema.org structured data**: Parse JSON-LD for article images with +22 bonus points
- **Twitter Card support**: Extract `twitter:image` meta tags with +20 bonus points
- **Advanced context analysis**: HTML hierarchy analysis for better image relevance
- **JPG conversion**: Automatic conversion of all images to JPG format with transparency handling
- **Single image output**: Only the most relevant image per article (no clutter)
- **Enhanced scoring system**: 0-100 point scoring with detailed penalties and bonuses
- **Tracking pixel protection**: Specific blocking of Facebook, Google Analytics, and other tracking URLs
- **Configuration file**: Centralized settings in `config.py`
- **Example articles**: Sample JSON files for testing
- **Comprehensive documentation**: Updated README with detailed usage and features

### Changed
- **Scoring thresholds**: Raised minimum acceptable score to 40 points
- **Method prioritization**: OpenGraph > Schema.org > Trafilatura > Newspaper3k > BeautifulSoup
- **URL filtering**: Enhanced pattern matching for better tracking pixel detection
- **Image validation**: Improved size validation with PIL integration
- **Error handling**: More detailed logging and error reporting

### Fixed
- **Facebook tracking pixel bypass**: Fixed URL filtering to properly block `facebook.com/tr` patterns
- **Logo detection**: Improved algorithms to better identify and exclude company logos
- **Image quality**: Better selection of relevant article images vs irrelevant content
- **Memory usage**: Optimized image processing to handle large files more efficiently

### Removed
- **Multiple image download**: Removed support for downloading multiple images per article
- **Legacy scoring**: Simplified scoring system with clearer point allocation

## [1.0.0] - 2024-12-01

### Added
- **Multi-fallback extraction**: Trafilatura → Newspaper3k → BeautifulSoup chain
- **Basic image filtering**: URL pattern matching and size validation
- **Multiple image support**: Download up to 3 images per article
- **Error handling**: Basic retry logic and error logging
- **JSON metadata**: Process article metadata from JSON files
- **Organized output**: Create structured folders for each article

### Features
- Support for news websites and blog platforms
- Basic logo and ad filtering
- Image size validation (100x100 minimum)
- File size limits (10MB maximum)
- Retry mechanism for failed downloads
- Comprehensive logging system

---

## Version History

- **v2.0.0**: Advanced single-image extraction with OpenGraph/Schema.org support
- **v1.0.0**: Initial release with multi-fallback extraction and basic filtering
