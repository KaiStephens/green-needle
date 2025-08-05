# Contributing to Green Needle

Thank you for your interest in contributing to Green Needle! We welcome contributions from everyone.

## Getting Started

1. Fork the repository on GitHub
2. Clone your fork locally:
   ```bash
   git clone https://github.com/yourusername/green-needle.git
   cd green-needle
   ```
3. Create a virtual environment and install dependencies:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   pip install -r requirements-dev.txt
   pip install -e .
   ```

## Development Workflow

1. Create a new branch for your feature or fix:
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. Make your changes and ensure they follow our coding standards

3. Run tests:
   ```bash
   pytest
   pytest --cov=green_needle  # With coverage
   ```

4. Run linters:
   ```bash
   black src/ tests/
   flake8 src/ tests/
   mypy src/
   ```

5. Commit your changes:
   ```bash
   git add .
   git commit -m "Add your descriptive commit message"
   ```

6. Push to your fork:
   ```bash
   git push origin feature/your-feature-name
   ```

7. Open a Pull Request on GitHub

## Code Style

- We use [Black](https://github.com/psf/black) for code formatting
- Follow PEP 8 guidelines
- Use type hints where appropriate
- Write descriptive docstrings for all functions and classes

## Testing

- Write tests for new features
- Ensure all tests pass before submitting PR
- Aim for high test coverage
- Use pytest for testing

## Documentation

- Update README.md if adding new features
- Add docstrings to all new functions/classes
- Update API documentation if changing interfaces

## Pull Request Guidelines

1. **Title**: Use a clear and descriptive title
2. **Description**: Explain what changes you made and why
3. **Testing**: Describe how you tested your changes
4. **Screenshots**: Include screenshots for UI changes
5. **Breaking Changes**: Clearly note any breaking changes

## Reporting Issues

When reporting issues, please include:
- Python version
- Operating system
- Steps to reproduce
- Expected behavior
- Actual behavior
- Error messages/logs

## Feature Requests

We welcome feature requests! Please:
- Check existing issues first
- Clearly describe the feature
- Explain use cases
- Consider implementation approach

## Code of Conduct

- Be respectful and inclusive
- Welcome newcomers
- Be patient and helpful
- Focus on constructive criticism

## Questions?

Feel free to:
- Open an issue for questions
- Join our Discord community
- Email us at contribute@greenneedle.io

Thank you for contributing to Green Needle!