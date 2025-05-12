# rk-utils Development Guide

## Build Commands
- Setup environment: `poetry install`
- Run linting: `poetry run black src/ && poetry run isort src/ && poetry run flake8 src/`
- Run type checking: `poetry run mypy src/`
- Run single test: `poetry run pytest tests/path_to_test.py::test_function_name -v`
- Run notebook: `poetry run jupyter lab`

## Code Style Guidelines
- **Python version**: 3.11+
- **Line length**: 120 characters (defined in black, isort, and flake8)
- **Formatting**: Use black and isort (configured in pyproject.toml)
- **Import order**: standard library → third-party → local (managed by isort)
- **Naming**: Use snake_case for functions/variables, UPPER_CASE for constants
- **Type hints**: Required for function parameters and return values
- **Documentation**: Use docstrings for functions, classes, and modules
- **Error handling**: Use specific exception types, provide helpful error messages
- **Packages**: All code should be within the src/ directory

## Tools Used
- **Package manager**: Poetry
- **Linting**: black, isort, flake8, pylint
- **Type checking**: mypy
- **Pre-commit hooks**: Configured for consistent code quality
