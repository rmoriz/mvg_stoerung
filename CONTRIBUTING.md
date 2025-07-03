# Contributing to MVG Stoerung

Thank you for your interest in contributing to MVG Stoerung! This document provides guidelines and instructions for contributing.

## Development Setup

1. **Clone the repository:**
   ```bash
   git clone https://github.com/your-org/mvg-incident-parser.git
   cd mvg-incident-parser
   ```

2. **Set up development environment:**
   ```bash
   make dev-setup
   ```
   
   Or manually:
   ```bash
   pip install -r requirements.txt
   pip install black isort flake8 mypy bandit safety coverage build twine pre-commit
   pre-commit install
   ```

## Development Workflow

### Code Style

We use several tools to maintain code quality:

- **Black** for code formatting
- **isort** for import sorting
- **flake8** for linting
- **mypy** for type checking
- **bandit** for security analysis

Format your code before committing:
```bash
make format
```

Check code quality:
```bash
make lint
make security
```

### Testing

Run all tests:
```bash
make test
```

Run tests with coverage:
```bash
make test-coverage
```

### Pre-commit Hooks

Pre-commit hooks are automatically installed with `make dev-setup`. They will run on every commit to ensure code quality.

To run pre-commit hooks manually:
```bash
pre-commit run --all-files
```

## Making Changes

1. **Create a feature branch:**
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make your changes:**
   - Write clean, well-documented code
   - Add tests for new functionality
   - Update documentation if needed

3. **Test your changes:**
   ```bash
   make ci  # Run full CI pipeline locally
   ```

4. **Commit your changes:**
   ```bash
   git add .
   git commit -m "feat: add your feature description"
   ```

5. **Push and create a pull request:**
   ```bash
   git push origin feature/your-feature-name
   ```

## Commit Message Format

We follow conventional commit format:

- `feat:` for new features
- `fix:` for bug fixes
- `docs:` for documentation changes
- `test:` for adding tests
- `refactor:` for code refactoring
- `style:` for formatting changes
- `ci:` for CI/CD changes

Examples:
```
feat: add HTML entity decoding support
fix: handle empty lines array in deduplication
docs: update README with new features
test: add tests for timestamp formatting
```

## Code Guidelines

### Python Style

- Follow PEP 8 style guidelines
- Use type hints where appropriate
- Write docstrings for all functions and classes
- Keep functions focused and small
- Use meaningful variable and function names

### Testing

- Write unit tests for all new functions
- Aim for high test coverage (>90%)
- Test edge cases and error conditions
- Use descriptive test names

Example test structure:
```python
def test_function_name_scenario(self):
    """Test description of what is being tested"""
    # Arrange
    input_data = {...}
    expected = {...}
    
    # Act
    result = function_under_test(input_data)
    
    # Assert
    self.assertEqual(result, expected)
```

### Documentation

- Update README.md for user-facing changes
- Add docstrings to new functions
- Include examples in docstrings when helpful
- Update CHANGELOG.md for releases

## Pull Request Process

1. **Ensure CI passes:** All tests, linting, and security checks must pass
2. **Update documentation:** Include relevant documentation updates
3. **Add tests:** New features must include comprehensive tests
4. **Describe changes:** Provide a clear description of what changed and why
5. **Link issues:** Reference any related issues in the PR description

## Reporting Issues

When reporting issues, please include:

- Python version
- Operating system
- Steps to reproduce the issue
- Expected vs actual behavior
- Error messages or logs
- Minimal code example if applicable

## Security

If you discover a security vulnerability, please email us directly instead of opening a public issue.

## Questions?

Feel free to open an issue for questions about contributing or reach out to the maintainers.

Thank you for contributing! 🎉