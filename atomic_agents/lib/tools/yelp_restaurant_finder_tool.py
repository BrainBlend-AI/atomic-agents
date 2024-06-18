import os
import requests
from pydantic import BaseModel, Field
from typing import List, Optional
from rich.console import Console
from rich.table import Table
from enum import Enum

from atomic_agents.agents.base_chat_agent import BaseAgentIO
from atomic_agents.lib.tools.base import BaseTool, BaseToolConfig

################
# INPUT SCHEMA #
################
class YelpCategory(Enum):
    ITALIAN = "italian"
    MEXICAN = "mexican"
    PIZZA = "pizza"
    SUSHI = "sushi"
    CHINESE = "chinese"
    INDIAN = "indian"
    THAI = "thai"
    FRENCH = "french"
    GREEK = "greek"
    JAPANESE = "japanese"
    KOREAN = "korean"
    VIETNAMESE = "vietnamese"
    AMERICAN = "american"
    BBQ = "bbq"
    BURGERS = "burgers"
    SEAFOOD = "seafood"
    STEAKHOUSES = "steakhouses"
    VEGAN = "vegan"
    VEGETARIAN = "vegetarian"

class PriceRange(Enum):
    ONE = "1"
    TWO = "2"
    THREE = "3"
    FOUR = "4"

class YelpSearchToolSchema(BaseAgentIO):
    location: str = Field(..., description="Location to search for food.")
    term: Optional[str] = Field(None, description="Search term (e.g., 'pizza', 'sushi').")
    categories: Optional[List[YelpCategory]] = Field(None, description="Categories to filter by (e.g., 'italian, mexican').")
    price: Optional[List[PriceRange]] = Field(None, description="Price range to filter by (e.g., '1', '2', '3', '4'). Can be multiple. 1 is cheap. 2 and 3 are mid-range. 4 is the most high-end.")
    open_now: Optional[bool] = Field(False, description="Filter for businesses that are open now.")
    sort_by: Optional[str] = Field("best_match", description="Sort by criteria (e.g., 'best_match', 'rating', 'review_count', 'distance').")
    limit: Optional[int] = Field(10, description="Number of results to return.")

    class Config:
        title = "YelpSearchTool"
        description = "Tool for searching for food using the Yelp API. Returns a list of businesses with details such as name, rating, and address."
        json_schema_extra = {
            "title": title,
            "description": description
        }

####################
# OUTPUT SCHEMA(S) #
####################
class YelpSearchResultSchema(BaseAgentIO):
    name: str
    url: str
    rating: float
    review_count: int
    address: str
    phone: Optional[str] = None
    categories: List[str]

class YelpSearchToolOutputSchema(BaseAgentIO):
    results: List[YelpSearchResultSchema]
    
    class Config:
        title = "YelpSearchToolOutput"
        description = "Output schema for the YelpSearchTool, containing a list of search results with details such as name, rating, and address."
        json_schema_extra = {
            "title": title,
            "description": description
        }

##############
# TOOL LOGIC #
##############
class YelpSearchToolConfig(BaseToolConfig):
    api_key: str = ""
    max_results: int = 10

class YelpSearchTool(BaseTool):
    """
    Tool for performing searches using the Yelp API based on the provided queries.

    Attributes:
        input_schema (YelpSearchToolSchema): The schema for the input data.
        output_schema (YelpSearchToolOutputSchema): The schema for the output data.
        api_key (str): The API key for the Yelp API.
        max_results (int): The maximum number of search results to return.
    """
    input_schema = YelpSearchToolSchema
    output_schema = YelpSearchToolOutputSchema

    def __init__(self, config: YelpSearchToolConfig = YelpSearchToolConfig()):
        """
        Initializes the YelpSearchTool.

        Args:
            config (YelpSearchToolConfig): Configuration for the tool, including API key, max results, and optional title and description overrides.
        """
        super().__init__(config)
        self.api_key = config.api_key
        self.max_results = config.max_results

    def run(self, params: YelpSearchToolSchema) -> YelpSearchToolOutputSchema:
        """
        Runs the YelpSearchTool with the given parameters.

        Args:
            params (YelpSearchToolSchema): The input parameters for the tool, adhering to the input schema.
            max_results (Optional[int]): The maximum number of search results to return.

        Returns:
            YelpSearchToolOutputSchema: The output of the tool, adhering to the output schema.

        Raises:
            ValueError: If the API key is not provided.
            Exception: If the request to Yelp API fails.
        """
        if not self.api_key:
            raise ValueError("API key is required to use the Yelp API.")

        # Prepare the query parameters
        query_params = {
            "location": params.location,
            "term": params.term,
            "categories": ",".join([category.value for category in params.categories]) if params.categories else None,
            "price": ",".join([price.value for price in params.price]) if params.price else None,
            "sort_by": params.sort_by,
            "limit": self.max_results,
            "open_now": params.open_now
        }

        # Make the GET request
        headers = {
            'Authorization': f'Bearer {self.api_key}'
        }
        response = requests.get("https://api.yelp.com/v3/businesses/search", headers=headers, params=query_params)

        # Check if the request was successful
        if response.status_code != 200:
            raise Exception(f"Failed to fetch search results: {response.status_code} {response.reason}")

        results = response.json().get('businesses', [])

        # Convert to output schema format
        output_results = [
            YelpSearchResultSchema(
                name=result['name'],
                url=result['url'].split('?')[0],
                rating=result['rating'],
                review_count=result['review_count'],
                address=", ".join(result['location']['display_address']),
                phone=result.get('display_phone'),
                categories=[category['title'] for category in result['categories']]
            )
            for result in results
        ]

        return YelpSearchToolOutputSchema(results=output_results)

#################
# EXAMPLE USAGE #
#################
if __name__ == "__main__":
    rich_console = Console()
    search_tool_instance = YelpSearchTool(config=YelpSearchToolConfig(api_key=os.getenv('YELP_API_KEY'), max_results=10))
    
    search_input = YelpSearchTool.input_schema(
        location="Diepenbeek, Belgium",
        term="",
        categories=[YelpCategory.PIZZA],
        price=[PriceRange.ONE, PriceRange.TWO, PriceRange.THREE, PriceRange.FOUR],
        sort_by="best_match"
    )

    output = search_tool_instance.run(search_input)
    
    rich_console.print(output)