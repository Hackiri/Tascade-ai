# Contributing to Tascade AI

Thank you for your interest in contributing to Tascade AI! This document provides guidelines and instructions for contributing to this project.

## Code of Conduct

Please be respectful and considerate of others when contributing to this project. We aim to foster an inclusive and welcoming community.

## How to Contribute

### Reporting Bugs

If you find a bug, please create an issue with the following information:
- A clear, descriptive title
- Steps to reproduce the bug
- Expected behavior
- Actual behavior
- Any relevant logs or screenshots
- Your environment (OS, Python version, etc.)

### Suggesting Enhancements

We welcome suggestions for enhancements! Please create an issue with:
- A clear, descriptive title
- A detailed description of the enhancement
- Any relevant examples or mockups
- The rationale for the enhancement

### Pull Requests

1. Fork the repository
2. Create a new branch for your feature or bug fix
3. Make your changes
4. Add or update tests as necessary
5. Ensure all tests pass
6. Submit a pull request

### Pull Request Process

1. Update the README.md or documentation with details of changes if appropriate
2. Update the CHANGELOG.md if applicable
3. The PR will be merged once it has been reviewed and approved

## Development Setup

1. Clone the repository
   ```bash
   git clone https://github.com/Hackiri/tascade-aI.git
   cd tascade-ai
   ```

2. Create and activate a virtual environment
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies
   ```bash
   pip install -r requirements.txt
   ```

4. Install development dependencies
   ```bash
   pip install pytest pytest-cov flake8
   ```

## Coding Standards

- Follow PEP 8 style guidelines
- Write docstrings for all functions, classes, and modules
- Include type hints where appropriate
- Write unit tests for new functionality

## Testing

Run tests with pytest:
```bash
pytest tests/
```

Run tests with coverage:
```bash
pytest tests/ --cov=src
```

## Documentation

- Update documentation when changing functionality
- Use clear, descriptive variable and function names
- Include comments for complex logic

## Commit Messages

- Use clear, descriptive commit messages
- Reference issue numbers when applicable
- Use present tense ("Add feature" not "Added feature")

## Branch Naming

- Feature branches: `feature/short-description`
- Bug fix branches: `fix/short-description`
- Documentation branches: `docs/short-description`

Thank you for contributing to Tascade AI!
