# FPL Agent Configuration Guide

This document explains how to configure and use the FPL Agent library's configuration system.

## Overview

The FPL Agent library uses a centralized configuration system that supports:
- YAML configuration files
- Environment variable overrides
- Default fallback values
- Type-safe configuration classes

## Configuration Structure

The configuration is organized into the following sections:

### Database Configuration
- `path`: Path to SQLite database file (relative to project root or absolute)
- `timeout`: Connection timeout in seconds
- `check_same_thread`: Allow connections from multiple threads

### API Configuration
- `fpl_base_url`: Base URL for Fantasy Premier League API
- `github_data_base_url`: Base URL for GitHub historical data repository
- `request_timeout`: Request timeout in seconds
- `retry_attempts`: Number of retry attempts for failed requests
- `retry_delay`: Delay between retry attempts in seconds

### Analysis Configuration
- `default_season`: Default season for analysis (format: YYYY-YY)
- `lookback_gameweeks`: Number of previous gameweeks to consider for trends
- `prediction_horizon`: Number of future gameweeks to predict
- `min_minutes_played`: Minimum minutes played to consider a player performance
- `confidence_threshold`: Confidence threshold for predictions (0.0 to 1.0)
- `model_retrain_frequency`: How often to retrain models (in gameweeks)

### Optimization Configuration
- `squad_size`: Total squad size (default: 15)
- `starting_xi_size`: Starting XI size (default: 11)
- `max_players_per_team`: Maximum players from same team (default: 3)
- `formation_constraints`: Formation constraints for team optimization
- `transfer_budget`: Available transfer budget
- `free_transfers`: Number of free transfers per gameweek

### Logging Configuration
- `level`: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
- `format`: Log message format
- `file_path`: Optional log file path (null for console only)
- `max_file_size`: Maximum log file size in bytes
- `backup_count`: Number of backup log files to keep

## Usage

### Basic Usage

```python
from fpl_agent import get_config

# Get the global configuration
config = get_config()

# Access configuration values
print(f"Default season: {config.analysis.default_season}")
print(f"Database path: {config.database.path}")
print(f"API timeout: {config.api.request_timeout}")
```

### Using Configuration Manager

```python
from fpl_agent import get_config_manager

# Get the configuration manager
config_manager = get_config_manager()

# Get absolute database path
db_path = config_manager.get_database_path()

# Build API URLs
fixtures_url = config_manager.get_api_url("fixtures/")

# Build GitHub data URLs
teams_url = config_manager.get_github_data_url("2024-25", "teams.csv")
```

### Custom Configuration File

```python
from fpl_agent import init_config

# Initialize with custom config file
config_manager = init_config("/path/to/custom/config.yaml")
config = config_manager.config
```

## Configuration Files

### Default Locations

The configuration system searches for configuration files in the following order:
1. `FPL_CONFIG_PATH` environment variable
2. `config.yaml` in the current directory
3. `config.yml` in the current directory
4. `~/.fpl_agent/config.yaml` in the user's home directory
5. `/etc/fpl_agent/config.yaml` system-wide configuration

### Example Configuration File

See `config.example.yaml` for a complete example configuration file with all available options and documentation.

### Creating Your Own Configuration

1. Copy `config.example.yaml` to `config.yaml`
2. Modify the values as needed for your environment
3. The library will automatically load your configuration

## Environment Variable Overrides

You can override specific configuration values using environment variables:

```bash
export FPL_DB_PATH="/custom/path/to/database.db"
export FPL_DEFAULT_SEASON="2024-25"
export FPL_API_BASE_URL="https://custom-api.example.com"
export FPL_GITHUB_BASE_URL="https://custom-github.example.com"
export FPL_LOG_LEVEL="DEBUG"
export FPL_LOG_FILE="/var/log/fpl_agent.log"
```

## Configuration in Different Modules

The configuration system is integrated throughout the FPL Agent library:

### Database Module
- Automatically uses configured database path and connection settings
- Connection timeout and thread safety settings from configuration

### API Calls
- All API requests use configured timeouts and retry settings
- Base URLs are configurable for both FPL API and GitHub data

### Analysis Module
- Default season from configuration
- Analysis parameters like lookback periods and confidence thresholds

### Optimization Module
- Team constraints and formation rules from configuration
- Transfer budget and free transfer settings

## Best Practices

1. **Use Default Configuration**: Start with the default configuration and only override what you need
2. **Environment Variables**: Use environment variables for deployment-specific settings
3. **Version Control**: Keep `config.example.yaml` in version control, but add `config.yaml` to `.gitignore`
4. **Validation**: The configuration system validates types and provides meaningful error messages
5. **Documentation**: Comment your custom configurations for team members

## Troubleshooting

### Configuration Not Loading
- Check file permissions on your configuration file
- Verify YAML syntax using a YAML validator
- Enable debug logging to see configuration loading messages

### Environment Variables Not Working
- Ensure environment variable names match exactly (case-sensitive)
- Restart your Python process after setting environment variables
- Check that variables are exported (`export VAR=value`, not just `VAR=value`)

### Database Path Issues
- Use absolute paths for database files when possible
- Ensure the directory exists before specifying the database path
- Check file permissions for the database directory

## Migration from Hardcoded Values

If you're upgrading from a version with hardcoded values:

1. Review your existing code for hardcoded database paths, API URLs, etc.
2. Update imports to include configuration functions
3. Replace hardcoded values with configuration access
4. Test with both default and custom configurations
5. Update any scripts or deployment processes to use environment variables