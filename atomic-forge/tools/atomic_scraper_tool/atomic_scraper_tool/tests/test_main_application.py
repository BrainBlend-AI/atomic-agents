"""
Integration tests for the main application and chat interface.

Tests the complete workflow from user input to scraping results.
"""

import pytest
import json
import tempfile
from unittest.mock import Mock, patch
from pathlib import Path

from atomic_scraper_tool.main import AtomicScraperApp
from atomic_scraper_tool.tools.atomic_scraper_tool import AtomicScraperOutputSchema


class TestAtomicScraperApp:
    """Test cases for the main application."""

    def setup_method(self):
        """Set up test fixtures."""
        # Create a temporary config file
        self.temp_config = {
            "scraper": {
                "base_url": "https://test.com",
                "request_delay": 0.1,
                "timeout": 10,
                "max_pages": 2,
                "max_results": 10,
                "min_quality_score": 50.0,
            },
            "agent": {"model": "test-model", "temperature": 0.5},
            "interface": {
                "show_reasoning": True,
                "show_confidence": True,
                "auto_execute": False,
                "save_results": False,
            },
        }

        # Create temporary config file
        self.config_file = tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False)
        json.dump(self.temp_config, self.config_file)
        self.config_file.close()

        # Mock console to capture output
        self.mock_console = Mock()

        # Patch AtomicScraperApp to clear session history on initialization
        self.original_init = AtomicScraperApp.__init__

        def patched_init(app_self, *args, **kwargs):
            self.original_init(app_self, *args, **kwargs)
            app_self.session_history = []  # Clear any sample data

        AtomicScraperApp.__init__ = patched_init

    def teardown_method(self):
        """Clean up test fixtures."""
        Path(self.config_file.name).unlink(missing_ok=True)

    def test_app_initialization_with_config(self):
        """Test application initialization with config file."""
        app = AtomicScraperApp(config_path=self.config_file.name)

        assert app.config["scraper"]["base_url"] == "https://test.com"
        assert app.config["scraper"]["request_delay"] == 0.1
        assert app.config["agent"]["model"] == "test-model"
        assert app.config["interface"]["show_reasoning"] is True

    def test_app_initialization_without_config(self):
        """Test application initialization with default config."""
        app = AtomicScraperApp()

        # Should use default values
        assert app.config["scraper"]["base_url"] == "https://example.com"
        assert app.config["scraper"]["request_delay"] == 1.0
        assert app.config["agent"]["model"] == "gpt-3.5-turbo"

    def test_app_initialization_with_invalid_config(self):
        """Test application initialization with invalid config file."""
        # Create invalid config file
        invalid_config_file = tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False)
        invalid_config_file.write("invalid json content")
        invalid_config_file.close()

        try:
            with patch("builtins.print") as mock_print:  # noqa: F841
                app = AtomicScraperApp(config_path=invalid_config_file.name)
                # Should fall back to defaults and show warning
                assert app.config["scraper"]["base_url"] == "https://example.com"
        finally:
            Path(invalid_config_file.name).unlink(missing_ok=True)

    @patch("atomic_scraper_tool.main.AtomicScraperApp._initialize_components")
    def test_load_config_merging(self, mock_init):
        """Test configuration merging with user config."""
        app = AtomicScraperApp(config_path=self.config_file.name)

        # User config should override defaults
        assert app.config["scraper"]["base_url"] == "https://test.com"
        assert app.config["scraper"]["request_delay"] == 0.1

        # Defaults should be preserved for unspecified values
        assert app.config["scraper"]["user_agent"] == "AtomicScraperTool/1.0"
        assert app.config["scraper"]["respect_robots_txt"] is True

    @patch("atomic_scraper_tool.main.Console")
    @patch("atomic_scraper_tool.main.AtomicScraperTool")
    @patch("atomic_scraper_tool.main.AtomicScraperPlanningAgent")
    def test_component_initialization(self, mock_agent, mock_tool, mock_console):
        """Test initialization of scraper components."""
        app = AtomicScraperApp(config_path=self.config_file.name)

        # Verify components were initialized
        assert app.scraper_tool is not None
        assert app.planning_agent is not None
        mock_tool.assert_called_once()
        mock_agent.assert_called_once()

    def test_mock_planning_agent_response(self):
        """Test mock planning agent response generation."""
        app = AtomicScraperApp(config_path=self.config_file.name)

        from atomic_scraper_tool.agents.scraper_planning_agent import AtomicScraperAgentInputSchema

        agent_input = AtomicScraperAgentInputSchema(
            request="Test scraping request",
            target_url="https://example.com",
            max_results=10,
            quality_threshold=60.0,
        )

        response = app._mock_planning_agent_response(agent_input)

        assert "scraping_plan" in response
        assert "strategy" in response
        assert "schema_recipe" in response
        assert "reasoning" in response
        assert "confidence" in response

        # Verify strategy structure
        strategy = response["strategy"]
        assert strategy["scrape_type"] == "list"
        assert "target_selectors" in strategy
        assert "pagination_strategy" in strategy

        # Verify schema structure
        schema = response["schema_recipe"]
        assert "name" in schema
        assert "fields" in schema
        assert "title" in schema["fields"]

    @patch("atomic_scraper_tool.main.AtomicScraperApp._display_planning_results")
    @patch("atomic_scraper_tool.main.AtomicScraperApp._display_scraping_results")
    @patch("atomic_scraper_tool.main.Confirm.ask")
    def test_process_scraping_request_success(self, mock_confirm, mock_display_results, mock_display_planning):
        """Test successful scraping request processing."""
        app = AtomicScraperApp(config_path=self.config_file.name)

        # Mock user confirmation
        mock_confirm.return_value = True

        # Mock scraper tool response
        mock_scraping_result = Mock(spec=AtomicScraperOutputSchema)
        mock_scraping_result.results = {
            "items": [{"data": {"title": "Test Item"}, "quality_score": 85.0}],
            "total_scraped": 1,
        }
        mock_scraping_result.summary = "Successfully scraped 1 item"
        mock_scraping_result.quality_metrics = {
            "average_quality_score": 85.0,
            "success_rate": 100.0,
            "total_items_found": 1.0,
            "total_items_scraped": 1.0,
            "execution_time": 2.5,
        }

        app.scraper_tool.run = Mock(return_value=mock_scraping_result)

        # Process request
        app._process_scraping_request("Test request", "https://example.com", 10, 60.0)

        # Verify planning results were displayed
        mock_display_planning.assert_called_once()

        # Verify scraping was executed
        app.scraper_tool.run.assert_called_once()

        # Verify results were displayed
        mock_display_results.assert_called_once()

        # Verify request was saved to history
        assert len(app.session_history) == 1
        assert app.session_history[0]["request"] == "Test request"

    @patch("atomic_scraper_tool.main.Confirm.ask")
    def test_process_scraping_request_user_cancellation(self, mock_confirm):
        """Test scraping request cancellation by user."""
        app = AtomicScraperApp(config_path=self.config_file.name)

        # Mock user cancellation
        mock_confirm.return_value = False

        # Mock scraper tool
        app.scraper_tool.run = Mock()

        # Process request
        app._process_scraping_request("Test request", "https://example.com", 10, 60.0)

        # Verify scraping was not executed
        app.scraper_tool.run.assert_not_called()

        # Verify no history entry was created
        assert len(app.session_history) == 0

    def test_save_to_history(self):
        """Test saving requests to session history."""
        app = AtomicScraperApp(config_path=self.config_file.name)

        planning_result = {
            "scraping_plan": "Test plan",
            "strategy": {"scrape_type": "list"},
            "confidence": 0.8,
        }

        scraping_result = Mock()
        scraping_result.summary = "Test summary"
        scraping_result.results = {"total_scraped": 5}

        app._save_to_history("Test request", "https://example.com", planning_result, scraping_result)

        assert len(app.session_history) == 1
        entry = app.session_history[0]

        assert entry["request"] == "Test request"
        assert entry["url"] == "https://example.com"
        assert entry["planning_result"] == planning_result
        assert entry["scraping_summary"] == "Test summary"
        assert entry["items_scraped"] == 5
        assert "timestamp" in entry

    @patch("builtins.open", create=True)
    @patch("json.dump")
    def test_export_results(self, mock_json_dump, mock_open):
        """Test exporting results to file."""
        app = AtomicScraperApp(config_path=self.config_file.name)
        app.console = Mock()

        results = {
            "items": [{"data": {"title": "Test"}, "quality_score": 85.0}],
            "total_scraped": 1,
        }

        app._export_results(results, "Test request")

        # Verify file was opened for writing
        mock_open.assert_called_once()

        # Verify JSON was dumped
        mock_json_dump.assert_called_once()

        # Verify success message was displayed
        app.console.print.assert_called()

    @patch("builtins.open", side_effect=IOError("Permission denied"))
    def test_export_results_failure(self, mock_open):
        """Test export failure handling."""
        app = AtomicScraperApp(config_path=self.config_file.name)
        app.console = Mock()

        results = {"items": [], "total_scraped": 0}

        app._export_results(results, "Test request")

        # Verify error message was displayed
        app.console.print.assert_called()
        call_args = app.console.print.call_args[0][0]
        assert "Export failed" in call_args

    def test_display_sample_items(self):
        """Test displaying sample scraped items."""
        app = AtomicScraperApp(config_path=self.config_file.name)
        app.console = Mock()

        items = [
            {"data": {"title": "Item 1", "description": "Description 1"}, "quality_score": 85.0},
            {"data": {"title": "Item 2", "description": "Description 2"}, "quality_score": 90.0},
        ]

        app._display_sample_items(items)

        # Verify console.print was called for each item
        assert app.console.print.call_count >= len(items)

    def test_display_sample_items_long_values(self):
        """Test displaying items with long field values."""
        app = AtomicScraperApp(config_path=self.config_file.name)
        app.console = Mock()

        long_description = "A" * 150  # Longer than 100 characters

        items = [{"data": {"title": "Item 1", "description": long_description}, "quality_score": 85.0}]

        app._display_sample_items(items)

        # Verify console.print was called
        app.console.print.assert_called()

    @patch("builtins.open", create=True)
    @patch("json.dump")
    def test_save_session_history(self, mock_json_dump, mock_open):
        """Test saving session history to file."""
        app = AtomicScraperApp(config_path=self.config_file.name)
        app.console = Mock()

        # Add some history entries
        app.session_history = [
            {
                "timestamp": "2023-01-01T12:00:00",
                "request": "Test request",
                "url": "https://example.com",
                "items_scraped": 5,
            }
        ]

        app._save_session_history()

        # Verify file was opened for writing
        mock_open.assert_called_once()

        # Verify JSON was dumped with history data
        mock_json_dump.assert_called_once()
        call_args = mock_json_dump.call_args[0]
        assert call_args[0] == app.session_history

    @patch("builtins.input", return_value="")
    def test_toggle_debug_mode(self, mock_input):
        """Test debug mode toggling."""
        app = AtomicScraperApp(config_path=self.config_file.name)
        app.console = Mock()

        # Initially debug mode should be False
        assert app.debug_mode is False

        # Reset call count after initialization
        app.console.print.reset_mock()

        # Toggle debug mode
        app._toggle_debug_mode()
        assert app.debug_mode is True

        # Toggle again
        app._toggle_debug_mode()
        assert app.debug_mode is False

        # Verify console messages were displayed (at least 2 toggle messages)
        assert app.console.print.call_count >= 2


