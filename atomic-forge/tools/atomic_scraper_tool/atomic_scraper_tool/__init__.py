"""
Atomic Scraper Tool - Next-Generation Intelligent Web Scraping

AI-powered scraping tool built on the atomic agents framework that provides
natural language interface and dynamic strategy generation for effortless data extraction.
"""

__version__ = "1.0.0"
__author__ = "Atomic Scraper Tool"

# Import main components
from atomic_scraper_tool.tools.atomic_scraper_tool import AtomicScraperTool
from atomic_scraper_tool.config.scraper_config import AtomicScraperConfig, ScraperConfiguration
from atomic_scraper_tool.models.base_models import ScrapingStrategy, ScrapedItem, ScrapingResult
from atomic_scraper_tool.models.schema_models import SchemaRecipe, FieldDefinition

__all__ = [
    "AtomicScraperTool", 
    "AtomicScraperConfig",
    "ScraperConfiguration",
    "ScrapingStrategy",
    "ScrapedItem", 
    "ScrapingResult",
    "SchemaRecipe",
    "FieldDefinition"
]