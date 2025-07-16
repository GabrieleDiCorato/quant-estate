# Copilot Instructions

## Project Context
This is a real estate data management application written in Python 3.12 using:
- **Database**: MongoDB for data storage
- **Architecture**: Connector composed of a Scraper and a Storage layer
- **Key Libraries**: pymongo, requests, BeautifulSoup, pydantic v2
- **Package Manager**: uv (modern Python dependency management)
- **Configuration**: YAML defaults

## Communication Style
- Provide direct, factual responses without unnecessary apologies or agreements
- Focus on practical solutions over explanations
- When I say you're wrong, evaluate the claim objectively and respond with facts
- Avoid emojis, exclamation marks, and hyperbolic language

## Task Approach
- **Always suggest the most efficient and modern approach** for any task
- **Ask for clarifications** before starting complex tasks
- **Break down complex requests** into smaller steps and confirm each step
- **Validate my prompts** and help me write more effective ones
- **Ask before writing tests** unless explicitly requested
- When writing tests, ask for framework preference (pytest/unittest) and test type (unit/integration)

## Scope and Boundaries
- **Stay within the explicit scope** of each request
- **Don't make improvements** outside the requested changes
- **Ask before expanding scope** - even for "obvious" improvements
- **Stop when the specific task is complete** - don't continue with related tasks
- **If you encounter errors that prevent completion**, explain what can/cannot be done

## Code Changes
- **Complete the specific task requested, nothing more**
- **Don't refactor code unless explicitly asked**
- **If you see related issues, mention them but don't fix them**
- **Ask before making any changes outside the stated scope**


## Python Coding Standards

### Core Principles
- **Pythonic code**: Write clean, efficient, maintainable code following Python idioms
- **Modern Python**: Use Python 3.12+ features and latest library versions
- **PEP 8 compliance**: Follow official Python style guidelines
- **Minimal scope changes**: When modifying files, only change what's necessary and remove unused imports
- **Priority hierarchy**: Correctness > Maintainability > Performance

### Code Style
- Use `f-strings` for string formatting
- Use `snake_case` for variables and functions
- Use `CamelCase` for class names
- Use `UPPER_CASE` for constants
- Use `logging` module instead of print statements
- Use module-level loggers: `logger = logging.getLogger(__name__)`

### Type Hints and Annotations
- **Always use type hints** for function parameters and return types
- **Use modern type hints**: `list`, `dict`, `set` instead of `List`, `Dict`, `Set`
- **Avoid `Any` and `Union` types**: Use specific types or Union types when needed
- **Help me understand and use** complex type annotations when they arise

### Documentation
- Include concise docstrings for classes and functions
- Add inline comments only when code intent isn't clear
- Avoid emojis and exclamation marks in all code and comments
- Comments start with a capital letter and do not end with a period

## Terminal Usage
- Prefer PowerShell syntax (Windows environment)
- Use `uv` for Python package management: `uv add package_name`
- MongoDB operations through Python code, not CLI commands

## Architecture Overview

### 3-Tier Connector Pattern
The application follows a clean 3-tier architecture:

1. **Connector Layer** (`sources/connectors/base_connector.py`)
   - Orchestrates the entire data pipeline
   - Manages configuration and coordinates scraper/storage operations
   - Handles high-level workflow logic

2. **Scraper Layer** (`sources/connectors/base_scraper.py`)
   - Implements data extraction logic for specific sources
   - Handles HTTP requests, parsing, and data validation
   - Converts raw data to structured `ListingDetails` objects

3. **Storage Layer** (`sources/connectors/base_storage.py`)
   - Manages data persistence operations
   - Handles MongoDB connections and CRUD operations
   - Implements data deduplication and validation

### Data Flow
```
URL → Connector → Scraper → ListingDetails → Storage → MongoDB
```

### Key Components

#### Data Models (`sources/datamodel/`)
- **Base**: `QuantEstateDataObject` with Pydantic v2 configuration
- **Core**: `ListingDetails` - comprehensive real estate property model
- **Enumerations**: Type-safe enums for property types, contracts, conditions
- **Identifiers**: `ListingId` for unique property identification

#### Configuration System (`sources/config/`)
- **Modern Pydantic**: Type-safe configuration with validation
- **Dual Sources**: YAML defaults

#### Current Implementations
- **Immobiliare.it**: Complete scraper with JSON extraction from `__NEXT_DATA__`
- **MongoDB Storage**: Full CRUD operations with connection pooling
- **Request Handling**: Configurable delays and user agent rotation

### Exception Hierarchy
- `ConnectorError` → `ScrapingError`, `StorageError`, `ConfigurationError`
- Source-specific: `ImmobiliareError` with validation extensions
- Comprehensive error handling throughout the pipeline

## Project-Specific Conventions

### Configuration Management
- **Primary**: Use `sources/config/pydantic_config_manager.py` for all configuration
- **Models**: Configuration classes in `sources/config/settings.py`
- **YAML Structure**: Maintain hierarchical structure in default config files

### Data Model Design
- **Inheritance**: All models inherit from `QuantEstateDataObject`
- **Validation**: Use Pydantic v2 field validation with descriptive error messages
- **Enums**: Create type-safe enums in `enumerations.py` with `BaseEnum` inheritance
- **Immutability**: Data models are frozen by default (`frozen=True`)

### Connector Implementation
- **Base Classes**: Always inherit from `AbstractConnector`, `AbstractScraper`, `AbstractStorage`
- **Error Handling**: Use specific exception types from `sources/exceptions.py`
- **Logging**: Module-level loggers with structured logging
- **Configuration**: Source-specific config in YAML with type validation

### MongoDB Integration
- **Connection**: Use connection pooling through storage layer
- **Collections**: Follow naming convention `{source}_{data_type}` (e.g., `immobiliare_listings`)
- **Indexes**: Create appropriate indexes for query performance
- **Deduplication**: Implement based on `ListingId` uniqueness

### Request Handling
- **Delays**: Configurable request delays to respect rate limits
- **User Agents**: Rotate user agents for scraping resilience
- **Error Recovery**: Implement retry logic for transient failures
- **Validation**: Validate all extracted data before storage

### Development Workflow
- **Dependencies**: Use `uv` for all package management operations
- **Testing**: Write tests for each component layer independently. Put tests in `tests/` directory
- **Documentation**: Update relevant `.md` files when adding features
- **Logging**: Use structured logging with appropriate levels
