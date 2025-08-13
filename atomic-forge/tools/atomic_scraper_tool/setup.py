from setuptools import setup, find_packages

setup(
    name="atomic-scraper-tool",
    version="0.1.0",
    description="AI-powered web scraping tool with intelligent strategy planning and structured data extraction",
    packages=find_packages(),
    install_requires=[
        "atomic-agents>=1.1.11",
        "requests>=2.32.3",
        "beautifulsoup4>=4.12.3",
        "markdownify>=0.9.0",
        "pydantic>=2.11.0",
        "instructor>=1.9.0",
        "openai>=1.35.12",
        "rich>=13.7.1",
        "python-dotenv>=1.0.0",
        "lxml>=5.3.0",
        "readability-lxml>=0.8.1",
        "lxml-html-clean>=0.4.0",
    ],
    python_requires=">=3.11",
)