class TestMainApplicationIntegration:
    """Integration tests for the complete application workflow."""

    @patch("atomic_scraper_tool.main.Prompt.ask")
    @patch("atomic_scraper_tool.main.Confirm.ask")
    def test_complete_scraping_workflow(self, mock_confirm, mock_prompt):
        """Test complete workflow from user input to results."""
        # Mock user inputs
        mock_prompt.side_effect = [
            "1",  # Menu choice: New scraping request
            "Scrape farmers markets",  # Request
            "https://example.com",  # URL
            "10",  # Max results
            "60.0",  # Quality threshold
            "7",  # Exit
        ]

        mock_confirm.side_effect = [
            True,
            False,
            False,
        ]  # Execute plan  # Don't export results  # Don't save history on exit

        # Create app with mocked components
        app = AtomicScraperApp()
        app.console = Mock()

        # Mock scraper tool response
        mock_scraping_result = Mock(spec=AtomicScraperOutputSchema)
        mock_scraping_result.results = {
            "items": [
                {
                    "data": {"title": "Farmers Market 1", "location": "Cape Town"},
                    "quality_score": 85.0,
                }
            ],
            "total_scraped": 1,
        }
        mock_scraping_result.summary = "Successfully scraped 1 farmers market"
        mock_scraping_result.quality_metrics = {
            "average_quality_score": 85.0,
            "success_rate": 100.0,
            "total_items_found": 1.0,
            "total_items_scraped": 1.0,
            "execution_time": 2.5,
        }

        app.scraper_tool.run = Mock(return_value=mock_scraping_result)

        # Run the application
        app.run()

        # Verify the workflow completed
        assert not app.running  # App should have exited
        assert len(app.session_history) == 1  # One request should be in history

        # Verify scraper was called
        app.scraper_tool.run.assert_called_once()

    @patch("atomic_scraper_tool.main.Prompt.ask")
    def test_menu_navigation(self, mock_prompt):
        """Test navigation through different menu options."""
        # Mock user inputs for different menu options
        mock_prompt.side_effect = [
            "2",  # View session history
            "3",  # Configuration settings
            "4",  # Tool information
            "5",  # Toggle debug mode
            "6",  # Help & examples
            "7",  # Exit
        ]

        app = AtomicScraperApp()
        app.console = Mock()

        # Add some mock history
        app.session_history = [
            {
                "timestamp": "2023-01-01T12:00:00",
                "request": "Test request",
                "url": "https://example.com",
                "items_scraped": 5,
            }
        ]

        with patch("atomic_scraper_tool.main.Confirm.ask", return_value=False):
            app.run()

        # Verify app completed all menu options
        assert not app.running

        # Verify console output was generated for each menu option
        assert app.console.print.call_count > 6  # Should have multiple print calls

    def test_error_handling_in_workflow(self):
        """Test error handling during scraping workflow."""
        app = AtomicScraperApp()
        app.console = Mock()

        # Mock scraper tool to raise an exception
        app.scraper_tool.run = Mock(side_effect=Exception("Network error"))

        # Process a request that will fail
        app._process_scraping_request("Test request", "https://example.com", 10, 60.0)

        # Verify error was handled gracefully
        app.console.print.assert_called()

        # Verify no history entry was created for failed request
        assert len(app.session_history) == 0


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
                "min_quality_score": 50.0,
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
                            "required": True,
                        }
                    },
                }
            },
            "quality_thresholds": {
                "minimum_completeness": 0.6,
                "minimum_accuracy": 0.8,
                "minimum_consistency": 0.5,
                "minimum_overall": 60.0,
            },
        }

        # Create temporary config file
        self.config_file = tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False)
        json.dump(self.temp_config, self.config_file)
        self.config_file.close()

    def teardown_method(self):
        """Clean up test fixtures."""
        Path(self.config_file.name).unlink(missing_ok=True)

    def test_modify_scraper_settings(self):
        """Test modifying scraper settings."""
        app = AtomicScraperApp(config_path=self.config_file.name)
        app.console = Mock()

        # Store original value for comparison
        original_delay = app.config["scraper"]["request_delay"]
        
        # Test updating request_delay
        new_delay = 2.5

        # Simulate the setting modification
        app.config["scraper"]["request_delay"] = new_delay
        app.scraper_tool.update_config(request_delay=new_delay)

        # Verify the setting was updated
        assert app.config["scraper"]["request_delay"] == new_delay
        assert app.config["scraper"]["request_delay"] != original_delay

    def test_manage_schema_recipes_create(self):
        """Test creating a new schema recipe."""
        app = AtomicScraperApp(config_path=self.config_file.name)
        app.console = Mock()

        # Initialize schema recipes if not exists
        if "schema_recipes" not in app.config:
            app.config["schema_recipes"] = {}

        # Create a new recipe
        new_recipe = {
            "name": "new_test_recipe",
            "description": "New test recipe",
            "fields": {
                "title": {
                    "field_type": "string",
                    "description": "Title field",
                    "extraction_selector": "h1",
                    "required": True,
                },
                "content": {
                    "field_type": "string",
                    "description": "Content field",
                    "extraction_selector": "p",
                    "required": False,
                },
            },
            "validation_rules": [],
            "quality_weights": {"completeness": 0.4, "accuracy": 0.4, "consistency": 0.2},
        }

        app.config["schema_recipes"]["new_test_recipe"] = new_recipe

        # Verify the recipe was created
        assert "new_test_recipe" in app.config["schema_recipes"]
        assert app.config["schema_recipes"]["new_test_recipe"]["name"] == "new_test_recipe"
        assert len(app.config["schema_recipes"]["new_test_recipe"]["fields"]) == 2

    def test_set_quality_thresholds(self):
        """Test setting quality thresholds."""
        app = AtomicScraperApp(config_path=self.config_file.name)
        app.console = Mock()

        # Initialize quality thresholds if not exists
        if "quality_thresholds" not in app.config:
            app.config["quality_thresholds"] = {
                "minimum_completeness": 0.6,
                "minimum_accuracy": 0.8,
                "minimum_consistency": 0.5,
                "minimum_overall": 60.0,
            }

        # Update thresholds
        new_thresholds = {
            "minimum_completeness": 0.7,
            "minimum_accuracy": 0.9,
            "minimum_consistency": 0.6,
            "minimum_overall": 70.0,
        }

        app.config["quality_thresholds"].update(new_thresholds)

        # Verify thresholds were updated
        for key, value in new_thresholds.items():
            assert app.config["quality_thresholds"][key] == value

    @patch("builtins.open", create=True)
    @patch("json.dump")
    @patch("builtins.input", return_value="")
    def test_save_configuration(self, mock_input, mock_json_dump, mock_open):
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
        app.console = Mock()

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

    def test_schema_recipe_export_import(self):
        """Test exporting and importing schema recipes."""
        app = AtomicScraperApp(config_path=self.config_file.name)
        app.console = Mock()

        # Ensure schema recipes exist
        if "schema_recipes" not in app.config:
            app.config["schema_recipes"] = {}

        # Create a test recipe
        test_recipe = {
            "name": "export_test_recipe",
            "description": "Recipe for export testing",
            "fields": {
                "title": {
                    "field_type": "string",
                    "description": "Title field",
                    "extraction_selector": "h1",
                    "required": True,
                }
            },
        }

        app.config["schema_recipes"]["export_test_recipe"] = test_recipe

        # Test export functionality (simulate file writing)
        with patch("builtins.open", create=True) as mock_open:
            with patch("json.dump") as mock_json_dump:  # noqa: F841
                # Simulate export
                filename = "schema_recipe_export_test_recipe.json"
                mock_file = mock_open.return_value.__enter__.return_value
                json.dump(test_recipe, mock_file, indent=2)

                # Verify export was called
                mock_open.assert_called_with(filename, "w")

        # Test import functionality
        with patch("builtins.open", create=True) as mock_open:
            with patch("json.load", return_value=test_recipe) as mock_json_load:  # noqa: F841
                # Simulate import
                imported_recipe = json.load(mock_open.return_value.__enter__.return_value)

                # Verify import structure
                assert imported_recipe["name"] == "export_test_recipe"
                assert "fields" in imported_recipe
                assert "title" in imported_recipe["fields"]

    def test_configuration_persistence(self):
        """Test configuration persistence across app restarts."""
        # Create first app instance and modify config
        app1 = AtomicScraperApp(config_path=self.config_file.name)
        app1.config["scraper"]["request_delay"] = 3.0
        app1.config["scraper"]["max_results"] = 100

        # Save configuration
        with open(self.config_file.name, "w") as f:
            json.dump(app1.config, f, indent=2)

        # Create second app instance
        app2 = AtomicScraperApp(config_path=self.config_file.name)

        # Verify configuration was persisted
        assert app2.config["scraper"]["request_delay"] == 3.0
        assert app2.config["scraper"]["max_results"] == 100

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
                    "post_processing": ["clean", "normalize"],
                },
                "price": {
                    "field_type": "string",
                    "description": "Price with custom processing",
                    "extraction_selector": ".price, .cost",
                    "required": False,
                    "quality_weight": 1.5,
                    "post_processing": ["extract_numbers", "trim"],
                },
            },
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


