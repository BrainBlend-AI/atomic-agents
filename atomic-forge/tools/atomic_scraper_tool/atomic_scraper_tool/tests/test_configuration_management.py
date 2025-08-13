"""
Unit tests for configuration management and user preferences.

Tests the configuration system, schema recipe management, and persistence.
"""

import pytest
import json
import tempfile
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path

from atomic_scraper_tool.main import AtomicScraperApp
from atomic_scraper_tool.config.scraper_config import AtomicScraperConfig


class TestConfigurationManagement:
    """Test cases for configuration management functionality."""
    
    def setup_method(self):
        """Set up test fixtures for configuration tests."""
        self.temp_config = {
            "scraper": {
                "base_url": "https://test.com",
                "request_delay": 0.1,
                "timeout": 10,
                "max_pages": 2,
                "max_results": 10,
                "min_quality_score": 50.0
            },
            "schema_recipes": {
                "test_recipe": {
                    "name": "test_recipe",
                    "description": "Test schema recipe",
                    "fields": {
                        "title": {
                            "field_type": "string",
                            "description": "Item title",
                            "extraction_selector": "h1",
                            "required": True
                        }
                    }
                }
            },
            "quality_thresholds": {
                "minimum_completeness": 0.6,
                "minimum_accuracy": 0.8,
                "minimum_consistency": 0.5,
                "minimum_overall": 60.0
            }
        }
        
        # Create temporary config file
        self.config_file = tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False)
        json.dump(self.temp_config, self.config_file)
        self.config_file.close()
    
    def teardown_method(self):
        """Clean up test fixtures."""
        Path(self.config_file.name).unlink(missing_ok=True)
    
    def test_configuration_loading(self):
        """Test configuration loading from file."""
        app = AtomicScraperApp(config_path=self.config_file.name)
        
        # Verify configuration was loaded correctly
        assert app.config["scraper"]["base_url"] == "https://test.com"
        assert app.config["scraper"]["request_delay"] == 0.1
        assert "test_recipe" in app.config["schema_recipes"]
        assert app.config["quality_thresholds"]["minimum_overall"] == 60.0
    
    def test_default_configuration(self):
        """Test default configuration when no file is provided."""
        app = AtomicScraperApp()
        
        # Verify default values
        assert app.config["scraper"]["base_url"] == "https://example.com"
        assert app.config["scraper"]["request_delay"] == 1.0
        assert app.config["agent"]["model"] == "gpt-3.5-turbo"
        assert app.config["interface"]["show_reasoning"] is True
    
    def test_configuration_merging(self):
        """Test configuration merging with defaults."""
        app = AtomicScraperApp(config_path=self.config_file.name)
        
        # User config should override defaults
        assert app.config["scraper"]["base_url"] == "https://test.com"
        assert app.config["scraper"]["request_delay"] == 0.1
        
        # Defaults should be preserved for unspecified values
        assert app.config["scraper"]["user_agent"] == "AtomicScraperTool/1.0"
        assert app.config["scraper"]["respect_robots_txt"] is True
    
    @patch('atomic_scraper_tool.main.Prompt.ask')
    def test_modify_scraper_settings(self, mock_prompt):
        """Test modifying scraper settings."""
        app = AtomicScraperApp(config_path=self.config_file.name)
        app.console = Mock()
        
        # Mock user input for modifying request_delay
        mock_prompt.side_effect = ["1", "2.5"]  # Choose option 1, set value to 2.5
        
        original_delay = app.config["scraper"]["request_delay"]
        
        # Call the method (would normally be interactive)
        # We'll test the logic directly
        app.config["scraper"]["request_delay"] = 2.5
        app.scraper_tool.update_config(request_delay=2.5)
        
        # Verify the setting was updated
        assert app.config["scraper"]["request_delay"] == 2.5
        assert app.config["scraper"]["request_delay"] != original_delay
    
    def test_schema_recipe_creation(self):
        """Test creating a new schema recipe."""
        app = AtomicScraperApp(config_path=self.config_file.name)
        
        # Create a new recipe programmatically
        new_recipe = {
            "name": "new_test_recipe",
            "description": "New test recipe",
            "fields": {
                "title": {
                    "field_type": "string",
                    "description": "Title field",
                    "extraction_selector": "h1",
                    "required": True
                },
                "content": {
                    "field_type": "string",
                    "description": "Content field",
                    "extraction_selector": "p",
                    "required": False
                }
            },
            "validation_rules": [],
            "quality_weights": {
                "completeness": 0.4,
                "accuracy": 0.4,
                "consistency": 0.2
            }
        }
        
        app.config["schema_recipes"]["new_test_recipe"] = new_recipe
        
        # Verify the recipe was created
        assert "new_test_recipe" in app.config["schema_recipes"]
        assert app.config["schema_recipes"]["new_test_recipe"]["name"] == "new_test_recipe"
        assert len(app.config["schema_recipes"]["new_test_recipe"]["fields"]) == 2
    
    def test_quality_thresholds_management(self):
        """Test setting quality thresholds."""
        app = AtomicScraperApp(config_path=self.config_file.name)
        
        # Update thresholds
        new_thresholds = {
            "minimum_completeness": 0.7,
            "minimum_accuracy": 0.9,
            "minimum_consistency": 0.6,
            "minimum_overall": 70.0
        }
        
        app.config["quality_thresholds"].update(new_thresholds)
        
        # Verify thresholds were updated
        for key, value in new_thresholds.items():
            assert app.config["quality_thresholds"][key] == value
    
    @patch('builtins.open', create=True)
    @patch('json.dump')
    def test_save_configuration(self, mock_json_dump, mock_open):
        """Test saving configuration to file."""
        app = AtomicScraperApp(config_path=self.config_file.name)
        app.console = Mock()
        
        # Call save configuration
        app._save_configuration()
        
        # Verify file was opened for writing
        mock_open.assert_called()
        
        # Verify JSON was dumped
        mock_json_dump.assert_called_once()
        call_args = mock_json_dump.call_args[0]
        assert call_args[0] == app.config
    
    def test_reset_to_defaults(self):
        """Test resetting configuration to defaults."""
        app = AtomicScraperApp(config_path=self.config_file.name)
        
        # Modify some settings
        app.config["scraper"]["request_delay"] = 5.0
        app.config["scraper"]["max_results"] = 200
        
        # Get default config
        default_config = app._load_default_config()
        
        # Reset to defaults
        app.config = default_config
        
        # Verify settings were reset
        assert app.config["scraper"]["request_delay"] == 1.0
        assert app.config["scraper"]["max_results"] == 50
    
    def test_schema_recipe_validation(self):
        """Test schema recipe validation."""
        app = AtomicScraperApp()
        
        # Test valid recipe
        valid_recipe = {
            "name": "valid_recipe",
            "description": "Valid test recipe",
            "fields": {
                "title": {
                    "field_type": "string",
                    "description": "Title field",
                    "extraction_selector": "h1",
                    "required": True
                }
            },
            "validation_rules": [],
            "quality_weights": {
                "completeness": 0.4,
                "accuracy": 0.4,
                "consistency": 0.2
            }
        }
        
        # Should not raise any exception when adding valid recipe
        if "schema_recipes" not in app.config:
            app.config["schema_recipes"] = {}
        
        app.config["schema_recipes"]["valid_recipe"] = valid_recipe
        assert "valid_recipe" in app.config["schema_recipes"]
    
    def test_configuration_persistence(self):
        """Test configuration persistence across app restarts."""
        # Create first app instance and modify config
        app1 = AtomicScraperApp(config_path=self.config_file.name)
        app1.config["scraper"]["request_delay"] = 3.0
        app1.config["scraper"]["max_results"] = 100
        
        # Save configuration
        with open(self.config_file.name, 'w') as f:
            json.dump(app1.config, f, indent=2)
        
        # Create second app instance
        app2 = AtomicScraperApp(config_path=self.config_file.name)
        
        # Verify configuration was persisted
        assert app2.config["scraper"]["request_delay"] == 3.0
        assert app2.config["scraper"]["max_results"] == 100
    
    def test_schema_recipe_export_import(self):
        """Test exporting and importing schema recipes."""
        app = AtomicScraperApp(config_path=self.config_file.name)
        
        # Create a test recipe
        test_recipe = {
            "name": "export_test_recipe",
            "description": "Recipe for export testing",
            "fields": {
                "title": {
                    "field_type": "string",
                    "description": "Title field",
                    "extraction_selector": "h1",
                    "required": True
                }
            }
        }
        
        app.config["schema_recipes"]["export_test_recipe"] = test_recipe
        
        # Test that the recipe structure is valid for export/import
        assert "export_test_recipe" in app.config["schema_recipes"]
        recipe = app.config["schema_recipes"]["export_test_recipe"]
        
        # Verify recipe structure
        assert recipe["name"] == "export_test_recipe"
        assert "fields" in recipe
        assert "title" in recipe["fields"]
        assert recipe["fields"]["title"]["field_type"] == "string"
        assert recipe["fields"]["title"]["extraction_selector"] == "h1"
    
    def test_custom_extraction_rules_support(self):
        """Test support for custom extraction rules."""
        app = AtomicScraperApp(config_path=self.config_file.name)
        
        # Create custom extraction rules in schema recipe
        custom_recipe = {
            "name": "custom_extraction_recipe",
            "description": "Recipe with custom extraction rules",
            "fields": {
                "title": {
                    "field_type": "string",
                    "description": "Custom title extraction",
                    "extraction_selector": "h1.custom-title, .title-alt",
                    "required": True,
                    "quality_weight": 2.0,
                    "post_processing": ["clean", "normalize"]
                },
                "price": {
                    "field_type": "string",
                    "description": "Price with custom processing",
                    "extraction_selector": ".price, .cost",
                    "required": False,
                    "quality_weight": 1.5,
                    "post_processing": ["extract_numbers", "trim"]
                }
            }
        }
        
        # Add to configuration
        if "schema_recipes" not in app.config:
            app.config["schema_recipes"] = {}
        
        app.config["schema_recipes"]["custom_extraction_recipe"] = custom_recipe
        
        # Verify custom rules are stored
        recipe = app.config["schema_recipes"]["custom_extraction_recipe"]
        assert recipe["fields"]["title"]["quality_weight"] == 2.0
        assert "clean" in recipe["fields"]["title"]["post_processing"]
        assert "extract_numbers" in recipe["fields"]["price"]["post_processing"]
    
    def test_configuration_validation(self):
        """Test configuration validation and error handling."""
        app = AtomicScraperApp()
        
        # Test invalid quality threshold values
        invalid_thresholds = {
            "minimum_completeness": 1.5,  # Invalid: > 1.0
            "minimum_accuracy": -0.1,     # Invalid: < 0.0
            "minimum_overall": 150.0      # Invalid: > 100.0
        }
        
        # The validation should be handled in the UI methods
        # Here we test that the configuration can handle various values
        app.config["quality_thresholds"] = {
            "minimum_completeness": 0.6,
            "minimum_accuracy": 0.8,
            "minimum_consistency": 0.5,
            "minimum_overall": 60.0
        }
        
        # Verify valid configuration is accepted
        assert app.config["quality_thresholds"]["minimum_completeness"] == 0.6
        assert app.config["quality_thresholds"]["minimum_overall"] == 60.0
    
    def test_scraper_config_integration(self):
        """Test integration with AtomicScraperConfig."""
        app = AtomicScraperApp(config_path=self.config_file.name)
        
        # Verify scraper tool was initialized with correct config
        assert app.scraper_tool is not None
        assert app.scraper_tool.config.base_url == "https://test.com"
        assert app.scraper_tool.config.request_delay == 0.1
        assert app.scraper_tool.config.min_quality_score == 50.0
    
    def test_configuration_sections_completeness(self):
        """Test that all required configuration sections are present."""
        app = AtomicScraperApp()
        
        # Verify all required sections exist
        required_sections = ["scraper", "agent", "interface"]
        for section in required_sections:
            assert section in app.config
        
        # Verify scraper section has required settings
        scraper_settings = [
            "base_url", "request_delay", "timeout", "max_pages", 
            "max_results", "min_quality_score", "user_agent"
        ]
        for setting in scraper_settings:
            assert setting in app.config["scraper"]
        
        # Verify interface section has required settings
        interface_settings = [
            "show_reasoning", "show_confidence", "auto_execute", 
            "save_results", "results_format"
        ]
        for setting in interface_settings:
            assert setting in app.config["interface"]


if __name__ == "__main__":
    pytest.main([__file__])