"""
Configuration management classes for the Atomic Scraper Tool.

Provides centralized configuration management with validation and defaults
for the next-generation intelligent web scraping tool.
"""

import json
import os
from pathlib import Path
from typing import Dict, List, Any, Optional, Union
from pydantic import BaseModel, Field, field_validator, ConfigDict
from atomic_agents.lib.base.base_tool import BaseToolConfig

from atomic_scraper_tool.models.schema_models import SchemaRecipe
from atomic_scraper_tool.models.extraction_models import ExtractionRule
from atomic_scraper_tool.core.exceptions import ConfigurationError


class AtomicScraperConfig(BaseToolConfig):
    """Configuration for the Atomic Scraper Tool."""
    
    # Network settings
    base_url: str = Field(..., description="Base URL for scraping")
    request_delay: float = Field(1.0, ge=0.1, le=10.0, description="Delay between requests in seconds")
    timeout: int = Field(30, ge=5, le=300, description="Request timeout in seconds")
    user_agent: str = Field(
        "AtomicScraperTool/1.0 (+https://github.com/atomic-agents/atomic-scraper-tool)",
        description="User agent string for requests"
    )
    
    # Quality and limits
    min_quality_score: float = Field(50.0, ge=0.0, le=100.0, description="Minimum quality score for results")
    max_pages: int = Field(10, ge=1, le=100, description="Maximum pages to scrape")
    max_results: int = Field(100, ge=1, le=1000, description="Maximum results to return")
    
    # Retry settings
    max_retries: int = Field(3, ge=0, le=10, description="Maximum retry attempts")
    retry_delay: float = Field(2.0, ge=0.1, le=30.0, description="Delay between retries in seconds")
    
    # Compliance settings
    respect_robots_txt: bool = Field(True, description="Whether to respect robots.txt")
    enable_rate_limiting: bool = Field(True, description="Whether to enable rate limiting")
    
    @field_validator('base_url')
    @classmethod
    def validate_base_url(cls, v):
        """Validate that base_url is a valid URL."""
        if not v.startswith(('http://', 'https://')):
            raise ValueError('base_url must start with http:// or https://')
        return v