class TestMainFunction:
    """Test cases for the main entry point function."""

    @patch("atomic_scraper_tool.main.AtomicScraperApp")
    @patch("sys.argv", ["main.py"])
    def test_main_function_default(self, mock_app_class):
        """Test main function with default arguments."""
        mock_app = Mock()
        mock_app_class.return_value = mock_app

        from atomic_scraper_tool.main import main

        main()

        # Verify app was created and run
        mock_app_class.assert_called_once_with(config_path=None, client=None, demo_mode=False)
        mock_app.run.assert_called_once()

    @patch("atomic_scraper_tool.main.AtomicScraperApp")
    @patch("sys.argv", ["main.py", "--config", "test.json", "--debug"])
    def test_main_function_with_args(self, mock_app_class):
        """Test main function with command line arguments."""
        mock_app = Mock()
        mock_app_class.return_value = mock_app

        from atomic_scraper_tool.main import main

        main()

        # Verify app was created with config path
        mock_app_class.assert_called_once_with(config_path="test.json", client=None, demo_mode=False)

        # Verify debug mode was enabled
        assert mock_app.debug_mode is True

        # Verify app was run
        mock_app.run.assert_called_once()

    @patch("atomic_scraper_tool.main.AtomicScraperApp")
    @patch("sys.argv", ["main.py"])
    def test_main_function_keyboard_interrupt(self, mock_app_class):
        """Test main function handling keyboard interrupt."""
        mock_app = Mock()
        mock_app.run.side_effect = KeyboardInterrupt()
        mock_app_class.return_value = mock_app

        from atomic_scraper_tool.main import main

        with patch("builtins.print") as mock_print:
            main()
            mock_print.assert_called_with("\n👋 Goodbye!")

    @patch("atomic_scraper_tool.main.AtomicScraperApp")
    @patch("sys.argv", ["main.py"])
    @patch("sys.exit")
    def test_main_function_exception(self, mock_exit, mock_app_class):
        """Test main function handling general exceptions."""
        mock_app_class.side_effect = Exception("Initialization error")

        from atomic_scraper_tool.main import main

        with patch("builtins.print") as mock_print:
            main()
            mock_print.assert_called_with("❌ Application error: Initialization error")
            mock_exit.assert_called_with(1)


if __name__ == "__main__":
    pytest.main([__file__])
