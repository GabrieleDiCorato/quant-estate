import os
from pathlib import Path
from typing import Dict, Any
import yaml
from functools import lru_cache

class ConfigurationError(Exception):
    """Raised when there's an error loading or processing configuration."""
    pass

@lru_cache()
def get_config_path() -> Path:
    """Get the path to the configuration directory."""
    return Path(__file__).parent

def load_yaml_file(file_path: Path) -> Dict[str, Any]:
    """Load a YAML file and return its contents as a dictionary."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    except Exception as e:
        raise ConfigurationError(f"Failed to load YAML file {file_path}: {e}")

def merge_configs(base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
    """Recursively merge two configuration dictionaries."""
    result = base.copy()
    
    for key, value in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = merge_configs(result[key], value)
        else:
            result[key] = value
    
    return result

class Config:
    """Configuration management class."""
    
    def __init__(self, env: str = None):
        """Initialize configuration with optional environment override."""
        self.env = env or os.getenv('IMMOBILIARE_ENV', 'development')
        self.config_path = get_config_path()
        self._config = self._load_config()
    
    def _load_config(self) -> Dict[str, Any]:
        """Load and merge configuration files."""
        # Load default configuration
        default_config = load_yaml_file(self.config_path / 'default.yaml')
        
        # Load environment-specific configuration if it exists
        env_config_path = self.config_path / f'{self.env}.yaml'
        if env_config_path.exists():
            env_config = load_yaml_file(env_config_path)
            return merge_configs(default_config, env_config)
        
        return default_config
    
    @property
    def base_url(self) -> str:
        """Get the base URL."""
        return self._config['base_url']
    
    @property
    def headers(self) -> Dict[str, str]:
        """Get the request headers."""
        return self._config['headers']
    
    @property
    def request_settings(self) -> Dict[str, Any]:
        """Get the request settings."""
        return self._config['request_settings']
    
    @property
    def storage_settings(self) -> Dict[str, Any]:
        """Get the storage settings."""
        return self._config['storage_settings']
    
    def get_storage_path(self) -> str:
        """Get the storage path for the current date."""
        from datetime import datetime
        return os.path.join(
            self.storage_settings['base_path'],
            datetime.today().strftime(self.storage_settings['date_format'])
        )

# Create a default configuration instance
config = Config() 