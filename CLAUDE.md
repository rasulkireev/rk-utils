# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

rk-utils is a collection of personal utilities and scripts for data analysis, content processing, and API integrations. The project is organized into modular components covering different services and use cases:

- **Obsidian integration**: Tools for processing markdown files and frontmatter
- **Readwise integration**: Fetching and analyzing reading highlights and stats
- **GitHub integration**: Repository analysis and commit summarization using AI
- **Content scrapers**: Extracting content from various sources
- **Data processing**: TypeSense search, MongoDB storage, and data analysis
- **Social media**: Twitter and other platform integrations
- **PayPal API**: Payment processing utilities
- **Newsletter generation**: Personal newsletter automation

## Development Commands

**Dependencies**: Use Poetry for dependency management
```bash
poetry install                    # Install dependencies
poetry add <package>              # Add new dependency
poetry add --group dev <package>  # Add dev dependency
```

**Code Quality**: The project uses Black, isort, flake8, mypy, and pylint
```bash
poetry run black src/             # Format code (120 char line length)
poetry run isort src/             # Sort imports (Black profile)
poetry run flake8 src/            # Lint code
poetry run mypy src/              # Type checking
poetry run pylint src/            # Additional linting
```

**Jupyter**: JupyterLab is available for analysis notebooks
```bash
poetry run jupyter lab            # Launch JupyterLab
```

## Architecture

**Configuration**: Environment-based configuration using python-dotenv
- All API keys and sensitive data loaded from `.env` file
- Centralized config in `src/config.py`

**Authentication**: Shared client initialization in `src/auth.py`
- TypeSense client for search functionality
- MongoDB client for data storage

**Utilities**: Core utilities in `src/utils.py`
- File system operations and directory traversal

**Service Structure**: Each integration is organized in its own module
- Self-contained modules with their own utilities
- API clients and data processing logic co-located
- Common patterns: fetch data → process → store/analyze

**AI Integration**: Uses Anthropic Claude for content analysis
- GitHub commit summarization with rate limiting
- Content processing and summarization workflows

## Key Patterns

**Rate Limiting**: GitHub API operations include comprehensive rate limit handling with automatic retry logic

**Caching**: Long-running operations cache results in `caches/` directory

**Error Handling**: Defensive programming with try/catch blocks for API calls and file operations

**Data Flow**: Typical pattern is API → processing → storage (MongoDB/TypeSense) → analysis
