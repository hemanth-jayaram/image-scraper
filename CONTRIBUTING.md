# Contributing to Article Image Scraper Pipeline

Thank you for your interest in contributing to the Article Image Scraper Pipeline! This document provides guidelines and information for contributors.

## 🚀 Getting Started

1. **Fork the repository** on GitHub
2. **Clone your fork** locally:
   ```bash
   git clone https://github.com/yourusername/article-image-scraper.git
   cd article-image-scraper
   ```
3. **Create a virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```
4. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

## 🛠️ Development Setup

1. **Install development dependencies**:
   ```bash
   pip install -r requirements.txt
   pip install pytest black flake8 mypy
   ```

2. **Run tests** (when available):
   ```bash
   pytest tests/
   ```

3. **Format code**:
   ```bash
   black image_scraper_pipeline.py
   ```

4. **Check code quality**:
   ```bash
   flake8 image_scraper_pipeline.py
   mypy image_scraper_pipeline.py
   ```

## 📝 Making Changes

### Code Style
- Follow PEP 8 style guidelines
- Use meaningful variable and function names
- Add docstrings to all functions and classes
- Keep functions focused and single-purpose

### Commit Messages
Use clear, descriptive commit messages:
```
feat: add OpenGraph image extraction support
fix: resolve Facebook tracking pixel filtering issue
docs: update README with new features
refactor: improve image scoring algorithm
```

### Pull Request Process

1. **Create a feature branch**:
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make your changes** and test them thoroughly

3. **Commit your changes**:
   ```bash
   git add .
   git commit -m "feat: add your feature description"
   ```

4. **Push to your fork**:
   ```bash
   git push origin feature/your-feature-name
   ```

5. **Create a Pull Request** on GitHub

## 🎯 Areas for Contribution

### High Priority
- **Additional image sources**: Support for more meta tag formats
- **Better logo detection**: Improve algorithms to identify company logos
- **Performance optimization**: Speed up image processing and validation
- **Error handling**: More robust error recovery and logging

### Medium Priority
- **Configuration system**: Make more settings configurable
- **Plugin architecture**: Allow custom image extraction methods
- **Batch processing**: Optimize for processing large numbers of articles
- **Image quality assessment**: Better algorithms for image relevance

### Low Priority
- **GUI interface**: Web or desktop interface for the pipeline
- **API endpoints**: REST API for image extraction
- **Docker support**: Containerization for easy deployment
- **Cloud integration**: Support for cloud storage services

## 🧪 Testing

When adding new features:

1. **Test with various article types**:
   - News articles
   - Blog posts
   - E-commerce pages
   - Social media content

2. **Test edge cases**:
   - Articles with no images
   - Articles with only logos
   - Articles with tracking pixels
   - Malformed HTML

3. **Test performance**:
   - Large batches of articles
   - Slow network conditions
   - Memory usage with large images

## 📋 Pull Request Checklist

Before submitting a PR, ensure:

- [ ] Code follows the project's style guidelines
- [ ] All functions have proper docstrings
- [ ] New features are tested with various article types
- [ ] No breaking changes (or clearly documented)
- [ ] README.md updated if needed
- [ ] Requirements.txt updated if new dependencies added
- [ ] Commit messages are clear and descriptive

## 🐛 Reporting Issues

When reporting bugs, please include:

1. **Python version** and operating system
2. **Steps to reproduce** the issue
3. **Expected vs actual behavior**
4. **Sample article URLs** (if applicable)
5. **Error messages** and logs
6. **Screenshots** (if relevant)

## 💡 Feature Requests

For feature requests, please:

1. **Check existing issues** to avoid duplicates
2. **Describe the use case** and benefits
3. **Provide examples** of how it would work
4. **Consider implementation complexity**

## 📞 Getting Help

- **GitHub Issues**: For bugs and feature requests
- **Discussions**: For questions and general discussion
- **Email**: contact@example.com for private matters

## 📄 License

By contributing to this project, you agree that your contributions will be licensed under the MIT License.

Thank you for contributing! 🎉
