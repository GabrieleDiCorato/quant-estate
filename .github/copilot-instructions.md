# Copilot Instructions

## Project Context
Real estate data scraping and analysis application using Python 3.12:
- **Architecture**: Direct scrapers with storage layer (no connector abstraction)
- **Database**: MongoDB via pymongo or CSV files 
- **Key Libraries**: pydantic v2, undetected-chromedriver, pymongo
- **Package Manager**: uv
- **Environment**: Windows PowerShell

## Communication Style
- Direct, factual responses without apologies or excitement
- Focus on practical solutions over explanations
- Ask for clarifications before complex tasks
- Validate prompts and suggest improvements

## Task Boundaries
- **Complete only the requested task**
- **Ask before expanding scope** or making improvements
- **Don't refactor unless explicitly asked**
- **Mention related issues but don't fix them**

## Python Standards

### Code Style (Ruff enforced)
- Python 3.12+ features, f-strings, modern type hints
- `snake_case` for variables/functions, `CamelCase` for classes
- Module-level loggers: `logger = logging.getLogger(__name__)`
- Line length: 150 characters
- Remove unused imports when editing files

### Type Hints
- Always use type hints for functions
- Use modern built-ins: `list`, `dict`, `set` (not `List`, `Dict`, `Set`)
- Avoid `Any` - use specific types

## Architecture

### Current Structure
```
sources/
├── config/           # Pydantic settings with env file support
├── datamodel/        # Pydantic v2 models (frozen=True)
├── scrapers/         # Selenium-based scrapers
├── storage/          # MongoDB/CSV storage implementations
├── mappers/          # Data transformation utilities
└── logging/          # Logging configuration
```

### Key Components

#### Data Models (`sources/datamodel/`)
- **Base**: `QuantEstateDataObject` (Pydantic v2, frozen, enum values)
- **Core**: `ListingDetails`, `ListingId`, `ListingRecord`
- **Enums**: Type-safe property types, conditions, etc.

#### Configuration (`sources/config/`)
- **Manager**: `ConfigManager` with LRU caching
- **Settings**: Environment-based Pydantic settings
- **Structure**: `StorageSettings`, `ScraperSettings` subclasses

#### Scrapers (`sources/scrapers/`)
- **Base**: `SeleniumScraper` with undetected Chrome WebDriver management
- **Implementation**: `ImmobiliareIdScraper`, `ImmobiliareListingScraper`
- **Features**: Request delays, headless mode, window sizing

#### Storage (`sources/storage/`)
- **Interface**: `Storage.create_storage()` factory
- **Types**: `FileStorage` (CSV), `MongoDBStorage`
- **Collections**: `{source}_{type}` naming (e.g., `immobiliare_listings`)

### Exception Handling
- Custom hierarchy: `ConnectorError` → `ScrapingError`, `StorageError`, `ConfigurationError`
- Source-specific exceptions for validation errors

## Project Conventions

### Configuration
- Use `ConfigManager` for all settings
- Environment files in `sources/resources/`
- Pydantic validation with descriptive errors

### Data Models  
- Inherit from `QuantEstateDataObject`
- Frozen models with enum value serialization
- Type-safe enums with `BaseEnum`

### Development
- Use `uv` for package management
- Tests in `tests/` directory (ask about pytest vs unittest)
- Structured logging with appropriate levels
- Update documentation when adding features
