"""
Environment Variable Support for Quant Estate Configuration

This document explains how to use environment variables to override configuration settings
in the Quant Estate project.
"""

# Environment Variable Support

## Overview

The Quant Estate project now supports environment variable overrides for configuration settings.
Environment variables take precedence over YAML configuration files, allowing for flexible
deployment configurations without modifying code.

## Priority Order

1. **Environment Variables** (highest priority)
2. **YAML Configuration Files** (middle priority)
3. **Pydantic Field Defaults** (lowest priority)

## MongoDB Configuration

### Available Environment Variables

| Environment Variable | Description | Type | Example |
|---------------------|-------------|------|---------|
| `MONGODB_HOST` | MongoDB host address | string | `localhost` |
| `MONGODB_DATABASE` | Database name | string | `prod_estate` |
| `MONGODB_COLLECTION` | Collection name | string | `properties` |
| `MONGODB_DB_QUERY` | Database query | string | `{"active": true}` |
| `MONGODB_USERNAME` | MongoDB username | string | `admin` |
| `MONGODB_PASSWORD` | MongoDB password | string | `secret123` |
| `MONGODB_AUTH_SOURCE` | Authentication database | string | `admin` |
| `MONGODB_AUTH_MECHANISM` | Authentication mechanism | string | `SCRAM-SHA-256` |
| `MONGODB_CONNECTION_STRING` | Full connection string | string | `mongodb://user:pass@host:port/db` |
| `MONGODB_SSL` | Enable SSL/TLS | boolean | `true` |
| `MONGODB_REPLICA_SET` | Replica set name | string | `rs0` |
| `MONGODB_MAX_POOL_SIZE` | Maximum connection pool size | integer | `200` |
| `MONGODB_MIN_POOL_SIZE` | Minimum connection pool size | integer | `10` |
| `MONGODB_MAX_IDLE_TIME_MS` | Maximum idle time in milliseconds | integer | `30000` |
| `MONGODB_WRITE_CONCERN_W` | Write acknowledgment level | integer | `1` |
| `MONGODB_WRITE_CONCERN_WTIMEOUT` | Write timeout in milliseconds | integer | `10000` |

### Example Usage

```bash
# Windows PowerShell
$env:MONGODB_HOST = "prod-mongodb.example.com"
$env:MONGODB_DATABASE = "production_estate"
$env:MONGODB_USERNAME = "prod_user"
$env:MONGODB_PASSWORD = "secure_password"
$env:MONGODB_SSL = "true"
$env:MONGODB_MAX_POOL_SIZE = "200"

# Linux/macOS
export MONGODB_HOST="prod-mongodb.example.com"
export MONGODB_DATABASE="production_estate"
export MONGODB_USERNAME="prod_user"
export MONGODB_PASSWORD="secure_password"
export MONGODB_SSL="true"
export MONGODB_MAX_POOL_SIZE="200"
```

## Scrapers Configuration

### Available Environment Variables

| Environment Variable | Description | Type | Example |
|---------------------|-------------|------|---------|
| `SCRAPERS_IMMOBILIARE_ENABLED` | Enable/disable immobiliare scraper | boolean | `false` |
| `SCRAPERS_IMMOBILIARE_BASE_URL` | Base URL for immobiliare scraper | string | `https://api.immobiliare.it` |
| `SCRAPERS_REQUEST_MIN_DELAY` | Minimum delay between requests (seconds) | integer | `5` |
| `SCRAPERS_REQUEST_MAX_DELAY` | Maximum delay between requests (seconds) | integer | `30` |
| `SCRAPERS_STORAGE_TYPE` | Storage type (`file` or `mongodb`) | string | `file` |

### Example Usage

```bash
# Windows PowerShell
$env:SCRAPERS_IMMOBILIARE_ENABLED = "true"
$env:SCRAPERS_IMMOBILIARE_BASE_URL = "https://www.immobiliare.it"
$env:SCRAPERS_REQUEST_MIN_DELAY = "15"
$env:SCRAPERS_REQUEST_MAX_DELAY = "25"
$env:SCRAPERS_STORAGE_TYPE = "mongodb"

# Linux/macOS
export SCRAPERS_IMMOBILIARE_ENABLED="true"
export SCRAPERS_IMMOBILIARE_BASE_URL="https://www.immobiliare.it"
export SCRAPERS_REQUEST_MIN_DELAY="15"
export SCRAPERS_REQUEST_MAX_DELAY="25"
export SCRAPERS_STORAGE_TYPE="mongodb"
```

## Docker Support

### Docker Compose Example