class ScraperConfiguration:
    """Centralized configuration management for the Atomic Scraper Tool."""
    
    def __init__(self, config_file: Optional[str] = None, config_dir: Optional[str] = None):
        """
        Initialize configuration manager.
        
        Args:
            config_file: Path to main configuration file
            config_dir: Directory containing configuration files
        """
        self.config_dir = Path(config_dir) if config_dir else Path.home() / ".atomic_scraper_tool"
        self.config_file = Path(config_file) if config_file else self.config_dir / "config.json"
        
        # Ensure config directory exists
        self.config_dir.mkdir(parents=True, exist_ok=True)
        
        # Load configuration
        self._config_data = self._load_configuration()
        self._schema_recipes = self._load_schema_recipes()
        self._extraction_rules = self._load_extraction_rules()
    
    def _load_configuration(self) -> Dict[str, Any]:
        """Load main configuration from file."""
        if not self.config_file.exists():
            # Create default configuration
            default_config = {
                "default_settings": {
                    "request_delay": 1.0,
                    "timeout": 30,
                    "min_quality_score": 50.0,
                    "max_pages": 10,
                    "max_results": 100,
                    "respect_robots_txt": True,
                    "enable_rate_limiting": True
                },
                "user_agent": "AtomicScraperTool/1.0 (+https://github.com/atomic-agents/atomic-scraper-tool)",
                "schema_recipes_dir": str(self.config_dir / "schema_recipes"),
                "extraction_rules_dir": str(self.config_dir / "extraction_rules")
            }
            
            with open(self.config_file, 'w') as f:
                json.dump(default_config, f, indent=2)
            
            return default_config
        
        try:
            with open(self.config_file, 'r') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            raise ConfigurationError(f"Failed to load configuration from {self.config_file}: {e}")
    
    def _load_schema_recipes(self) -> Dict[str, SchemaRecipe]:
        """Load predefined schema recipes from files."""
        recipes_dir = Path(self._config_data.get("schema_recipes_dir", self.config_dir / "schema_recipes"))
        recipes_dir.mkdir(parents=True, exist_ok=True)
        
        recipes = {}
        
        # Create default schema recipes if directory is empty
        if not any(recipes_dir.glob("*.json")):
            self._create_default_schema_recipes(recipes_dir)
        
        # Load all recipe files
        for recipe_file in recipes_dir.glob("*.json"):
            try:
                with open(recipe_file, 'r') as f:
                    recipe_data = json.load(f)
                    recipe = SchemaRecipe(**recipe_data)
                    recipes[recipe.name] = recipe
            except (json.JSONDecodeError, IOError, ValueError) as e:
                print(f"Warning: Failed to load schema recipe from {recipe_file}: {e}")
        
        return recipes
    
    def _load_extraction_rules(self) -> Dict[str, ExtractionRule]:
        """Load custom extraction rules from files."""
        rules_dir = Path(self._config_data.get("extraction_rules_dir", self.config_dir / "extraction_rules"))
        rules_dir.mkdir(parents=True, exist_ok=True)
        
        rules = {}
        
        # Load all rule files
        for rule_file in rules_dir.glob("*.json"):
            try:
                with open(rule_file, 'r') as f:
                    rule_data = json.load(f)
                    rule = ExtractionRule(**rule_data)
                    rules[rule.field_name] = rule
            except (json.JSONDecodeError, IOError, ValueError) as e:
                print(f"Warning: Failed to load extraction rule from {rule_file}: {e}")
        
        return rules
    
    def _create_default_schema_recipes(self, recipes_dir: Path):
        """Create default schema recipes for common website types."""
        default_recipes = [
            {
                "name": "generic_list",
                "description": "Generic schema for list-based content",
                "fields": {
                    "title": {
                        "field_type": "string",
                        "description": "Item title or name",
                        "extraction_selector": "h1, h2, h3, .title, .name",
                        "required": True,
                        "quality_weight": 2.0
                    },
                    "description": {
                        "field_type": "string", 
                        "description": "Item description",
                        "extraction_selector": "p, .description, .summary",
                        "required": False,
                        "quality_weight": 1.0
                    },
                    "url": {
                        "field_type": "string",
                        "description": "Item URL or link",
                        "extraction_selector": "a[href]",
                        "required": False,
                        "quality_weight": 1.5
                    }
                },
                "validation_rules": ["title_not_empty"],
                "quality_weights": {
                    "completeness": 0.4,
                    "accuracy": 0.4,
                    "consistency": 0.2
                }
            }
        ]
        
        for recipe_data in default_recipes:
            recipe_file = recipes_dir / f"{recipe_data['name']}.json"
            with open(recipe_file, 'w') as f:
                json.dump(recipe_data, f, indent=2)
    
    def get_tool_config(self, base_url: str, **overrides) -> AtomicScraperConfig:
        """
        Get tool configuration for a specific URL.
        
        Args:
            base_url: Base URL for scraping
            **overrides: Configuration overrides
            
        Returns:
            Configured AtomicScraperConfig instance
        """
        config_data = {
            "base_url": base_url,
            **self._config_data.get("default_settings", {}),
            **overrides
        }
        
        try:
            return AtomicScraperConfig(**config_data)
        except ValueError as e:
            raise ConfigurationError(f"Invalid configuration: {e}")
    
    def get_schema_recipe(self, name: str) -> Optional[SchemaRecipe]:
        """Get schema recipe by name."""
        return self._schema_recipes.get(name)
    
    def get_extraction_rule(self, field_name: str) -> Optional[ExtractionRule]:
        """Get extraction rule by field name."""
        return self._extraction_rules.get(field_name)
    
    def list_schema_recipes(self) -> List[str]:
        """List available schema recipe names."""
        return list(self._schema_recipes.keys())
    
    def list_extraction_rules(self) -> List[str]:
        """List available extraction rule field names."""
        return list(self._extraction_rules.keys())
    
    def save_schema_recipe(self, recipe: SchemaRecipe) -> None:
        """Save a schema recipe to file."""
        recipes_dir = Path(self._config_data.get("schema_recipes_dir", self.config_dir / "schema_recipes"))
        recipe_file = recipes_dir / f"{recipe.name}.json"
        
        try:
            with open(recipe_file, 'w') as f:
                json.dump(recipe.dict(), f, indent=2)
            self._schema_recipes[recipe.name] = recipe
        except IOError as e:
            raise ConfigurationError(f"Failed to save schema recipe {recipe.name}: {e}")
    
    def save_extraction_rule(self, rule: ExtractionRule) -> None:
        """Save an extraction rule to file."""
        rules_dir = Path(self._config_data.get("extraction_rules_dir", self.config_dir / "extraction_rules"))
        rule_file = rules_dir / f"{rule.field_name}.json"
        
        try:
            with open(rule_file, 'w') as f:
                json.dump(rule.dict(), f, indent=2)
            self._extraction_rules[rule.field_name] = rule
        except IOError as e:
            raise ConfigurationError(f"Failed to save extraction rule {rule.field_name}: {e}")
    
    def validate_configuration(self) -> List[str]:
        """
        Validate configuration and return any issues.
        
        Returns:
            List of validation issues (empty if valid)
        """
        issues = []
        
        # Validate directories exist
        for dir_key in ["schema_recipes_dir", "extraction_rules_dir"]:
            if dir_key in self._config_data:
                dir_path = Path(self._config_data[dir_key])
                if not dir_path.exists():
                    issues.append(f"Directory {dir_path} does not exist")
        
        # Validate schema recipes
        for name, recipe in self._schema_recipes.items():
            try:
                # Validate recipe structure
                if not recipe.fields:
                    issues.append(f"Schema recipe '{name}' has no fields defined")
                
                # Validate field definitions
                for field_name, field_def in recipe.fields.items():
                    if not field_def.extraction_selector:
                        issues.append(f"Field '{field_name}' in recipe '{name}' has no extraction selector")
            except Exception as e:
                issues.append(f"Invalid schema recipe '{name}': {e}")
        
        return issues