```yaml
version: '3.8'
services:
  quant-estate:
    build: .
    environment:
      # MongoDB Configuration
      MONGODB_HOST: mongodb
      MONGODB_DATABASE: estate_data
      MONGODB_USERNAME: ${MONGO_USER}
      MONGODB_PASSWORD: ${MONGO_PASSWORD}
      MONGODB_SSL: "false"
      MONGODB_MAX_POOL_SIZE: "50"
      
      # Scrapers Configuration
      SCRAPERS_IMMOBILIARE_ENABLED: "true"
      SCRAPERS_REQUEST_MIN_DELAY: "10"
      SCRAPERS_REQUEST_MAX_DELAY: "20"
      SCRAPERS_STORAGE_TYPE: "mongodb"
    depends_on:
      - mongodb
      
  mongodb:
    image: mongo:7
    environment:
      MONGO_INITDB_ROOT_USERNAME: ${MONGO_USER}
      MONGO_INITDB_ROOT_PASSWORD: ${MONGO_PASSWORD}
```

### .env File Example

```env
# MongoDB Settings
MONGO_USER=estate_admin
MONGO_PASSWORD=secure_password_123

# Application Settings
MONGODB_HOST=mongodb
MONGODB_DATABASE=estate_production
MONGODB_SSL=false
MONGODB_MAX_POOL_SIZE=100

# Scraper Settings
SCRAPERS_IMMOBILIARE_ENABLED=true
SCRAPERS_REQUEST_MIN_DELAY=15
SCRAPERS_REQUEST_MAX_DELAY=25
SCRAPERS_STORAGE_TYPE=mongodb
```

## Python Code Examples

### Basic Usage

```python
from sources.config import PydanticConfigManager

# Initialize configuration manager
config_manager = PydanticConfigManager()

# Get MongoDB configuration (with env var overrides)
mongodb_config = config_manager.get_mongodb_config()
print(f"Database: {mongodb_config.database}")
print(f"Host: {mongodb_config.host}")
print(f"Max pool size: {mongodb_config.max_pool_size}")

# Get scrapers configuration (with env var overrides)
scrapers_config = config_manager.get_scrapers_config()
print(f"Immobiliare enabled: {scrapers_config.immobiliare.enabled}")
print(f"Min delay: {scrapers_config.immobiliare.request_settings.min_delay}")
```

### Setting Environment Variables Programmatically

```python
import os
from sources.config import PydanticConfigManager

# Set environment variables
os.environ['MONGODB_DATABASE'] = 'test_database'
os.environ['SCRAPERS_IMMOBILIARE_ENABLED'] = 'false'

# Clear cache if config manager already exists
config_manager = PydanticConfigManager()
config_manager.clear_cache()

# Get updated configuration
mongodb_config = config_manager.get_mongodb_config()
print(f"Database: {mongodb_config.database}")  # Will print 'test_database'
```

## Data Type Conversion

Environment variables are automatically converted to the appropriate Python types:

- **Strings**: Used as-is
- **Booleans**: `"true"`, `"True"`, `"1"` → `True`; `"false"`, `"False"`, `"0"` → `False`
- **Integers**: Converted using `int()`
- **Floats**: Converted using `float()`

## Best Practices

1. **Security**: Never commit sensitive environment variables to version control
2. **Documentation**: Document required environment variables in your deployment docs
3. **Validation**: Environment variables are validated by Pydantic models
4. **Testing**: Use different environment variables for different environments (dev, staging, prod)
5. **Defaults**: Always provide sensible defaults in YAML configuration files

## Error Handling

Invalid environment variables will raise configuration errors:

```python
# This will raise ConfigurationError if MONGODB_MAX_POOL_SIZE is not a valid integer
os.environ['MONGODB_MAX_POOL_SIZE'] = 'not_a_number'
config_manager = PydanticConfigManager()
config_manager.get_mongodb_config()  # Raises ConfigurationError
```

## Troubleshooting

1. **Environment variables not working**: Check variable name spelling and case
2. **Type conversion errors**: Ensure environment variable values match expected types
3. **Cache issues**: Call `config_manager.clear_cache()` after changing environment variables
4. **Nested configuration**: Use the exact environment variable names shown in tables above

## Migration from YAML-only Configuration

Existing YAML configurations will continue to work without changes. Environment variables
provide overrides when needed, making the migration seamless.

```python
# Old approach (still works)
config = config_manager.get_mongodb_config()
database = config.database  # From YAML

# New approach (with environment variable support)
os.environ['MONGODB_DATABASE'] = 'production_db'
config_manager.clear_cache()
config = config_manager.get_mongodb_config()
database = config.database  # From environment variable
```
